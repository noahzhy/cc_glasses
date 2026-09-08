"""Remove disconnected copper fragments that reach no component pad."""

import json
import sys
from collections import defaultdict
from pathlib import Path

import shapely
from shapely.geometry import LineString, Point, Polygon

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

root = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((root / "route_geometry.json").read_text())
for zone in json.loads((root / "filled_regions.json").read_text()):
    items.append(
        dict(
            kind="zone",
            net=zone["net"],
            coords=zone["coords"],
            layers=[["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"].index(zone["layer"])],
        )
    )


def copper(item):
    if item["kind"] in {"zone", "pad", "keepout"}:
        return Polygon(item["coords"]).buffer(0)
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


net_items = defaultdict(list)
for item in items:
    if item["net"] and item["layers"]:
        net_items[item["net"]].append(item)
removed = set()
for net, members in net_items.items():
    shapes = [copper(p) for p in members]
    tree = shapely.STRtree(shapes)
    pairs = tree.query(shapes, predicate="dwithin", distance=0.001)
    parents = list(range(len(members)))

    def find(i):
        while parents[i] != i:
            i = parents[i]
        return i

    for a, b in pairs.T:
        if a > b and set(members[a]["layers"]) & set(members[b]["layers"]):
            parents[find(a)] = find(b)
    anchored = {find(i) for i, p in enumerate(members) if p["kind"] == "pad"}
    for i, item in enumerate(members):
        if find(i) not in anchored and item["kind"] in {"track", "via"}:
            removed.add(item["uuid"])
path = root / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))
for node in tree[:]:
    if not isinstance(node, list) or str(node[0]) not in {"segment", "via"}:
        continue
    uid = next(
        v[1] for v in node if isinstance(v, list) and str(v[0]) == "uuid"
    )
    if uid in removed:
        tree.remove(node)
path.write_text(sx.dumps(tree), encoding="utf-8")
print("Removed padless copper fragments:", len(removed))
