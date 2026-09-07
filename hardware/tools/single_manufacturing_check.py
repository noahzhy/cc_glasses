"""Verify ordinary through-vias do not drill into SMT lands."""

import json
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Point, box

root = Path("hardware/ir_glasses/EVT_E")
items = json.loads((root / "route_geometry.json").read_text())
lands = []
for pad in items:
    if pad["kind"] != "pad" or pad["layers"] != [0]:
        continue
    x, y = pad["size"]
    shape = (
        Point(0, 0).buffer(x / 2)
        if pad["circle"]
        else box(-x / 2, -y / 2, x / 2, y / 2)
    )
    lands.append(
        (
            pad,
            translate(rotate(shape, -pad["angle"], origin=(0, 0)), *pad["xy"]),
        )
    )
hits = []
for via in items:
    if via["kind"] != "via":
        continue
    for pad, shape in lands:
        if shape.distance(Point(via["a"])) < 0.15:
            hits.append([via["net"], via["a"], pad["ref"], pad["pin"]])
report = {"via_drill_to_smt_land_overlaps": len(hits), "overlaps": hits}
(root / "manufacturing_validation.json").write_text(
    json.dumps(report, indent=2)
)
assert not hits, hits
print("No drilled vias overlap SMT lands.")
