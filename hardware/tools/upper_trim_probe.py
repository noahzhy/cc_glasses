import json
from pathlib import Path
from shapely.geometry import LineString,Point
items=json.loads(Path('hardware/ir_glasses/EVT_D/route_geometry.json').read_text())
for ident in ['3d7c7ae0-bb16-463a-9c9f-5aaa19026970','cce4010c-d627-4378-bfde-f2138a8a3382','740a7508-31a1-49bd-987b-ff933b8f3a43']:
    t=next(t for t in items if t.get('uuid')==ident); line=LineString([t['a'],t['b']]); contacts=[]
    for o in items:
        if o is t or o['net']!=t['net'] or not set(o['layers'])&set(t['layers']): continue
        pts=[o['xy']] if o['kind']=='pad' else [o['a'],o['b']]
        for xy in pts:
            p=Point(xy)
            if line.distance(p)<.151:
                contacts.append([line.project(p),xy,o.get('uuid',o.get('ref'))])
    print(t,contacts)
