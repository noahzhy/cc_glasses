"""Keep ordinary drilled vias outside the solderable component lands."""

import json
from pathlib import Path

import numpy as np
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_E")
items = json.loads((root / "route_geometry.json").read_text())
geometry = json.loads((root / "geometry.json").read_text())
board = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)


def shape(item):
    if item["kind"] == "keepout":
        return Polygon(item["coords"])
    if item["kind"] == "pad":
        x, y = item["size"]
        copper = (
            Point(0, 0).buffer(x / 2)
            if item["circle"]
            else box(-x / 2, -y / 2, x / 2, y / 2)
        )
        if item.get("npth"):
            copper = copper.buffer(0.1)
        return translate(
            rotate(copper, -item["angle"], origin=(0, 0)), *item["xy"]
        )
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


shapes = [shape(item) for item in items]
lands = unary_union(
    [
        s
        for item, s in zip(items, shapes)
        if item["kind"] == "pad" and item["layers"] == [0]
    ]
)
moves = []
for via in items:
    if via["kind"] != "via" or lands.distance(Point(via["a"])) >= 0.15:
        continue
    old = via["a"]
    net = via["net"]
    attached = [
        t
        for t in items
        if t["kind"] == "track"
        and t["net"] == net
        and (t["a"] == old or t["b"] == old)
    ]
    obstacles = [
        unary_union(
            [
                s
                for item, s in zip(items, shapes)
                if item["net"] != net and layer in item["layers"]
            ]
        )
        for layer in range(4)
    ]
    through = unary_union(obstacles)
    candidates = sorted(
        (dx * dx + dy * dy, round(old[0] + dx, 5), round(old[1] + dy, 5))
        for dx in np.arange(-2, 2.01, 0.05)
        for dy in np.arange(-2, 2.01, 0.05)
    )
    found = None
    for _, x, y in candidates:
        point = Point(x, y)
        if not board.buffer(-0.56).contains(point):
            continue
        if through.distance(point) < 0.405 or lands.distance(point) < 0.26:
            continue
        if any(
            t["kind"] == "via"
            and t is not via
            and Point(t["a"]).distance(point) < 0.56
            for t in items
        ):
            continue
        valid = True
        for t in attached:
            other = t["b"] if t["a"] == old else t["a"]
            line = LineString([(x, y), other]).buffer(t["width"] / 2)
            if (
                not board.buffer(-0.3).covers(line)
                or obstacles[t["layers"][0]].distance(line) < 0.152
            ):
                valid = False
                break
        if valid:
            found = [x, y]
            break
    print(net, old, "->", found, flush=True)
    if found is not None:
        moves.append({"net": net, "old": old[:], "new": found})
        via["a"] = via["b"] = found
        for t in attached:
            for end in ["a", "b"]:
                if t[end] == old:
                    t[end] = found
        shapes = [shape(item) for item in items]
(root / "via_moves.json").write_text(json.dumps(moves))
