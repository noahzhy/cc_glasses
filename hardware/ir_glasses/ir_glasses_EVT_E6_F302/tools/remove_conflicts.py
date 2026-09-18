from pathlib import Path
import json,sys,sexpdata as s
R=Path(__file__).resolve().parents[1];p=R/(R.name+'.kicad_pcb');b=s.load(open(p));K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
d=json.load(open(sys.argv[1]));ids=set()
for v in d['violations']:
 if v['type'] in ['clearance','shorting_items','hole_clearance','solder_mask_bridge','track_dangling','via_dangling','track_not_centered_on_via']:
  ids.update(x['uuid'] for x in v['items'])
before=len(b);b=[e for e in b if not(K(e) in ['segment','via'] and C(e,'uuid')[1] in ids)];p.write_text(s.dumps(b)+'\n');print('Removed',before-len(b),'conflicting/dangling copper objects')
