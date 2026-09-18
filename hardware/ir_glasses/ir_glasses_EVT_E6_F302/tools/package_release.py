from pathlib import Path
import json,hashlib,zipfile,csv,datetime
from release_gate import verify
verify()
R=Path(__file__).resolve().parents[1]
for f in ['erc.json','drc.json','carrier/drc.json']:
 d=json.load(open(R/f));bad=d.get('violations',[])+d.get('unconnected_items',[])+d.get('schematic_parity',[])+sum((x.get('violations',[]) for x in d.get('sheets',[])),[]);assert not bad,f
for f in ['design_validation.json','carrier_validation.json','manufacturing_validation.json','via_assembly_validation.json','bom_validation.json','timing_validation.json']:assert json.load(open(R/f))['status']=='passed',f
for n,h in json.load(open(R/'timing_validation.json'))['input_sha256'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n+' changed after timing validation'
fab=json.load(open(R/'fabrication_audit.json'));assert fab['status']=='geometry_subset_passed_factory_approval_pending' and hashlib.sha256((R/(R.name+'.kicad_pcb')).read_bytes()).hexdigest()==fab['board_sha256']
cam=json.load(open(R/'manufacturing_validation.json'))
for f,h in {**cam['board_hashes'],**cam['cam_hashes']}.items():assert hashlib.sha256((R/f).read_bytes()).hexdigest()==h,f+' changed after CAM validation'
assert hashlib.sha256((R/'bom_EVT_E6_F302.xlsx').read_bytes()).hexdigest()==json.load(open(R/'bom_validation.json'))['xlsx_sha256']
for key,file in [('unit_sha256',R/(R.name+'.kicad_pcb')),('carrier_sha256',R/'carrier'/(R.name+'_carrier.kicad_pcb'))]:assert hashlib.sha256(file.read_bytes()).hexdigest()==json.load(open(R/'carrier_validation.json'))[key]
assert hashlib.sha256((R/(R.name+'.kicad_pcb')).read_bytes()).hexdigest()==json.load(open(R/'via_assembly_validation.json'))['board_sha256']
tests=list(csv.DictReader(open(R/'first_board_tests.csv',encoding='utf-8-sig')));assert len(tests)==21 and all(t['Status']=='PENDING' for t in tests)
smt={'carrier/JLC_upload.zip':'Gerber_drill/JLC_upload.zip','bom_jlc.csv':'BOM/bom_jlc.csv','bom_EVT_E6_F302.xlsx':'BOM/bom_EVT_E6_F302.xlsx','carrier/manufacturing/positions_jlc.csv':'CPL/positions_jlc.csv','assembly_notes.md':'assembly_notes.md','populated_assembly.pdf':'populated_assembly.pdf','first_board_tests.csv':'first_board_tests.csv','verification_report.md':'verification_report.md','README.md':'project_README.md','factory_review_request.md':'factory_review_request.md','preproduction_audit.md':'preproduction_audit.md','operating_constraints.json':'operating_constraints.json'}
with zipfile.ZipFile(R/'F302_R2_SMT_package.zip','w',zipfile.ZIP_DEFLATED) as z:
 for src,dest in smt.items():z.write(R/src,dest)
root_ext={'.kicad_sch','.kicad_pcb','.kicad_pro','.json','.csv','.md','.pdf','.xlsx','.h','.png','.svg','.zip'}
files=[p for p in R.iterdir() if p.is_file() and p.suffix in root_ext and p.name not in ['release_manifest.json','F302_R1_SMT_package.zip']]
files += [R/'fp-lib-table',R/'sym-lib-table']
for sub in ['libraries','models','manufacturing','carrier','analog_validation']:
 files.extend(p for p in (R/sub).rglob('*') if p.is_file() and p.suffix not in ['.kicad_prl'] and '__pycache__' not in p.parts)
for f in ['source_hashes.json','change_manifest.json','bom_data.json','erc_all.json']:files.append(R/'evidence'/f)
files.extend((R/'evidence/preproduction_audit').glob('*report.json'))
files.append(R/'evidence/preproduction_audit/changes.json')
files.extend((R/'evidence/stock').glob('*.json'))
files.extend((R/'outputs/f302_bom').glob('*.png'))
for f in ['README.md','validate_design.py','validate_carrier.py','validate_manufacturing.py','validate_via_assembly.py','validate_bom.py','export_manufacturing.py','simulate_frontend.py','draw_assembly.py','package_release.py','release_gate.py','validate_timing.py','audit_fabrication.py']:files.append(R/'tools'/f)
files=sorted(set(files));manifest=dict(release='EVT E6 F302 R2',generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='design_files_checked_bench_pending',bench_tests_pending=len(tests),firmware_binary_included=False,files={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files})
(R/'release_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(R/'release_manifest.json')
out=R.parent/'ir_glasses_EVT_E6_F302_R2_release.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,str(Path(R.name)/p.relative_to(R)))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name,v in manifest['files'].items():assert hashlib.sha256(z.read(R.name+'/'+name)).hexdigest()==v['sha256']
with zipfile.ZipFile(R/'F302_R2_SMT_package.zip') as z:assert z.testzip() is None
print(json.dumps(dict(release=str(out),files=len(files),size_MB=out.stat().st_size/1e6,sha256=hashlib.sha256(out.read_bytes()).hexdigest()),indent=2))
