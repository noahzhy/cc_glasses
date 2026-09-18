import sys,json
from shapely.geometry import Point,Polygon,LineString
from shapely.strtree import STRtree
G=json.load(open(sys.argv[1]));D=json.load(open(sys.argv[2]));items={e['id']:e for e in G['items']};rm={i['uuid'] for v in D['violations'] if v['type'] in ['track_dangling','via_dangling'] for i in v['items']};rows=[]
for e in G['items']:
 if e['type']=='pad':ss=[(l,Polygon(p)) for l,p in e['polys']]
 else:ss=[(l,Point(e['start']).buffer(e['width']/2) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(e['width']/2)) for l in e['layers']]
 for l,sh in ss:rows.append((e,l,sh))
tree=STRtree([r[2] for r in rows]);front=list(rm)
for iteration in range(500):
 candidates=set()
 for u in front:
  if u not in items or items[u]['type']=='pad':continue
  e=items[u]
  for xy in [e['start'],e['end']]:
   p=Point(xy).buffer(.000003)
   for idx in tree.query(p,predicate='intersects'):
    f,l,sh=rows[idx]
    if f['id'] not in rm and f['net']==e['net'] and l in e['layers'] and f['type']=='track':candidates.add(f['id'])
 fresh=set()
 for u in candidates:
  e=items[u]
  for pos in [e['start'],e['end']]:
   p=Point(pos).buffer(.000003);hit=False
   for idx in tree.query(p,predicate='intersects'):
    f,l,sh=rows[idx]
    if f['id']!=u and f['id'] not in rm and f['net']==e['net'] and l in e['layers']:hit=True;break
   if not hit:fresh.add(u);break
 if not fresh:break
 rm.update(fresh);front=list(fresh)
json.dump({'remove_ids':list(rm)},open(sys.argv[3],'w'));print('pruned attached',len(rm),'in',iteration,'rounds')
