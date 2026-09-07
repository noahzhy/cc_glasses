"""Move three short routing bends away from nearby copper."""

from pathlib import Path

import pcbnew as pcb

path = Path("hardware/ir_glasses/EVT_E/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))
for track in board.GetTracks():
    via = isinstance(track, pcb.PCB_VIA)
    net = track.GetNetname()
    for getter, setter in [
        (track.GetStart, track.SetStart),
        (track.GetEnd, track.SetEnd),
    ]:
        pos = getter()
        x, y = pcb.ToMM(pos.x), pcb.ToMM(pos.y)
        if net == "SWCLK_BOOT0" and 114.8 <= x <= 115.26 and 60.2 <= y <= 61:
            x += 0.05
        if net == "VREF_1V65" and 151.08 <= x <= 151.19 and 61.2 <= y <= 61.83:
            x += 0.07
        if (
            net == "AGND"
            and abs(x - 154.7165) < 0.0001
            and abs(y - 61.5852) < 0.0001
        ):
            y -= 0.03
        setter(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
        if via:
            break
pcb.SaveBoard(str(path), board)
