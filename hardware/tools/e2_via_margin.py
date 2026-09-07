"""Apply the three DRC-verified via shifts beside the new PD lands."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402


def child(node, key):
    return next(n for n in node if isinstance(n, list) and n
                and str(n[0]) == key)


path = Path("hardware/ir_glasses/EVT_E2/ir_glasses.kicad_pcb")
tree = sx.loads(path.read_text(encoding="utf-8"))
moves = {
    "63944768-a87e-48f8-b145-dfa3a37b5479": (139.4187, 65.309199),
    "0438a7a7-e560-4039-ba8b-d8a2407002fb": (80.496, 66.5451),
    "ac4c3952-8514-4f55-8b5e-ea1842b5ce72": (46.48, 78.0469),
}
items = [n for n in tree if isinstance(n, list) and n]
for via in [n for n in items if str(n[0]) == "via"]:
    uid = child(via, "uuid")[1]
    if uid not in moves:
        continue
    at = child(via, "at")
    old = at[1:3]
    new = moves[uid]
    net = child(via, "net")[1]
    count = 0
    for track in [n for n in items if str(n[0]) == "segment"]:
        if child(track, "net")[1] != net:
            continue
        for key in ["start", "end"]:
            end = child(track, key)
            if math.dist(end[1:3], old) < 0.0001:
                end[1:3] = new
                count += 1
    at[1:3] = new
    print(uid, new, count)
path.write_text(sx.dumps(tree), encoding="utf-8")
