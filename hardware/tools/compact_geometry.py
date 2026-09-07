"""Plan a compact outline with LEDs on the inner optical ring."""

import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import nearest_points, unary_union

root = Path('hardware/ir_glasses')
source = root / 'EVT_A'
target = root / 'EVT_B'
target.mkdir(exist_ok=True)
parts = json.loads((source / 'parts.json').read_text())
geometry = json.loads(Path('hardware/tools/geometry.json').read_text())
holes = [Polygon(p) for p in geometry['holes']]
for index in range(1, 17):
    hole = holes[1 if index <= 8 else 0]
    old = Point(parts[f'PD{index}']['xy'])
    edge = nearest_points(hole.boundary, old)[0]
    dx, dy = old.x - edge.x, old.y - edge.y
    length = math.hypot(dx, dy)
    nx, ny = dx / length, dy / length
    angle = round(math.degrees(math.atan2(nx, ny)) / 45) * 45
    for ref, distance in [(f'D{index}', 1.9), (f'PD{index}', 5.2)]:
        parts[ref]['xy'] = [round(edge.x + nx * distance, 3),
                            round(edge.y + ny * distance, 3)]
        parts[ref]['angle'] = angle
for index in range(1, 9):
    for prefix in ['D', 'PD']:
        left = parts[f'{prefix}{index}']
        right = parts[f'{prefix}{index + 8}']
        right['xy'] = [-left['xy'][0], left['xy'][1]]
        right['angle'] = -left['angle']
for ref, part in parts.items():
    if ref.startswith(('PD', 'D', 'TP')):
        continue
    if part['xy'][1] >= 28:
        part['xy'][1] -= 4
parts['D17']['xy'] = [31, -27]
parts['C25']['xy'] = [34, -36.4]
parts['C19']['xy'] = [-2, -36.6]
for index in range(1, 13):
    x = -65 + (index - 1) * 3.5 if index <= 6 else 47.5 + (index - 7) * 3.5
    parts[f'TP{index}']['xy'] = [x, -30]
outer = unary_union([
    *(h.buffer(8, quad_segs=8) for h in holes),
    box(-65, -35.5, 65, -24).buffer(2, quad_segs=8),
    box(-54, 23, 54, 32).buffer(2, quad_segs=8),
    box(-10, -30, 10, 28),
]).buffer(1, quad_segs=8).buffer(-1, quad_segs=8).simplify(.05)
(target / 'parts.json').write_text(json.dumps(parts, indent=2))
(target / 'geometry.json').write_text(json.dumps({
    'outer': list(outer.exterior.coords), 'holes': geometry['holes'],
}))
old = Polygon(geometry['outer']).difference(unary_union(holes))
new = outer.difference(unary_union(holes))
print('Bounds:', outer.bounds)
print('Board material area reduction:', 1 - new.area / old.area)

