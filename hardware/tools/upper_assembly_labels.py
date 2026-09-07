from pathlib import Path
import sexpdata as sx
p=Path('hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'); n=sx.loads(p.read_text(encoding='utf-8'))
for f in n:
    if not isinstance(f,list) or str(f[0])!='footprint': continue
    ref=next(x[2] for x in f if isinstance(x,list) and str(x[0])=='property' and x[1]=='Reference')
    if not(ref.startswith('TP') or ref=='D17'): continue
    for t in f:
        if not isinstance(t,list) or str(t[0])!='fp_text': continue
        for e in t:
            if isinstance(e,list) and str(e[0])=='effects':
                font=next(x for x in e if isinstance(x,list) and str(x[0])=='font')
                for v in font:
                    if isinstance(v,list) and str(v[0])=='size': v[1:]=[.65,.65]
                    if isinstance(v,list) and str(v[0])=='thickness': v[1]=.1
p.write_text(sx.dumps(n),encoding='utf-8')
