"""Open local escape space around the remaining disconnected lands."""

import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx  # noqa: E402

ROOT = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((ROOT / "route_geometry.json").read_text())
report = json.loads((ROOT / "drc.json").read_text(encoding="utf-8"))
ids = {i["uuid"] for v in report["unconnected_items"] for i in v["items"]}
pads = [p for p in items if p["kind"] == "pad" and p["uuid"] in ids]
shapes = [(p, Polygon(p["coords"])) for p in pads]
remove, nets = set(), set()
for item in items:
    if item["kind"] not in {"via", "track"}:
        continue
    shape = (
        Point(item["a"])
        if item["kind"] == "via"
        else LineString([item["a"], item["b"]])
    ).buffer(item["width"] / 2)
    if any(
        item["net"] != p["net"] and shape.distance(s) < 0.75 for p, s in shapes
    ):
        remove.add(item["uuid"])
        nets.add(item["net"])
path = ROOT / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))
tree = [
    n
    for n in tree
    if not (
        isinstance(n, list)
        and str(n[0]) in {"segment", "via"}
        and any(
            isinstance(v, list) and str(v[0]) == "uuid" and v[1] in remove
            for v in n
        )
    )
]
path.write_text(sx.dumps(tree), encoding="utf-8")
(ROOT / "escape_pads.json").write_text(
    json.dumps([[p["ref"], p["pin"]] for p in pads])
)
nets.update(json.loads((ROOT / "reroute_nets.json").read_text()))
(ROOT / "reroute_nets.json").write_text(json.dumps(sorted(nets)))
print(
    "Local escape clearance:", len(remove), "tracks/vias;", len(pads), "lands"
)
