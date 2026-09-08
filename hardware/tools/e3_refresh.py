"""Refresh manufacturing metadata from the final native PCB."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E3")
board = pcb.LoadBoard(str(root / "ir_glasses.kicad_pcb"))
parts = json.loads((root / "parts.json").read_text(encoding="utf-8"))
for fp in board.GetFootprints():
    part = parts[fp.GetReference()]
    position = fp.GetPosition()
    part.update(
        xy=[pcb.ToMM(position.x) - 110, pcb.ToMM(position.y) - 85],
        angle=fp.GetOrientationDegrees(),
        nets={p.GetNumber(): p.GetNetname() for p in fp.Pads()},
        footprint=fp.GetFPIDAsString(),
    )
(root / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
