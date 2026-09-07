import json
import math
from pathlib import Path
from shapely.geometry import Point, Polygon, box
from shapely.affinity import rotate, translate

root = Path("hardware/ir_glasses/EVT_D")
p = json.loads((root / "parts.json").read_text())
g = json.loads((root / "geometry.json").read_text())
outer = Polygon(g["outer"])
holes = [Polygon(h) for h in g["holes"]]
for ref, neighbor in [("D8", "PD8"), ("D16", "PD16")]:
    old = Point(p[ref]["xy"])
    hole = min(holes, key=lambda h: h.distance(old))
    np = p[neighbor]
    courtyard = translate(
        rotate(box(-2.5, -1.6, 2.5, 1.6), -np["angle"], origin=(0, 0)),
        *np["xy"],
    )
    best = None
    for offset in [1.65, 1.7, 1.75, 1.8]:
        ring = hole.buffer(offset, quad_segs=32).exterior
        start = ring.project(old)
        for step in range(-20, 21):
            pos = start + step * 0.05
            pt = ring.interpolate(pos % ring.length)
            a = ring.interpolate((pos - 0.4) % ring.length)
            b = ring.interpolate((pos + 0.4) % ring.length)
            angle = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
            pads = translate(
                rotate(box(-1.7, -0.65, 1.7, 0.65), angle, origin=(0, 0)),
                pt.x,
                pt.y,
            )
            court = translate(
                rotate(box(-1.95, -1, 1.95, 1), angle, origin=(0, 0)),
                pt.x,
                pt.y,
            )
            if (
                pads.distance(hole) < 0.35
                or not outer.buffer(-0.35).covers(pads)
                or court.distance(courtyard) < 0.05
            ):
                continue
            score = pt.distance(old)
            if best is None or score < best[0]:
                best = (score, pt, angle)
    assert best, ref
    _, pt, angle = best
    p[ref].update(xy=[round(pt.x, 4), round(pt.y, 4)], angle=round(-angle, 3))
    print(ref, p[ref]["xy"], p[ref]["angle"], "shift", best[0])
(root / "parts.json").write_text(json.dumps(p, indent=2))
