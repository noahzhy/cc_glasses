"""Apply routing margins around the optical cutouts."""

import json
import re
from pathlib import Path

from shapely.geometry import Polygon

root = Path("hardware/ir_glasses/EVT_C")
filename = root / "ir_glasses.dsn"
text = filename.read_text()
geometry = json.loads((root / "geometry.json").read_text())
loops = []
for coords in geometry["holes"]:
    polygon = Polygon(coords).buffer(0.25, quad_segs=4).simplify(0.02)
    points = " ".join(
        f"{(x + 110) * 1000:.1f} {-(y + 85) * 1000:.1f}"
        for x, y in polygon.exterior.coords
    )
    loops.append(f'(keepout "" (polygon signal 0 {points}))')
index = iter(loops)
text = re.sub(
    r'\(keepout "" \(polygon signal 0 .*?\)\)',
    lambda _: next(index),
    text,
    count=2,
    flags=re.S,
)
text = text.replace("(width 180)", "(width 150)")
filename.write_text(text)
