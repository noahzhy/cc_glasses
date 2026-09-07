import json
from pathlib import Path
from shapely.geometry import Polygon, box

root = Path('hardware/tools')
holes = [Polygon(p).simplify(.08, preserve_topology=True)
         for p in json.loads((root / 'holes.json').read_text())]
outer = box(-76, -40, 76, 38).buffer(2, quad_segs=8)
(root / 'geometry.json').write_text(json.dumps({
    'outer': list(outer.exterior.coords),
    'holes': [list(p.exterior.coords) for p in holes],
}))
