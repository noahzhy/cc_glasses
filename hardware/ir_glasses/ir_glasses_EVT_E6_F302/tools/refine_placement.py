from pathlib import Path
import sexpdata as s,json,sys
R=Path(__file__).resolve().parents[1];p=R/(R.name+'.kicad_pcb');b=s.load(open(p));parts=json.load(open(R/'parts.json'))
K=lambda e:str(e[0]) if isinstance(e,list) and e else ''
C=lambda e,k:next((x for x in e if K(x)==k),None)
moves={'U16':(100.5,61.2,90),'C10':(103.65,59.5,0),'C29':(103.65,65.3,0),'R11':(103.65,66.3,0),'C32':(100.9,67.2,0),'C30':(107.3,69.0,0),'R6':(113.15,69.0,0),'C11':(104.338,63.7,90),'C44':(101.7,65.25,0),'C47':(101.7,66.25,0)}
moves['C46']=(99,64.7,0)
if len(sys.argv)>1:moves=json.loads(sys.argv[1])
nets=set()
for f in b:
 if K(f)!='footprint':continue
 ref=next(x[2] for x in f if K(x)=='property' and x[1]=='Reference')
 if ref not in moves:continue
 x,y,a=moves[ref];at=C(f,'at');delta=a-(at[3] if len(at)>3 else 0);at[1:]=[x,y,a]
 for pad in [e for e in f if K(e)=='pad']:
  pa=C(pad,'at');pa[1:]=pa[1:3]+[((pa[3] if len(pa)>3 else 0)+delta)%360]
  net=C(pad,'net');nets.add(net[-1]) if net else None
 parts[ref].update(pcb_xy=[x,y],angle=a)
# Rip signals touched by moves; power stubs are left for native dangling cleanup.
nets-={'GND','3V3','3V3_A'}
b=[e for e in b if not(K(e) in ['segment','via'] and C(e,'net') and C(e,'net')[-1] in nets)]
p.write_text(s.dumps(b)+'\n');(R/'parts.json').write_text(json.dumps(parts,indent=2,ensure_ascii=False));print(moves)
