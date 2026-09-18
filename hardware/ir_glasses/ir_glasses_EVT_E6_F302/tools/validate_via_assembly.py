#!/usr/bin/env python3
"""KiCad pcbnew audit of tented via holes near exposed SMD/test-pad copper."""
from pathlib import Path
import pcbnew as p,json,math,hashlib,collections
root=Path(__file__).resolve().parents[1];path=root/'ir_glasses_EVT_E6_F302.kicad_pcb';b=p.LoadBoard(str(path));pads=[]
xy=lambda q:(p.ToMM(q.x),p.ToMM(q.y))
def distance(q,a,z):
 dx,dy=z[0]-a[0],z[1]-a[1];den=dx*dx+dy*dy;t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/den)) if den else 0
 return math.hypot(q[0]-a[0]-t*dx,q[1]-a[1]-t*dy)
def pdist(q,poly):
 inside=False
 for a,z in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>q[1])!=(z[1]>q[1]) and q[0]<(z[0]-a[0])*(q[1]-a[1])/(z[1]-a[1])+a[0]:inside=not inside
 return 0 if inside else min(distance(q,a,z) for a,z in zip(poly,poly[1:]+poly[:1]))
for f in b.GetFootprints():
 for pad in f.Pads():
  if max(xy(pad.GetDrillSize())):continue
  for layer in [p.F_Cu,p.B_Cu]:
   if not pad.IsOnLayer(layer):continue
   poly=p.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,layer,0,p.FromMM(.002),p.ERROR_OUTSIDE)
   for j in range(poly.OutlineCount()):
    c=poly.Outline(j);pads.append((f.GetReference()+'.'+pad.GetNumber(),[xy(c.CPoint(k)) for k in range(c.PointCount())]))
nearest=[];sizes=collections.Counter()
for v in b.GetTracks():
 if not isinstance(v,p.PCB_VIA):continue
 pos=xy(v.GetPosition());drill=p.ToMM(v.GetDrillValue());diam=p.ToMM(v.GetWidth(p.F_Cu));sizes[(diam,drill)]+=1
 gap,ref=min((pdist(pos,poly)-drill/2,ref) for ref,poly in pads)
 nearest.append(dict(uuid=v.m_Uuid.AsString(),net=v.GetNetname(),xy_mm=pos,drill_mm=drill,diameter_mm=diam,nearest_pad=ref,hole_to_pad_mm=gap))
nearest.sort(key=lambda r:r['hole_to_pad_mm']);bad=[r for r in nearest if r['hole_to_pad_mm']<.10-1e-6]
report=dict(status='passed' if not bad else 'failed',board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scope='Actual via drill edge to outer SMD/test-pad copper, conservative 2um polygon; factory mask registration and tenting DFM remain pending',minimum_hole_to_pad_mm=nearest[0]['hole_to_pad_mm'],via_sizes=[dict(diameter_mm=d,drill_mm=h,count=n) for (d,h),n in sorted(sizes.items())],nearest_ten=nearest[:10],violations=bad)
(root/'via_assembly_validation.json').write_text(json.dumps(report,indent=2));assert not bad,bad
print('PASS:',len(nearest),'vias; minimum hole-to-pad',round(nearest[0]['hole_to_pad_mm'],4),'mm')
