import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path('hardware/tools/pylib').resolve()))
import sexpdata as sx
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union

root = Path('D:/Program Files/KiCad/10.0/share/kicad/symbols')
def children(node, name):
    return [x for x in node if isinstance(x, list) and str(x[0]) == name]

def pins(node):
    result = []
    for x in node:
        if isinstance(x, list):
            if str(x[0]) == 'pin':
                result.append((children(x, 'number')[0][1],
                               children(x, 'name')[0][1], str(x[1])))
            else:
                result.extend(pins(x))
    return result

for lib, name in [('MCU_ST_STM32C0', 'STM32C031C_4-6_Tx'),
                  ('Amplifier_Operational', 'TLV9061xDBV'),
                  ('Sensor_Motion', 'LSM6DS3TR-C')]:
    data = sx.loads((root / (lib + '.kicad_sym')).read_text())
    node = next((x for x in children(data, 'symbol') if x[1] == name), None)
    print(name, pins(node) if node else 'absent')
    if node and children(node, 'extends'):
        print('extends', children(node, 'extends'))

svg = Path('assets/blender/topview_outline.svg').read_text()
lines = [LineString([(float(a), float(b)), (float(c), float(d))])
         for a, b, c, d in re.findall(
             r'M ([-\d.]+) ([-\d.]+) L ([-\d.]+) ([-\d.]+)', svg)
         if (a, b) != (c, d)]
polys = sorted(polygonize(unary_union(lines)), key=lambda p: p.area,
               reverse=True)
print('polygons', [(round(p.area, 1), p.bounds) for p in polys[:8]])
Path('hardware/tools/holes.json').write_text(json.dumps(
    [list(p.exterior.coords) for p in polys[:2]]))
