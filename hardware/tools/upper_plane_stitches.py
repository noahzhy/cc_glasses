"""Bridge separate ground copper regions with clearance-checked vias."""

import json
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_D")
items = json.loads((root / "copper.json").read_text())
regions = json.loads((root / "filled_regions.json").read_text())
g = json.loads((root / "geometry.json").read_text())
board = translate(Polygon(g["outer"], g["holes"]), 110, 85).buffer(-0.61)
result = []
for name in ["AGND", "GND"]:
    rows = [r for r in regions if r["net"] == name]
    shapes = [Polygon(r["coords"]).buffer(0) for r in rows]
    parent = list(range(len(shapes)))

    def find(i):
        while i != parent[i]:
            i = parent[i]
        return i

    def union(indices):
        if indices:
            for i in indices[1:]:
                parent[find(i)] = find(indices[0])

    obstacles = []
    for t in items:
        if t["type"] == "via" and t["net"] == name:
            p = Point(t["a"])
            union([i for i, s in enumerate(shapes) if s.covers(p)])
        if t["net"] == name and t["type"] != "via":
            continue
        if t["type"] == "pad":
            shape = box(*t["box"]).buffer(0.455)
        elif t["type"] == "via":
            radius = 0.56 if t["net"] == name else t["width"] / 2 + 0.455
            shape = Point(t["a"]).buffer(radius)
        else:
            shape = LineString([t["a"], t["b"]]).buffer(t["width"] / 2 + 0.455)
        obstacles.append(shape)
    blocked = unary_union(obstacles)
    for i, a in enumerate(shapes):
        for j in range(i):
            if rows[i]["layer"] == rows[j]["layer"] or find(i) == find(j):
                continue
            common = a.intersection(shapes[j]).intersection(board)
            common = common.difference(blocked)
            if common.is_empty or common.area < 0.002:
                continue
            if common.geom_type == "MultiPolygon":
                common = max(common.geoms, key=lambda s: s.area)
            p = common.representative_point()
            result.append({"net": name, "x": p.x, "y": p.y})
            union([i, j])
            blocked = blocked.union(p.buffer(0.56))
    print(name, "remaining region groups:", len({find(i) for i in parent}))
(root / "stitches.json").write_text(json.dumps(result))
print("New stitching vias:", len(result))
