from pathlib import Path
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1]
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
def clean(f):
 return [e for e in f if not(K(e) in ('fp_poly','fp_line','fp_circle','fp_arc') and C(e,'layer') and C(e,'layer')[1]=='F.SilkS')]
for name in ['C:0402','IC:LGA-14']:
 lib,fp=name.split(':');path=ROOT/'libraries'/f'{lib}.pretty'/f'{fp}.kicad_mod';path.write_text(sx.dumps(clean(sx.load(path.open())))+'\n')
p=ROOT/'ir_glasses_EVT_E6.kicad_pcb';b=sx.load(p.open());b=[clean(f) if K(f)=='footprint' and f[1] in ['C:0402','IC:LGA-14'] else f for f in b];p.write_text(sx.dumps(b)+'\n')
print('Local library graphics synchronized: pads, courtyards and fabrication pin-1 markings unchanged')
