"""Reuse the P3 carrier mechanical geometry around the new F302 unit."""
from pathlib import Path
import sexpdata as sx,json,copy
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'ir_glasses_EVT_E6';OUT=ROOT/'carrier';OUT.mkdir(exist_ok=True)
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
board=sx.load(open(ROOT/(ROOT.name+'.kicad_pcb')));base=sx.load(open(SRC/'ir_glasses_EVT_E6.kicad_pcb'));carrier=sx.load(open(SRC/'carrier/ir_glasses_EVT_E6_carrier.kicad_pcb'))
base_ids={C(e,'uuid')[1] for e in base if isinstance(e,list) and C(e,'uuid')}
board=[e for e in board if not(K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts')]
extras=[]
for e in carrier:
 if not isinstance(e,list):continue
 isedge=K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts';u=C(e,'uuid')
 if isedge or (u and u[1] not in base_ids and K(e) in ('gr_line','gr_arc','gr_text','footprint','zone')):
  if K(e)=='zone' and not C(e,'keepout'):continue
  v=copy.deepcopy(e)
  if K(v)=='gr_text':v[1]=v[1].replace('EVT E6 / TOP / 1-UP','EVT E6 F302 R2 / TOP / 1-UP')
  extras.append(v)
board.extend(extras);name=ROOT.name+'_carrier'
text=sx.dumps(board).replace('${KIPRJMOD}/models/','${KIPRJMOD}/../models/');(OUT/(name+'.kicad_pcb')).write_text(text+'\n')
pro=json.load(open(ROOT/(ROOT.name+'.kicad_pro')));pro['meta']['filename']=name+'.kicad_pro';(OUT/(name+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
for name in ['fp-lib-table','sym-lib-table']:(OUT/name).write_text((ROOT/name).read_text().replace('${KIPRJMOD}/libraries/','${KIPRJMOD}/../libraries/'))
(OUT/'carrier_geometry.json').write_bytes((SRC/'carrier/carrier_geometry.json').read_bytes())
print('Carrier frame-only items',len(extras))
