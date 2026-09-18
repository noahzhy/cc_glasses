import sexpdata as s,sys,math
from pathlib import Path
from shapely.geometry import box,LineString
from shapely.ops import polygonize,unary_union
from shapely.affinity import rotate,translate
R=Path(__file__).resolve().parents[1];b=s.load(open(R/(R.name+'.kicad_pcb')));K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
shapes={}
for f in b:
 if K(f)!='footprint' or C(f,'layer')[1]!='F.Cu':continue
 ref=next(x[2] for x in f if K(x)=='property' and x[1]=='Reference');at=C(f,'at');lines=[];rect=[]
 for e in f:
  if not C(e,'layer') if isinstance(e,list) else True:continue
  if C(e,'layer')[1]!='F.CrtYd':continue
  if K(e)=='fp_rect':
   a=C(e,'start')[1:];z=C(e,'end')[1:];rect.append(box(min(a[0],z[0]),min(a[1],z[1]),max(a[0],z[0]),max(a[1],z[1])))
  if K(e)=='fp_line':lines.append(LineString([C(e,'start')[1:],C(e,'end')[1:]]))
 if not rect and not lines:continue
 shape=unary_union(rect+list(polygonize(lines)));shape=rotate(shape,-(at[3] if len(at)>3 else 0),origin=(0,0));shapes[ref]=translate(shape,at[1],at[2])
target=sys.argv[1];ob=unary_union([v for k,v in shapes.items() if k!=target]);out=[]
for ix in range(980,1051):
 for iy in range(640,691):
  x,y=ix/10,iy/10
  for a in [0,90]:
   q=translate(rotate(box(-.94,-.49,.94,.49),a,origin=(0,0)),x,y)
   if not q.intersects(ob):out.append((math.hypot(x-100.5,y-61.2),x,y,a))
print(sorted(out)[:20])
