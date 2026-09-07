import pcbnew as pcb
f = 'hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'
b = pcb.LoadBoard(f)
remove = {'b0b62e88-70a3-4db8-8e79-b7b67129fb30', 'f071c288-092f-487b-8777-22c9cd2ff3db', 'f1704811-143b-44bd-8739-73d3c1ce53f8'}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in remove:
        b.Remove(t)
points = [(117.6611,63.75),(117.5,63.75),(116.424,64.826),(116.424,64.9871)]
for a,z in zip(points,points[1:]):
    t=pcb.PCB_TRACK(b)
    t.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1])))
    t.SetEnd(pcb.VECTOR2I(pcb.FromMM(z[0]),pcb.FromMM(z[1])))
    t.SetWidth(pcb.FromMM(.15)); t.SetLayer(pcb.B_Cu); t.SetNet(b.FindNet('LED_K3')); b.Add(t)
pcb.SaveBoard(f,b)
