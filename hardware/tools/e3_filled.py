"""Export filled copper polygons for checking cross-layer connections."""

import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx

root = Path("hardware/ir_glasses/EVT_E3")
n = sx.loads((root / "ir_glasses.kicad_pcb").read_text(encoding="utf-8"))


def children(node, key):
    return [v for v in node if isinstance(v, list) and str(v[0]) == key]


out = []
for z in children(n, "zone"):
    name = children(z, "net")[0][1]
    for f in children(z, "filled_polygon"):
        out.append(
            {
                "net": name,
                "layer": children(f, "layer")[0][1],
                "coords": [v[1:] for v in children(f, "pts")[0][1:]],
            }
        )
(root / "filled_regions.json").write_text(json.dumps(out))
print("Filled polygons:", len(out))
