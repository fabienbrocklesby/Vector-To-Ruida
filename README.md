# Vector-To-Ruida Universal Converter

A comprehensive Python toolkit for converting various file formats to RD files for Ruida-based laser cutters.

## Features

This tool converts multiple file formats to Ruida laser format:
- **SVG** - Vector graphics (preserves paths and curves)
- **DXF** - CAD drawings  
- **PDF** - Documents (vectors and rasters)
- **JPG/PNG** - Raster images (with quality control)

### Key Capabilities
- **Quality Control**: 0-100% quality scaling for performance vs output balance
- **Smart Auto-scaling**: Prevents memory issues with large images
- **Curve Support**: Handles Bézier curves, arcs, and complex SVG paths
- **Preset Modes**: Optimized settings for engraving vs cutting
- **Multi-layer Processing**: Automatic color separation for engraving

## Quick Start

```bash
# Basic usage with preset
python3 main.py data/examples/example.jpg --preset engrave --quality 70

# Vector cutting
python3 main.py data/examples/demo.svg --preset cut

# High-quality photo engraving
python3 main.py data/examples/example.jpg --preset engrave --quality 90 --num_colors 10
```

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage Examples

### Quality Control (0-100%)
```bash
# Maximum quality (slow, best detail)
python3 main.py input.jpg --preset engrave --quality 100

# Balanced quality/speed
python3 main.py input.jpg --preset engrave --quality 50  

# Fast processing (lower quality)
python3 main.py input.jpg --preset engrave --quality 20
```

### Preset Modes
```bash
# Engraving preset (multiple power levels)
python3 main.py input.jpg --preset engrave

# Cutting preset (single power level)  
python3 main.py input.svg --preset cut
```

### Advanced Options
```bash
# Custom power and speed
python3 main.py input.jpg --preset engrave --min_power 5 --max_power 80 --speed 400

# Control color count
python3 main.py input.jpg --preset engrave --num_colors 8 --quality 80

# Scale image
python3 main.py input.jpg --preset engrave --img_scale 1.5
```

## Comprehensive Demo Guide

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for detailed examples covering:
- All file format conversions
- Quality setting comparisons  
- Material-specific presets
- Troubleshooting guides
- Performance optimization tips

## Dependencies

The script requires several Python libraries:
```bash
pip install svg.path pillow PyMuPDF ezdxf
```

## File Format Details

- **SVG**: Direct path extraction with curve approximation
- **DXF**: Converted via ezdxf library  
- **PDF**: Vector extraction with PyMuPDF, raster fallback
- **Images**: PIL-based processing with quantization and scaling

## Output

Generates `.rd` files compatible with Ruida laser controllers. Files are optimized for:
- Lightburn compatibility
- Direct USB transfer
- Ethernet laser communication

