import subprocess
import sys
import os

def convert_image_to_svg(image_path, svg_path):
    """Converts a raster image to a vector SVG using potrace."""
    
    # Check if potrace is installed
    try:
        subprocess.run(["potrace", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: potrace is not installed or not in your PATH.")
        print("Please install it to use this functionality.")
        print("On macOS with Homebrew: brew install potrace")
        sys.exit(1)

    # potrace needs a BMP file, so we might need to convert first if not a BMP.
    # For simplicity, this script will assume a BMP or a format potrace can handle.
    # A more robust solution would use a library like Pillow to convert any image to BMP first.
    
    print(f"Vectorizing {image_path}...")
    try:
        subprocess.run(
            ["potrace", image_path, "--svg", "-o", svg_path],
            check=True
        )
        print(f"Successfully created {svg_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during potrace execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python img2svg.py input.bmp output.svg")
        sys.exit(1)
    
    convert_image_to_svg(sys.argv[1], sys.argv[2])
