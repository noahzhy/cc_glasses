"""Apply the PD21 footprints, optical placement and new board outline."""

import json
from pathlib import Path

import pcbnew as pcb


ROOT = Path("hardware/ir_glasses/EVT_E2")
SOURCE = ROOT.parent / "EVT_E1"
board = pcb.LoadBoard(str(SOURCE / "ir_glasses.kicad_pcb"))
targets = json.loads((ROOT / "optics_target.json").read_text())
geometry = json.loads((ROOT / "geometry.json").read_text())


def point(xy):
    return pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1]))


for fp in list(board.GetFootprints()):
    ref = fp.GetReference()
    if ref not in targets:
        continue
    if ref.startswith("PD"):
        replacement = pcb.FootprintLoad(str(ROOT / "IR_Glasses.pretty"),
                                        "Everlight_PD15_21B")
        replacement.SetReference(ref)
        replacement.SetValue("PD15-21B/TR8")
        replacement.SetFPID(pcb.LIB_ID("IR_Glasses", "Everlight_PD15_21B"))
        replacement.SetPath(fp.GetPath())
        replacement.SetUuid(fp.m_Uuid)
        replacement.SetAttributes(fp.GetAttributes())
        for field in fp.GetFields():
            name = field.GetName()
            if name in {"Reference", "Value", "Footprint"}:
                continue
            replacement.SetField(name, field.GetText())
        for name, value in [("Manufacturer", "Everlight"),
                            ("MPN", "PD15-21B/TR8"),
                            ("LCSC", "C2921391")]:
            replacement.SetField(name, value)
        for pad in replacement.Pads():
            net = "AGND" if pad.GetNumber() == "1" else f"PD_IN{ref[2:]}"
            pad.SetNet(board.FindNet(net))
        board.Remove(fp)
        board.Add(replacement)
        fp = replacement
    target = targets[ref]
    fp.SetPosition(point([target["xy"][0] + 110, target["xy"][1] + 85]))
    fp.SetOrientationDegrees(target["angle"])
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)

for drawing in list(board.GetDrawings()):
    if drawing.GetLayer() == pcb.Edge_Cuts:
        board.Remove(drawing)
    elif isinstance(drawing, pcb.PCB_TEXT):
        drawing.SetText(drawing.GetText().replace("EVT E1", "EVT E2")
                        .replace("EVT E", "EVT E2")
                        .replace("EVT E22", "EVT E2"))
for loop in [geometry["outer"], *geometry["holes"]]:
    if loop[0] != loop[-1]:
        loop.append(loop[0])
    for a, b in zip(loop, loop[1:]):
        edge = pcb.PCB_SHAPE(board)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetStart(point([a[0] + 110, a[1] + 85]))
        edge.SetEnd(point([b[0] + 110, b[1] + 85]))
        edge.SetWidth(pcb.FromMM(0.05))
        edge.SetLayer(pcb.Edge_Cuts)
        board.Add(edge)
pcb.SaveBoard(str(ROOT / "ir_glasses.kicad_pcb"), board)
print("Updated 16 PD footprints and 32 optical placements")
