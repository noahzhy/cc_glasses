from pathlib import Path
import sexpdata as s,json,uuid
from shapely.geometry import box,LineString
R=Path(__file__).resolve().parents[1];b=s.load(open(R.parent/'ir_glasses_EVT_E6/ir_glasses_EVT_E6.kicad_pcb'));K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
rect=box(104.3,57.2,115.5,68.5);items=[]
for e in b:
 if K(e)!='segment' or C(e,'net')[-1] not in ['UART_TX','UART_RX']:continue
 line=LineString([C(e,'start')[1:3],C(e,'end')[1:3]])
 if not line.intersects(rect) or rect.covers(line):continue
 clipped=line.difference(rect)
 for q in list(clipped.geoms) if hasattr(clipped,'geoms') else [clipped]:
  if q.is_empty:continue
  items.append(dict(type='track',net=C(e,'net')[-1],width=C(e,'width')[1],layers=[['F.Cu','In1.Cu','In2.Cu','B.Cu'].index(C(e,'layer')[1])],start=list(q.coords[0]),end=list(q.coords[-1])))
(R/'evidence/uart_clips.json').write_text(json.dumps({'items':items}));print(items)
