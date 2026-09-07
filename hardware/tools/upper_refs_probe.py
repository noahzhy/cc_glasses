from pathlib import Path
import sexpdata as sx
n=sx.loads(Path('hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb').read_text(encoding='utf-8'))
for f in n:
    if not isinstance(f,list) or str(f[0])!='footprint': continue
    refs=[x for x in f if isinstance(x,list) and str(x[0])=='property' and x[1]=='Reference']
    if refs and refs[0][2] in ['TP1','TP10','D17']:
        print(refs[0][2], [x for x in f if isinstance(x,list) and (str(x[0])=='fp_text' or str(x[0])=='property' and x[1]=='Reference')])
