"""Give the six left-side driver pins staggered, independent via exits."""

import json
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box

root = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((root / "route_geometry.json").read_text())
pads = {p["pin"]: p for p in items if p["kind"] == "pad" and p["ref"] == "U1"}
routes = []
for number in range(1, 7):
    pad = pads[str(number)]
    target = [118.25 if number % 2 else 117.55, pad["xy"][1]]
    routes.extend(
        [
            dict(
                kind="track",
                net=pad["net"],
                a=pad["xy"],
                b=target,
                width=0.15,
                layers=[0],
            ),
            dict(
                kind="via",
                net=pad["net"],
                a=target,
                b=target,
                width=0.5,
                layers=[0, 1, 2, 3],
            ),
        ]
    )


def copper(item):
    if item["kind"] == "pad":
        return Polygon(item["coords"])
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


new_shapes = [copper(r) for r in routes]
removed = set()
nets = {r["net"] for r in routes}
window = box(117.1, 60.3, 119.6, 63.7)
for item in items:
    if item["kind"] not in {"pad", "via", "track"}:
        continue
    shape = copper(item)
    for route, new in zip(routes, new_shapes):
        foreign = item["net"] != route["net"]
        common_layer = set(item["layers"]) & set(route["layers"])
        conflict = foreign and common_layer and shape.distance(new) < 0.152
        if item["kind"] == "pad":
            assert not conflict, (item["ref"], item["pin"], route["net"])
            if route["kind"] == "via":
                assert Point(route["a"]).distance(shape) >= 0.3
            continue
        close_vias = (
            item["kind"] == route["kind"] == "via"
            and Point(item["a"]).distance(Point(route["a"])) < 0.65
        )
        old_exit = (
            item["kind"] == "track"
            and item["layers"] == [0]
            and item["net"] in nets
            and shape.intersects(window)
        )
        if conflict or close_vias or old_exit:
            removed.add(item["uuid"])
(root / "manual_routes.json").write_text(json.dumps(routes))
(root / "ripup_uuids.json").write_text(json.dumps(sorted(removed)))
print("New fanout items:", len(routes), "replaced items:", len(removed))
