"""Bind native electrical checks to exact design inputs; reject stale evidence."""
from pathlib import Path
import hashlib,json,subprocess,datetime,sys
R=Path(__file__).resolve().parents[1]
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PROOF=R/'native_check_provenance.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 files=list(R.glob('*.kicad_sch'))+list(R.glob('*.kicad_pcb'))+list(R.glob('*.kicad_pro'))
 files += list((R/'carrier').glob('*.kicad_pcb'))+list((R/'carrier').glob('*.kicad_pro'))
 files += [R/'parts.json',R/'fp-lib-table',R/'sym-lib-table',R/'carrier/fp-lib-table',R/'carrier/sym-lib-table']
 files += [p for p in (R/'libraries').rglob('*') if p.is_file()]
 return {str(p.relative_to(R)):sha(p) for p in sorted(set(files))}
def report_clean(path):
 d=json.loads(path.read_text());bad=d.get('violations',[])+d.get('unconnected_items',[])+d.get('schematic_parity',[])+sum((s.get('violations',[]) for s in d.get('sheets',[])),[])
 if bad:raise RuntimeError(str(path)+' contains findings')
def verify(expected=None,current=None):
 d=expected or json.loads(PROOF.read_text());actual=current if current is not None else inputs()
 if actual!=d['design_inputs']:raise RuntimeError('Design changed after native checks; rerun release_gate.py run')
 for rel,h in d['reports'].items():
  if sha(R/rel)!=h:raise RuntimeError('Native report changed: '+rel)
  if rel.endswith('.json'):report_clean(R/rel)
 return True
def run():
 commands=[['sch','erc','--severity-all','--format','json','-o',str(R/'erc.json'),str(R/(R.name+'.kicad_sch'))],['sch','export','netlist','--format','kicadxml','-o',str(R/'netlist.xml'),str(R/(R.name+'.kicad_sch'))],['pcb','drc','--refill-zones','--save-board','--schematic-parity','--severity-all','--format','json','-o',str(R/'drc.json'),str(R/(R.name+'.kicad_pcb'))],['pcb','drc','--refill-zones','--save-board','--severity-all','--format','json','-o',str(R/'carrier/drc.json'),str(R/'carrier'/(R.name+'_carrier.kicad_pcb'))]]
 for c in commands:subprocess.run([CLI]+c,check=True)
 reports=['erc.json','drc.json','carrier/drc.json','netlist.xml']
 for rel in reports[:3]:report_clean(R/rel)
 d={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Enabled KiCad checks only; ignored ERC checks remain disclosed','design_inputs':inputs(),'reports':{rel:sha(R/rel) for rel in reports}}
 PROOF.write_text(json.dumps(d,indent=2));verify()
def selftest():
 d=json.loads(PROOF.read_text());mutated=dict(d['design_inputs']);k=next(iter(mutated));mutated[k]='0'*64
 try:verify(d,mutated)
 except RuntimeError:pass
 else:raise AssertionError('stale design accepted')
 removed=dict(d['design_inputs']);removed.pop(next(iter(removed)))
 try:verify(d,removed)
 except RuntimeError:pass
 else:raise AssertionError('missing design input accepted')
 verify();print('Fresh evidence accepted; altered/missing input fingerprints rejected')
if __name__=='__main__':
 {'run':run,'verify':verify,'selftest':selftest}[sys.argv[1] if len(sys.argv)>1 else 'verify']()
