"""Mark the IMU axes for the pin-1-at-upper-left, front-side orientation."""

from pathlib import Path

import pcbnew as pcb

path = Path("hardware/ir_glasses/EVT_E/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))


def point(x, y):
    return pcb.VECTOR2I(pcb.FromMM(x + 110), pcb.FromMM(y + 85))


for item in board.GetDrawings():
    if isinstance(item, pcb.PCB_TEXT) and item.GetText() == "IMU":
        item.SetPosition(point(-3.85, -15.3))
for label, x, y in [("X", -3.6, -12.25), ("Y", -5.05, -14.05)]:
    text = pcb.PCB_TEXT(board)
    text.SetText(label)
    text.SetLayer(pcb.F_SilkS)
    text.SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.8), pcb.FromMM(0.8)))
    text.SetTextThickness(pcb.FromMM(0.1))
    text.SetPosition(point(x, y))
    board.Add(text)
for start, end in [
    ((-5.05, -12.25), (-4.25, -12.25)),
    ((-4.25, -12.25), (-4.55, -12.45)),
    ((-4.25, -12.25), (-4.55, -12.05)),
    ((-5.05, -12.25), (-5.05, -13.35)),
    ((-5.05, -13.35), (-5.25, -13.05)),
    ((-5.05, -13.35), (-4.85, -13.05)),
]:
    line = pcb.PCB_SHAPE()
    line.SetShape(pcb.SHAPE_T_SEGMENT)
    line.SetLayer(pcb.F_SilkS)
    line.SetWidth(pcb.FromMM(0.1))
    line.SetStart(point(*start))
    line.SetEnd(point(*end))
    board.Add(line)
pcb.SaveBoard(str(path), board)
