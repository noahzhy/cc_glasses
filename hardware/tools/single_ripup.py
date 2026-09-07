"""Release two local fanout paths for the remaining connections."""

from pathlib import Path

import pcbnew as pcb

path = Path("hardware/ir_glasses/EVT_E/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))
removed = []
for track in list(board.GetTracks()):
    if isinstance(track, pcb.PCB_VIA):
        continue
    x = pcb.ToMM(track.GetStart().x)
    if track.m_Uuid.AsString() == "24c9c323-d74e-4a63-9d25-fc9dd2471365":
        board.Remove(track)
        removed.append("TIA5")
    if (
        track.GetNetname() == "LED_K13"
        and track.GetLayer() == pcb.F_Cu
        and x < 126
    ):
        board.Remove(track)
        removed.append("LED_K13")
pcb.SaveBoard(str(path), board)
print("Released:", removed)
