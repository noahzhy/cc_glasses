"""Run the established geometry router with 0.10 mm tracks, including power stubs."""
from pathlib import Path
import sys
import json
PLANE_DATA=[]
if '--planes' in sys.argv:
 i=sys.argv.index('--planes');PLANE_DATA=json.load(open(sys.argv[i+1]));del sys.argv[i:i+2]
source=Path('.e6_work/power_fix/route_escape.py').read_text()
if '--coarse' in sys.argv:
 sys.argv.remove('--coarse')
 source=source.replace('step=.0125;origin=(43,56);W=10720;H=4320','step=.025;origin=(43,56);W=5360;H=2160')
source=source.replace("connections=[c for c in connections if c[1]['net'] not in ('3V3','GND')];",'')
if PLANE_DATA:
 source=source.replace(' aa,bb=find(aid),find(bid)', ''' for z in PLANE_DATA:
  if z['net']!=net:continue
  layer={0:0,2:3,4:1,6:2}[z['layer']];rr=[r for r in rows if r[1]==layer]
  if not rr:continue
  tree=STRtree([r[2] for r in rr])
  for pp in z['polys']:
   hits=list(tree.query(Polygon(pp['outer'],pp['holes']),predicate='intersects'))
   for j in hits[1:]:join(rr[hits[0]][0]['id'],rr[j][0]['id'])
 aa,bb=find(aid),find(bid)''')
 source=source.replace(' return images', ''' for z in PLANE_DATA:
  if z['net']!=net:continue
  layer={0:0,2:3,4:1,6:2}[z['layer']];rr=[r for r in rows if r[1]==layer]
  if not rr:continue
  tree=STRtree([r[2] for r in rr])
  for pp in z['polys']:
   shape=Polygon(pp['outer'],pp['holes']);hits=list(tree.query(shape,predicate='intersects'))
   if not hits:continue
   group=find(rr[hits[0]][0]['id'])
   if group==aa:drawpoly(draws[0][layer],shape,1)
   if group==bb:drawpoly(draws[1][layer],shape,1)
 return images''')
 source=source.replace('connections=[]', '''ground_target=next(e for e in G['items'] if e.get('ref')=='C2' and e['net']=='GND')
for e in G['items']:
 if e['type']=='pad' and e['net']=='GND' and e.get('ref') in ['U9','C10','C11','C29','C30','C40','C44','C45','C46','C47','R29','C17','C24','U19','C31','C8','C49']:
  D['unconnected_items'].append({'items':[{'uuid':v['id'],'pos':{'x':v['pos'][0],'y':v['pos'][1]}} for v in [e,ground_target]]})
connections=[]''')
source=source.replace("new=[];failed=[]", "connections.sort(key=lambda c: (0 if c[1]['net'] in ('ADC_A','ADC_B','BOOT0','LED_LAT','LED_SCLK','MUX_A1','3V3_A','GND','3V3','NRST') else 1, c[0]));new=[];failed=[]")
# J2 Tag-Connect keepout: permit traces but prohibit new vias in the entire connector rectangle.
source=source.replace('comp=component_images(net,ea[\'id\'],eb[\'id\'])',"vd.rectangle([pix((48.5,57.3)),pix((57.3,64.5))],fill=1)\n comp=component_images(net,ea['id'],eb['id'])")
exec(compile(source,'route_remaining_engine','exec'))
