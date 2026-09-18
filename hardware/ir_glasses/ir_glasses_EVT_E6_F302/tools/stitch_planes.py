import json,sys,uuid
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import polygonize,unary_union
from shapely.strtree import STRtree
G=json.load(open(sys.argv[1]));zones=json.load(open(sys.argv[2]));rows=[];out=[]
for e in G['items']:
 if e['type']=='pad':sh=[(l,Polygon(p)) for l,p in e['polys']]
 else:
  p=Point(e['start']).buffer(e['width']/2) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(e['width']/2)
  sh=[(l,p) for l in e['layers']]
 for l,g in sh:rows.append((e,l,g))
for z in zones:
 for pp in z['polys']:
  e={'id':str(uuid.uuid4()),'type':'zone','net':z['net']};rows.append((e,{0:0,2:3,4:1,6:2}[z['layer']],Polygon(pp['outer'],pp['holes'])))
board=max(polygonize([LineString(e) for e in G['edges']]),key=lambda p:p.area)
for net in ['GND','3V3']:
 rr=[r for r in rows if r[0]['net']==net];parent={e['id']:e['id'] for e,l,g in rr}
 def find(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 for l in range(4):
  layer=[r for r in rr if r[1]==l];sh=[r[2].buffer(.000001) for r in layer];tree=STRtree(sh)
  for i,g in enumerate(sh):
   for j in tree.query(g,predicate='intersects'):parent[find(layer[i][0]['id'])]=find(layer[j][0]['id'])
 groups={}
 for e,l,g in rr:groups.setdefault(find(e['id']),[]).append((e,l,g))
 root=max(groups,key=lambda k:sum(g.area for e,l,g in groups[k]));rootshape=unary_union([g for e,l,g in groups[root]])
 obstacle=[]
 for e,l,g in rows:
  if e['type']=='zone':continue
  if e['net']!=net:obstacle.append(g.buffer(.52 if e['type']=='pad' and max(e.get('drill',[0]))>0 else .285))
  elif e['type']=='pad':obstacle.append(g.buffer(.18))
  elif e['type']=='via':obstacle.append(g.buffer(.30))
 safe=board.buffer(-.505).difference(unary_union(obstacle)).difference(box(48.5,57.3,57.3,64.5))
 netcode=next(e['netcode'] for e in G['items'] if e['net']==net)
 for k,group in groups.items():
  if k==root:continue
  shape=unary_union([g for e,l,g in group]);allowed=shape.intersection(rootshape).intersection(safe)
  pads=sorted(set(e.get('ref','') for e,l,g in group if e['type']=='pad'))
  if allowed.is_empty:print(net,'NO VIA OVERLAP',pads,shape.bounds,flush=True);continue
  pt=allowed.representative_point();pos=[round(pt.x,5),round(pt.y,5)];print(net,'VIA',pos,pads,flush=True)
  out.append({'type':'via','start':pos,'end':pos,'width':.35,'drill':.15,'layers':list(range(4)),'net':net,'netcode':netcode})
  safe=safe.difference(pt.buffer(.58));rootshape=unary_union([rootshape,shape])
json.dump({'items':out},open(sys.argv[3],'w'));print('Added',len(out))
