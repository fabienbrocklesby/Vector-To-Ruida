# ruida-laser
Understanding the protocol between RDWorks, usb-stick, ethernet, and laser.

## References[&nbsp;&nbsp;](#references)

* https://www.ruidacontroller.com/rdc6442s/
* http://wiki.fablab-nuernberg.de/w/Diskussion:Nova_35
* http://stefan.schuermans.info/rdcam/
* https://github.com/t-oster/VisiCut/issues/404
* https://web.archive.org/web/20191231204307/http://en.rd-acs.com/down.aspx
* https://edutechwiki.unige.ch/en/Ruida
* https://web.archive.org/web/20191218093847/http://www.rogerclark.net/network-aware-laser-cutter-security/

# SVG to RD File Converter

A simple python script to convert SVG files to RD files for Ruida-based laser cutters.

This script extracts paths from an SVG file and converts them into an RD file format suitable for laser cutting. It handles various SVG elements like `<path>`, `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<polyline>`, and `<polygon>`.

## Usage

To use the script, run it from the command line with the input SVG file and the desired output RD file as arguments:

```bash
python3 svg2rd.py input.svg output.rd
```

## Dependencies

The script requires the `svg.path` library. You can install it using pip:

```bash
pip install svg.path
```

