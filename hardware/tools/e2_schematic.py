"""Create the EVT E2 photodiode library and update the five schematics."""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

ROOT = Path("hardware/ir_glasses/EVT_E2")
NAME = "Everlight_PD15_21B"
LIB_ID = f"IR_Glasses:{NAME}"
DATASHEET = (
    "https://en.everlight.com/wp-content/plugins/ItemRelationship/"
    "product_files/pdf/PD15-21B-TR8.pdf"
)


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and str(x[0]) == key]


def prop(node, name):
    return next(x for x in children(node, "property") if x[1] == name)


def write_tree(path, tree):
    path.write_text(sx.dumps(tree) + "\n", encoding="utf-8")


def same_point(first, second):
    return all(abs(a - b) < 0.0001 for a, b in zip(first, second))


symbol_text = f'''(symbol "{NAME}"
    (pin_names (offset 0.5)) (in_bom yes) (on_board yes)
    (property "Reference" "PD" (at 0 6.35 0)
        (effects (font (size 1.27 1.27))))
    (property "Value" "PD15-21B/TR8" (at 0 8.89 0)
        (effects (font (size 1.27 1.27))))
    (property "Footprint" "{LIB_ID}" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "{DATASHEET}" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
    (property "Description" "940nm PIN photodiode; 1=A, 2=K" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
    (symbol "{NAME}_0_1"
        (rectangle (start -10.16 2.54) (end 10.16 -2.54)
            (stroke (width 0.254) (type default)) (fill (type background))))
    (symbol "{NAME}_1_1"
        (pin passive line (at -12.7 0 0) (length 2.54)
            (name "K" (effects (font (size 1 1))))
            (number "2" (effects (font (size 1 1)))))
        (pin passive line (at 12.7 0 180) (length 2.54)
            (name "A" (effects (font (size 1 1))))
            (number "1" (effects (font (size 1 1)))))))'''
symbol = sx.loads(symbol_text)

footprint_text = f'''(footprint "{NAME}"
    (version 20260206) (generator "pcbnew") (layer "F.Cu")
    (descr "Everlight PD15-21B/TR8 Rev5 p2; 1=A right, 2=K left")
    (property "Reference" "REF**" (at 0 0 0) (layer "F.SilkS")
        (hide yes) (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Value" "PD15-21B/TR8" (at 0 0 0) (layer "F.Fab")
        (hide yes) (effects (font (size 0.6 0.6) (thickness 0.1))))
    (property "Datasheet" "{DATASHEET}" (at 0 0 0) (layer "F.Fab")
        (hide yes) (effects (font (size 0.6 0.6) (thickness 0.1))))
    (attr smd)
    (fp_rect (start -2.05 -1.0) (end 2.05 1.0)
        (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
    (fp_rect (start -1.6 -0.75) (end 1.6 0.75)
        (stroke (width 0.05) (type solid)) (fill no) (layer "F.Fab"))
    (fp_line (start -0.5 -0.5) (end -0.5 0.5)
        (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
    (fp_line (start -1.1 -0.7) (end -1.1 0.7)
        (stroke (width 0.1) (type solid)) (layer "F.Fab"))
    (pad "1" smd rect (at 1.3 0) (size 1.0 1.5)
        (layers "F.Cu" "F.Paste" "F.Mask"))
    (pad "2" smd rect (at -1.3 0) (size 1.0 1.5)
        (layers "F.Cu" "F.Paste" "F.Mask"))
    (model "${{KIPRJMOD}}/models/{NAME}.wrl"
        (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'''
write_tree(ROOT / "IR_Glasses.pretty" / f"{NAME}.kicad_mod",
           sx.loads(footprint_text))

# KiCad interprets VRML model units as 0.1 inch (2.54 mm).
model = "#VRML V2.0 utf8\n# Dimension model, not an optical simulation.\n"
for x, y, z, width, depth, height, color in [
    (0, 0, 0.55, 3.2, 1.5, 1.1, ".06 .06 .07"),
    (-1.35, 0, 0.3, 0.5, 1.5, 0.6, ".7 .7 .72"),
    (1.35, 0, 0.3, 0.5, 1.5, 0.6, ".7 .7 .72"),
    (-0.95, 0, 1.095, 0.15, 1.3, 0.01, ".75 .75 .75"),
]:
    position = " ".join(f"{v / 2.54:.9f}" for v in (x, y, z))
    size = " ".join(f"{v / 2.54:.9f}" for v in (width, depth, height))
    model += (
        f"Transform {{ translation {position} children [ Shape {{ "
        f"appearance Appearance {{ material Material {{ diffuseColor {color} "
        f"}} }} geometry Box {{ size {size} }} }} ] }}\n"
    )
(ROOT / "models" / f"{NAME}.wrl").write_text(model, encoding="utf-8")

library_path = ROOT / "IR_Glasses.kicad_sym"
library = sx.loads(library_path.read_text(encoding="utf-8"))
library = [x for x in library if not (
    isinstance(x, list) and str(x[0]) == "symbol"
    and x[1] in {"PD15_22B", NAME})]
library.append(copy.deepcopy(symbol))
write_tree(library_path, library)

count = 0
for path in ROOT.glob("*.kicad_sch"):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    title = children(tree, "title_block")[0]
    children(title, "rev")[0][1] = "EVT E2"
    children(title, "date")[0][1] = "2026-09-07"
    symbols = children(tree, "lib_symbols")[0]
    had_old = any(x[1] == "IR_Glasses:PD15_22B"
                  for x in children(symbols, "symbol"))
    if had_old:
        symbols[:] = [x for x in symbols if not (
            isinstance(x, list) and str(x[0]) == "symbol"
            and x[1] == "IR_Glasses:PD15_22B")]
        embedded = copy.deepcopy(symbol)
        embedded[1] = LIB_ID
        symbols.append(embedded)
    for item in children(tree, "symbol"):
        if children(item, "lib_id")[0][1] != "IR_Glasses:PD15_22B":
            continue
        count += 1
        x, y, angle = children(item, "at")[0][1:4]
        assert angle == 0
        children(item, "lib_id")[0][1] = LIB_ID
        for field, value in {
            "Value": "PD15-21B/TR8", "MPN": "PD15-21B/TR8",
            "LCSC": "C2921391", "Footprint": LIB_ID,
        }.items():
            prop(item, field)[2] = value
        datasheet = copy.deepcopy(prop(item, "Footprint"))
        datasheet[1:3] = ["Datasheet", DATASHEET]
        item.append(datasheet)
        item[:] = [v for v in item if not (
            isinstance(v, list) and str(v[0]) == "pin" and v[1] in {"3", "4"})]
        for sign in [-1, 1]:
            old_top = (x + sign * 12.7, y - 1.27)
            old_bottom = (x + sign * 12.7, y + 1.27)
            bottom_wire = next(w for w in children(tree, "wire")
                               if same_point(children(w, "pts")[0][1][1:3],
                                             old_bottom))
            end = children(bottom_wire, "pts")[0][2][1:3]
            tree.remove(bottom_wire)
            bottom_label = next(g for g in children(tree, "global_label")
                                if same_point(children(g, "at")[0][1:3], end))
            tree.remove(bottom_label)
            top_wire = next(w for w in children(tree, "wire")
                            if same_point(children(w, "pts")[0][1][1:3],
                                          old_top))
            end = children(top_wire, "pts")[0][2][1:3]
            top_label = next(g for g in children(tree, "global_label")
                             if same_point(children(g, "at")[0][1:3], end))
            children(top_label, "at")[0][2] = y
            for point in children(top_wire, "pts")[0][1:]:
                point[2] = y
    write_tree(path, tree)
print(f"Created {LIB_ID}; updated {count} photodiodes.")
