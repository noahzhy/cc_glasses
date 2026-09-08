"""Provide a small upper pocket for the eFuse output capacitor."""

import json
import sys
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx  # noqa: E402

ROOT = Path("hardware/ir_glasses/EVT_E3")
geometry = json.loads((ROOT / "geometry.json").read_text())
board = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)
pocket = box(155, 56, 162, 57.5).buffer(0.5, quad_segs=8)
updated = board.union(pocket)
assert updated.is_valid and updated.geom_type == "Polygon"
assert len(updated.interiors) == 2
local = translate(updated, -110, -85)
geometry["outer"] = list(local.exterior.coords)
(ROOT / "geometry.json").write_text(json.dumps(geometry))
path = ROOT / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))


def children(node, key):
    return [n for n in node if isinstance(n, list) and str(n[0]) == key]


tree = [
    n
    for n in tree
    if not (
        isinstance(n, list)
        and str(n[0]).startswith("gr_")
        and children(n, "layer")
        and children(n, "layer")[0][1] == "Edge.Cuts"
    )
]
for ring in [updated.exterior, *updated.interiors]:
    for a, b in zip(ring.coords, list(ring.coords)[1:]):
        tree.append(
            sx.loads(
                f"(gr_line (start {a[0]:.6f} {a[1]:.6f})"
                f" (end {b[0]:.6f} {b[1]:.6f})"
                ' (stroke (width 0.05) (type solid)) (layer "Edge.Cuts"))'
            )
        )
path.write_text(sx.dumps(tree), encoding="utf-8")
(ROOT / "upper_power_pocket.json").write_text(
    json.dumps(
        {
            "height_added_mm": 1.5,
            "x_range_mm": [154.5, 162.5],
            "added_area_mm2": updated.area - board.area,
            "original_bbox_mm": board.bounds,
            "updated_bbox_mm": updated.bounds,
            "reason": "Place C25 near U14 OUT; keep eye and 3 mm frame",
        },
        indent=2,
    )
)
