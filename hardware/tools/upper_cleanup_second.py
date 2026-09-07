import pcbnew as pcb
f='hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'; b=pcb.LoadBoard(f)
remove={'253a018b-5e20-4b10-a2a0-0fc80784c738','9a1e6611-1351-47f3-95d4-17570259539b'}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in remove:
        b.Remove(t); continue
    if t.GetNetname()!='3V3': continue
    if isinstance(t,pcb.PCB_VIA):
        p=t.GetPosition()
        if abs(pcb.ToMM(p.x)-52.85)<.0001 and abs(pcb.ToMM(p.y)-61.8)<.0001:
            t.SetPosition(pcb.VECTOR2I(pcb.FromMM(52.7),p.y))
    else:
        for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
            p=getter()
            if abs(pcb.ToMM(p.x)-52.85)<.0001 and abs(pcb.ToMM(p.y)-61.8)<.0001:
                setter(pcb.VECTOR2I(pcb.FromMM(52.7),p.y))
pcb.SaveBoard(f,b)
