import sexpdata as s,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/(R.name+'.kicad_pcb');b=s.load(open(p));old=s.load(open(R.parent/'ir_glasses_EVT_E6/ir_glasses_EVT_E6.kicad_pcb'))
K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
oldids={C(e,'uuid')[1] for e in old if K(e) in ['segment','via']};tracks={C(e,'uuid')[1]:e for e in b if K(e) in ['segment','via']};d=json.load(open(sys.argv[1]));rm=set()
for v in d['violations']:
 if v['type'] in ['track_dangling','via_dangling','isolated_copper','track_not_centered_on_via']:continue
 ids=[i['uuid'] for i in v['items']];candidates=[u for u in ids if u in tracks]
 if len(candidates)==len(ids):
  fresh=[u for u in candidates if u not in oldids];rm.update(fresh or candidates)
 else:rm.update(candidates)
b=[e for e in b if not(K(e) in ['segment','via'] and C(e,'uuid')[1] in rm)]
for z in [e for e in b if K(e)=='zone']:
 f=C(z,'fill')
 if f and C(f,'island_removal_mode'):C(f,'island_removal_mode')[1]=0
p.write_text(s.dumps(b)+'\n');print('Removed',len(rm))
