"""Export the validated EVT C manufacturing and review artifacts."""

import os
import subprocess
from pathlib import Path

root = Path("hardware/ir_glasses/EVT_C")
cli = "D:/Program Files/KiCad/10.0/bin/kicad-cli.exe"
board = str(root / "ir_glasses.kicad_pcb")
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
    "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,"
    "B.Silkscreen,F.Mask,B.Mask,Edge.Cuts",
)
run("pcb", "export", "drill", "--output", str(root / "manufacturing"))
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
for name, layers in [
    ("pcb_routed", "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,Edge.Cuts"),
    ("assembly_front", "F.Fab,Edge.Cuts"),
    ("assembly_back", "B.Fab,Edge.Cuts"),
]:
    run(
        "pcb",
        "export",
        "svg",
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
