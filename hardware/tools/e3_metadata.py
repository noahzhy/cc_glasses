"""Synchronize component identity, local models and NC nets for E3."""

import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx  # noqa: E402

ROOT = Path("hardware/ir_glasses/EVT_E3")
parts = json.loads((ROOT / "parts.json").read_text())


def children(node, key):
    return [n for n in node if isinstance(n, list) and str(n[0]) == key]


def set_property(node, key, value):
    fields = children(node, "property")
    field = next((n for n in fields if n[1] == key), None)
    if field is None:
        field = copy.deepcopy(
            next(n for n in fields if n[1] == "Footprint")
            if any(n[1] == "Footprint" for n in fields)
            else next(n for n in fields if n[1] == "Value")
        )
        field[1] = key
        node.append(field)
    field[2] = value


for ref, pin, label in [
    ("U13", "1", "NC"),
    ("U14", "3", "AUXOFF"),
    ("U14", "4", "~{FLT}"),
    ("U14", "10", "ITIMER"),
]:
    parts[ref]["nets"][pin] = f"unconnected-({ref}-{label}-Pad{pin})"

for path in [*ROOT.glob("*.kicad_sch"), ROOT / "ir_glasses.kicad_pcb"]:
    tree = sx.loads(path.read_text(encoding="utf-8"))
    pcb_file = path.suffix == ".kicad_pcb"
    for node in children(tree, "footprint" if pcb_file else "symbol"):
        fields = {n[1]: n[2] for n in children(node, "property")}
        ref = fields.get("Reference")
        if ref not in parts:
            continue
        part = parts[ref]
        for field, value in [
            ("Manufacturer", part.get("manufacturer", "")),
            ("MPN", part.get("mpn", "")),
            ("LCSC", part.get("lcsc", "")),
        ]:
            set_property(node, field, value)
        if pcb_file:
            for pad in children(node, "pad"):
                if (ref == "U13" and pad[1] == "1") or (
                    ref == "U14" and pad[1] in {"3", "4", "10"}
                ):
                    net = part["nets"][pad[1]]
                    existing = children(pad, "net")
                    if existing:
                        existing[0][1:] = [net]
                    else:
                        pad.append([sx.Symbol("net"), net])
    path.write_text(sx.dumps(tree), encoding="utf-8")

# Keep all newly introduced models local to the delivered project.
model_root = Path("D:/Program Files/KiCad/10.0/share/kicad/3dmodels")
for path in [
    ROOT / "ir_glasses.kicad_pcb",
    *ROOT.glob("IR_Glasses.pretty/*.kicad_mod"),
]:
    tree = sx.loads(path.read_text(encoding="utf-8"))
    nodes = (
        children(tree, "footprint") if path.suffix == ".kicad_pcb" else [tree]
    )
    for node in nodes:
        for model in children(node, "model"):
            if not model[1].startswith("${KICAD"):
                continue
            relative = model[1].split("}/", 1)[1]
            source = model_root / relative
            if source.is_file():
                shutil.copy2(source, ROOT / "models" / source.name)
                model[1] = "${KIPRJMOD}/models/" + source.name
    path.write_text(sx.dumps(tree), encoding="utf-8")
(ROOT / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
