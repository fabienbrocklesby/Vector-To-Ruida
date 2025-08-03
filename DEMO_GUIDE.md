# Vector-To-Ruida Demo Guide

This guide provides comprehensive examples of how to use the Universal Vector-to-Ruida converter with all supported file formats and settings.

## Quick Start

The basic syntax is:
```bash
python3 main.py [input_file] [options]
```

## File Format Support

The converter supports these input formats:
- **SVG** - Vector graphics (direct conversion)
- **DXF** - CAD drawings (via SVG conversion)
- **PDF** - Documents (via SVG conversion)
- **JPG/JPEG** - Raster images (via SVG conversion)
- **PNG** - Raster images (via SVG conversion)

## Available Example Files

Located in `data/examples/`:
- `demo.svg` - Simple vector graphics with curves
- `example.dxf` - CAD drawing file
- `example.pdf` - PDF document
- `example.jpg` - Raster photograph
- `example.png` - Raster image
- `example_raster.svg` - Rasterized SVG content

## Quality Settings

### Quality Percentage (Recommended)
Use `--quality 0-100` for fine-grained control:

```bash
# Maximum quality (slow, large files, best detail)
python3 main.py data/examples/example.jpg --preset engrave --quality 100

# High quality (good balance)
python3 main.py data/examples/example.jpg --preset engrave --quality 80

# Balanced (recommended for most uses)
python3 main.py data/examples/example.jpg --preset engrave --quality 50

# Performance focused (fast, smaller files)
python3 main.py data/examples/example.jpg --preset engrave --quality 20

# Maximum performance (very fast, lowest quality)
python3 main.py data/examples/example.jpg --preset engrave --quality 10
```

### Legacy Mode Settings
```bash
# Quality mode (preserves resolution)
python3 main.py data/examples/example.jpg --preset engrave --mode quality

# Performance mode (auto-scales large images)
python3 main.py data/examples/example.jpg --preset engrave --mode performance
```

## Preset Examples

### Engraving Presets
```bash
# Basic engraving with default settings
python3 main.py data/examples/example.jpg --preset engrave

# High-quality photo engraving
python3 main.py data/examples/example.jpg --preset engrave --quality 90 --min_power 5 --max_power 80 --speed 400

# Fast draft engraving
python3 main.py data/examples/example.jpg --preset engrave --quality 30 --speed 800

# Detailed engraving with many shades
python3 main.py data/examples/example.jpg --preset engrave --num_colors 16 --quality 100
```

### Cutting Presets
```bash
# Basic vector cutting
python3 main.py data/examples/demo.svg --preset cut

# High-power cutting
python3 main.py data/examples/demo.svg --preset cut --min_power 90 --speed 15

# Fast cutting for thin materials
python3 main.py data/examples/demo.svg --preset cut --min_power 60 --speed 40
```

## File Format Specific Examples

### SVG Files (Vector Graphics)
```bash
# Direct SVG to RD conversion
python3 main.py data/examples/demo.svg --preset cut

# SVG engraving (rasterizes vector content)
python3 main.py data/examples/demo.svg --preset engrave --quality 80
```

### DXF Files (CAD Drawings)
```bash
# Convert CAD drawing for cutting
python3 main.py data/examples/example.dxf --preset cut --output_file output/cad_cut.rd

# Convert CAD for engraving
python3 main.py data/examples/example.dxf --preset engrave --quality 70
```

### PDF Files
```bash
# Convert PDF for cutting (extracts vectors)
python3 main.py data/examples/example.pdf --preset cut

# Convert PDF for engraving (rasterizes content)
python3 main.py data/examples/example.pdf --preset engrave --quality 60
```

### Image Files (JPG/PNG)
```bash
# Photo engraving - high quality
python3 main.py data/examples/example.jpg --preset engrave --quality 85 --num_colors 10

# Photo engraving - balanced
python3 main.py data/examples/example.jpg --preset engrave --quality 50

# Photo engraving - fast preview
python3 main.py data/examples/example.jpg --preset engrave --quality 25

# Image vectorization for cutting (experimental)
python3 main.py data/examples/example.png --preset cut --quality 40
```

## Advanced Parameter Examples

### Color/Shade Control
```bash
# Few shades for simple engraving
python3 main.py data/examples/example.jpg --preset engrave --num_colors 4

# Many shades for detailed work
python3 main.py data/examples/example.jpg --preset engrave --num_colors 12

# Black and white only
python3 main.py data/examples/example.jpg --preset engrave --num_colors 2
```

### Image Scaling
```bash
# Enlarge small image
python3 main.py data/examples/example.jpg --preset engrave --img_scale 2.0

# Reduce large image
python3 main.py data/examples/example.jpg --preset engrave --img_scale 0.5

# Precise sizing
python3 main.py data/examples/example.jpg --preset engrave --img_scale 1.5 --quality 80
```

### Power and Speed Tuning
```bash
# Light engraving (wood)
python3 main.py data/examples/example.jpg --preset engrave --min_power 3 --max_power 25 --speed 600

# Medium engraving (plywood)
python3 main.py data/examples/example.jpg --preset engrave --min_power 10 --max_power 60 --speed 400

# Deep engraving (hardwood)
python3 main.py data/examples/example.jpg --preset engrave --min_power 20 --max_power 90 --speed 200

# Precise cutting (3mm plywood)
python3 main.py data/examples/demo.svg --preset cut --min_power 70 --speed 20

# Fast cutting (cardboard)
python3 main.py data/examples/demo.svg --preset cut --min_power 40 --speed 60
```

### Custom Output Files
```bash
# Specify output filename
python3 main.py data/examples/example.jpg --preset engrave --output_file output/my_engraving.rd

# Short form output option
python3 main.py data/examples/demo.svg --preset cut -o output/my_cut.rd
```

## Performance vs Quality Comparison

### Image Processing Performance
```bash
# Test different quality levels on the same image
python3 main.py data/examples/example.jpg --preset engrave --quality 10 -o output/q10.rd
python3 main.py data/examples/example.jpg --preset engrave --quality 30 -o output/q30.rd
python3 main.py data/examples/example.jpg --preset engrave --quality 50 -o output/q50.rd
python3 main.py data/examples/example.jpg --preset engrave --quality 70 -o output/q70.rd
python3 main.py data/examples/example.jpg --preset engrave --quality 90 -o output/q90.rd
```

Then compare file sizes:
```bash
ls -la output/q*.rd
```

## Troubleshooting Examples

### Memory/Performance Issues
```bash
# If processing hangs on large images
python3 main.py data/examples/example.jpg --preset engrave --quality 20

# For very large images, use minimal settings
python3 main.py data/examples/example.jpg --preset engrave --quality 10 --num_colors 3
```

### Quality Issues
```bash
# If output looks pixelated, increase quality
python3 main.py data/examples/example.jpg --preset engrave --quality 80

# If too many colors, reduce them
python3 main.py data/examples/example.jpg --preset engrave --num_colors 6 --quality 70
```

## Batch Processing Examples

### Multiple Quality Tests
```bash
# Create multiple versions for comparison
for q in 20 40 60 80 100; do
    python3 main.py data/examples/example.jpg --preset engrave --quality $q -o output/test_q${q}.rd
done
```

### Different Materials
```bash
# Wood engraving preset
python3 main.py data/examples/example.jpg --preset engrave --quality 70 --min_power 5 --max_power 30 --speed 500 -o output/wood_engrave.rd

# Acrylic engraving preset  
python3 main.py data/examples/example.jpg --preset engrave --quality 80 --min_power 8 --max_power 50 --speed 400 -o output/acrylic_engrave.rd

# Leather engraving preset
python3 main.py data/examples/example.jpg --preset engrave --quality 60 --min_power 15 --max_power 70 --speed 300 -o output/leather_engrave.rd
```

## File Size Guidelines

Based on testing, expect these approximate file sizes:

- **Quality 10-20%**: 500KB - 1MB (fast processing)
- **Quality 30-50%**: 1MB - 2MB (balanced)
- **Quality 60-80%**: 2MB - 4MB (high quality)
- **Quality 90-100%**: 4MB+ (maximum quality)

## Tips and Best Practices

1. **Start with quality 50** for most projects
2. **Use quality 20-30** for quick tests and previews
3. **Use quality 80-100** for final production runs
4. **Adjust `--num_colors`** to control engraving complexity
5. **Use `--img_scale`** to resize images before processing
6. **Check file sizes** - larger files may take longer to transfer to laser

## Error Resolution

### "Image file not found"
Make sure to include the full path:
```bash
# Wrong
python3 main.py example.jpg --preset engrave

# Correct
python3 main.py data/examples/example.jpg --preset engrave
```

### "SVG conversion failed"
Check file permissions and try a different quality setting:
```bash
python3 main.py data/examples/example.jpg --preset engrave --quality 30
```

## Getting Help

View all available options:
```bash
python3 main.py --help
```

## Output Files

All generated `.rd` files are saved to the `output/` directory and can be transferred to your Ruida laser controller via USB, Ethernet, or direct file copy.
