#!/usr/bin/env python3
from pathlib import Path
import sexpdata as sx,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
u=sx.load(open(ROOT/'ir_glasses_EVT_E6.kicad_pcb'));b=sx.load(open(ROOT/'carrier/ir_glasses_EVT_E6_carrier.kicad_pcb'));old=sx.load(open(ROOT.parent/'ir_glasses_EVT_E4/carrier/ir_glasses_EVT_E4_carrier.kicad_pcb'))
checks=[]
def check(name,value):
 checks.append({'check':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
items=lambda board,key:{C(e,'uuid')[1]:e for e in board if K(e)==key}
for typ in ['segment','via','footprint']:
 uu=items(u,typ);bb=items(b,typ)
 for id,e in uu.items():
  expected=sx.dumps(e).replace('${KIPRJMOD}/models/','${KIPRJMOD}/../models/')
  check(typ+' preserved '+id,id in bb and sx.dumps(bb[id])==expected)
 if typ!='footprint':check(typ+' count unchanged',len(uu)==len(bb))
check('seven frame fixtures only',len(items(b,'footprint'))-len(items(u,'footprint'))==7)
edges=lambda board:sorted(sx.dumps(e) for e in board if K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts')
check('E4 carrier contour exact',edges(b)==edges(old))
keep=lambda board:sorted(sx.dumps(e) for e in board if K(e)=='zone' and C(e,'keepout'))
check('E4 carrier milling keepouts exact',keep(b)==keep(old))

result={'status':'PASS','scope':'geometry preservation only; native DRC still incomplete','checks':checks,'check_count':len(checks)}
(ROOT/'carrier_geometry_check.json').write_text(json.dumps(result,indent=2));print(len(checks),'carrier geometry checks passed; not a release approval')
