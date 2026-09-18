"""Find short top-side ground escapes into filled inner ground copper."""
import json,sys,math
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
G=json.load(open(sys.argv[1]));D=json.load(open(sys.argv[2]));Z=json.load(open(sys.argv[3]));items={e['id']:e for e in G['items']};out=[]
polys=[Polygon(p['outer'],p['holes']) for z in Z if z['net']=='GND' and z['layer']==4 for p in z['polys']];plane=unary_union(polys)
targets={i['uuid'] for v in D['unconnected_items'] for i in v['items'] if i['uuid'] in items and items[i['uuid']]['type']=='pad' and items[i['uuid']]['net']=='GND'}
if '--force' in sys.argv:targets.update(e['id'] for e in G['items'] if e['type']=='pad' and e['net']=='GND' and e.get('ref') in ['U9','C10','R29'])
for uid in targets:
 pad=items[uid];start=pad['pos'];trace_ob=[];via_ob=[]
 for e in G['items']+out:
  if e['type']=='pad':shapes=[(l,Polygon(p)) for l,p in e['polys']]
  else:
   sh=Point(e['start']).buffer(e['width']/2) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(e['width']/2);shapes=[(l,sh) for l in e['layers']]
  for l,sh in shapes:
   if e['net']!='GND':
    if l==0:trace_ob.append(sh.buffer(.151))
    via_ob.append(sh.buffer(.285))
   elif e['type']=='pad':via_ob.append(sh.buffer(.18))
   elif e['type']=='via':via_ob.append(sh.buffer(.28))
 to=unary_union(trace_ob);vo=unary_union(via_ob);solutions=[]
 for ix in range(-40,41):
  for iy in range(-40,41):
   end=[round(start[0]+ix*.1,5),round(start[1]+iy*.1,5)];pt=Point(end)
   if not plane.contains(pt) or vo.intersects(pt):continue
   dx=end[0]-start[0];dy=end[1]-start[1];diag=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
   for mid in [[start[0]+sx*diag,start[1]+sy*diag],[end[0]-sx*diag,end[1]-sy*diag]]:
    line=LineString([start,mid,end])
    if not line.intersects(to):solutions.append((line.length,end,mid))
 if not solutions:print('NO GND ESCAPE',pad.get('ref'),start);continue
 _,end,mid=min(solutions);code=pad['netcode']
 for a,b in [(start,mid),(mid,end)]:
  if math.dist(a,b)>1e-5:out.append(dict(type='track',start=a,end=b,width=.1,layers=[0],net='GND',netcode=code))
 out.append(dict(type='via',start=end,end=end,width=.35,drill=.15,layers=[0,1,2,3],net='GND',netcode=code));print('GND escape',pad.get('ref'),start,'->',end)
json.dump({'items':out},open(sys.argv[4],'w'))
