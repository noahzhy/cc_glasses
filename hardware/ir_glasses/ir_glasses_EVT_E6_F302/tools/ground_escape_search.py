import json,math,sys
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.strtree import STRtree
from shapely.ops import polygonize
R=Path(__file__).resolve().parents[1];G=json.load(open(sys.argv[1] if len(sys.argv)>1 else R/'evidence/geom20.json'));rows=[]
board=max(polygonize([LineString(e) for e in G['edges']]),key=lambda q:q.area).buffer(-.35)
for e in G['items']:
 if e['net']=='GND':continue
 sh=[Polygon(p) for l,p in e['polys'] if l==0] if e['type']=='pad' else [Point(e['start']).buffer(e['width']/2) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(e['width']/2)] if 0 in e['layers'] else []
 rows.extend((e,s.buffer(.151)) for s in sh)
starts=json.loads(sys.argv[2]) if len(sys.argv)>2 else [[104.13,59.5],[107.75,58.8375],[112.25,67.1625]]
excluded={e.get('ref') for e in G['items'] if e['type']=='pad' and e['net']=='GND' and e['pos'] in starts}
tree=STRtree([s for e,s in rows]);targets=[e['start'] for e in G['items'] if e['type']=='via' and e['net']=='GND'];targets += [e['pos'] for e in G['items'] if e['type']=='pad' and e['net']=='GND' and e.get('ref') not in excluded];out=[];rm=set()
for start in starts:
 best=None
 for end in targets:
  if math.dist(start,end)>10:continue
  dx=end[0]-start[0];dy=end[1]-start[1];dd=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
  paths=[[start,[start[0]+sx*dd,start[1]+sy*dd],end],[start,[end[0]-sx*dd,end[1]-sy*dd],end],[start,[start[0],end[1]],end],[start,[end[0],start[1]],end]]
  for offset in [.8,1.1,1.4,1.8,2.2]:
   for sign in [-1,1]:paths.append([start,[start[0],start[1]+sign*offset],[end[0],start[1]+sign*offset],end])
   for sign in [-1,1]:paths.append([start,[start[0]+sign*offset,start[1]],[start[0]+sign*offset,end[1]],end])
  for path in paths:
   line=LineString(path)
   if not board.covers(line):continue
   hits={rows[j][0]['id']:rows[j][0] for j in tree.query(line,predicate='intersects')}
   if any(e['type']=='pad' for e in hits.values()):continue
   nets={e['net'] for e in hits.values()};score=sum(1000 if n.startswith(('LED_K','TIA','PD_IN','ADC','DRIVE')) else 10 for n in nets)+len(hits)*.01+line.length*.001
   if best is None or score<best[0]:best=(score,path,hits)
 score,path,hits=best;rm.update(hits);print(start,'->',path[-1],score,sorted(set(e['net'] for e in hits.values())))
 for a,b in zip(path,path[1:]):
  if math.dist(a,b)>1e-5:out.append(dict(type='track',start=a,end=b,width=.1,layers=[0],net='GND'))
(R/'evidence/ground_minrip.json').write_text(json.dumps({'remove_ids':list(rm),'items':out},indent=2))
