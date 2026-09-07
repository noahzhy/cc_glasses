"""Add ground regions after importing the completed routing session."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_C")
filename = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(filename))
assert board.GetAreaCount() == 0
for fp in board.GetFootprints():
    name = str(fp.GetFPID().GetLibItemName())
    if name.startswith("Everlight_"):
        ref = fp.Reference()
        ref.SetLayer(pcb.F_Fab)
        ref.SetVisible(True)
        ref.SetPosition(fp.GetPosition())
        ref.SetTextAngle(pcb.EDA_ANGLE(0, pcb.DEGREES_T))
        ref.SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.6), pcb.FromMM(0.6)))
        ref.SetTextThickness(pcb.FromMM(0.1))
text = pcb.PCB_TEXT(board)
text.SetText("TOP / EVT C")
text.SetLayer(pcb.F_SilkS)
text.SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.8), pcb.FromMM(0.8)))
text.SetTextThickness(pcb.FromMM(0.12))
text.SetPosition(pcb.VECTOR2I(pcb.FromMM(110), pcb.FromMM(58)))
board.Add(text)
pcb.SaveBoard(str(filename), board)
zones = []
for item in json.loads((root / "zones.json").read_text()):
    name = item["name"]
    code = board.FindNet(name).GetNetCode()
    points = " ".join(
        f"(xy {x + 110:.6f} {y + 85:.6f})" for x, y in item["coords"][:-1]
    )
    zones.append(
        f'(zone (net {code}) (net_name "{name}") (layer "In1.Cu")'
        " (hatch edge 0.5) (connect_pads yes (clearance 0.2))"
        " (min_thickness 0.15) (fill yes (thermal_gap 0.2)"
        f" (thermal_bridge_width 0.25)) (polygon (pts {points})))"
    )
zones += [zone.replace("In1.Cu", "In2.Cu") for zone in zones]
data = filename.read_text().rstrip()
filename.write_text(data[:-1] + "\n".join(zones) + "\n)")
