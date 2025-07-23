import argparse
from PIL import Image
import numpy as np
import logging
import time

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def image_to_svg_grayscale(image_path, svg_path, num_shades=5, scale_factor=1.0):
    """
    Converts a raster image to a multi-toned SVG file.
    - Quantizes the image into a specific number of grayscale shades.
    - Creates a separate, optimized path for each shade.
    - Allows downscaling to reduce final file size and complexity.
    """
    try:
        logging.info(f"Opening image: {image_path}")
        img = Image.open(image_path)

        # --- Handle Transparency ---
        # If the image has an alpha channel, composite it onto a white background
        # to ensure transparent areas are treated as white, not black.
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            logging.info("Image has transparency. Compositing onto a white background.")
            # Create a new white background image in RGBA mode
            background = Image.new('RGBA', img.size, (255, 255, 255, 255))
            # Paste the original image onto the background using its alpha channel as a mask
            background.paste(img, (0, 0), img)
            img = background # Use the composited image for further processing

    except FileNotFoundError:
        logging.error(f"Image file not found at {image_path}")
        return

    # --- 1. Scaling (for file size reduction) ---
    if scale_factor < 1.0:
        original_size = img.size
        new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
        logging.info(f"Scaling image from {original_size} to {new_size}")
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # --- 2. Convert to Grayscale and Quantize ---
    logging.info(f"Converting to grayscale and quantizing to {num_shades} shades.")
    # Convert to grayscale first
    img_gray = img.convert('L')
    # Quantize the image to a limited number of colors (shades of gray)
    # The 'P' mode uses a palette. We create a simple grayscale palette.
    img_quantized = img_gray.quantize(colors=num_shades)
    # Get the palette and convert it to a list of gray values
    palette = img_quantized.getpalette()
    
    if not palette:
        logging.error("Could not get palette from quantized image.")
        return

    # The actual number of shades might be less than requested
    num_actual_shades = len(palette) // 3
    gray_values = [palette[i*3] for i in range(num_actual_shades)]

    width, height = img_quantized.size
    logging.info(f"Image dimensions: {width}x{height}")

    # --- 3. Generate SVG ---
    logging.info("Generating SVG content...")
    dwg_paths = {} # Store path data for each shade of gray

    # Convert image to numpy array for fast processing
    img_array = np.array(img_quantized)

    # Process each shade of gray separately
    for shade_index, gray_value in enumerate(gray_values):
        # Pure white is often the background, so we can skip it.
        if gray_value >= 250:
            logging.info(f"Skipping shade {shade_index} (value: {gray_value}) as it is considered background.")
            continue

        logging.info(f"Processing shade {shade_index} (value: {gray_value})...")
        path_data = []
        # Create a boolean mask for the current shade
        shade_mask = (img_array == shade_index)

        for y in range(height):
            row = shade_mask[y, :]
            if not np.any(row): # Skip empty rows
                continue

            padded_row = np.concatenate(([False], row, [False]))
            diffs = np.diff(padded_row.astype(np.int8))
            starts = np.where(diffs == 1)[0]
            ends = np.where(diffs == -1)[0]

            for start, end in zip(starts, ends):
                # Add 0.5 to y for crisp rendering
                path_data.append(f"M{start},{y + 0.5}h{end - start}")
        
        if path_data:
            dwg_paths[gray_value] = " ".join(path_data)

    # --- 4. Save SVG File ---
    logging.info("Saving SVG file...")
    with open(svg_path, 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n')
        f.write('  <g shape-rendering="crispEdges">\n')
        for gray_value, path_d in dwg_paths.items():
            hex_color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"
            f.write(f'    <path d="{path_d}" stroke="{hex_color}" stroke-width="1" />\n')
        f.write('  </g>\n')
        f.write('</svg>\n')

    logging.info(f"Successfully converted {image_path} to {svg_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Convert a raster image to a multi-toned SVG file for laser engraving.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_image', help='Path to the input raster image (e.g., PNG, JPG).')
    parser.add_argument('output_svg', help='Path to the output SVG file.')
    parser.add_argument(
        '--shades',
        type=int,
        default=5,
        help='Number of grayscale shades to use in the final SVG.'
    )
    parser.add_argument(
        '--scale',
        type=float,
        default=0.5,
        help='Factor by which to scale the image before processing. E.g., 0.5 for half resolution.'
    )
    
    args = parser.parse_args()
    
    # Clamp scale to be between 0.01 and 1.0
    scale_factor = max(0.01, min(args.scale, 1.0))

    image_to_svg_grayscale(args.input_image, args.output_svg, args.shades, scale_factor)

if __name__ == '__main__':
    main()
