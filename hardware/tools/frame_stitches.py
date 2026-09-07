"""Find clearance-checked ground stitching positions on existing tracks."""

import json
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

root = Path("hardware/ir_glasses/EVT_C")
items = json.loads((root / "copper.json").read_text())
g = json.loads((root / "geometry.json").read_text())
board = translate(Polygon(g["outer"], g["holes"]), 110, 85).buffer(-0.61)
zones = json.loads((root / "zones.json").read_text())
result = []
for name in ["GND", "AGND"]:
    own_zone = unary_union(
        [
            translate(Polygon(z["coords"]), 110, 85)
            for z in zones
            if z["name"] == name
        ]
    ).buffer(-0.46)
    safe = prep(board.intersection(own_zone))
    obstacles = []
    for t in items:
        if t["net"] == name and t["type"] != "via":
            continue
        if t["type"] == "pad":
            shape = box(*t["box"]).buffer(0.46)
        elif t["type"] == "via":
            radius = 0.56 if t["net"] == name else t["width"] / 2 + 0.46
            shape = Point(t["a"]).buffer(radius)
        else:
            shape = LineString([t["a"], t["b"]]).buffer(t["width"] / 2 + 0.46)
        obstacles.append(shape)
    blocked = prep(unary_union(obstacles))
    added = []
    for t in items:
        if t["type"] != "track" or t["net"] != name:
            continue
        line = LineString([t["a"], t["b"]])
        steps = max(1, int(line.length / 0.4))
        for i in range(steps + 1):
            p = line.interpolate(i / steps, normalized=True)
            if safe.contains(p) and not blocked.intersects(p):
                if all(p.distance(q) > 2 for q in added):
                    added.append(p)
                    result.append({"net": name, "x": p.x, "y": p.y})
(root / "stitches.json").write_text(json.dumps(result))
print("Stitch vias:", len(result))
