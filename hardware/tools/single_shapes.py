"""Export local courtyard and pad coordinates for one-face packing."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E")
board = pcb.LoadBoard(str(root / "ir_glasses.kicad_pcb"))
result = {}


def point(value):
    return [pcb.ToMM(value.x), pcb.ToMM(value.y)]


for fp in board.GetFootprints():
    fp.SetOrientationDegrees(0)
    fp.SetPosition(pcb.VECTOR2I(0, 0))
    boxes = [
        graphic.GetBoundingBox()
        for graphic in fp.GraphicalItems()
        if graphic.GetLayer() == pcb.F_CrtYd
    ]
    bounds = (
        [
            min(pcb.ToMM(b.GetLeft()) for b in boxes),
            min(pcb.ToMM(b.GetTop()) for b in boxes),
            max(pcb.ToMM(b.GetRight()) for b in boxes),
            max(pcb.ToMM(b.GetBottom()) for b in boxes),
        ]
        if boxes
        else [-0.8, -0.8, 0.8, 0.8]
    )
    result[fp.GetReference()] = {
        "courtyard": bounds,
        "pads": [
            {
                "pin": p.GetNumber(),
                "net": p.GetNetname(),
                "xy": point(p.GetPosition()),
                "size": point(p.GetSize()),
            }
            for p in fp.Pads()
            if p.IsOnLayer(pcb.F_Cu)
        ],
    }
(root / "local_shapes.json").write_text(json.dumps(result, indent=2))
for ref in ["U9", "U1", "U10", "J1", "J2", "U2", "R1", "C28"]:
    print(ref, result[ref]["courtyard"])
