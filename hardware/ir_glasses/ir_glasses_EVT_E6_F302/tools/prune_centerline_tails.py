import sys,json
from shapely.geometry import Point,Polygon,LineString
from shapely.strtree import STRtree
G=json.load(open(sys.argv[1]));D=json.load(open(sys.argv[2]));items={e['id']:e for e in G['items']};rm={i['uuid'] for v in D['violations'] if v['type'] in ['track_dangling','via_dangling'] for i in v['items']};rows=[]
for e in G['items']:
 if e['type']=='pad':ss=[(l,Polygon(p)) for l,p in e['polys']]
 else:ss=[(l,Point(e['start']).buffer(.000002) if e['type']=='via' else LineString([e['start'],e['end']]).buffer(.000002)) for l in e['layers']]
 for l,sh in ss:rows.append((e,l,sh))
tree=STRtree([r[2] for r in rows]);seednets={items[u]['net'] for u in rm if u in items}
for iteration in range(200):
 fresh=set()
 for e in G['items']:
  if e['id'] in rm or e['net'] not in seednets or e['net'] in ['GND','3V3'] or e['type']!='track':continue
  for pos in [e['start'],e['end']]:
   p=Point(pos).buffer(.000003);hit=False
   for idx in tree.query(p,predicate='intersects'):
    f,l,sh=rows[idx]
    if f['id']!=e['id'] and f['id'] not in rm and f['net']==e['net'] and l in e['layers']:hit=True;break
   if not hit:fresh.add(e['id']);break
 if not fresh:break
 rm.update(fresh)
json.dump({'remove_ids':list(rm)},open(sys.argv[3],'w'));print('pruned',len(rm),'in',iteration,'rounds')
