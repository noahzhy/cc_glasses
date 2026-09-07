from pathlib import Path
import pcbnew as pcb

b = pcb.LoadBoard('hardware/ir_glasses/refinement/ir_glasses.kicad_pcb')
for t in b.GetTracks():
    a, c = t.GetStart(), t.GetEnd()
    if 97 < pcb.ToMM(a.x) < 103 and 59 < pcb.ToMM(a.y) < 66:
        print(t.m_Uuid.AsString(), t.GetNetname(), t.GetLayerName(),
              tuple(round(pcb.ToMM(v), 4) for v in [a.x, a.y, c.x, c.y]))
print('3d', [x for x in dir(pcb) if '3DMODEL' in x])
