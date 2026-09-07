"""Remove obsolete copper and synchronize PD metadata before rerouting."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402


ROOT = Path("hardware/ir_glasses/EVT_E2")
path = ROOT / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and str(x[0]) == key]


report = json.loads((ROOT / "drc.json").read_text(encoding="utf-8"))
remove = {item["uuid"] for error in report["violations"]
          if error["type"] in {"clearance", "shorting_items", "hole_clearance",
                               "copper_edge_clearance", "solder_mask_bridge",
                               "track_dangling"}
          for item in error["items"]}
count = 0
for node in tree[:]:
    if not isinstance(node, list) or not node:
        continue
    kind = str(node[0])
    if kind in {"segment", "via", "arc"}:
        if children(node, "uuid")[0][1] in remove:
            tree.remove(node)
            count += 1
    elif kind == "footprint":
        fields = {x[1]: x for x in children(node, "property")}
        ref = fields["Reference"][2]
        if ref.startswith("PD"):
            for field in fields.values():
                if not children(field, "hide"):
                    field.append([sx.Symbol("hide"), sx.Symbol("yes")])
            fields["Datasheet"][2] = (
                "https://en.everlight.com/wp-content/plugins/"
                "ItemRelationship/product_files/pdf/PD15-21B-TR8.pdf")
    elif kind == "title_block":
        for rev in children(node, "rev"):
            rev[1] = "EVT E2"
setup = children(tree, "setup")[0]
if not children(setup, "stackup"):
    setup.append([sx.Symbol("stackup")])
stackup = children(setup, "stackup")[0]
finish = children(stackup, "copper_finish")
if finish:
    finish[0][1] = "ENIG"
else:
    stackup.append([sx.Symbol("copper_finish"), "ENIG"])
path.write_text(sx.dumps(tree), encoding="utf-8")
print("Removed obsolete copper items:", count)
