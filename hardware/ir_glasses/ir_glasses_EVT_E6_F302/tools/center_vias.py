from pathlib import Path
import sexpdata as s,json,math,sys
root=Path(__file__).resolve().parents[1];p=root/(root.name+'.kicad_pcb');b=s.load(p.open());K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
byid={C(e,'uuid')[1]:e for e in b if K(e) in ['segment','via']};d=json.load(open(sys.argv[1]));rm=set();n=0
for v in d['violations']:
 if False:
  rm.update(i['uuid'] for i in v['items'])
 if v['type']=='track_not_centered_on_via':
  a,z=[byid[i['uuid']] for i in v['items']]
  if K(a)=='via':a,z=z,a
  xy=C(z,'at')[1:3];es=[C(a,k) for k in ['start','end']];n+=1
  if all(math.dist(e[1:3],xy)+C(a,'width')[1]/2<=C(z,'size')[1]/2+.0001 for e in es):rm.add(C(a,'uuid')[1]);continue
  e=min(es,key=lambda e:math.dist(e[1:3],xy));e[1:3]=xy
b[:]=[e for e in b if not(K(e) in ['segment','via'] and C(e,'uuid')[1] in rm)];p.write_text(s.dumps(b)+'\n');print('remove',len(rm),'center',n)
