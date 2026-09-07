import json
from pathlib import Path
import pcbnew as pcb

root = Path('hardware/ir_glasses/refinement')
board = pcb.LoadBoard(str(root / 'ir_glasses.kicad_pcb'))
report = json.loads((root / 'drc_refine.json').read_text(encoding='utf-8'))
invalid = {i['uuid'] for v in report['violations'] for i in v['items']}
for track in list(board.GetTracks()):
    if track.m_Uuid.AsString() in invalid:
        board.Remove(track)
pcb.SaveBoard(str(root / 'ir_glasses.kicad_pcb'), board)
filename = root / 'ir_glasses.kicad_pcb'
data = filename.read_text()
zones = []
for name, coords in json.loads(Path('hardware/tools/zones.json').read_text()).items():
    code = board.FindNet(name).GetNetCode()
    points = ' '.join(f'(xy {x + 110:.6f} {y + 85:.6f})' for x, y in coords[:-1])
    zones.append(
        f'(zone (net {code}) (net_name "{name}") (layer "B.Cu")'
        ' (hatch edge 0.5) (connect_pads yes (clearance 0.2))'
        ' (min_thickness 0.15) (fill yes (thermal_gap 0.2)'
        f' (thermal_bridge_width 0.25)) (polygon (pts {points})))')
filename.write_text(data.rstrip()[:-1] + '\n'.join(zones) + '\n)')
