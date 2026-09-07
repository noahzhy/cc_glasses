"""Create a separate PCB revision while preserving the routed checkpoint."""

import json
from pathlib import Path
import pcbnew as pcb

source = Path('hardware/ir_glasses')
target = source / 'refinement'
board = pcb.LoadBoard(str(source / 'checkpoints/first_routed.kicad_pcb'))
parts = json.loads((source / 'parts.json').read_text())
positions = {
    'C3': (-43.8, -31), 'C4': (-43.8, 32),
    'C5': (34.2, -31), 'C6': (34.2, 32),
    'C8': (-1, 18.5), 'C9': (8, 18.5),
    'C10': (-6.8, -30), 'C11': (-6.8, -28), 'R4': (-9, -31),
}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in positions:
        x, y = positions[ref]
        fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(110 + x), pcb.FromMM(85 + y)))
        parts[ref]['xy'] = [x, y]
report = json.loads((source / 'drc_routed.json').read_text(encoding='utf-8'))
invalid = {i['uuid'] for v in report['violations']
           if v['type'] in {'copper_edge_clearance', 'via_dangling'}
           for i in v['items']}
for track in list(board.GetTracks()):
    if track.GetNetname() in {'3V3', '3V3_A', 'AGND', 'GND'}:
        board.Remove(track)
    elif track.m_Uuid.AsString() in invalid:
        board.Remove(track)
    elif not isinstance(track, pcb.PCB_VIA) and track.GetWidth() < pcb.FromMM(.15):
        track.SetWidth(pcb.FromMM(.15))
pcb.SaveBoard(str(target / 'ir_glasses.kicad_pcb'), board)
(target / 'parts.json').write_text(json.dumps(parts, indent=2))
print('Created refinement revision; source and checkpoint are unchanged.')

