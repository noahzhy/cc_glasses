import pcbnew as pcb

p = "hardware/ir_glasses/EVT_C/ir_glasses.kicad_pcb"
b = pcb.LoadBoard(p)
moves = {
    ("TIA14", 144907500, 107480000): (144907500, 107460000),
    ("TIA14", 143928900, 107480000): (143928900, 107460000),
    ("PD_IN16", 151088500, 110274000): (151088500, 110284000),
    ("PD_IN16", 152217200, 110274000): (152217200, 110284000),
    ("PD_IN4", 68605100, 60400000): (68575100, 60400000),
}
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() == "c733ff58-bd71-4d90-baae-cd5f5939e9bc":
        b.Remove(t)
        continue
    for getter, setter in [(t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)]:
        q = getter()
        key = (t.GetNetname(), q.x, q.y)
        if key in moves:
            setter(pcb.VECTOR2I(*moves[key]))
pcb.SaveBoard(p, b)
