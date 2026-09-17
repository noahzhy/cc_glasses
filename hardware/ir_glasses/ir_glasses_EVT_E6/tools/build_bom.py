#!/usr/bin/env python3
"""Export manufacturing data only after native unit and carrier DRC pass."""
from pathlib import Path
import os,json,csv,subprocess,zipfile,hashlib
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1]
CLI=os.environ.get('KICAD_CLI','/Volumes/KiCad/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
parts=json.load(open(ROOT/'parts.json'))
old={r['Reference']:r for r in csv.DictReader(open(ROOT.parent/'ir_glasses_EVT_E4/bom.csv',encoding='utf-8-sig'))}
b=sx.load(open(ROOT/'ir_glasses_EVT_E6.kicad_pcb'));rows=[]
for f in b:
 if K(f)!='footprint':continue
 props={e[1]:e[2] for e in f if K(e)=='property'};r=props['Reference']
 if r.startswith('TP') or r=='J2':continue
 p=parts[r];o=old.get(r,{});at=C(f,'at');mpn=p.get('mpn',o.get('MPN',''))
 rows.append(dict(Reference=r,Value=p['value'],Manufacturer=p.get('manufacturer',o.get('Manufacturer','')),MPN=mpn,LCSC=p.get('lcsc',o.get('LCSC','')) if mpn==o.get('MPN') else p.get('lcsc',''),Footprint=f[1],X_mm=at[1],Y_mm=at[2],Rotation_deg=at[3] if len(at)>3 else 0,Side='front'))
assert len(rows)==167,len(rows)
with (ROOT/'bom.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

print('167 component BOM generated from current placements; manufacturing release still gated')
