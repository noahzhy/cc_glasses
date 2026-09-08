"""Separate the eFuse ground exit from its soft-start via."""

import json
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon


root = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((root / "route_geometry.json").read_text())
routes = []
for net, points in [
    ("GND", [(159.4, 62.325), (160.4546, 62.325), (160.4546, 62.2529)]),
    (
        "INRUSH_RC",
        [(159.225, 62.8), (159.8, 62.8), (160.05, 63.05), (160.05, 63.2)],
    ),
]:
    for a, b in zip(points, points[1:]):
        routes.append(
            dict(kind="track", net=net, a=a, b=b, width=0.15, layers=[0])
        )
routes.append(
    dict(
        kind="via",
        net="INRUSH_RC",
        a=(160.05, 63.2),
        b=(160.05, 63.2),
        width=0.5,
        layers=[0, 1, 2, 3],
    )
)


def copper(item):
    if item["kind"] == "pad":
        return Polygon(item["coords"])
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


removed = set()
for item in items:
    if item["kind"] not in {"pad", "via", "track"}:
        continue
    for route in routes:
        conflict = (
            item["net"] != route["net"]
            and set(item["layers"]) & set(route["layers"])
            and copper(item).distance(copper(route)) < 0.15
        )
        if item["kind"] == "pad":
            assert not conflict, item
            if route["kind"] == "via":
                assert Point(route["a"]).distance(copper(item)) >= 0.30
        elif conflict:
            removed.add(item["uuid"])
(root / "manual_routes.json").write_text(json.dumps(routes))
(root / "ripup_uuids.json").write_text(json.dumps(list(removed)))
print(
    "Replaced copper:",
    [(p["net"], p["kind"]) for p in items if p.get("uuid") in removed],
)
