import pcbnew as pcb
f='hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'; b=pcb.LoadBoard(f)
pcb.ImportSpecctraSES(b,'hardware/ir_glasses/EVT_D/ir_glasses.ses')
for t in b.GetTracks():
    if t.GetNetname()=='LED_LAT':
        print('via' if isinstance(t,pcb.PCB_VIA) else t.GetLayerName(), [pcb.ToMM(t.GetStart().x),pcb.ToMM(t.GetStart().y)], [pcb.ToMM(t.GetEnd().x),pcb.ToMM(t.GetEnd().y)])
