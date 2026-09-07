"""Create revision B without changing the completed revision A."""

import json
import shutil
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path('hardware/tools/pylib').resolve()))
import sexpdata as sx

root = Path('hardware/ir_glasses')
source = root / 'EVT_A'
target = root / 'EVT_B'
for pattern in ['*.kicad_sch', '*.kicad_pro', '*.kicad_sym']:
    for path in source.glob(pattern):
        shutil.copy2(path, target / path.name)
for name in ['fp-lib-table', 'sym-lib-table', 'ir_glasses.net',
             'mechanical_reference.svg', 'optical_map.csv']:
    shutil.copy2(source / name, target / name)
for name in ['IR_Glasses.pretty', 'models']:
    shutil.copytree(source / name, target / name, dirs_exist_ok=True)
data = sx.loads((source / 'ir_glasses.kicad_pcb').read_text())
data = [node for node in data if not isinstance(node, list)
        or str(node[0]) not in {'segment', 'via', 'zone', 'gr_line',
                               'gr_arc', 'gr_text'}]
filename = target / 'ir_glasses.kicad_pcb'
filename.write_text(sx.dumps(data))
board = pcb.LoadBoard(str(filename))
parts = json.loads((target / 'parts.json').read_text())
for fp in board.GetFootprints():
    part = parts[fp.GetReference()]
    x, y = part['xy']
    fp.SetOrientationDegrees(part['angle'])
    fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x + 110), pcb.FromMM(y + 85)))
geometry = json.loads((target / 'geometry.json').read_text())
for coords in [geometry['outer'], *geometry['holes']]:
    for start, end in zip(coords, coords[1:]):
        line = pcb.PCB_SHAPE()
        line.SetShape(pcb.SHAPE_T_SEGMENT)
        line.SetLayer(pcb.Edge_Cuts)
        line.SetWidth(pcb.FromMM(.05))
        line.SetStart(pcb.VECTOR2I(pcb.FromMM(start[0] + 110),
                                 pcb.FromMM(start[1] + 85)))
        line.SetEnd(pcb.VECTOR2I(pcb.FromMM(end[0] + 110),
                               pcb.FromMM(end[1] + 85)))
        board.Add(line)
for label, x, y in [('IR GLASSES / EVT B', -56, -34),
                    ('LED INNER / PD OUTER', 55, -34)]:
    text = pcb.PCB_TEXT(board)
    text.SetText(label)
    text.SetLayer(pcb.F_SilkS)
    text.SetTextSize(pcb.VECTOR2I(pcb.FromMM(.8), pcb.FromMM(.8)))
    text.SetTextThickness(pcb.FromMM(.12))
    text.SetPosition(pcb.VECTOR2I(pcb.FromMM(x + 110), pcb.FromMM(y + 85)))
    board.Add(text)
board.GetTitleBlock().SetRevision('EVT B')
pcb.SaveBoard(str(target / 'ir_glasses.kicad_pcb'), board)
print('Compact revision B created.')
