"""Remove only the native segments selected by the negotiated router."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

root = Path("hardware/ir_glasses/EVT_E3")
path = root / "ir_glasses.kicad_pcb"
removed = set(json.loads((root / "ripup_uuids.json").read_text()))
tree = sx.loads(path.read_text(encoding="utf-8"))
count = 0
for node in tree[:]:
    if not isinstance(node, list) or str(node[0]) not in {"segment", "via"}:
        continue
    uid = next(
        x[1] for x in node if isinstance(x, list) and str(x[0]) == "uuid"
    )
    if uid in removed:
        tree.remove(node)
        count += 1
assert count == len(removed)
path.write_text(sx.dumps(tree), encoding="utf-8")
print("Removed selected segments:", count)
