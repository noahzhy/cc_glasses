"""Audit J1 manufacturer land pattern, preserved signal ordering, and inrush part."""
from pathlib import Path
import json,sexpdata as s,hashlib,math
R=Path(__file__).resolve().parents[1];K=lambda x:str(x[0]) if isinstance(x,list) and x else '';C=lambda x,k:next((e for e in x if K(e)==k),None)
b=s.load(open(R/'ir_glasses_EVT_E6.kicad_pcb'));f=next(f for f in b if K(f)=='footprint' and any(K(e)=='property' and e[1:3]==['Reference','J1'] for e in f));l=s.load(open(R/'libraries/J.pretty/GUOCONN_0.5K-AS-5PWB-RW.kicad_mod'));checks=[]
def check(n,v):
 checks.append({'check':n,'pass':bool(v)});assert v,n
for fp in [f,l]:
 pads=[p for p in fp if K(p)=='pad'];check('7 lands',len(pads)==7)
 for i in range(1,6):
  p=next(p for p in pads if str(p[1])==str(i));check('signal pad '+str(i),C(p,'at')[1:3]==[-1+(i-1)*.5,-1.35] and C(p,'size')[1:]==[.3,1.25])
 for p in [p for p in pads if p[1]=='MP']:check('mechanical land',abs(C(p,'at')[1])==2.54 and C(p,'at')[2]==.975 and C(p,'size')[1:]==[2,3])
check('J1 absolute pose preserved',C(f,'at')[1:]==[165,61.7,180])
nets=['VIN_HOST','GND','HOST_TX','HOST_RX','NRST_EXT']
for i,n in enumerate(nets,1):check('J1 pin '+str(i)+' net',C(next(p for p in f if K(p)=='pad' and str(p[1])==str(i)),'net')[-1]==n)
p=json.load(open(R/'parts.json'));check('J1 selected MPN',p['J1']['mpn']=='0.5K-AS-5PWB-RW' and p['J1']['lcsc']=='C51901197');check('C38 soft start 22nF',p['C38']['mpn']=='CL05B223KB5VPNC' and p['C38']['value']=='22n X7R')
report={'status':'passed','checks':checks,'board_sha256':hashlib.sha256((R/'ir_glasses_EVT_E6.kicad_pcb').read_bytes()).hexdigest(),'pin1_global_mm':[166,63.05],'mouth_direction':'toward board top edge (-Y); copper facing upper contacts','rating_A_per_contact':.4,'board_input_current_limiter':'U18 TPS2553DRVR / R29 110k','actual_FPC_continuity_and_transients':'pending bench measurement'}
(R/'connector_validation.json').write_text(json.dumps(report,indent=2));print(len(checks),'J1 land-pattern / pin-map / C38 checks passed')
