"""Create the single-side revision without changing EVT D."""

import json
import shutil
from pathlib import Path

source = Path("hardware/ir_glasses/EVT_D")
root = Path("hardware/ir_glasses/EVT_E")
root.mkdir(exist_ok=True)
for pattern in ["*.kicad_sch", "*.kicad_pro", "*.kicad_sym"]:
    for path in source.glob(pattern):
        if path.stem != "plane_candidate":
            shutil.copy2(path, root / path.name)
for name in ["IR_Glasses.pretty", "models"]:
    shutil.copytree(source / name, root / name, dirs_exist_ok=True)
for name in [
    "fp-lib-table",
    "sym-lib-table",
    "ir_glasses.net",
    "geometry.json",
    "mechanical_reference.svg",
    "mechanical_reference.png",
    "optical_map.csv",
    "optical_placement.csv",
    "optical_orientation.json",
    "README.md",
    "bom.csv",
]:
    shutil.copy2(source / name, root / name)
parts = json.loads((source / "parts.json").read_text(encoding="utf-8"))
for part in parts.values():
    part["side"] = "front"
(root / "parts.json").write_text(json.dumps(parts, indent=2))
script = Path("hardware/tools/upper_board.py").read_text()
script = script.replace("EVT_D", "EVT_E").replace("EVT_C", "EVT_D")
script = script.replace("EVT D", "EVT E")
Path("hardware/tools/single_board.py").write_text(script)
