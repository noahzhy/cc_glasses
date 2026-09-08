"""Refresh native fills, DRC, and routing geometry in a fixed order."""

import os
import subprocess
import sys

os.environ["PYTHONUTF8"] = "1"
native = "D:/Program Files/KiCad/10.0/bin/python.exe"
cli = "D:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
root = "hardware/ir_glasses/EVT_E3/"
commands = [
    [native, "hardware/tools/e3_fill.py"],
    [
        cli,
        "pcb",
        "drc",
        "--format",
        "json",
        "--schematic-parity",
        "--output",
        root + "drc.json",
        root + "ir_glasses.kicad_pcb",
    ],
    [native, "hardware/tools/e3_route_geometry.py"],
    [sys.executable, "hardware/tools/e3_filled.py"],
]
for command in commands:
    subprocess.run(command, check=True)
