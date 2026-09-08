"""Extend each inner ground reference beyond the fragmented surface pours."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

root = Path("hardware/ir_glasses/EVT_E3")
path = root / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))
for node in tree[:]:
    if not isinstance(node, list) or str(node[0]) != "zone":
        continue
    layer = next(
        v[1] for v in node if isinstance(v, list) and str(v[0]) == "layer"
    )
    if layer in {"In1.Cu", "In2.Cu"}:
        tree.remove(node)
geometry = json.loads((root / "geometry.json").read_text())
points = " ".join(
    f"(xy {x + 110:.6f} {y + 85:.6f})" for x, y in geometry["outer"]
)
for layer, net in [("In1.Cu", "GND"), ("In2.Cu", "AGND")]:
    tree.append(
        sx.loads(
            f'(zone (net "{net}") (layer "{layer}") '
            f'(uuid "{uuid.uuid4()}") (hatch edge .5) '
            "(connect_pads yes (clearance .2)) (min_thickness .15) "
            "(fill yes (thermal_gap .2) (thermal_bridge_width .25)) "
            f"(polygon (pts {points})))"
        )
    )
path.write_text(sx.dumps(tree), encoding="utf-8")
print("Inner pours: In1.Cu GND; In2.Cu AGND; original NT1 retained")
