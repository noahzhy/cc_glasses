#!/usr/bin/env python3
"""Place the final E6 circuit into the unchanged E4 support frame geometry."""
from pathlib import Path
import sexpdata as sx,json,copy
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'ir_glasses_EVT_E4';OUT=ROOT/'carrier';OUT.mkdir(exist_ok=True)
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
board=sx.load(open(ROOT/'ir_glasses_EVT_E6.kicad_pcb'));e4=sx.load(open(SRC/'ir_glasses_EVT_E4.kicad_pcb'));carrier=sx.load(open(SRC/'carrier/ir_glasses_EVT_E4_carrier.kicad_pcb'))
base_ids={C(e,'uuid')[1] for e in e4 if isinstance(e,list) and C(e,'uuid')}
# Carrier outer contour includes closed milling slots; replace the unit edge only.
board=[e for e in board if not(K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts')]
extras=[]
for e in carrier:
 if not isinstance(e,list):continue
 isedge=K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts'
 u=C(e,'uuid')
 if isedge or (u and u[1] not in base_ids and K(e) in ('gr_line','gr_arc','gr_text','footprint','zone')):
  if K(e)=='zone' and not C(e,'keepout'):continue
  extras.append(copy.deepcopy(e))
board.extend(extras)
text=sx.dumps(board).replace('EVT_E4','EVT_E6').replace('EVT E4','EVT E6').replace('${KIPRJMOD}/models/','${KIPRJMOD}/../models/')
(OUT/'ir_glasses_EVT_E6_carrier.kicad_pcb').write_text(text+'\n')
pro=json.load(open(ROOT/'ir_glasses_EVT_E6.kicad_pro'));pro['meta']['filename']='ir_glasses_EVT_E6_carrier.kicad_pro';(OUT/'ir_glasses_EVT_E6_carrier.kicad_pro').write_text(json.dumps(pro,indent=2))
for name in ['fp-lib-table','sym-lib-table']:(OUT/name).write_text((ROOT/name).read_text().replace('${KIPRJMOD}/libraries/','${KIPRJMOD}/../libraries/'))
(OUT/'carrier_geometry.json').write_bytes((SRC/'carrier/carrier_geometry.json').read_bytes())
print('Carrier added',len(extras),'frame-only items')
