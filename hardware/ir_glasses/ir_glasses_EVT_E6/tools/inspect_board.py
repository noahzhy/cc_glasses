from pathlib import Path
import pcbnew as p,json
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'ir_glasses_EVT_E6.kicad_pcb'));out={}
for f in b.GetFootprints():
 box=f.GetBoundingBox(False,False);a=f.GetPosition();out[f.GetReference()]={'box':[p.ToMM(box.GetX()),p.ToMM(box.GetY()),p.ToMM(box.GetRight()),p.ToMM(box.GetBottom())],'xy':[p.ToMM(a.x),p.ToMM(a.y)],'angle':f.GetOrientationDegrees(),'pads':[{'num':q.GetNumber(),'net':q.GetNetname(),'xy':[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)],'size':[p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y)]} for q in f.Pads()]}
(ROOT/'placement_geometry.json').write_text(json.dumps(out,indent=2))
for r in ['U7','U8','U9','U15','U16','U17']:print(r,out[r]['box'],out[r]['xy'])
