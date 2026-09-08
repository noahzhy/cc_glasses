"""Import the routing session without changing physical board geometry."""

import shutil
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx

root = Path("hardware/ir_glasses/EVT_E3")
source = root / "ir_glasses.kicad_pcb"
target = root / "routing_candidate.kicad_pcb"
tree = sx.loads(source.read_text(encoding="utf-8"))
tree = [
    item
    for item in tree
    if not (isinstance(item, list) and str(item[0]) in {"segment", "via"})
]
target.write_text(sx.dumps(tree), encoding="utf-8")
shutil.copyfile(
    source.with_suffix(".kicad_pro"), target.with_suffix(".kicad_pro")
)
board = pcb.LoadBoard(str(target))
poses = {
    f.GetReference(): (f.GetPosition().x, f.GetPosition().y)
    for f in board.GetFootprints()
}
before = {
    (f.GetReference(), p.GetNumber()): (
        p.GetPosition().x,
        p.GetPosition().y,
        p.GetNetname(),
    )
    for f in board.GetFootprints()
    for p in f.Pads()
}
assert pcb.ImportSpecctraSES(board, str(root / "routing_fresh.ses"))
for footprint in board.GetFootprints():
    footprint.SetPosition(pcb.VECTOR2I(*poses[footprint.GetReference()]))
after = {
    (f.GetReference(), p.GetNumber()): (
        p.GetPosition().x,
        p.GetPosition().y,
        p.GetNetname(),
    )
    for f in board.GetFootprints()
    for p in f.Pads()
}
assert before == after
pcb.ZONE_FILLER(board).Fill(board.Zones())
pcb.SaveBoard(str(target), board)
print("Candidate imported; pad positions and nets unchanged.")
