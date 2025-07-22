import sys
import os
import ezdxf
from ezdxf.math import Vec3
from ezdxf import bbox as ezdxf_bbox

def format_path_data(points):
    if not points:
        return ""
    
    path_data = f"M {points[0].x} {points[0].y} "
    for p in points[1:]:
        path_data += f"L {p.x} {p.y} "
    return path_data.strip()

def dxf_to_svg(dxf_path, svg_path):
    """
    Converts a DXF file to an SVG file by converting DXF entities to SVG paths.
    """
    try:
        doc = ezdxf.readfile(dxf_path)
    except IOError:
        print(f"Error: Cannot open DXF file: {dxf_path}")
        sys.exit(1)
    except ezdxf.DXFStructureError:
        print(f"Error: Invalid or corrupted DXF file: {dxf_path}")
        sys.exit(2)

    msp = doc.modelspace()
    
    # Get bounding box to set viewBox, or use default if empty
    try:
        bbox = ezdxf_bbox.extents(msp)
        min_point = bbox.extmin
        max_point = bbox.extmax
        width = max_point.x - min_point.x
        height = max_point.y - min_point.y
        if width == 0 or height == 0:
            raise ValueError("Invalid bounding box dimensions")
        # SVG has y-axis pointing down, so we need to adjust the viewBox y and transform the group
        view_box = f"{min_point.x} {-max_point.y} {width} {height}"
    except (ezdxf_bbox.EmptyBoundingBoxError, ValueError):
        view_box = "0 0 100 100" # Default viewBox

    with open(svg_path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}">\n')
        # Apply a transform to flip the Y-axis
        f.write('<g fill="none" stroke="black" stroke-width="0.1%" transform="scale(1, -1)">\n')

        for entity in msp:
            d_attr = ""
            if entity.dxftype() in {'LINE', 'LWPOLYLINE', 'POLYLINE'}:
                if entity.dxftype() == 'LINE':
                    points = [entity.dxf.start, entity.dxf.end]
                else: # LWPOLYLINE, POLYLINE
                    points = list(entity.points())
                    if entity.is_closed:
                        points.append(points[0])
                
                d_attr = format_path_data([Vec3(p) for p in points])

            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                # Represent circle with two arcs for SVG path
                p1 = center + Vec3(radius, 0, 0)
                p2 = center + Vec3(-radius, 0, 0)
                d_attr = (f"M {p1.x} {p1.y} A {radius},{radius} 0 1 0 {p2.x},{p2.y} "
                          f"A {radius},{radius} 0 1 0 {p1.x},{p1.y}")

            elif entity.dxftype() == 'ARC':
                arc = entity
                center = arc.dxf.center
                radius = arc.dxf.radius
                start_angle = arc.dxf.start_angle
                end_angle = arc.dxf.end_angle
                
                start_point = arc.start_point
                end_point = arc.end_point

                # Determine sweep flag
                if arc.dxf.extrusion.z < 0:
                    sweep_flag = 0
                else:
                    sweep_flag = 1

                d_attr = f"M {start_point.x} {start_point.y} A {radius},{radius} 0 0 {sweep_flag} {end_point.x} {end_point.y}"

            if d_attr:
                f.write(f'  <path d="{d_attr}" />\n')

        f.write('</g>\n')
        f.write('</svg>\n')
    
    print(f"Successfully converted {dxf_path} to {svg_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python dxf2svg.py input.dxf output.svg")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not input_file.lower().endswith(".dxf"):
        print("Error: Input file must be a .dxf file.")
        sys.exit(1)

    dxf_to_svg(input_file, output_file)
