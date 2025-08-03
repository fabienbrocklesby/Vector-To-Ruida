#!/usr/bin/env python3
import sys
import argparse
from xml.etree import ElementTree as ET
from svg.path import parse_path, Line
import math
import re
from .ruida import Ruida, RuidaLayer

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

def hex_to_rgb(color_str):
    """Converts a color string (hex or named) to an (R, G, B) tuple."""
    
    # Basic dictionary of SVG color names.
    COLOR_NAME_TO_HEX = {
        "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000",
        "blue": "#0000ff", "yellow": "#ffff00", "cyan": "#00ffff", "magenta": "#ff00ff",
        "silver": "#c0c0c0", "gray": "#808080", "maroon": "#800000", "olive": "#808000",
        "purple": "#800080", "teal": "#008080", "navy": "#000080", "none": "#ffffff" # Treat 'none' as white
    }
    
    color_str = color_str.lower().strip()
    
    if color_str in COLOR_NAME_TO_HEX:
        hex_color = COLOR_NAME_TO_HEX[color_str]
    else:
        hex_color = color_str

    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    if len(hex_color) != 6:
        # Fallback for invalid color formats
        return (255, 255, 255) # Return white for any parsing error
    try:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255) # Return white if conversion fails

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
            if isinstance(seg, Line):
                # Handle straight lines directly
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
            else:
                # Handle curves (QuadraticBezier, CubicBezier, Arc) by approximating with line segments
                # Use 20 segments for smooth approximation of curves
                num_segments = 20
                path = []
                
                for i in range(num_segments + 1):
                    t = i / num_segments
                    try:
                        # Get point along the curve at parameter t
                        point = seg.point(t)
                        x, y = point.real, point.imag
                        
                        # Apply combined local transform
                        x_transformed = x * csx + ctx
                        y_transformed = y * csy + cty
                        
                        # Apply global transform for final positioning
                        mx = x_transformed * global_scale + global_ox
                        my = (h - y_transformed) * global_scale + global_oy
                        path.append([mx, my])
                    except (AttributeError, ValueError):
                        # Skip segments that don't support point() method or have errors
                        continue
                
                if len(path) >= 2:  # Only add paths with at least 2 points
                    paths[stroke_color].append(path)

    # 2) <line> elements
    for line in element.findall("./svg:line", SVG_NS):
        stroke_color = line.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []
        
        x1 = float(line.get("x1", 0))
        y1 = float(line.get("y1", 0))
        x2 = float(line.get("x2", 0))
        y2 = float(line.get("y2", 0))
        
        # Apply combined local transform
        x1_transformed = x1 * csx + ctx
        y1_transformed = y1 * csy + cty
        x2_transformed = x2 * csx + ctx
        y2_transformed = y2 * csy + cty
        
        # Apply global transform for final positioning
        mx1 = x1_transformed * global_scale + global_ox
        my1 = (h - y1_transformed) * global_scale + global_oy
        mx2 = x2_transformed * global_scale + global_ox
        my2 = (h - y2_transformed) * global_scale + global_oy
        
        paths[stroke_color].append([[mx1, my1], [mx2, my2]])

    # 3) <rect> elements
    for rect in element.findall("./svg:rect", SVG_NS):
        stroke_color = rect.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []
        
        x = float(rect.get("x", 0))
        y = float(rect.get("y", 0))
        width = float(rect.get("width", 0))
        height = float(rect.get("height", 0))
        
        # Create rectangle as four lines
        corners = [
            [x, y], [x + width, y], [x + width, y + height], [x, y + height], [x, y]
        ]
        
        path = []
        for corner in corners:
            cx, cy = corner
            # Apply combined local transform
            cx_transformed = cx * csx + ctx
            cy_transformed = cy * csy + cty
            
            # Apply global transform for final positioning
            mx = cx_transformed * global_scale + global_ox
            my = (h - cy_transformed) * global_scale + global_oy
            path.append([mx, my])
        
        paths[stroke_color].append(path)

    # 4) <circle> elements
    for circle in element.findall("./svg:circle", SVG_NS):
        stroke_color = circle.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []
        
        cx = float(circle.get("cx", 0))
        cy = float(circle.get("cy", 0))
        r = float(circle.get("r", 0))
        
        # Approximate circle with 36 line segments (10 degree increments)
        num_segments = 36
        path = []
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            
            # Apply combined local transform
            x_transformed = x * csx + ctx
            y_transformed = y * csy + cty
            
            # Apply global transform for final positioning
            mx = x_transformed * global_scale + global_ox
            my = (h - y_transformed) * global_scale + global_oy
            path.append([mx, my])
        
        paths[stroke_color].append(path)

    # 5) <ellipse> elements
    for ellipse in element.findall("./svg:ellipse", SVG_NS):
        stroke_color = ellipse.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []
        
        cx = float(ellipse.get("cx", 0))
        cy = float(ellipse.get("cy", 0))
        rx = float(ellipse.get("rx", 0))
        ry = float(ellipse.get("ry", 0))
        
        # Approximate ellipse with 36 line segments
        num_segments = 36
        path = []
        for i in range(num_segments + 1):
            angle = 2 * math.pi * i / num_segments
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            
            # Apply combined local transform
            x_transformed = x * csx + ctx
            y_transformed = y * csy + cty
            
            # Apply global transform for final positioning
            mx = x_transformed * global_scale + global_ox
            my = (h - y_transformed) * global_scale + global_oy
            path.append([mx, my])
        
        paths[stroke_color].append(path)

    # 6) <polyline> elements
    for polyline in element.findall("./svg:polyline", SVG_NS):
        stroke_color = polyline.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []
        
        points_str = polyline.get("points", "")
        if points_str:
            # Parse points string like "10,90 20,80 30,90 40,80 50,90"
            point_pairs = points_str.strip().split()
            path = []
            for point_pair in point_pairs:
                if ',' in point_pair:
                    x, y = map(float, point_pair.split(','))
                    
                    # Apply combined local transform
                    x_transformed = x * csx + ctx
                    y_transformed = y * csy + cty
                    
                    # Apply global transform for final positioning
                    mx = x_transformed * global_scale + global_ox
                    my = (h - y_transformed) * global_scale + global_oy
                    path.append([mx, my])
            
            if path:
                paths[stroke_color].append(path)

    # 7) <polygon> elements
    for polygon in element.findall("./svg:polygon", SVG_NS):
        stroke_color = polygon.get("stroke", "#000000")
        if stroke_color not in paths:
            paths[stroke_color] = []
        
        points_str = polygon.get("points", "")
        if points_str:
            # Parse points string and close the polygon
            point_pairs = points_str.strip().split()
            path = []
            for point_pair in point_pairs:
                if ',' in point_pair:
                    x, y = map(float, point_pair.split(','))
                    
                    # Apply combined local transform
                    x_transformed = x * csx + ctx
                    y_transformed = y * csy + cty
                    
                    # Apply global transform for final positioning
                    mx = x_transformed * global_scale + global_ox
                    my = (h - y_transformed) * global_scale + global_oy
                    path.append([mx, my])
            
            # Close the polygon by adding the first point at the end
            if path and len(path) > 2:
                path.append(path[0])
                paths[stroke_color].append(path)

    # Recurse into <g> elements
    for g in element.findall("./svg:g", SVG_NS):
        sub_paths = extract_paths_recursive(g, (csx, csy, ctx, cty), global_scale, global_ox, global_oy, h)
        for color, path_list in sub_paths.items():
            if color not in paths:
                paths[color] = []
            paths[color].extend(path_list)
            
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
    total_layers = len([color for color in sorted_colors if paths_by_color[color]])
    current_layer = 0
    
    for color_hex in sorted_colors:
        paths = paths_by_color[color_hex]
        if not paths:
            continue
            
        current_layer += 1
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
        
        print(f"- Layer {current_layer}/{total_layers}: Color {color_hex} (Gray: {gray_value}) -> Power: {power:.1f}%, Speed: {speed}mm/s")
        print(f"  Processing {len(paths)} path segments...", end=" ", flush=True)

        layer = RuidaLayer(paths=paths, speed=speed, power=[power, power], color=list(rgb))
        rd.addLayer(layer)
        print("Done.")

    print("Writing RD file...", end=" ", flush=True)

    print("Writing RD file...", end=" ", flush=True)
    with open(rd_file, "wb") as f:
        rd.write(f)
    print("Done.")
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