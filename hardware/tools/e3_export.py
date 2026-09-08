"""Export the validated EVT E3 manufacturing and review artifacts."""

import os
import subprocess
import sys
from pathlib import Path

root = Path("hardware/ir_glasses/EVT_E3")
if "--carrier" in sys.argv:
    root /= "carrier"
cli = "D:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
stem = "ir_glasses_carrier" if "--carrier" in sys.argv else "ir_glasses"
board = str(root / f"{stem}.kicad_pcb")
env = os.environ.copy()
env["KICAD10_3DMODEL_DIR"] = "D:/Program Files/KiCad/10.0/share/kicad/3dmodels"


def run(*args):
    subprocess.run([cli, *args, board], env=env, check=True)


(root / "manufacturing").mkdir(exist_ok=True)
run(
    "pcb",
    "export",
    "gerbers",
    "--output",
    str(root / "manufacturing"),
    "--layers",
    "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
)
run(
    "pcb",
    "export",
    "drill",
    "--excellon-separate-th",
    "--output",
    str(root / "manufacturing"),
)
run(
    "pcb",
    "export",
    "pos",
    "--format",
    "csv",
    "--units",
    "mm",
    "--smd-only",
    "--exclude-fp-th",
    "--output",
    str(root / "manufacturing/positions.csv"),
)
if "--carrier" in sys.argv:
    (root / "positions.csv").write_bytes(
        (root / "manufacturing/positions.csv").read_bytes()
    )
for name, layers in [
    ("pcb_routed", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,Edge.Cuts"),
    ("assembly_front", "F.Fab,Edge.Cuts"),
    ("assembly_back", "B.Fab,Edge.Cuts"),
]:
    run(
        "pcb",
        "export",
        "svg",
        *(["--mirror"] if name == "assembly_back" else []),
        *(["--black-and-white"] if name.startswith("assembly_") else []),
        "--mode-single",
        "--page-size-mode",
        "2",
        "--exclude-drawing-sheet",
        "--layers",
        layers,
        "--output",
        str(root / f"{name}.svg"),
    )
for side, name in [("top", "pcb_3d"), ("bottom", "pcb_back")]:
    run(
        "pcb",
        "render",
        "--width",
        "1600",
        "--height",
        "900",
        "--side",
        side,
        "--zoom",
        "1.45",
        "--background",
        "opaque",
        "--quality",
        "high",
        "--output",
        str(root / f"{name}.png"),
    )
