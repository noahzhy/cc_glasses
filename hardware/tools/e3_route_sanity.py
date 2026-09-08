"""Check proposed copper against retained copper before native insertion."""

import json
from pathlib import Path

import shapely
from shapely.geometry import LineString, Point, Polygon

root = Path("hardware/ir_glasses/EVT_E3")
removed = set(json.loads((root / "ripup_uuids.json").read_text()))
native = json.loads((root / "route_geometry.json").read_text())
routes = json.loads((root / "manual_routes.json").read_text())
items = [p for p in native if p.get("uuid") not in removed] + routes


def shape(item):
    if item["kind"] in {"pad", "keepout"}:
        return Polygon(item["coords"]).buffer(0)
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


shapes = [shape(p) for p in items]
tree = shapely.STRtree(shapes)
errors = []
for i in range(len(items) - len(routes), len(items)):
    for j in tree.query(shapes[i], predicate="dwithin", distance=0.1499):
        if items[i]["net"] == items[j]["net"]:
            continue
        if not set(items[i]["layers"]) & set(items[j]["layers"]):
            continue
        errors.append(
            {
                "route": items[i],
                "other": items[j],
                "clearance": shapes[i].distance(shapes[j]),
            }
        )
(root / "proposed_route_conflicts.json").write_text(
    json.dumps(errors, indent=2)
)
print("Proposed route conflicts:", len(errors))
