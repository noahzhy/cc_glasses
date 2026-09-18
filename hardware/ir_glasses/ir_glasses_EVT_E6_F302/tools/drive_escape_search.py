import json,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.strtree import STRtree
R=Path(__file__).resolve().parents[1];G=json.load(open(R/'evidence/geom19.json'));rows=[]
for e in G['items']:
 if e['net']=='DRIVE_A':continue
 sh=[(l,Polygon(p)) for l,p in e['polys']] if e['type']=='pad' else [(l,Point(e['start']).buffer(e['width']/2) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(e['width']/2)) for l in e['layers']]
 rows.extend((e,l,z) for l,z in sh)
layers=[[r for r in rows if r[1]==l] for l in range(4)];trees=[STRtree([r[2].buffer(.151) for r in a]) for a in layers];vt=STRtree([r[2].buffer(.285) for r in rows]);source=[100.175,64.5];pad=[103.14,66.3];best=None
def score(hits):
 es={e['id']:e for e in hits}
 if any(e['type']=='pad' for e in es.values()):return 1e9
 nets={e['net'] for e in es.values()};return sum(1000 if n.startswith(('LED_K','PD_IN','TIA')) else 10 for n in nets)+len(es)*.05
for ix in range(-15,16):
 for iy in range(-15,16):
  end=[round(pad[0]+ix*.1,5),round(pad[1]+iy*.1,5)]
  if math.dist(end,pad)<.6:continue
  base=[rows[j][0] for j in vt.query(Point(end),predicate='intersects')]+[layers[0][j][0] for j in trees[0].query(LineString([pad,end]),predicate='intersects')]
  if score(base)>=1e9:continue
  dx=end[0]-source[0];dy=end[1]-source[1];dd=min(abs(dx),abs(dy));sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1
  mids=[[source[0]+sx*dd,source[1]+sy*dd],[end[0]-sx*dd,end[1]-sy*dd],[source[0],end[1]],[end[0],source[1]]]
  for l in [1,2,3]:
   for mid in mids:
    line=LineString([source,mid,end]);hits=base+[layers[l][j][0] for j in trees[l].query(line,predicate='intersects')];value=score(hits)+line.length*.001
    if best is None or value<best[0]:best=(value,end,mid,l,{e['id']:e for e in hits})
value,end,mid,l,hits=best;print('score',value,'via',end,'layer',l,'nets',sorted(set(e['net'] for e in hits.values())))
items=[dict(type='via',start=end,end=end,width=.35,drill=.15,layers=[0,1,2,3],net='DRIVE_A')]
for a,b,ll in [(pad,end,0),(source,mid,l),(mid,end,l)]:
 if math.dist(a,b)>1e-5:items.append(dict(type='track',start=a,end=b,width=.1,layers=[ll],net='DRIVE_A'))
(R/'evidence/drive_escape_minrip.json').write_text(json.dumps({'remove_ids':list(hits),'items':items},indent=2))
