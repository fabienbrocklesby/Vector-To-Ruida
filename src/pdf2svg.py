import fitz  # PyMuPDF
import sys
import os
import io
from PIL import Image

def convert_pdf_to_svg(pdf_path, svg_path):
    """
    Converts a PDF to an SVG.
    It first tries to extract vector drawings. If none are found,
    it extracts any raster images and vectorizes the first one found using potrace.
    """
    output_dir = os.path.dirname(svg_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    doc = fitz.open(pdf_path)
    if not doc.page_count:
        print("PDF has no pages.")
        return
    page = doc.load_page(0)
    
    drawings = page.get_drawings()
    
    if drawings:
        # Vector-based PDF content found
        print("Vector drawings found. Converting to SVG...")
        svg_content = f'<svg viewBox="0 0 {page.rect.width} {page.rect.height}" xmlns="http://www.w3.org/2000/svg">\n'
        
        for path in drawings:
            if path["type"] == "f" or path["type"] == "fs":
                d = ""
                for item in path["items"]:
                    if item[0] == "l": d += f"L {item[1].x} {item[1].y} "
                    elif item[0] == "m": d += f"M {item[1].x} {item[1].y} "
                    elif item[0] == "c": d += f"C {item[1].x} {item[1].y} {item[2].x} {item[2].y} {item[3].x} {item[3].y} "
                if d:
                    svg_content += f'  <path d="{d.strip()}" fill="none" stroke="black" />\n'
            elif path["type"] == "s":
                d = ""
                for item in path["items"]:
                    if item[0] == "l": d += f"L {item[1].x} {item[1].y} "
                    elif item[0] == "m": d += f"M {item[1].x} {item[1].y} "
                    elif item[0] == "c": d += f"C {item[1].x} {item[1].y} {item[2].x} {item[2].y} {item[3].x} {item[3].y} "
                if d:
                    svg_content += f'  <path d="{d.strip()}" fill="none" stroke="black" />\n'
            elif path["type"] == "fr":
                rect = path["rect"]
                svg_content += f'  <rect x="{rect.x0}" y="{rect.y0}" width="{rect.width}" height="{rect.height}" fill="none" stroke="black" />\n'
        
        svg_content += "</svg>"
        with open(svg_path, "w") as f:
            f.write(svg_content)
        print(f"Converted vector drawings from {pdf_path} to {svg_path}")

    else:
        # No vector drawings, assume image-based PDF
        print("No vector drawings found. Attempting to extract and vectorize image...")
        images = page.get_images(full=True)
        if not images:
            print("No images found in the PDF either. Cannot convert.")
            # Create a blank SVG to avoid errors downstream
            with open(svg_path, "w") as f:
                f.write(f'<svg viewBox="0 0 {page.rect.width} {page.rect.height}" xmlns="http://www.w3.org/2000/svg"></svg>')
            return

        # Process the first image found
        img_info = images[0]
        xref = img_info[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        
        # Load image bytes into Pillow and save as a temporary BMP file
        temp_bmp_path = os.path.join(output_dir, "temp_image.bmp")
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.save(temp_bmp_path, "BMP")
            
            # Use the img2svg module to vectorize the BMP
            from . import img2svg
            img2svg.image_to_svg_grayscale(temp_bmp_path, svg_path, num_shades=2, scale_factor=1.0)
        finally:
            # Clean up the temporary image file
            if os.path.exists(temp_bmp_path):
                os.remove(temp_bmp_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf2svg.py input.pdf output.svg")
        sys.exit(1)
    
    convert_pdf_to_svg(sys.argv[1], sys.argv[2])
