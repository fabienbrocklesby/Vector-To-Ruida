#!/usr/bin/env python3
import argparse
import os
import sys
from src import dxf2svg, pdf2svg, img2svg, svg2rd

def setup_parser():
    """Sets up and returns the argument parser."""
    parser = argparse.ArgumentParser(
        description='Universal converter to .rd files for Ruida laser cutters.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_file', help='Path to the input file (DXF, PDF, PNG, JPG, SVG).')
    parser.add_argument('--output_file', '-o', help='Path to the output .rd file. Defaults to input file with .rd extension.')
    
    parser.add_argument('--preset', choices=['engrave', 'cut'], help='Choose a preset for engraving or cutting settings.')
    
    # Quality/Performance controls
    parser.add_argument('--mode', choices=['quality', 'performance'], default='performance',
                       help='Processing mode: "quality" preserves image resolution but may be slow, "performance" auto-scales large images for speed.')
    parser.add_argument('--quality', type=int, metavar='0-100', 
                       help='Quality percentage (0-100): 100=max quality/slow, 50=balanced, 20=fast/lower quality. Overrides --mode setting.')

    # Power and Speed settings
    parser.add_argument('--min_power', type=float, help='Laser power for the lightest shade (engraving) or for all cuts.')
    parser.add_argument('--max_power', type=float, help='Laser power for the darkest shade (engraving). Not used for cutting.')
    parser.add_argument('--speed', type=float, help='Engraving or cutting speed (mm/s).')

    # Image to SVG specific arguments
    parser.add_argument('--num_colors', type=int, help='[Engrave] Number of shades to quantize the image to.')
    parser.add_argument('--img_scale', type=float, help='[Engrave] Factor by which to scale the image before processing.')

    return parser

def apply_preset_defaults(args):
    """Applies default settings based on the chosen preset."""
    # Convert quality percentage to effective mode if quality is specified
    if args.quality is not None:
        if not (0 <= args.quality <= 100):
            print("Error: Quality must be between 0 and 100", file=sys.stderr)
            sys.exit(1)
        # Override mode based on quality percentage
        args.effective_mode = 'quality' if args.quality >= 70 else 'performance'
        args.quality_factor = args.quality / 100.0
    else:
        # Use the mode setting
        args.effective_mode = args.mode
        args.quality_factor = 1.0 if args.mode == 'quality' else 0.2
    
    if args.preset == 'engrave':
        if args.speed is None: args.speed = 400.0
        if args.min_power is None: args.min_power = 5.0
        if args.max_power is None: args.max_power = 80.0
        # Adjust num_colors based on quality factor
        if args.num_colors is None: 
            # Scale colors from 2 (lowest quality) to 12 (highest quality)
            min_colors, max_colors = 2, 12
            args.num_colors = int(min_colors + (max_colors - min_colors) * args.quality_factor)
        if args.img_scale is None: args.img_scale = 1.0
    elif args.preset == 'cut':
        if args.speed is None: args.speed = 20.0
        if args.min_power is None: args.min_power = 80.0
        if args.max_power is None: args.max_power = 80.0 # For cutting, max_power is same as min_power
        if args.num_colors is None: args.num_colors = 2 # For vectorization, we want black and white
        if args.img_scale is None: args.img_scale = 1.0

def auto_scale_for_image_size(input_path, preset, img_scale, num_colors, quality_factor, quality_percentage=None):
    """Automatically scale down large images based on quality setting."""
    try:
        from PIL import Image
        img = Image.open(input_path)
        width, height = img.size
        total_pixels = width * height
        
        # Calculate scaling threshold based on quality factor
        # Quality 100% = 2M pixels, Quality 0% = 50K pixels
        min_threshold = 50_000
        max_threshold = 2_000_000
        pixel_threshold = int(min_threshold + (max_threshold - min_threshold) * quality_factor)
        
        # Display quality info
        if quality_percentage is not None:
            print(f"Quality setting: {quality_percentage}% (threshold: {pixel_threshold:,} pixels)")
        else:
            mode_name = "Quality" if quality_factor >= 0.7 else "Performance"
            print(f"{mode_name} mode (threshold: {pixel_threshold:,} pixels)")
        
        print(f"Image resolution: {width}x{height} = {total_pixels:,} pixels")
        
        # Only scale if image exceeds threshold and we're in engrave mode
        if preset == 'engrave' and total_pixels > pixel_threshold:
            # Calculate scale factor based on quality
            # Higher quality = less aggressive scaling
            min_scale = 0.1 + (0.4 * quality_factor)  # 0.1 to 0.5 range
            target_pixels = pixel_threshold
            calculated_scale = (target_pixels / total_pixels) ** 0.5
            scale_factor = max(min_scale, min(1.0, calculated_scale))
            
            print(f"Auto-scaling from {img_scale} to {scale_factor:.3f}")
            print(f"Final size: {int(width*scale_factor)}x{int(height*scale_factor)} ({int(width*scale_factor * height*scale_factor):,} pixels)")
            if quality_percentage is not None:
                print(f"Tip: Use --quality {min(100, quality_percentage + 20)} for higher resolution")
            else:
                print("Tip: Use --quality 80 for higher resolution or --quality 20 for faster processing")
            
            return scale_factor
        else:
            if total_pixels > 500_000:
                print("Large image - processing may take time...")
            return img_scale
            
    except Exception:
        # If we can't read the image, just return the original scale
        return img_scale

def convert_to_svg(input_path, ext, preset, num_colors, img_scale, quality_factor, quality_percentage=None):
    """Converts the input file to an SVG file."""
    temp_svg_path = os.path.splitext(input_path)[0] + "_temp.svg"
    
    if ext == '.dxf':
        print("Converting DXF to SVG...")
        dxf2svg.dxf_to_svg(input_path, temp_svg_path)
        return temp_svg_path
    elif ext == '.pdf':
        print("Converting PDF to SVG...")
        pdf2svg.convert_pdf_to_svg(input_path, temp_svg_path)
        return temp_svg_path
    elif ext in ['.png', '.jpg', '.jpeg']:
        # Auto-scale large images based on quality setting
        scaled_img_scale = auto_scale_for_image_size(input_path, preset, img_scale, num_colors, quality_factor, quality_percentage)
        
        if preset == 'cut':
             print("Vectorizing Image for cutting...")
             # This is a placeholder for a proper vectorization function
             # For now, it will produce a high-contrast grayscale SVG
             img2svg.image_to_svg_grayscale(input_path, temp_svg_path, num_shades=2, scale_factor=scaled_img_scale)
        else: # engrave
            print("Converting Image to SVG for engraving...")
            img2svg.image_to_svg_grayscale(input_path, temp_svg_path, num_shades=num_colors, scale_factor=scaled_img_scale)
        return temp_svg_path
    elif ext == '.svg':
        return input_path
    else:
        print(f"Error: Unsupported input file format '{ext}'.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = setup_parser()
    args = parser.parse_args()

    apply_preset_defaults(args)

    input_path = args.input_file
    output_path = args.output_file
    
    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".rd"

    _, ext = os.path.splitext(input_path)
    ext = ext.lower()

    temp_svg_path = None

    try:
        svg_input = convert_to_svg(input_path, ext, args.preset, args.num_colors, args.img_scale, 
                                 args.quality_factor, args.quality)
        
        if not svg_input or not os.path.exists(svg_input):
            print("Error: SVG conversion failed.", file=sys.stderr)
            sys.exit(1)

        print("Converting SVG to RD...")
        svg2rd.svg_to_rd(svg_input, output_path, args.min_power, args.max_power, args.speed)
        print(f"\nSuccessfully created {output_path}")

    finally:
        if temp_svg_path and os.path.exists(temp_svg_path):
            os.remove(temp_svg_path)
            print(f"Cleaned up temporary file: {temp_svg_path}")

if __name__ == "__main__":
    main()
