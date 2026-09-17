#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
import sexpdata as sx
r=Path(__file__).resolve().parents[1];a=r/'analog_validation';d=json.loads((a/'results.json').read_text());parts=json.loads((r/'parts.json').read_text());checks=[]
def ck(n,v):
 checks.append({'check':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
for ref in ['U16','U17']:ck(ref+' exact replacement',parts[ref]['mpn']=='TLV9062IDGKR' and parts[ref]['lcsc']=='C398356')
for ref in ['R11','R12']:ck(ref+' isolation resistor',parts[ref]['value']=='100' and parts[ref]['mpn']=='RC0402FR-07100RL')
for ref in ['C29','C30']:ck(ref+' 330pF C0G 5%',parts[ref]['mpn']=='GRM1555C1H331JA01D')
ck('official model unchanged',hashlib.sha256((a/'TLV9062_TI_RevD.lib').read_bytes()).hexdigest()==d['model_sha256'])
ck('driver sensitivity PM >=50deg',d['selected_min_driver_PM_deg']>=50)
ck('first buffer sensitivity PM >=45deg',d['selected_min_stage1_PM_deg']>=45)
for st in d['steps']:
 if st['name'].endswith('_100') or 'sensitivity' in st['name']:
  for key in ['rise_settle_s','fall_settle_s']:ck(st['name']+' '+key,st[key] is not None and st[key]<5e-6)
for st in d['kickback']:ck('kickback '+str(st['reset_V'])+'V <5us',st['settle_s'] is not None and st['settle_s']<5e-6)
for key in ['rise_settle_s','fall_settle_s']:ck('ideal TIA pole '+key+' <50us',d['tia_first_order'][key]<50e-6)
# Noise is characterized, with no application noise acceptance budget supplied.
ck('noise result characterized only',all(x['buffer_divider_RMS_V']>0 for x in d['noise']))
result={'status':'passed','scope':'selected TLV9062 + 100ohm/330pF static values and typical-model engineering gates only','noise_acceptance':'NOT_SET; quantified partial budget, bench and algorithm acceptance pending','board_sha256':hashlib.sha256((r/'ir_glasses_EVT_E6.kicad_pcb').read_bytes()).hexdigest(),'simulation_files_sha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in a.iterdir() if p.is_file() and not p.name.startswith('.')},'simulation_script_sha256':hashlib.sha256((r/'tools/simulate_tlv9062.py').read_bytes()).hexdigest(),'checks':checks,'bench_status':'pending'}
(r/'analog_validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));print(len(checks),'analog engineering checks passed; bench pending')
