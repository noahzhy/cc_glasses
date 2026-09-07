"""Add the IMU identification and prepare ordinary through-via routing."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E")
path = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
for fp in board.GetFootprints():
    if fp.GetReference() == "RF13":
        for graphic in list(fp.GraphicalItems()):
            if graphic.GetLayer() == pcb.F_SilkS:
                fp.Remove(graphic)
text = pcb.PCB_TEXT(board)
text.SetText("IMU")
text.SetLayer(pcb.F_SilkS)
text.SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.8), pcb.FromMM(0.8)))
text.SetTextThickness(pcb.FromMM(0.12))
text.SetPosition(pcb.VECTOR2I(pcb.FromMM(106.1), pcb.FromMM(71.3)))
board.Add(text)
pcb.SaveBoard(str(path), board)
project = root / "ir_glasses.kicad_pro"
settings = json.loads(project.read_text())
default = settings["net_settings"]["classes"][0]
default.update(track_width=0.15, via_diameter=0.5, via_drill=0.3)
project.write_text(json.dumps(settings, indent=2))
