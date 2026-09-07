"""Move two resistors into the available gap beside the LED driver."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E")
path = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
parts = json.loads((root / "parts.json").read_text())
for fp in board.GetFootprints():
    if fp.GetReference() in {"R1", "R10"}:
        pos = fp.GetPosition()
        pos.x += pcb.FromMM(1.5)
        fp.SetPosition(pos)
        parts[fp.GetReference()]["xy"][0] += 1.5
removed = 0
for track in list(board.GetTracks()):
    remove = track.GetNetname() in {"IREF", "LED_BLANK", "LED_K16"}
    if not isinstance(track, pcb.PCB_VIA) and track.GetLayer() == pcb.F_Cu:
        for p in [track.GetStart(), track.GetEnd()]:
            x, y = pcb.ToMM(p.x), pcb.ToMM(p.y)
            if (
                track.GetNetname() == "3V3"
                and 124 <= x <= 126
                and 60.45 <= y <= 62.4
            ):
                remove = True
    if remove:
        board.Remove(track)
        removed += 1
pcb.SaveBoard(str(path), board)
(root / "parts.json").write_text(json.dumps(parts, indent=2))
print("Resistors moved 1.5 mm; released route items:", removed)
