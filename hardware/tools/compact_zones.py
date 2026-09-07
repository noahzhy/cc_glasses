"""Prepare two ground regions for the compact board."""

import json
from pathlib import Path

from shapely.geometry import Polygon, box

root = Path('hardware/ir_glasses/EVT_B')
geometry = json.loads((root / 'geometry.json').read_text())
outer = Polygon(geometry['outer'])
digital = box(-31, -42, 32, 0).intersection(outer)
analog = outer.difference(digital)
(root / 'zones.json').write_text(json.dumps({
    'GND': list(digital.exterior.coords),
    'AGND': list(analog.exterior.coords),
}))
for index in range(1, 17):
    parts = json.loads((root / 'parts.json').read_text())
    hole = Polygon(geometry['holes'][1 if index <= 8 else 0])
    from shapely.geometry import Point
    led = hole.distance(Point(parts[f'D{index}']['xy']))
    pd = hole.distance(Point(parts[f'PD{index}']['xy']))
    assert 1.7 < led < 2.1 and 5 < pd < 5.4
print('All 16 LEDs are closer to the eye openings than their paired PDs.')
