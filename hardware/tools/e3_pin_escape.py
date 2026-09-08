"""Reserve two driver exits and reconnect the PA10 debug test point."""

import json
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon

root = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((root / "route_geometry.json").read_text())
pads = {(p["ref"], p["pin"]): p for p in items if p["kind"] == "pad"}
routes = []


def path(net, points, layer):
    for a, b in zip(points, points[1:]):
        routes.append(
            dict(kind="track", net=net, a=a, b=b, width=0.15, layers=[layer])
        )


path("LED_LAT", [[118.25, 60.75], [115.0, 60.75]], 3)
path("LED_K1", [[117.55, 61.25], [115.0, 61.25]], 3)
path("BOOT_RX_PA10", [pads["U9", "32"]["xy"], [113.1, 62.25]], 0)
path("BOOT_RX_PA10", [[113.1, 62.25], [116.65, 62.25], [116.7, 62.2]], 3)
path("BOOT_RX_PA10", [[116.7, 62.2], [116.7, 63.1], pads["TP6", "1"]["xy"]], 0)
for xy in [[113.1, 62.25], [116.7, 62.2]]:
    routes.append(
        dict(
            kind="via",
            net="BOOT_RX_PA10",
            a=xy,
            b=xy,
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


protected = set(json.loads((root / "u1_fanout_uuids.json").read_text()))
removed = set()
for item in items:
    if item["kind"] not in {"pad", "track", "via"}:
        continue
    shape = copper(item)
    for route in routes:
        conflict = (
            item["net"] != route["net"]
            and set(item["layers"]) & set(route["layers"])
            and shape.distance(copper(route)) < 0.152
        )
        if item["kind"] == "pad":
            assert not conflict, (item["ref"], item["pin"], route)
            if route["kind"] == "via":
                assert Point(route["a"]).distance(shape) >= 0.3
            continue
        replace_boot = item["net"] == "BOOT_RX_PA10"
        if conflict or replace_boot:
            assert item["uuid"] not in protected
            removed.add(item["uuid"])
(root / "manual_routes.json").write_text(json.dumps(routes))
(root / "ripup_uuids.json").write_text(json.dumps(sorted(removed)))
print("Reserved exits:", len(routes), "replaced items:", len(removed))
