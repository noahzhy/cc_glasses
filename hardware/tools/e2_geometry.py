"""Place the smaller receivers and trim only the side and lower rims."""

import json
import math
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union


ROOT = Path("hardware/ir_glasses/EVT_E2")
SOURCE = ROOT.parent / "EVT_E1"
geometry = json.loads((SOURCE / "geometry.json").read_text())
parts = json.loads((SOURCE / "parts.json").read_text())
holes = [Polygon(coords) for coords in geometry["holes"]]
old_outer = Polygon(geometry["outer"])
outer = old_outer.intersection(
    unary_union([*(hole.buffer(3.0, quad_segs=32) for hole in holes),
                 box(-100, -100, 100, -10.5)])
).simplify(0.005, preserve_topology=True)
outer = outer.union(outer.buffer(0.8, quad_segs=16).buffer(
    -0.8, quad_segs=16)).intersection(old_outer).simplify(0.005)
board = outer.difference(unary_union(holes))
records = []
for number in range(1, 17):
    for prefix in ["D", "PD"]:
        ref = f"{prefix}{number}"
        old = Point(parts[ref]["xy"])
        hole = min(holes, key=lambda item: item.distance(old))
        offset = 1.15 if prefix == "D" else 1.25
        ring = hole.buffer(offset, quad_segs=32).exterior
        station = ring.project(old)
        center = ring.interpolate(station)
        a = ring.interpolate((station - 0.4) % ring.length)
        b = ring.interpolate((station + 0.4) % ring.length)
        tangent = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
        copper = (box(-1.8, -0.75, 1.8, 0.75) if prefix == "PD"
                  else box(-1.7, -0.65, 1.7, 0.65))
        envelope = box(-1.7, -0.85, 1.7, 0.85)
        choices = []
        for delta in range(-10, 11):
            angle = tangent + delta
            pads = translate(rotate(copper, angle, origin=(0, 0)),
                             center.x, center.y)
            body = translate(rotate(envelope, angle, origin=(0, 0)),
                             center.x, center.y)
            clearance = pads.distance(board.boundary)
            if not board.covers(pads) or not board.covers(body):
                continue
            if clearance < 0.35 or body.distance(board.boundary) < 0.25:
                continue
            choices.append((abs(delta), -clearance, angle, clearance))
        _, _, angle, clearance = min(choices)
        # Keep the original end-to-end polarity orientation where possible.
        rotation = -angle
        if abs((rotation - parts[ref]["angle"] + 180) % 360 - 180) > 90:
            rotation += 180
        rotation = (rotation + 180) % 360 - 180
        parts[ref].update(xy=[round(center.x, 4), round(center.y, 4)],
                          angle=round(rotation, 3), side="front")
        records.append({"ref": ref, "center_to_hole_mm": offset,
                        "copper_to_edge_mm": round(clearance, 4),
                        "rotation_deg": round(rotation, 3)})
geometry["outer"] = list(outer.exterior.coords)
(ROOT / "geometry.json").write_text(json.dumps(geometry), encoding="utf-8")
(ROOT / "optics_target.json").write_text(json.dumps(
    {r["ref"]: parts[r["ref"]] for r in records}, indent=2), encoding="utf-8")
report = {
    "nominal_rim_width_mm": 3.0,
    "old_nominal_rim_width_mm": 3.7,
    "local_widening": [],
    "upper_transition_fillet_mm": 0.8,
    "eye_openings_unchanged": True,
    "upper_electronics_outline_unchanged_above_local_y_mm": -10.5,
    "width_mm": outer.bounds[2] - outer.bounds[0],
    "height_mm": outer.bounds[3] - outer.bounds[1],
    "material_area_mm2": board.area,
    "old_material_area_mm2": old_outer.difference(unary_union(holes)).area,
    "optics": records,
}
(ROOT / "mechanical_validation.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "optics"}, indent=2))
