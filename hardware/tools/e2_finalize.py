"""Apply the verified ground stitch and smooth upper rim transitions."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402


ROOT = Path("hardware/ir_glasses/EVT_E2")
path = ROOT / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))
geometry = json.loads((ROOT / "geometry.json").read_text())


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and str(x[0]) == key]


tree = [node for node in tree if not (
    isinstance(node, list) and node and str(node[0]).startswith("gr_")
    and children(node, "layer") and children(node, "layer")[0][1]
    == "Edge.Cuts")]
for ring in [geometry["outer"], *geometry["holes"]]:
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    for a, b in zip(ring, ring[1:]):
        tree.append(sx.loads(
            f'(gr_line (start {a[0] + 110:.6f} {a[1] + 85:.6f}) '
            f'(end {b[0] + 110:.6f} {b[1] + 85:.6f}) '
            '(stroke (width 0.05) (type solid)) (layer "Edge.Cuts") '
            f'(uuid "{uuid.uuid4()}"))'))
if not any(children(v, "at")[0][1:3] == [145.6, 107.85]
           for v in children(tree, "via")):
    tree.append(sx.loads(
        '(via (at 145.6 107.85) (size 0.5) (drill 0.3) '
        '(layers "F.Cu" "B.Cu") (net "AGND") '
        f'(uuid "{uuid.uuid4()}"))'))
path.write_text(sx.dumps(tree), encoding="utf-8")
print("Applied the verified AGND stitch and finished outline")
