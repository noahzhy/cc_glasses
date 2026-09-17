#!/usr/bin/env python3
"""Export manufacturing data only after native unit and carrier DRC pass."""
from pathlib import Path
import os,json,csv,subprocess,zipfile,hashlib
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1]
CLI=os.environ.get('KICAD_CLI','/Volumes/KiCad/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
for f in ['erc.json','drc.json','carrier/drc.json']:
 d=json.load(open(ROOT/f));bad=d.get('violations',[])+d.get('unconnected_items',[])+d.get('schematic_parity',[])
 if 'sheets' in d:bad+=sum((s.get('violations',[]) for s in d['sheets']),[])
 if bad:raise RuntimeError(f+' has unresolved findings; manufacturing export blocked')
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
for suffix,name in [('', 'ir_glasses_EVT_E6'),('carrier','ir_glasses_EVT_E6_carrier')]:
 folder=ROOT/suffix;out=folder/'manufacturing';out.mkdir(exist_ok=True);board=folder/(name+'.kicad_pcb')
 subprocess.run([CLI,'pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','-o',str(out)+'/',str(board)],check=True)
 subprocess.run([CLI,'pcb','export','drill','--excellon-separate-th','--drill-origin','absolute','-o',str(out)+'/',str(board)],check=True)
 subprocess.run([CLI,'pcb','export','pos','--format','csv','--units','mm','--side','front','-o',str(out/'positions_raw.csv'),str(board)],check=True)
 native=list(csv.DictReader(open(out/'positions_raw.csv')));native={r['Ref']:r for r in native}
 with (out/'positions_jlc.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
  for row in rows:
   r=native[row['Reference']];w.writerow([r['Ref'],r['PosX'],r['PosY'],'Top',r['Rot']])
 for row in rows:
  n=native[row['Reference']];assert abs(float(n['PosX'])-row['X_mm'])<1e-5 and abs(float(n['PosY'])+row['Y_mm'])<1e-5
 with zipfile.ZipFile(folder/('JLC_upload.zip' if suffix else 'ir_glasses_unit_reference.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(out.iterdir()):
   if p.suffix not in ['.csv']:z.write(p,p.name)
print('167 fitted components; unit/carrier manufacturing exports complete')
