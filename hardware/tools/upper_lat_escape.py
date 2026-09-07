import pcbnew as pcb
f='hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'; b=pcb.LoadBoard(f)
points=[(110.75,60.8375),(110.65,60.9375),(110.65,62.6496),(111.0036,63.0032),(111.6787,63.0032),(112.2055,62.4764)]
for a,z in zip(points,points[1:]):
    t=pcb.PCB_TRACK(b); t.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1]))); t.SetEnd(pcb.VECTOR2I(pcb.FromMM(z[0]),pcb.FromMM(z[1]))); t.SetWidth(pcb.FromMM(.15)); t.SetLayer(pcb.B_Cu); t.SetNet(b.FindNet('LED_LAT')); b.Add(t)
v=pcb.PCB_VIA(b); v.SetPosition(pcb.VECTOR2I(pcb.FromMM(112.2055),pcb.FromMM(62.4764))); v.SetWidth(pcb.FromMM(.5)); v.SetDrill(pcb.FromMM(.3)); v.SetViaType(pcb.VIATYPE_THROUGH); v.SetLayerPair(pcb.F_Cu,pcb.B_Cu); v.SetNet(b.FindNet('LED_LAT')); b.Add(v)
pcb.SaveBoard(f,b)
