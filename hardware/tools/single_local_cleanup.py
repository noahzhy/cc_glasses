"""Remove superseded fanouts underneath the relocated resistors."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E")
path = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
report = json.loads((root / "drc.json").read_text(encoding="utf-8"))
dangling = {
    item["uuid"]
    for v in report["violations"]
    if v["type"] == "via_dangling"
    for item in v["items"]
}
for track in list(board.GetTracks()):
    net = track.GetNetname()
    via = isinstance(track, pcb.PCB_VIA)
    x, y = pcb.ToMM(track.GetStart().x), pcb.ToMM(track.GetStart().y)
    remove = track.m_Uuid.AsString() in dangling
    if via and (
        (abs(x - 125.3775) < 0.001 and abs(y - 62.4075) < 0.001)
        or (abs(x - 125.4253) < 0.001 and abs(y - 59.0178) < 0.001)
    ):
        remove = True
    if not via and net == "GND" and track.GetLayer() == pcb.F_Cu:
        for p in [track.GetStart(), track.GetEnd()]:
            if 124 <= pcb.ToMM(p.x) <= 126.2 and 62.2 <= pcb.ToMM(p.y) <= 65.8:
                remove = True
    if remove:
        board.Remove(track)
        continue
    for getter, setter in [
        (track.GetStart, track.SetStart),
        (track.GetEnd, track.SetEnd),
    ]:
        p = getter()
        x, y = pcb.ToMM(p.x), pcb.ToMM(p.y)
        if (
            net == "AGND"
            and abs(x - 154.7165) < 0.0001
            and abs(y - 61.5552) < 0.0001
        ):
            y = 61.5852
        if (
            net == "VREF_1V65"
            and abs(x - 154.4804) < 0.0001
            and abs(y - 62.05) < 0.0001
        ):
            y = 62.09
        setter(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
        if via:
            break
pcb.SaveBoard(str(path), board)
