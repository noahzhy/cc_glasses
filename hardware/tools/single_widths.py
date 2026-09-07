"""Restore the specified minimum width after routing neck-down."""

from pathlib import Path

import pcbnew as pcb

path = Path("hardware/ir_glasses/EVT_E/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))
changed = 0
for track in board.GetTracks():
    if not isinstance(track, pcb.PCB_VIA) and track.GetWidth() < pcb.FromMM(
        0.15
    ):
        track.SetWidth(pcb.FromMM(0.15))
        changed += 1
pcb.SaveBoard(str(path), board)
print("Restored 0.15 mm minimum:", changed)
