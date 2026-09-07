"""Create revision B without changing the completed revision A."""

import json
import shutil
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx

root = Path("hardware/ir_glasses")
source = root / "EVT_A"
target = root / "EVT_C"
for pattern in ["*.kicad_sch", "*.kicad_pro", "*.kicad_sym"]:
    for path in source.glob(pattern):
        shutil.copy2(path, target / path.name)
for name in [
    "fp-lib-table",
    "sym-lib-table",
    "ir_glasses.net",
    "mechanical_reference.svg",
    "optical_map.csv",
]:
    shutil.copy2(source / name, target / name)
for name in ["IR_Glasses.pretty", "models"]:
    shutil.copytree(source / name, target / name, dirs_exist_ok=True)
data = sx.loads((source / "ir_glasses.kicad_pcb").read_text())
data = [
    node
    for node in data
    if not isinstance(node, list)
    or str(node[0])
    not in {"segment", "via", "zone", "gr_line", "gr_arc", "gr_text"}
]
new_name = "TSSOP-14_4.4x5mm_P0.65mm"
library = Path("D:/Program Files/KiCad/10.0/share/kicad/footprints")
module_path = library / "Package_SO.pretty" / f"{new_name}.kicad_mod"
shutil.copy2(module_path, target / "IR_Glasses.pretty" / module_path.name)
module = sx.loads(module_path.read_text(encoding="utf-8"))


def children(node, tag):
    return [n for n in node if isinstance(n, list) and str(n[0]) == tag]


for index, node in enumerate(data):
    if not isinstance(node, list) or str(node[0]) != "footprint":
        continue
    properties = {n[1]: n for n in children(node, "property")}
    ref = properties["Reference"][2]
    if ref not in {"U2", "U3", "U4", "U5"}:
        continue
    new = sx.loads(sx.dumps(module))
    new[1] = f"IR_Glasses:{new_name}"
    new = [
        n
        for n in new
        if not isinstance(n, list) or str(n[0]) not in {"version", "generator"}
    ]
    for tag in ["uuid", "path", "sheetname", "sheetfile"]:
        new.extend(children(node, tag))
    old_pads = {n[1]: n for n in children(node, "pad")}
    for pad in children(new, "pad"):
        for tag in ["net", "uuid", "pinfunction", "pintype"]:
            pad.extend(children(old_pads[pad[1]], tag))
    for prop in children(new, "property"):
        if prop[1] == "Reference":
            prop[2] = ref
        elif prop[1] == "Value":
            prop[2] = "TLV9064IPWR"
    data[index] = new
filename = target / "ir_glasses.kicad_pcb"
filename.write_text(sx.dumps(data))
board = pcb.LoadBoard(str(filename))
board.SetCopperLayerCount(4)
parts = json.loads((target / "parts.json").read_text())
for fp in board.GetFootprints():
    part = parts[fp.GetReference()]
    x, y = part["xy"]
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    if part["side"] == "back":
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(part["angle"])
    fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x + 110), pcb.FromMM(y + 85)))
geometry = json.loads((target / "geometry.json").read_text())
for coords in [geometry["outer"], *geometry["holes"]]:
    for start, end in zip(coords, coords[1:]):
        line = pcb.PCB_SHAPE()
        line.SetShape(pcb.SHAPE_T_SEGMENT)
        line.SetLayer(pcb.Edge_Cuts)
        line.SetWidth(pcb.FromMM(0.05))
        line.SetStart(
            pcb.VECTOR2I(pcb.FromMM(start[0] + 110), pcb.FromMM(start[1] + 85))
        )
        line.SetEnd(
            pcb.VECTOR2I(pcb.FromMM(end[0] + 110), pcb.FromMM(end[1] + 85))
        )
        board.Add(line)
board.GetTitleBlock().SetRevision("EVT C")
pcb.SaveBoard(str(target / "ir_glasses.kicad_pcb"), board)
print("EVT C with TSSOP-14 amplifiers created.")
