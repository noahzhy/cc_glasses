from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,hashlib,math
R=Path(__file__).resolve().parents[1];data=json.load(open(R/'evidence/bom_data.json'));parts=json.load(open(R/'parts.json'));ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};checks={};z=zipfile.ZipFile(R/'bom_EVT_E6_F302.xlsx');errors=[];formulas=0
for f in z.namelist():
 if f.startswith('xl/worksheets/sheet') and f.endswith('.xml'):
  tree=E.fromstring(z.read(f));errors.extend((f,c.get('r')) for c in tree.findall('.//s:c',ns) if c.get('t')=='e');formulas+=len(tree.findall('.//s:f',ns))
checks['no_formula_errors']=not errors;checks['formulas_present']=formulas==len(data['cost'])*3+9
checks['155_fitted_parts']=sum(r[3] for r in data['bom'])==155
checks['39_unique_SKUs']=len(data['bom'])==len({r[0] for r in data['bom']})==39
bad=[]
for r,p in parts.items():
 if r.startswith('TP') or r=='J2':continue
 snap=json.load(open(R/'evidence/stock'/(p['lcsc']+'.json')))
 if snap['status']!='retrieved' or snap['data']['productModel'].lower()!=p['mpn'].lower():bad.append(r)
checks['all_fitted_MPNs_match_live_SKU_snapshots']=not bad
old=[];new=[];delta=[]
for j in range(3):
 old.append(sum(x[2]*x[4+2*j] for x in data['cost']));new.append(sum(x[3]*x[5+2*j] for x in data['cost']));delta.append(old[-1]-new[-1])
tree=E.fromstring(z.read('xl/worksheets/sheet2.xml'));vals={c.get('r'):c.find('s:v',ns).text for c in tree.findall('.//s:c',ns) if c.find('s:v',ns) is not None};row=len(data['cost'])+4
checks['cached_excel_totals_match_independent_sums']=all(math.isclose(float(vals[f'{col}{row+i}']),expected,abs_tol=1e-8) for i,arr in enumerate([delta,old,new]) for col,expected in zip('KLM',arr))
report=dict(status='passed' if all(checks.values()) else 'failed',checks=checks,quantity_cases=[1,10,100],old_USD_per_board=old,new_USD_per_board=new,saving_USD_per_board=delta,scope='Same public LCSC USD snapshot tiers, net usage only, excludes MOQ surplus/waste/freight/tax/assembly; no purchasing commitment',xlsx_sha256=hashlib.sha256((R/'bom_EVT_E6_F302.xlsx').read_bytes()).hexdigest())
(R/'bom_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert all(checks.values())
