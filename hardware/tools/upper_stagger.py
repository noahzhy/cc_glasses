import pcbnew as pcb
f='hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'; b=pcb.LoadBoard(f)
for t in list(b.GetTracks()):
    if isinstance(t,pcb.PCB_VIA) or t.GetNetname()!='LED_K3' or t.GetLayer()!=pcb.B_Cu:
        continue
    pts=[t.GetStart(),t.GetEnd()]
    if all(116.4239<=pcb.ToMM(p.x)<=117.6612 and 63.7499<=pcb.ToMM(p.y)<=64.9872 for p in pts):
        b.Remove(t)
def add(net,points):
    for a,z in zip(points,points[1:]):
        t=pcb.PCB_TRACK(b); t.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1]))); t.SetEnd(pcb.VECTOR2I(pcb.FromMM(z[0]),pcb.FromMM(z[1]))); t.SetWidth(pcb.FromMM(.15)); t.SetLayer(pcb.B_Cu); t.SetNet(b.FindNet(net)); b.Add(t)
add('LED_K3',[(117.6611,63.75),(116.424,63.75),(116.424,64.9871)])
add('LED_K2',[(118.0625,64.25),(117.65,64.25),(117.6,64.3),(117.2,64.3)])
v=pcb.PCB_VIA(b); v.SetPosition(pcb.VECTOR2I(pcb.FromMM(117.2),pcb.FromMM(64.3))); v.SetWidth(pcb.FromMM(.5)); v.SetDrill(pcb.FromMM(.3)); v.SetViaType(pcb.VIATYPE_THROUGH); v.SetLayerPair(pcb.F_Cu,pcb.B_Cu); v.SetNet(b.FindNet('LED_K2')); b.Add(v)
pcb.SaveBoard(f,b)
