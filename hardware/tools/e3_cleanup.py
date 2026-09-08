"""Trim dangling copper and replace unused via junctions with planar stars."""

import json
import sys
import uuid
from pathlib import Path

import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points

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
report = json.loads((root / "drc.json").read_text(encoding="utf-8"))


def shape(p):
    if p["kind"] in {"zone", "pad", "keepout"}:
        return Polygon(p["coords"]).buffer(0)
    if p["kind"] == "via":
        return Point(p["a"]).buffer(p["width"] / 2)
    return LineString([p["a"], p["b"]]).buffer(p["width"] / 2)


shapes = [shape(p) for p in items]
tree = shapely.STRtree(shapes)
lookup = {p["uuid"]: i for i, p in enumerate(items) if "uuid" in p}
actions, stars = {}, []
for issue in report["violations"]:
    if issue["type"] not in {"track_dangling", "via_dangling"}:
        continue
    if "--tracks-only" in sys.argv and issue["type"] == "via_dangling":
        continue
    uid = issue["items"][0]["uuid"]
    if uid not in lookup:
        continue
    index = lookup[uid]
    item = items[index]
    nearby = [
        i
        for i in tree.query(shapes[index], predicate="dwithin", distance=0.001)
        if i != index
        and items[i]["net"] == item["net"]
        and set(items[i]["layers"]) & set(item["layers"])
    ]
    if issue["type"] == "via_dangling":
        center = Point(item["a"])
        for i in nearby:
            other = items[i]
            if other["kind"] != "track":
                continue
            line = LineString([other["a"], other["b"]])
            start = line.interpolate(line.project(center))
            if start.distance(center) > 0.0001:
                stars.append(
                    dict(
                        a=list(start.coords[0]),
                        b=item["a"],
                        net=item["net"],
                        layer=other["layers"][0],
                    )
                )
        actions[uid] = None
        continue
    line = LineString([item["a"], item["b"]])
    if line.length < 0.00001:
        actions[uid] = None
        continue
    anchors = []
    for i in nearby:
        other = items[i]
        if other["kind"] in {"track", "via"}:
            axis = (
                LineString([other["a"], other["b"]])
                if other["kind"] == "track"
                else Point(other["a"])
            )
            here, there = nearest_points(line, axis)
            anchors.append(line.project(here))
            if here.distance(there) > 0.0001:
                stars.append(
                    dict(
                        a=list(here.coords[0]),
                        b=list(there.coords[0]),
                        net=item["net"],
                        layer=item["layers"][0],
                    )
                )
            continue
        contact = line.intersection(shapes[i])
        if contact.is_empty:
            continue
        pieces = list(getattr(contact, "geoms", [contact]))
        for piece in pieces:
            if piece.geom_type not in {"LineString", "Point"}:
                continue
            point = (
                piece.interpolate(0.5, normalized=True)
                if piece.geom_type == "LineString"
                else piece
            )
            anchors.append(line.project(point))
    if len(anchors) < 2 or max(anchors) - min(anchors) < 0.0001:
        actions[uid] = None
    else:
        actions[uid] = [
            list(line.interpolate(v).coords[0])
            for v in [min(anchors), max(anchors)]
        ]

path = root / "ir_glasses.kicad_pcb"
board = sx.loads(path.read_text(encoding="utf-8"))
for node in board[:]:
    if not isinstance(node, list) or str(node[0]) not in {"segment", "via"}:
        continue
    uid = next(
        v[1] for v in node if isinstance(v, list) and str(v[0]) == "uuid"
    )
    if uid not in actions:
        continue
    if actions[uid] is None:
        board.remove(node)
    else:
        for key, point in zip(["start", "end"], actions[uid]):
            value = next(
                v for v in node if isinstance(v, list) and str(v[0]) == key
            )
            value[1:] = [round(v, 6) for v in point]
unique = {}
for star in stars:
    ends = sorted(tuple(round(v, 6) for v in star[p]) for p in ["a", "b"])
    unique[star["net"], star["layer"], *ends] = star
for star in unique.values():
    layer = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"][star["layer"]]
    board.append(
        [
            sx.Symbol("segment"),
            [sx.Symbol("start"), *[round(v, 6) for v in star["a"]]],
            [sx.Symbol("end"), *[round(v, 6) for v in star["b"]]],
            [sx.Symbol("width"), 0.15],
            [sx.Symbol("layer"), layer],
            [sx.Symbol("net"), star["net"]],
            [sx.Symbol("uuid"), str(uuid.uuid4())],
        ]
    )
seen = set()
for node in board[:]:
    if not isinstance(node, list) or str(node[0]) != "segment":
        continue
    fields = {str(v[0]): v[1:] for v in node[1:] if isinstance(v, list)}
    ends = sorted(tuple(fields[k]) for k in ["start", "end"])
    key = (fields["net"][0], fields["layer"][0], fields["width"][0], *ends)
    if key in seen:
        board.remove(node)
    seen.add(key)
path.write_text(sx.dumps(board), encoding="utf-8")
print("Dangling copper edits:", len(actions), "planar spokes:", len(stars))
