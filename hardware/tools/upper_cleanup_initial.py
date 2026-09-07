import pcbnew as pcb
f='hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'; b=pcb.LoadBoard(f)
remove={'98199413-4471-47ed-bef5-21479fcafc8a','362310cb-aa41-4d5c-8f48-4cfb8a20ddc9','1ca92eb0-6476-4c5d-99db-59e3701ff3bd','1de01645-0b3d-4d05-97f6-e1dad011edff','2ce291df-0301-4153-93bd-a8458c56b08e','2cfc930c-56da-4003-8761-ce788911176a','d55a3a0f-385b-4b6b-bd56-606fbaa31b8f'}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in remove:
        b.Remove(t)
pcb.SaveBoard(f,b)
