from pathlib import Path
import pcbnew as pcb

root = Path('hardware/ir_glasses/refinement')
b = pcb.LoadBoard(str(root / 'ir_glasses.kicad_pcb'))
for t in list(b.GetTracks()):
    ident = t.m_Uuid.AsString()
    if ident == '187896f1-7460-45d4-9d28-1c6fe03d1416':
        t.SetEnd(pcb.VECTOR2I(pcb.FromMM(100), pcb.FromMM(61.2)))
    elif ident == 'e676aed2-841c-4862-9401-eaad0bc2ebe2':
        t.SetLayer(pcb.B_Cu)
net = b.FindNet('3V3')
t = pcb.PCB_TRACK(b)
t.SetStart(pcb.VECTOR2I(pcb.FromMM(100), pcb.FromMM(61.2)))
t.SetEnd(pcb.VECTOR2I(pcb.FromMM(100), pcb.FromMM(63.2369)))
t.SetLayer(pcb.B_Cu)
t.SetWidth(pcb.FromMM(.15))
t.SetNet(net)
b.Add(t)
for x, y in [(100, 61.2), (100.7631, 64)]:
    via = pcb.PCB_VIA(b)
    via.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
    via.SetWidth(pcb.FromMM(.6))
    via.SetDrill(pcb.FromMM(.3))
    via.SetViaType(pcb.VIATYPE_THROUGH)
    via.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
    via.SetNet(net)
    b.Add(via)
pcb.SaveBoard(str(root / 'ir_glasses.kicad_pcb'), b)
print([a for a in dir(pcb.FP_3DMODEL()) if not a.startswith('_')])
