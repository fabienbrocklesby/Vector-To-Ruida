#!/usr/bin/env python3
import argparse
import os
import sys
from src import dxf2svg, pdf2svg, img2svg, svg2rd

def main():
    parser = argparse.ArgumentParser(
        description='Universal converter to .rd files for Ruida laser cutters.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_file', help='Path to the input file (DXF, PDF, PNG, JPG, SVG).')
    parser.add_argument('--output_file', '-o', help='Path to the output .rd file. Defaults to input file with .rd extension.')

    # SVG to RD specific arguments
    parser.add_argument('--min_power', type=float, default=10.0, help='[SVG->RD] Laser power for the lightest shade.')
    parser.add_argument('--max_power', type=float, default=70.0, help='[SVG->RD] Laser power for the darkest shade.')
    parser.add_argument('--speed', type=float, default=300.0, help='[SVG->RD] Engraving speed (mm/s).')

    # Image to SVG specific arguments
    parser.add_argument('--num_colors', type=int, default=16, help='[IMG->SVG] Number of shades to quantize the image to.')
    parser.add_argument('--img_scale', type=float, default=0.5, help='[IMG->SVG] Factor by which to scale the image before processing.')

    args = parser.parse_args()

    input_path = args.input_file
    output_path = args.output_file
    
    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".rd"

    _, ext = os.path.splitext(input_path)
    ext = ext.lower()

    temp_svg_path = None

    try:
        if ext == '.dxf':
            print(f"Converting DXF to SVG...")
            temp_svg_path = os.path.splitext(input_path)[0] + "_temp.svg"
            dxf2svg.dxf_to_svg(input_path, temp_svg_path)
            svg_input = temp_svg_path
        elif ext == '.pdf':
            print(f"Converting PDF to SVG...")
            temp_svg_path = os.path.splitext(input_path)[0] + "_temp.svg"
            pdf2svg.pdf_to_svg(input_path, temp_svg_path)
            svg_input = temp_svg_path
        elif ext in ['.png', '.jpg', '.jpeg']:
            print(f"Converting Image to SVG...")
            temp_svg_path = os.path.splitext(input_path)[0] + "_temp.svg"
            img2svg.image_to_svg_grayscale(input_path, temp_svg_path, args.num_colors, args.img_scale)
            svg_input = temp_svg_path
        elif ext == '.svg':
            svg_input = input_path
        else:
            print(f"Error: Unsupported input file format '{ext}'.", file=sys.stderr)
            sys.exit(1)

        print(f"Converting SVG to RD...")
        svg2rd.svg_to_rd(svg_input, output_path, args.min_power, args.max_power, args.speed)
        print(f"\nSuccessfully created {output_path}")

    finally:
        if temp_svg_path and os.path.exists(temp_svg_path):
            os.remove(temp_svg_path)
            print(f"Cleaned up temporary file: {temp_svg_path}")

if __name__ == "__main__":
    main()
