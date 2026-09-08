"""Pack the upper power components below the original straight board edge."""

import json
import sys
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Polygon, box

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx  # noqa: E402


root = Path("hardware/ir_glasses/EVT_E3")
path = root / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))
positions = {
    "C25": (158.5, 57.95),
    "D17": (159.0, 59.65),
    "U14": (158.5, 62.1),
    "C37": (159.6, 64.5),
}


def children(node, key):
    return [n for n in node if isinstance(n, list) and str(n[0]) == key]


for node in children(tree, "footprint"):
    ref = next(p[2] for p in children(node, "property") if p[1] == "Reference")
    if ref in positions:
        children(node, "at")[0][1:3] = positions[ref]
geometry = json.loads((root / "geometry.json").read_text())
old = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)
board = old.intersection(box(0, 57, 300, 200)).simplify(0.000001)
board = Polygon(
    [
        (x, y)
        for x, y in board.exterior.coords
        if not (51 < x < 168.9 and y < 57.01)
    ],
    board.interiors,
)
assert board.is_valid and len(board.interiors) == 2
geometry["outer"] = list(translate(board, -110, -85).exterior.coords)
(root / "geometry.json").write_text(json.dumps(geometry))
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
for ring in [board.exterior, *board.interiors]:
    for a, b in zip(ring.coords, list(ring.coords)[1:]):
        tree.append(
            sx.loads(
                f"(gr_line (start {a[0]:.6f} {a[1]:.6f})"
                f" (end {b[0]:.6f} {b[1]:.6f})"
                ' (stroke (width 0.05) (type solid)) (layer "Edge.Cuts"))'
            )
        )
path.write_text(sx.dumps(tree), encoding="utf-8")
(root / "upper_power_pocket.json").write_text(
    json.dumps(
        {
            "height_added_mm": 0,
            "removed_protrusion_mm": 1.5,
            "updated_bbox_mm": board.bounds,
            "reason": "Repacked C25, D17, U14 and C37 below the straight top",
            "positions_mm": positions,
        },
        indent=2,
    )
)
