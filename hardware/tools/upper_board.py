"""Build the revised KiCad board from the validated previous revision."""

import json
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx

source = Path("hardware/ir_glasses/EVT_C")
root = Path("hardware/ir_glasses/EVT_D")
p = root / "ir_glasses.kicad_pcb"
n = sx.loads((source / p.name).read_text(encoding="utf-8"))
n = [
    v
    for v in n
    if not isinstance(v, list)
    or str(v[0])
    not in {"segment", "via", "zone", "gr_line", "gr_arc", "gr_text"}
]
p.write_text(sx.dumps(n), encoding="utf-8")
b = pcb.LoadBoard(str(p))
parts = json.loads((root / "parts.json").read_text())
for fp in b.GetFootprints():
    item = parts[fp.GetReference()]
    back = item["side"] == "back"
    if fp.IsFlipped() != back:
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(item["angle"])
    x, y = item["xy"]
    fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(x + 110), pcb.FromMM(y + 85)))
g = json.loads((root / "geometry.json").read_text())
for coords in [g["outer"], *g["holes"]]:
    for a, z in zip(coords, coords[1:]):
        line = pcb.PCB_SHAPE()
        line.SetShape(pcb.SHAPE_T_SEGMENT)
        line.SetLayer(pcb.Edge_Cuts)
        line.SetWidth(pcb.FromMM(0.05))
        line.SetStart(
            pcb.VECTOR2I(pcb.FromMM(a[0] + 110), pcb.FromMM(a[1] + 85))
        )
        line.SetEnd(
            pcb.VECTOR2I(pcb.FromMM(z[0] + 110), pcb.FromMM(z[1] + 85))
        )
        b.Add(line)
b.GetTitleBlock().SetRevision("EVT D")
pcb.SaveBoard(str(p), b)
print("EVT D placed.")
