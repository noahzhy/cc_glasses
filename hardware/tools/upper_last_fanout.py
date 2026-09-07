import pcbnew as pcb
f='hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'; b=pcb.LoadBoard(f)
remove={'783f97e1-0894-4fab-a1a6-00fbbc998a08','d0018707-6023-4f44-8fec-abc7f8ad7c11','b16c9a11-13ab-4624-a68e-a7b46adceaf7'}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in remove:
        b.Remove(t); continue
    if isinstance(t,pcb.PCB_VIA) or t.GetNetname()!='3V3':
        continue
    for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
        p=getter(); x,y=pcb.ToMM(p.x),pcb.ToMM(p.y)
        if 52.34<x<52.41 and 62.29<y<62.41:
            setter(pcb.VECTOR2I(pcb.FromMM(x+.1),p.y))
pcb.SaveBoard(f,b)
