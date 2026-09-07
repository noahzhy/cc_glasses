"""Align optical footprints with local frame tangents and narrow the rims."""

import json
import math
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_D")
parts = json.loads((root / "parts.json").read_text())
reference = json.loads((root.parent / "EVT_C" / "parts.json").read_text())
g = json.loads((root / "geometry.json").read_text())
holes = [Polygon(h) for h in g["holes"]]
records = []
for number in range(1, 17):
    for prefix in ["PD", "D"]:
        ref = f"{prefix}{number}"
        old = Point(reference[ref]["xy"])
        hole = min(holes, key=lambda h: h.distance(old))
        best = None
        for offset in [1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0]:
            ring = hole.buffer(offset, quad_segs=32).exterior
            position = ring.project(old)
            p = ring.interpolate(position)
            a = ring.interpolate((position - 0.4) % ring.length)
            b = ring.interpolate((position + 0.4) % ring.length)
            tangent = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
            copper = (
                box(-2.25, -1.2, 2.25, 1.2)
                if prefix == "PD"
                else box(-1.7, -0.65, 1.7, 0.65)
            )
            body = (
                box(-1.6, -1.35, 1.6, 1.35)
                if prefix == "PD"
                else box(-1.5, -0.75, 1.5, 0.75)
            )
            for delta in range(-10, 11):
                angle = tangent + delta
                pads = translate(
                    rotate(copper, angle, origin=(0, 0)), p.x, p.y
                )
                case = translate(rotate(body, angle, origin=(0, 0)), p.x, p.y)
                if pads.distance(hole) < 0.35 or case.distance(hole) < 0.2:
                    continue
                required = max(
                    max(
                        hole.distance(Point(x, y))
                        for x, y in pads.exterior.coords
                    )
                    + 0.35,
                    max(
                        hole.distance(Point(x, y))
                        for x, y in case.exterior.coords
                    )
                    + 0.2,
                )
                score = (
                    required + abs(offset - 1.8) * 0.05 + abs(delta) * 0.002
                )
                if best is None or score < best[0]:
                    best = (score, p, angle, required, pads.distance(hole))
        assert best is not None, ref
        _, p, angle, required, inner = best
        parts[ref].update(
            xy=[round(p.x, 4), round(p.y, 4)], angle=round(-angle, 3)
        )
        records.append(
            {
                "ref": ref,
                "required_rim_mm": required,
                "inner_pad_clearance_mm": inner,
                "rotation_deg": round(-angle, 3),
            }
        )
width = math.ceil(max(r["required_rim_mm"] for r in records) * 10) / 10 + 0.1
outer = (
    unary_union(
        [
            *(h.buffer(width, quad_segs=16) for h in holes),
            box(-59, -27, 59, -20).buffer(1, quad_segs=8),
            box(-12, -24, 12, -12).buffer(1, quad_segs=8),
        ]
    )
    .buffer(0.8, quad_segs=8)
    .buffer(-0.8, quad_segs=8)
    .simplify(0.025)
)
g["outer"] = list(outer.exterior.coords)
(root / "parts.json").write_text(json.dumps(parts, indent=2))
(root / "geometry.json").write_text(json.dumps(g))
(root / "optical_orientation.json").write_text(
    json.dumps({"rim_width_mm": width, "items": records}, indent=2)
)
print(
    "Rim width:",
    width,
    "bounds:",
    outer.bounds,
    "material:",
    outer.difference(unary_union(holes)).area,
)
print("Maximum required width:", max(r["required_rim_mm"] for r in records))
