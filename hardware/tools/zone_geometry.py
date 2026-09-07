import json
from pathlib import Path
from shapely.geometry import Polygon, box

root = Path('hardware/tools')
g = json.loads((root / 'geometry.json').read_text())
outer = Polygon(g['outer'])
digital = box(-31, -42, 32, 0).intersection(outer)
analog = outer.difference(digital)
(root / 'zones.json').write_text(json.dumps({
    'GND': list(digital.exterior.coords),
    'AGND': list(analog.exterior.coords),
}))
