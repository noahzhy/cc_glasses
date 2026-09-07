"""Record the optical ring geometry from the final placement."""

import csv
import json
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

root = Path('hardware/ir_glasses/EVT_B')
parts = json.loads((root / 'parts.json').read_text())
geometry = json.loads((root / 'geometry.json').read_text())
holes = [Polygon(p) for p in geometry['holes']]
with (root / 'optical_clearance.csv').open('w', newline='') as output:
    writer = csv.writer(output)
    writer.writerow(['LED', 'PD', 'LED_center_to_opening_mm',
                     'PD_center_to_opening_mm'])
    for index in range(1, 17):
        hole = holes[1 if index <= 8 else 0]
        led = hole.distance(Point(parts[f'D{index}']['xy']))
        pd = hole.distance(Point(parts[f'PD{index}']['xy']))
        assert 1.7 < led < 2.1 and 5 < pd < 5.4
        writer.writerow([f'D{index}', f'PD{index}', round(led, 3),
                         round(pd, 3)])
outer = Polygon(geometry['outer'])
old = json.loads(Path('hardware/tools/geometry.json').read_text())
old_area = Polygon(old['outer']).difference(unary_union(holes)).area
new_area = outer.difference(unary_union(holes)).area
(root / 'mechanical_validation.json').write_text(json.dumps({
    'board_area_mm2': round(new_area, 2),
    'previous_board_area_mm2': round(old_area, 2),
    'board_material_reduction_percent': round(100 * (1 - new_area / old_area), 2),
    'original_eye_openings_preserved': geometry['holes'] == old['holes'],
    'all_leds_inside_pd_ring': True,
}, indent=2))
