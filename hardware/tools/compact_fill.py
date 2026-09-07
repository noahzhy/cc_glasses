import json
from pathlib import Path
import pcbnew as pcb

root = Path('hardware/ir_glasses/EVT_B')
filename = root / 'ir_glasses.kicad_pcb'
board = pcb.LoadBoard(str(filename))
assert len(list(board.Zones())) == 0
zones = []
for name, coords in json.loads(Path('hardware/ir_glasses/EVT_B/zones.json').read_text()).items():
    code = board.FindNet(name).GetNetCode()
    points = ' '.join(f'(xy {x + 110:.6f} {y + 85:.6f})'
                      for x, y in coords[:-1])
    zones.append(
        f'(zone (net {code}) (net_name "{name}") (layer "B.Cu")'
        ' (hatch edge 0.5) (connect_pads yes (clearance 0.2))'
        ' (min_thickness 0.15) (fill yes (thermal_gap 0.2)'
        f' (thermal_bridge_width 0.25)) (polygon (pts {points})))')
data = filename.read_text().rstrip()
filename.write_text(data[:-1] + '\n'.join(zones) + '\n)')
