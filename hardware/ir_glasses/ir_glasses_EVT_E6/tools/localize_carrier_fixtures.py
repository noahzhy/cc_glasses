from pathlib import Path
import sexpdata as sx,copy
root=Path(__file__).resolve().parents[1];K=lambda e:str(e[0]) if isinstance(e,list) and e else ''
b=sx.load(open(root/'carrier/ir_glasses_EVT_E6_carrier.kicad_pcb'));saved=set()
for f in b:
 if K(f)!='footprint' or ':' not in f[1]:continue
 lib,name=f[1].split(':',1)
 if lib not in ('MountingHole','Fiducial') or (lib,name) in saved:continue
 q=copy.deepcopy(f);q[1]=name;q[:]=[e for e in q if K(e) not in ('at','path','sheetname','sheetfile','uuid')]
 q.insert(2,[sx.Symbol('version'),20260206]);q.insert(3,[sx.Symbol('generator'),'pcbnew'])
 for e in q:
  if K(e)=='property' and e[1]=='Reference':e[2]='REF**'
  if K(e)=='pad':e[:]=[v for v in e if K(v) not in ('net','pinfunction','pintype')]
 folder=root/'libraries'/(lib+'.pretty');folder.mkdir(exist_ok=True);(folder/(name+'.kicad_mod')).write_text(sx.dumps(q)+'\n');saved.add((lib,name))
for folder,prefix in [(root,'${KIPRJMOD}/libraries/'),(root/'carrier','${KIPRJMOD}/../libraries/')]:
 file=folder/'fp-lib-table';s=file.read_text().rstrip();at=s.rfind(')');add=''.join('\n(lib (name "'+lib+'") (type "KiCad") (uri "'+prefix+lib+'.pretty") (options "") (descr "Local carrier fixtures"))' for lib in ['MountingHole','Fiducial'] if '(name "'+lib+'")' not in s);file.write_text(s[:at]+add+s[at:]+'\n')
print('Local carrier footprint libraries:',sorted(saved))
