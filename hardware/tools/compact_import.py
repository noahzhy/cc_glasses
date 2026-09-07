"""Import routing and synchronize every PCB pad with the schematic netlist."""

import json
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path('hardware/tools/pylib').resolve()))
import sexpdata as sx

root = Path('hardware/ir_glasses/EVT_B')
board = pcb.LoadBoard(str(root / 'ir_glasses.kicad_pcb'))
if len(sys.argv) > 1:
    if not pcb.ImportSpecctraSES(board, sys.argv[1]):
        raise RuntimeError('KiCad rejected the routing session.')


def children(node, name):
    return [n for n in node if isinstance(n, list) and str(n[0]) == name]


netlist = sx.loads((root / 'ir_glasses.net').read_text(encoding='utf-8'))
expected = {}
for entry in children(children(netlist, 'nets')[0], 'net'):
    name = children(entry, 'name')[0][1]
    for node in children(entry, 'node'):
        ref = children(node, 'ref')[0][1]
        pin = children(node, 'pin')[0][1]
        expected[(ref, str(pin))] = name

matched = 0
for fp in board.GetFootprints():
    for pad in fp.Pads():
        key = (fp.GetReference(), pad.GetNumber())
        if key not in expected:
            continue
        name = expected[key]
        current = pad.GetNetname()
        if current and current != name:
            raise ValueError(f'Conflicting pad {key}: {current} != {name}')
        if not current:
            net = board.FindNet(name)
            if net is None:
                net = pcb.NETINFO_ITEM(board, name)
                board.Add(net)
            pad.SetNet(net)
        matched += 1
pcb.SaveBoard(str(root / 'ir_glasses.kicad_pcb'), board)
print(f'Schematic/PCB pad net assignments verified: {matched}')
