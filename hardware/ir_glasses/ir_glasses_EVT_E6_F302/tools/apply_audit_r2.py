from pathlib import Path
import sexpdata as s,json,copy,uuid
R=Path(__file__).resolve().parents[1];K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
parts=json.load(open(R/'parts.json'));changes={'C11':dict(value='10n X7R',mpn='CL05B103KB5NNNC',manufacturer='Samsung Electro-Mechanics',lcsc='C15195'),'C40':dict(value='10u',mpn='CL10A106KP8NNNC',manufacturer='Samsung Electro-Mechanics',lcsc='C19702',footprint='C:0603',pcb_xy=[113.8,71.8],angle=90)}
for r,d in changes.items():parts[r].update(d)
for path in R.glob('*.kicad_sch'):
 b=s.load(path.open())
 for e in b:
  if K(e)=='symbol':
   props={x[1]:x for x in e if K(x)=='property'};ref=props.get('Reference',[0,0,''])[2]
   if ref in changes:
    for name,key in [('Value','value'),('MPN','mpn'),('Manufacturer','manufacturer'),('LCSC','lcsc'),('Footprint','footprint')]:
     if name in props:props[name][2]=parts[ref][key]
 path.write_text(s.dumps(b).replace('EVT E6 F302 R1','EVT E6 F302 R2')+'\n')
p=R/(R.name+'.kicad_pcb');b=s.load(p.open());fps={next(x[2] for x in e if K(x)=='property' and x[1]=='Reference'):e for e in b if K(e)=='footprint'}
f=copy.deepcopy(fps['C25']);old=fps['C40'];f[1]='C:0603';C(f,'at')[1:]=[113.8,71.8,90];C(f,'uuid')[1]=C(old,'uuid')[1]
# Preserve schematic identity and project instance path.
for key in ['path','sheetname','sheetfile']:
 f[:]=[e for e in f if K(e)!=key]
 if C(old,key):f.append(copy.deepcopy(C(old,key)))
for e in f:
 if K(e)=='property':
  vals={'Reference':'C40','Value':'10u','MPN':parts['C40']['mpn'],'Manufacturer':parts['C40']['manufacturer'],'LCSC':'C19702'}
  if e[1] in vals:e[2]=vals[e[1]]
 if K(e)=='pad':
  at=C(e,'at');at[1:]=at[1:3]+[((at[3] if len(at)>3 else 0)+90)%360]
 if isinstance(e,list) and C(e,'uuid'):C(e,'uuid')[1]=str(uuid.uuid4())
b[b.index(old)]=f
for ref in ['C11']:
 for e in fps[ref]:
  if K(e)=='property':
   vals={'Value':parts[ref]['value'],'MPN':parts[ref]['mpn'],'Manufacturer':parts[ref]['manufacturer'],'LCSC':parts[ref]['lcsc']}
   if e[1] in vals:e[2]=vals[e[1]]
p.write_text(s.dumps(b).replace('E6 F302 R1','E6 F302 R2')+'\n');(R/'parts.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2))
(R/'evidence/preproduction_audit/changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2));print('Applied C11 10nF and C40 local 10uF/0603; R2')
