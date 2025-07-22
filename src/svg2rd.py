#!/usr/bin/env python3
import sys
import argparse
from xml.etree import ElementTree as ET
from svg.path import parse_path, Line
import math
import re
from .ruida import Ruida, RuidaLayer

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

def hex_to_rgb(hex_color):
    """Converts a hex color string (e.g., '#RRGGBB') to an (R, G, B) tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def parse_transform(transform_str):
    """Parses an SVG transform string to get scale and translate values."""
    sx, sy, tx, ty = 1.0, 1.0, 0.0, 0.0
    if not transform_str:
        return sx, sy, tx, ty

    # This is a simplified parser for "scale(...) translate(...)" or matrix forms.
    scale_match = re.search(r'scale\(([^,)]+)(?:,([^)]+))?\)', transform_str)
    if scale_match:
        sx = float(scale_match.group(1))
        sy = float(scale_match.group(2)) if scale_match.group(2) else sx

    translate_match = re.search(r'translate\(([^,)]+)(?:,([^)]+))?\)', transform_str)
    if translate_match:
        tx = float(translate_match.group(1))
        ty = float(translate_match.group(2)) if translate_match.group(2) else 0.0
        
    matrix_match = re.search(r'matrix\(([^,)]+),([^,)]+),([^,)]+),([^,)]+),([^,)]+),([^,)]+)\)', transform_str)
    if matrix_match:
        sx = float(matrix_match.group(1))
        # Ignoring skew factors matrix_match.group(2) and matrix_match.group(3)
        sy = float(matrix_match.group(4))
        tx = float(matrix_match.group(5))
        ty = float(matrix_match.group(6))

    return sx, sy, tx, ty

def extract_paths_recursive(element, parent_transform, global_scale, global_ox, global_oy, h):
    """
    Recursively extracts paths from SVG elements, grouping them by stroke color.
    Returns a dictionary: {'#RRGGBB': [path1, path2, ...]}
    """
    paths = {}
    transform_str = element.get("transform", "")
    lsx, lsy, ltx, lty = parse_transform(transform_str)
    psx, psy, ptx, pty = parent_transform
    csx, csy = psx * lsx, psy * lsy
    ctx, cty = psx * ltx + ptx, psy * lty + pty

    # 1) <path> elements - This is the primary target for our raster SVGs
    for p in element.findall("./svg:path", SVG_NS):
        d = p.get("d")
        if not d:
            continue
        
        stroke_color = p.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []

        segs = parse_path(d)
        for seg in segs:
            # For our raster format, we only care about simple lines.
            # Each Line object from svg.path becomes a two-point path for Ruida.
            if isinstance(seg, Line):
                path = []
                for z in [seg.start, seg.end]:
                    x, y = z.real, z.imag
                    
                    # Apply combined local transform
                    x_transformed = x * csx + ctx
                    y_transformed = y * csy + cty
                    
                    # Apply global transform for final positioning
                    mx = x_transformed * global_scale + global_ox
                    my = (h - y_transformed) * global_scale + global_oy
                    path.append([mx, my])
                
                if path:
                    paths[stroke_color].append(path)

    # Recurse into <g> elements
    for g in element.findall("./svg:g", SVG_NS):
        sub_paths = extract_paths_recursive(g, (csx, csy, ctx, cty), global_scale, global_ox, global_oy, h)
        for color, path_list in sub_paths.items():
            if color not in paths:
                paths[color] = []
            paths[color].extend(path_list)
            
    # Note: Support for other shapes like <rect>, <circle> is omitted for clarity,
    # as the primary goal is to support the raster SVGs from img2svg.py.
        
    return paths

def extract_paths(root):
    vb_str = root.get("viewBox")
    if not vb_str:
        # Fallback for SVGs without a viewBox (e.g. from potrace)
        w_str = root.get("width")
        h_str = root.get("height")
        if not w_str or not h_str:
             raise ValueError("SVG has no viewBox, width, or height attributes.")
        w = float(re.sub(r'[^\d.]', '', w_str))
        h = float(re.sub(r'[^\d.]', '', h_str))
    else:
        vb = vb_str.split()
        _, _, w, h = map(float, vb)

    scale = 50.0 / max(w, h)
    ox = (50 - w * scale) / 2
    oy = (50 - h * scale) / 2

    initial_transform = (1.0, 1.0, 0.0, 0.0)
    return extract_paths_recursive(root, initial_transform, scale, ox, oy, h)

def svg_to_rd(svg_file, rd_file, min_power=10, max_power=80, speed=300):
    try:
        tree = ET.parse(svg_file)
    except ET.ParseError as e:
        print(f"Error parsing SVG file: {e}")
        return
        
    root = tree.getroot()
    paths_by_color = extract_paths(root)
    
    if not paths_by_color:
        print("Warning: No vector paths found in the SVG. The output file will be empty.")
        # Create an empty file
        with open(rd_file, "wb") as f:
            f.write(b'')
        return

    rd = Ruida()
    # Sort colors from lightest to darkest to engrave lighter areas first.
    # This is generally better for wood and other materials.
    sorted_colors = sorted(paths_by_color.keys(), key=lambda k: sum(hex_to_rgb(k)))

    print("Processing SVG layers:")
    for color_hex in sorted_colors:
        paths = paths_by_color[color_hex]
        if not paths:
            continue

        rgb = hex_to_rgb(color_hex)
        # Standard luminance calculation for grayscale value
        gray_value = int(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])

        # Map the grayscale value (0-255) to the laser power range.
        # Darker colors (lower gray_value) get higher power.
        power_range = max_power - min_power
        # Normalize gray value (0=black, 1=white)
        normalized_gray = gray_value / 255.0
        # Invert it so 1=black, 0=white
        inverted_gray = 1.0 - normalized_gray
        # Calculate power, ensuring it doesn't exceed max_power due to float precision
        power = min(max_power, min_power + (inverted_gray * power_range))
        
        print(f"- Layer Color: {color_hex} (Gray: {gray_value}) -> Power: {power:.1f}%, Speed: {speed}mm/s")

        layer = RuidaLayer(paths=paths, speed=speed, power=[power, power], color=list(rgb))
        rd.addLayer(layer)

    with open(rd_file, "wb") as f:
        rd.write(f)
    print(f"\nSuccessfully wrote {len(paths_by_color)} layer(s) to {rd_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Convert a multi-layer grayscale SVG to a Ruida .rd file with variable power.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_file', help='Path to the input SVG file.')
    parser.add_argument('output_file', help='Path to the output .rd file.')
    parser.add_argument('--min_power', type=float, default=10.0, help='Laser power (percent) for the lightest shade (white is ignored).')
    parser.add_argument('--max_power', type=float, default=70.0, help='Laser power (percent) for the darkest shade (black).')
    parser.add_argument('--speed', type=float, default=300.0, help='Engraving speed (mm/s) for all layers.')
    
    args = parser.parse_args()

    if not args.input_file.lower().endswith(".svg"):
        print("Error: This script now only directly supports .svg files.", file=sys.stderr)
        print("Please convert your file to SVG first using the appropriate script (e.g., img2svg.py).", file=sys.stderr)
        sys.exit(1)

    svg_to_rd(args.input_file, args.output_file, args.min_power, args.max_power, args.speed)

if __name__=="__main__":
    main()