from pathlib import Path
import pcbnew as p,json
R=Path(__file__).resolve().parents[1];path=R/(R.name+'.kicad_pcb');b=p.LoadBoard(str(path));c=b.GetConnectivity();c.Build(b);bad=[]
for t in b.GetTracks():
 q=p.VECTOR2I()
 if c.TestTrackEndpointDangling(t,True,q):bad.append(t)
items=[dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname()) for t in bad]
for t in bad:b.Remove(t)
if bad:p.SaveBoard(str(path),b)
(R/'evidence/native_tail_pass.json').write_text(json.dumps(items));print(len(bad),flush=True)
