"""Deterministic courtyard-aware placement of E6 additions and displaced passives."""
import sexpdata as sx,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,LineString
from shapely.ops import polygonize
ROOT=Path(__file__).resolve().parents[1]
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
b=sx.load(open(ROOT/'ir_glasses_EVT_E6.kicad_pcb'));parts=json.load(open(ROOT/'parts.json'))
lines=[]
for e in b:
 if K(e)=='gr_line' and C(e,'layer')[1]=='Edge.Cuts':lines.append(LineString([C(e,'start')[1:3],C(e,'end')[1:3]]))
poly=max(polygonize(lines),key=lambda p:p.area).buffer(-.1)
shapes={};orig={}
for f in b:
 if K(f)!='footprint':continue
 r=next(e[2] for e in f if K(e)=='property' and e[1]=='Reference');a=C(f,'at');orig[r]=parts[r]['pcb_xy']+[parts[r]['angle']]
 pts=[]
 for e in f:
  l=C(e,'layer') if isinstance(e,list) else None
  if l and l[1]=='F.CrtYd':
   if K(e)=='fp_circle':
    cen=C(e,'center')[1:3];end=C(e,'end')[1:3];radius=math.dist(cen,end);pts.extend([[cen[0]-radius,cen[1]-radius],[cen[0]+radius,cen[1]+radius]]);continue
   for key in ['start','end','center']:
    p=C(e,key)
    if p:pts.append(p[1:3])
 if not pts:
  for e in f:
   if K(e)=='pad':
    a=C(e,'at');sz=C(e,'size');pts.extend([[a[1]-sz[1]/2-.2,a[2]-sz[2]/2-.2],[a[1]+sz[1]/2+.2,a[2]+sz[2]/2+.2]])
 pts=np.array(pts);shapes[r]=(pts.min(0),pts.max(0))
def bounds(r,xy):
 mn,mx=shapes[r];th=math.radians(xy[2]);cs=math.cos(th);sn=math.sin(th)
 pts=np.array([[mn[0],mn[1]],[mn[0],mx[1]],[mx[0],mn[1]],[mx[0],mx[1]]]);rot=pts@np.array([[cs,-sn],[sn,cs]])+xy[:2]
 return np.r_[rot.min(0)-.026,rot.max(0)+.026]
def hit(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
# Fixed layout anchors. Buffers rotated so their long lead span runs vertically.
anchors={'U7':[94.5,61.6,90],'U8':[132.75,61.4,90],'U16':[102,61.2,90],'U17':[125.6,61.2,90],'U15':[114.5,70.7,0],'U13':[117.5,66.6,0]}
# Keep all other ICs, connectors, and optical components exactly at the E4 position.
fixed={r:xy for r,xy in orig.items() if r in ('C28','C37','R19') or r.startswith(('U','J','PD')) or (r.startswith('D') and r[1:].isdigit())}
fixed.update(anchors)
placed={r:xy for r,xy in orig.items() if r.startswith('TP')};boxes={}
for r,xy in fixed.items():
 bb=bounds(r,xy)
 for other,v in boxes.items():
  if hit(bb,v) and (r in anchors or other in anchors):raise RuntimeError(f'IC anchor collision {r} {other}')
 if not poly.covers(box(*bb)):pass
 placed[r]=xy;boxes[r]=bb
new=set(['R11','R12','C29','C30']+[r for r in parts if r not in json.load(open(ROOT.parent/'ir_glasses_EVT_E4/parts.json'))])
# Retain passives that remain clear of new circuitry; move test points first if necessary.
todo=[]
for r,xy in orig.items():
 if r in placed:continue
 bb=bounds(r,xy)
 if r not in new and not any(hit(bb,v) for v in boxes.values()):placed[r]=xy;boxes[r]=bb
 else:todo.append(r)
# Placement target = functional neighbor; capacitors grouped around their ICs.
target={'C39':[115.4,68.6],'C40':[113.2,70.2],'C41':[113.2,71.3],'C42':[115.4,73],'C43':[117.5,70.8],'R25':[115.4,68.6],'R26':[117.5,69], 'C29':[116.4,73],'C30':[114.4,73], 'R11':[117,73],'R12':[113.4,73], 'C44':[102,57.6],'C46':[102,58],'C45':[125.6,57.6],'C47':[125.6,58], 'R21':[102,65],'R22':[102,66.2], 'R23':[125.6,65],'R24':[125.6,66.2],'C8':[90,65.8],'C9':[127,65.8],'R27':[104,70]}
# New decouplers are placed before displaced general passives. For clearance, move old nearby passives too.
for r in list(placed):
 if r in fixed or r.startswith('TP'):continue
 bb=boxes[r]
 if (100<placed[r][0]<119 and placed[r][1]>68) or (100<placed[r][0]<104 and placed[r][1]<59) or (123<placed[r][0]<128 and placed[r][1]<59):
  del placed[r];del boxes[r];todo.append(r)
priority=list(target)+sorted(todo,key=lambda r:(0 if r.startswith(('RF','CF')) else 1 if r in json.load(open(ROOT.parent/'ir_glasses_EVT_E4/parts.json')) else 2,-(shapes[r][1]-shapes[r][0]).prod()))
todo=list(dict.fromkeys(r for r in priority if r in todo))
for r in todo:
 tx,ty=target.get(r,orig[r][:2]);best=None
 # Evaluate distance-ordered sites at 0.25mm pitch; retain sensible local placement.
 radius=100 if r.startswith('R') and r[1:].isdigit() and int(r[1:])>=28 else 35
 coords=[(float(x),float(y)) for x in np.arange(max(47,tx-radius),min(173,tx+radius)+.01,.25) for y in np.arange(57.5,74,.25)]
 coords.sort(key=lambda t:(t[0]-tx)**2+(t[1]-ty)**2)
 for x,y in coords:
  for a in [orig[r][2],(orig[r][2]+90)%180]:
   xy=[round(x,4),round(y,4),a];bb=bounds(r,xy)
   if any(hit(bb,v) for v in boxes.values()):continue
   if not poly.covers(box(*bb)):continue
   best=xy;break
  if best:break
 if best is None:raise RuntimeError('No placement '+r)
 placed[r]=best;boxes[r]=bounds(r,best)
 print(r,'->',best,'distance',round(math.dist(best[:2],[tx,ty]),2))
changes={r:xy for r,xy in placed.items() if xy!=orig[r] or r in anchors or r in new}
(ROOT/'placement.json').write_text(json.dumps(changes,indent=2));print('Placed',len(placed),'changed',len(changes))
