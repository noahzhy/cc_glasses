"""Apply the checked via and attached segment coordinate updates."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E")
path = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
moves = json.loads((root / "via_moves.json").read_text())
for move in moves:
    old = pcb.VECTOR2I(*[pcb.FromMM(v) for v in move["old"]])
    new = pcb.VECTOR2I(*[pcb.FromMM(v) for v in move["new"]])
    for track in list(board.GetTracks()):
        if track.GetNetname() != move["net"]:
            continue
        if isinstance(track, pcb.PCB_VIA):
            if track.GetPosition() == old:
                track.SetPosition(new)
            continue
        if track.GetStart() == old:
            track.SetStart(new)
        if track.GetEnd() == old:
            track.SetEnd(new)
        if track.GetStart() == track.GetEnd():
            board.Remove(track)
pcb.SaveBoard(str(path), board)
