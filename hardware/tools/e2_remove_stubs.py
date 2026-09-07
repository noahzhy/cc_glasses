"""Remove dangling tracks that have no junction along their interior."""

import json
import math
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E2")
path = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
report = json.loads((root / "drc.json").read_text(encoding="utf-8"))
ids = {
    item["uuid"]
    for v in report["violations"]
    if v["type"] == "track_dangling"
    for item in v["items"]
}
tracks = list(board.GetTracks())
removed = 0
for track in tracks:
    if track.m_Uuid.AsString() not in ids:
        continue
    a, b = track.GetStart(), track.GetEnd()
    dx, dy = b.x - a.x, b.y - a.y
    length = math.hypot(dx, dy)
    junction = False
    for other in tracks:
        if other is track or other.GetNetname() != track.GetNetname():
            continue
        if not other.IsOnLayer(track.GetLayer()):
            continue
        for p in [other.GetStart(), other.GetEnd()]:
            along = ((p.x - a.x) * dx + (p.y - a.y) * dy) / length
            across = abs((p.x - a.x) * dy - (p.y - a.y) * dx) / length
            if pcb.FromMM(0.15) < along < length - pcb.FromMM(
                0.15
            ) and across < pcb.FromMM(0.15):
                junction = True
    if not junction:
        board.Remove(track)
        removed += 1
    else:
        print(
            "Retained interior junction:",
            track.GetNetname(),
            track.m_Uuid.AsString(),
        )
pcb.SaveBoard(str(path), board)
print("Removed stubs:", removed)
