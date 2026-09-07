"""Create EVT E1 with explicit purchasing identities and a new FPC footprint."""

import copy
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

base = Path("hardware/ir_glasses")
source = base / "EVT_E"
root = base / "EVT_E1"
freeze = base / "material_freeze"
selections = json.loads((freeze / "selections.json").read_text())
root.mkdir(exist_ok=True)
for pattern in ["*.kicad_sch", "*.kicad_pro", "*.kicad_sym", "*.kicad_pcb"]:
    for path in source.glob(pattern):
        shutil.copy2(path, root / path.name)
for name in ["IR_Glasses.pretty", "models"]:
    shutil.copytree(source / name, root / name, dirs_exist_ok=True)
for name in ["fp-lib-table", "sym-lib-table", "parts.json", "geometry.json",
             "mechanical_reference.svg", "mechanical_reference.png",
             "optical_map.csv", "optical_placement.csv"]:
    shutil.copy2(source / name, root / name)


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and str(x[0]) == key]


def prop(node, name):
    return next(x for x in children(node, "property") if x[1] == name)


def add_field(node, name, value, template):
    field = copy.deepcopy(template)
    field[1:3] = [name, value]
    if not children(field, "hide"):
        field.append([sx.Symbol("hide"), sx.Symbol("yes")])
    node.append(field)


def write_tree(path, tree):
    path.write_text(sx.dumps(tree) + "\n", encoding="utf-8")


old_name = "TE_0-1734839-5_1x05-1MP_P0.5mm_Horizontal"
new_name = "TE_2492111-5_1x05_P0.5mm_Horizontal"
footprint_id = "IR_Glasses:" + new_name
mod = sx.loads((source / "IR_Glasses.pretty" / (old_name + ".kicad_mod"))
               .read_text())
mod[1] = new_name
prop(mod, "Value")[2] = "2492111-5"
children(mod, "descr")[0][1] = "TE 2492111 drawing A; top contacts; 0.3mm FPC"
for item in children(mod, "pad"):
    at = children(item, "at")[0]
    size = children(item, "size")[0]
    if item[1] == "MP":
        at[1:3] = [-2.6 if at[1] < 0 else 2.6, 0.82]
        size[1:3] = [2.2, 3.3]
    else:
        size[1:3] = [0.3, 1.2]
mod = [x for x in mod if not (
    isinstance(x, list) and x and str(x[0]) in
    {"fp_line", "fp_rect", "fp_text", "model"})]
for text in [
    '(fp_rect (start -4.3 -2.2) (end 4.3 3.72) '
    '(stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))',
    '(fp_rect (start -4.05 -1.73) (end 4.05 3.47) '
    '(stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
    '(fp_line (start -1.2 -0.55) (end -1 -0.15) '
    '(stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
    '(fp_line (start -1 -0.15) (end -0.8 -0.55) '
    '(stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
    '(fp_line (start -0.8 -0.55) (end -1.2 -0.55) '
    '(stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
    '(model "${KIPRJMOD}/models/TE_2492111-5_aligned.step" '
    '(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))',
]:
    mod.append(sx.loads(text))
write_tree(root / "IR_Glasses.pretty" / (new_name + ".kicad_mod"), mod)

rows = list(csv.DictReader((base / "production_review" /
                           "procurement_draft_2pcs.csv").open(
                               encoding="utf-8-sig")))
by_ref = {}
frozen = []
value_changes = {"R1": "2.67k", "J1": "2492111-5",
                 "D17": "PESD5V0S1BA,115", "U11": "PESD3V3L2BT,215",
                 "C28": "47u 16V X5R"}
for row in rows:
    refs = row["Designator"].split(",")
    manufacturer, mpn, code, specs, purchase = selections[refs[0]]
    value = value_changes.get(refs[0], row["Value"])
    footprint = footprint_id if refs[0] == "J1" else row["Footprint"]
    url = f"https://www.lcsc.com/product-detail/{code}.html"
    supplier = "LCSC"
    supplier_code = code
    availability = "Not reserved; confirm domestic SMT stock and attrition"
    if refs[0] == "J1":
        supplier = "DigiKey / customer supplied"
        supplier_code = "17-2492111-5CT-ND"
        url = ("https://www.digikey.com/en/products/detail/"
               "te-connectivity-amp-connectors/2492111-5/29274746")
        availability = "Public listing: 1910; customer supply; not reserved"
    if refs[0] == "PD1":
        availability = "HOLD: obsolete; public stock 10 < 32; conflicting caches"
    if refs[0] == "D1":
        availability = ("Domestic stock unconfirmed; Everlight Americas listing "
                        "3870; customer supply fallback; not reserved")
    if refs[0] == "C29":
        availability = ("JLCPCB public listing 29080; domestic SMT stock "
                        "unconfirmed; not reserved")
    entry = {
        "Designator": row["Designator"], "Value": value,
        "Manufacturer": manufacturer, "MPN": mpn, "LCSC": code,
        "Footprint": footprint, "Specifications": specs,
        "Qty_per_board": len(refs), "Net_qty_2_boards": 2 * len(refs),
        "Suggested_purchase_qty": purchase, "Supplier": supplier,
        "Supplier_code": supplier_code, "Source": url,
        "Engineering_status": "FROZEN_EVT_E1", "Supply_status": availability,
        "Side": "F.Cu", "Checked_on": "2026-09-06",
    }
    frozen.append(entry)
    for ref in refs:
        by_ref[ref] = entry
assert len(frozen) == 25 and len(by_ref) == 122
with (freeze / "bom_frozen_2pcs.csv").open("w", encoding="utf-8-sig",
                                        newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=frozen[0].keys())
    writer.writeheader()
    writer.writerows(frozen)
for filename, entries in [
    ("bom_jlc_import.csv", [r for r in frozen if r["LCSC"]]),
    ("customer_supplied.csv", [r for r in frozen if not r["LCSC"]]),
]:
    with (freeze / filename).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for row in entries:
            writer.writerow([row["MPN"], row["Designator"], row["Footprint"],
                             row["LCSC"]])

parts = json.loads((root / "parts.json").read_text())
for ref, row in by_ref.items():
    parts[ref].update(value=row["Value"], footprint=row["Footprint"],
                      manufacturer=row["Manufacturer"], mpn=row["MPN"],
                      lcsc=row["LCSC"])
(root / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")

for path in root.glob("*.kicad_sch"):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    children(children(tree, "title_block")[0], "rev")[0][1] = "EVT E1"
    for symbol in children(tree, "symbol"):
        ref = prop(symbol, "Reference")[2]
        if ref not in by_ref:
            continue
        row = by_ref[ref]
        prop(symbol, "Value")[2] = row["Value"]
        prop(symbol, "Footprint")[2] = row["Footprint"]
        template = prop(symbol, "Footprint")
        for key in ["Manufacturer", "MPN", "LCSC"]:
            add_field(symbol, key, row[key], template)
    write_tree(path, tree)

path = root / "ir_glasses.kicad_pcb"
board = sx.loads(path.read_text(encoding="utf-8"))
for fp in children(board, "footprint"):
    ref = prop(fp, "Reference")[2]
    if ref not in by_ref:
        continue
    row = by_ref[ref]
    prop(fp, "Value")[2] = row["Value"]
    template = prop(fp, "Value")
    for key in ["Manufacturer", "MPN", "LCSC"]:
        add_field(fp, key, row[key], template)
    if ref == "J1":
        fp[1] = footprint_id
        for pad in children(fp, "pad"):
            at = children(pad, "at")[0]
            size = children(pad, "size")[0]
            if pad[1] == "MP":
                at[1:3] = [-2.6 if at[1] < 0 else 2.6, 0.82]
                size[1:3] = [2.2, 3.3]
            else:
                size[1:3] = [0.3, 1.2]
        fp[:] = [x for x in fp if not (
            isinstance(x, list) and x and str(x[0]) in
            {"fp_line", "fp_rect", "fp_text", "model"})]
        fp.extend(copy.deepcopy(x) for x in mod if isinstance(x, list)
                  and x and str(x[0]) in
                  {"fp_line", "fp_rect", "fp_text", "model"})
for title in children(board, "title_block"):
    for revision in children(title, "rev"):
        revision[1] = "EVT E1"
write_tree(path, board)

data = list(csv.DictReader((source / "bom.csv").open(encoding="utf-8-sig")))
for row in data:
    selected = by_ref.get(row["Reference"])
    for key in ["Manufacturer", "MPN", "LCSC"]:
        row[key] = selected[key] if selected else ""
    if selected:
        row["Value"] = selected["Value"]
        row["Footprint"] = selected["Footprint"]
with (root / "bom.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
print("EVT E1:", len(frozen), "frozen groups;", len(by_ref), "parts per board")
