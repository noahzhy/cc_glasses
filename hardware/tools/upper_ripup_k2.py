import pcbnew as pcb
f = 'hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb'
b = pcb.LoadBoard(f)
tracks = [t for t in b.GetTracks() if t.GetNetname() == 'LED_K2']
for t in tracks:
    b.Remove(t)
pcb.SaveBoard(f, b)
print('LED_K2 reroute items:', len(tracks))

