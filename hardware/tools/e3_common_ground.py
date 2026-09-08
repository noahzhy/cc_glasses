"""Use a shared ground reference and remove the redundant star net tie."""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

root = Path("hardware/ir_glasses/EVT_E3")


def field(node, key):
    return next(
        (v for v in node if isinstance(v, list) and str(v[0]) == key), None
    )


def ref(node):
    return next(
        (
            v[2]
            for v in node
            if isinstance(v, list)
            and str(v[0]) == "property"
            and v[1] == "Reference"
        ),
        None,
    )


def rename(node):
    if isinstance(node, list):
        return [rename(v) for v in node]
    if isinstance(node, sx.Symbol):
        return node
    if isinstance(node, str):
        return node.replace("AGND", "GND")
    return node


for path in root.glob("*.kicad_sch"):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    if path.name == "power.kicad_sch":
        for node in tree[:]:
            if not isinstance(node, list):
                continue
            key = str(node[0])
            at = field(node, "at")
            uid = field(node, "uuid")
            remove = key == "symbol" and ref(node) == "NT1"
            remove |= (
                key == "global_label"
                and at is not None
                and (at[1:3] in [[148.59, 95.25], [161.29, 95.25]])
            )
            remove |= (
                key == "wire"
                and uid is not None
                and uid[1]
                in {
                    "f9c7d7dc-fe44-4000-8c2f-34ef3a3bd8cc",
                    "55c13424-e7c6-4734-8569-ea42129b8d8e",
                }
            )
            if remove:
                tree.remove(node)
    path.write_text(sx.dumps(rename(tree)), encoding="utf-8")

path = root / "ir_glasses.kicad_pcb"
tree = rename(sx.loads(path.read_text(encoding="utf-8")))
for node in tree[:]:
    if not isinstance(node, list):
        continue
    if str(node[0]) == "footprint" and ref(node) == "NT1":
        tree.remove(node)
    elif str(node[0]) == "zone" and field(node, "net") is not None:
        tree.remove(node)
geometry = json.loads((root / "geometry.json").read_text())
points = " ".join(
    f"(xy {x + 110:.6f} {y + 85:.6f})" for x, y in geometry["outer"]
)
for layer in ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]:
    tree.append(
        sx.loads(
            f'(zone (net "GND") (layer "{layer}") '
            f'(uuid "{uuid.uuid4()}") (hatch edge .5) '
            "(connect_pads yes (clearance .2)) (min_thickness .15) "
            "(fill yes (thermal_gap .2) (thermal_bridge_width .25)) "
            f"(polygon (pts {points})))"
        )
    )
path.write_text(sx.dumps(tree), encoding="utf-8")
path = root / "parts.json"
parts = rename(json.loads(path.read_text()))
parts.pop("NT1", None)
for part in parts.values():
    part["nets"] = {
        k: "GND" if v == "AGND" else v for k, v in part["nets"].items()
    }
path.write_text(json.dumps(parts, indent=2), encoding="utf-8")
print("Shared GND pours on four layers; redundant NT1 removed")
