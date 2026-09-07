"""Prepare EVT D with all amplifier circuits along the upper frame."""

import json
import shutil
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

source = Path("hardware/ir_glasses/EVT_C")
root = Path("hardware/ir_glasses/EVT_D")
for pattern in ["*.kicad_sch", "*.kicad_pro", "*.kicad_sym"]:
    for p in source.glob(pattern):
        shutil.copy2(p, root / p.name)
for name in ["IR_Glasses.pretty", "models"]:
    shutil.copytree(source / name, root / name, dirs_exist_ok=True)
for name in [
    "fp-lib-table",
    "sym-lib-table",
    "ir_glasses.net",
    "mechanical_reference.svg",
    "mechanical_reference.png",
    "optical_map.csv",
    "optical_placement.csv",
    "README.md",
]:
    shutil.copy2(source / name, root / name)
parts = json.loads((source / "parts.json").read_text())
changes = {
    "U3": (-45.6, -23.6, 90, "back"),
    "U5": (45.6, -23.6, 90, "back"),
    "J2": (-54.5, -23, 0, "back"),
    "C4": (-44, -20.3, 0, "front"),
    "C6": (44, -20.3, 0, "front"),
    "C22": (-49, -26, 0, "front"),
    "C23": (46, -26.5, 0, "front"),
    "C24": (52, -22.4, 0, "front"),
    "C14": (50.8, -23.6, 0, "front"),
    "U11": (56, -26, 0, "front"),
    "D17": (56, -22.5, 0, "front"),
}
for ref, (x, y, angle, side) in changes.items():
    parts[ref].update(xy=[x, y], angle=angle, side=side)
for first, cx in [(5, -46), (13, 46)]:
    for offset in range(4):
        for prefix, dy in [("RF", -0.85), ("CF", 0.85)]:
            parts[f"{prefix}{first + offset}"].update(
                xy=[cx - 2.925 + offset * 1.95, -23.3 + dy]
            )
g = json.loads((source / "geometry.json").read_text())
holes = [Polygon(h) for h in g["holes"]]
outer = (
    unary_union(
        [
            *(h.buffer(4.9, quad_segs=12) for h in holes),
            box(-59, -27, 59, -20).buffer(1, quad_segs=8),
            box(-12, -24, 12, -12).buffer(1, quad_segs=8),
        ]
    )
    .buffer(0.8, quad_segs=8)
    .buffer(-0.8, quad_segs=8)
    .simplify(0.04)
)
g["outer"] = list(outer.exterior.coords)
(root / "parts.json").write_text(json.dumps(parts, indent=2))
(root / "geometry.json").write_text(json.dumps(g))
print(
    "Bounds:", outer.bounds, "Area:", outer.difference(unary_union(holes)).area
)
