from pathlib import Path
import pcbnew as p,json
R=Path(__file__).resolve().parents[1];path=R/(R.name+'.kicad_pcb');removed=[]
for k in range(500):
 b=p.LoadBoard(str(path));c=b.GetConnectivity();c.Build(b);bad=[]
 for t in b.GetTracks():
  q=p.VECTOR2I()
  if c.TestTrackEndpointDangling(t,True,q):bad.append(t)
 if not bad:break
 for t in bad:
  removed.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname()));b.Remove(t)
 p.SaveBoard(str(path),b);print(k,len(bad),flush=True)
p.SaveBoard(str(path),b);(R/'evidence/native_tail_cleanup.json').write_text(json.dumps(dict(rounds=k,removed=removed),indent=2))
