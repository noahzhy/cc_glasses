import json,math,sys
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import polygonize
from shapely.strtree import STRtree
R=Path(__file__).resolve().parents[1];G=json.load(open(sys.argv[1]));net=sys.argv[2] if len(sys.argv)>2 else 'UART_RX';source_ref,target_ref=('U5','U7') if net=='TIA13' else ('U9','R9');rows=[];ob=[]
board=max(polygonize([LineString(e) for e in G['edges']]),key=lambda q:q.area).buffer(-.35)
for e in G['items']:
 sh=[(l,Polygon(p)) for l,p in e['polys']] if e['type']=='pad' else [(l,Point(e['start']).buffer(e['width']/2) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(e['width']/2)) for l in e['layers']]
 for l,g in sh:(rows if e['net']==net else ob).append((e,l,g))
parent={e['id']:e['id'] for e,l,g in rows}
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for l in range(4):
 rr=[r for r in rows if r[1]==l];tree=STRtree([r[2].buffer(.000005) for r in rr])
 for i,(e,ll,g) in enumerate(rr):
  for j in tree.query(g.buffer(.000005),predicate='intersects'):parent[find(e['id'])]=find(rr[j][0]['id'])
aid=next(e['id'] for e,l,g in rows if e.get('ref')==source_ref);bid=next(e['id'] for e,l,g in rows if e.get('ref')==target_ref);aa,bb=find(aid),find(bid);assert aa!=bb
points=[set(),set()]
for e,l,g in rows:
 group=find(e['id'])
 if group not in [aa,bb]:continue
 xy=[e['pos']] if e['type']=='pad' else [e['start'],e['end']]
 for p in xy:points[0 if group==aa else 1].add((p[0],p[1],l))
layers=[[r for r in ob if r[1]==l] for l in range(4)];trees=[STRtree([r[2].buffer(.151) for r in a]) for a in layers];best=None
if net=='TIA13':points=[{p for p in group if 110<=p[0]<=121 and 57<=p[1]<=67} for group in points]
for a in points[0]:
 for b in points[1]:
  if a[2]!=b[2]:continue
  l=a[2];start=list(a[:2]);end=list(b[:2]);dx=end[0]-start[0];dy=end[1]-start[1];dd=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
  mids=[[start[0]+sx*dd,start[1]+sy*dd],[end[0]-sx*dd,end[1]-sy*dd],[start[0],end[1]],[end[0],start[1]]]
  paths=[[start,mid,end] for mid in mids]
  paths += [[start,[start[0],y],[end[0],y],end] for y in [57.5+i*.5 for i in range(31)]]
  paths += [[start,[x,start[1]],[x,end[1]],end] for x in [98+i*.5 for i in range(49)]]
  for path in paths:
   line=LineString(path)
   if not board.covers(line):continue
   hits={layers[l][j][0]['id']:layers[l][j][0] for j in trees[l].query(line,predicate='intersects')}
   if any(e['type']=='pad' for e in hits.values()):continue
   nets={e['net'] for e in hits.values()};score=sum(1000 if n.startswith(('LED_K','TIA','PD_IN','ADC','DRIVE','3V3','GND','VREF','UART_RX')) else 10 for n in nets)+len(hits)*.01+line.length*.001
   if best is None or score<best[0]:best=(score,path,l,hits)
score,path,l,hits=best;print('score',score,'layer',l,'path',path,'rip',sorted(set(e['net'] for e in hits.values())))
items=[dict(type='track',start=x,end=y,width=.1,layers=[l],net=net) for x,y in zip(path,path[1:]) if math.dist(x,y)>1e-5]
(R/('evidence/'+net.lower()+'_minrip.json')).write_text(json.dumps({'remove_ids':list(hits),'items':items},indent=2))
