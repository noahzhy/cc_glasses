from pathlib import Path
import pcbnew as pcb

root = Path('hardware/ir_glasses/refinement')
b = pcb.LoadBoard(str(root / 'ir_glasses.kicad_pcb'))
for t in b.GetTracks():
    ident = t.m_Uuid.AsString()
    if ident == 'e17ffbfb-bd42-48a0-b0dd-655128e283f5':
        t.SetPosition(pcb.VECTOR2I(pcb.FromMM(101.2631), pcb.FromMM(64)))
    elif ident == 'e676aed2-841c-4862-9401-eaad0bc2ebe2':
        t.SetStart(pcb.VECTOR2I(pcb.FromMM(100), pcb.FromMM(62.7369)))
        t.SetEnd(pcb.VECTOR2I(pcb.FromMM(101.2631), pcb.FromMM(64)))
    elif ident == 'fe20166f-5239-44d1-be98-efd137e5bf89':
        t.SetStart(pcb.VECTOR2I(pcb.FromMM(101.2631), pcb.FromMM(64)))
    elif (not isinstance(t, pcb.PCB_VIA) and t.GetNetname() == '3V3'
          and t.GetLayer() == pcb.B_Cu
          and t.GetStart() == pcb.VECTOR2I(pcb.FromMM(100), pcb.FromMM(61.2))):
        t.SetEnd(pcb.VECTOR2I(pcb.FromMM(100), pcb.FromMM(62.7369)))
for fp in b.GetFootprints():
    name = str(fp.GetFPID().GetLibItemName())
    if name in {'Everlight_IR11_21C', 'Everlight_PD15_22B'}:
        model = pcb.FP_3DMODEL()
        model.m_Filename = f'${{KIPRJMOD}}/models/{name}.wrl'
        fp.Models().push_back(model)
pcb.SaveBoard(str(root / 'ir_glasses.kicad_pcb'), b)

