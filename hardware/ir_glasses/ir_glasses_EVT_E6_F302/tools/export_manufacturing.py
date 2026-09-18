"""Export only when all native release reports contain no findings."""
from pathlib import Path
import json,csv,subprocess,zipfile,sexpdata as sx
from release_gate import verify
verify()
R=Path(__file__).resolve().parents[1];CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
for f in ['erc.json','drc.json','carrier/drc.json']:
 d=json.load(open(R/f));bad=d.get('violations',[])+d.get('unconnected_items',[])+d.get('schematic_parity',[])
 bad+=sum((s.get('violations',[]) for s in d.get('sheets',[])),[])
 if bad:raise RuntimeError(f+' not clean; production export blocked')
parts=json.load(open(R/'parts.json'));K=lambda x:str(x[0]) if isinstance(x,list) and x else '';C=lambda x,k:next((e for e in x if K(e)==k),None)
b=sx.load(open(R/(R.name+'.kicad_pcb')));rows=[]
for f in b:
 if K(f)!='footprint':continue
 props={e[1]:e[2] for e in f if K(e)=='property'};r=props['Reference']
 if r.startswith('TP') or r=='J2':continue
 p=parts[r];at=C(f,'at');rows.append(dict(Reference=r,Value=p['value'],Manufacturer=p['manufacturer'],MPN=p['mpn'],LCSC=p['lcsc'],Footprint=f[1],X_mm=at[1],Y_mm=at[2],Rotation_deg=at[3] if len(at)>3 else 0,Side='front'))
assert len(rows)==155
with (R/'bom.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
groups={}
for p in rows:groups.setdefault((p['MPN'],p['LCSC'],p['Footprint']),[]).append(p['Reference'])
with (R/'bom_jlc.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #']);w.writerows([mpn,','.join(refs),fp,code] for (mpn,code,fp),refs in groups.items())
for suffix in ['', 'carrier']:
 folder=R/suffix;name=R.name+('_carrier' if suffix else '');out=folder/'manufacturing';out.mkdir(exist_ok=True);board=folder/(name+'.kicad_pcb')
 subprocess.run([CLI,'pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','-o',str(out)+'/',str(board)],check=True)
 subprocess.run([CLI,'pcb','export','drill','--excellon-separate-th','--drill-origin','absolute','-o',str(out)+'/',str(board)],check=True)
 subprocess.run([CLI,'pcb','export','pos','--format','csv','--units','mm','--side','front','-o',str(out/'positions_raw.csv'),str(board)],check=True)
 native={r['Ref']:r for r in csv.DictReader(open(out/'positions_raw.csv'))}
 with (out/'positions_jlc.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
  for row in rows:
   n=native[row['Reference']];assert abs(float(n['PosX'])-row['X_mm'])<1e-5 and abs(float(n['PosY'])+row['Y_mm'])<1e-5
   w.writerow([n['Ref'],n['PosX'],n['PosY'],'Top',n['Rot']])
 with zipfile.ZipFile(folder/('JLC_upload.zip' if suffix else 'unit_reference.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(out.iterdir()):
   if p.suffix!='.csv':z.write(p,p.name)
print('155 fitted components exported for unit and carrier')
