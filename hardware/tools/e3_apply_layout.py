"""Apply reviewed placements and clear the identified near-pad vias."""

import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path("hardware/ir_glasses/EVT_E3")
board = pcb.LoadBoard(str(ROOT / "ir_glasses.kicad_pcb"))
parts = json.loads((ROOT / "parts.json").read_text())
positions = json.loads((ROOT / "placements_e3.json").read_text())
fps = {f.GetReference(): f for f in board.GetFootprints()}
for ref, (x, y, angle) in positions.items():
    fp = fps[ref]
    fp.SetOrientationDegrees(angle)
    fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
    parts[ref].update(xy=[x - 110, y - 85], angle=angle)
removed = []
bad = {
    "bf5f8978-1448-4d99-9f9f-2477ed86f099",
    "26a255da-0175-4e9e-8a5c-aded2dabc975",
}
for track in list(board.GetTracks()):
    if track.GetNetname() == "LED_BLANK" or track.m_Uuid.AsString() in bad:
        removed.append(track.m_Uuid.AsString())
        board.Remove(track)
for item in list(board.GetDrawings()):
    if isinstance(item, pcb.PCB_TEXT) and item.GetText() in {
        "STAT",
        "E3",
        "S",
    }:
        board.Remove(item)
for label, x, y in [("S", 61.45, 57.8), ("E3", 51, 58.1)]:
    text = pcb.PCB_TEXT(board)
    text.SetText(label)
    text.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
    text.SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.8), pcb.FromMM(0.8)))
    text.SetTextThickness(pcb.FromMM(0.1))
    text.SetLayer(pcb.F_SilkS)
    board.Add(text)
pcb.SaveBoard(str(ROOT / "ir_glasses.kicad_pcb"), board)
(ROOT / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
(ROOT / "initial_removed_tracks.json").write_text(json.dumps(removed))
