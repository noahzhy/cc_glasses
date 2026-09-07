import json
import re
from pathlib import Path
from shapely.geometry import Polygon

p = Path('hardware/ir_glasses/refinement/ir_glasses.dsn')
s = p.read_text()
g = json.loads(Path('hardware/tools/geometry.json').read_text())
loops = []
for coords in g['holes']:
    polygon = Polygon(coords).buffer(.2, quad_segs=4).simplify(.02)
    points = ' '.join(f'{(x + 110) * 1000:.1f} {-(y + 85) * 1000:.1f}'
                      for x, y in polygon.exterior.coords)
    loops.append(f'(keepout "" (polygon signal 0 {points}))')
index = iter(loops)
s = re.sub(r'\(keepout "" \(polygon signal 0 .*?\)\)',
           lambda _: next(index), s, count=2, flags=re.S)
p.write_text(s)
