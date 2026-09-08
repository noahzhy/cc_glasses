"""Create E3 source changes while preserving the frozen E2 revision."""

import copy
import json
import math
import shutil
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path("hardware/ir_glasses").resolve()))
import generate as gen  # noqa: E402

sx = gen.sx
ROOT = Path("hardware/ir_glasses/EVT_E3")
LIB = Path("D:/Program Files/KiCad/10.0/share/kicad")
parts = json.loads((ROOT / "parts.json").read_text())
library = sx.loads((ROOT / "IR_Glasses.kicad_sym").read_text())
gen.SYMBOLS = {s[1]: s for s in gen.children(library, "symbol")}
new_refs = []


def write(path, tree):
    path.write_text(sx.dumps(tree) + "\n", encoding="utf-8")


def add(ref, symbol, value, footprint, nets, target, mpn, lcsc, maker):
    parts[ref] = dict(
        symbol=symbol,
        value=value,
        footprint="IR_Glasses:" + footprint,
        nets={str(k): v for k, v in nets.items()},
        xy=target,
        angle=0,
        page="protection",
        sch=[0, 0],
        side="front",
        manufacturer=maker,
        mpn=mpn,
        lcsc=lcsc,
    )
    new_refs.append(ref)


def passive(ref, template, nets, target):
    part = parts[template]
    add(
        ref,
        part["symbol"],
        part["value"],
        part["footprint"].split(":")[1],
        nets,
        target,
        part["mpn"],
        part["lcsc"],
        part["manufacturer"],
    )


gen.box_symbol(
    "SN74LVC1G123DCT",
    [
        ("1", "A", "input"),
        ("2", "B", "input"),
        ("3", "~{CLR}", "input"),
        ("4", "GND", "power_in"),
        ("5", "Q", "output"),
        ("6", "Cext", "passive"),
        ("7", "Rext/Cext", "passive"),
        ("8", "VCC", "power_in"),
    ],
)
gen.box_symbol(
    "SN74LVC1G04DBV",
    [
        ("1", "NC", "no_connect"),
        ("2", "A", "input"),
        ("3", "GND", "power_in"),
        ("4", "Y", "output"),
        ("5", "VCC", "power_in"),
    ],
)
gen.box_symbol(
    "TPS259470LRPW",
    [
        ("1", "EN/UVLO", "input"),
        ("2", "OVLO", "input"),
        ("3", "AUXOFF", "open_collector"),
        ("4", "~{FLT}", "open_collector"),
        ("5", "IN", "power_in"),
        ("6", "OUT", "power_out"),
        ("7", "DVDT", "passive"),
        ("8", "GND", "power_in"),
        ("9", "ILM", "passive"),
        ("10", "ITIMER", "passive"),
    ],
)
gen.read_symbol("Device", "LED")
gen.SYMBOLS["Status_LED"] = gen.SYMBOLS.pop("LED")
gen.SYMBOLS["Status_LED"][1] = "Status_LED"
for sub in gen.children(gen.SYMBOLS["Status_LED"], "symbol"):
    sub[1] = sub[1].replace("LED_", "Status_LED_")
gen.read_symbol("Device", "D_Zener")

# Preserve the original IR LED symbol, whose pad polarity is reversed.
original = next(s for s in gen.children(library, "symbol") if s[1] == "LED")
gen.SYMBOLS["LED"] = original

add(
    "U12",
    "SN74LVC1G123DCT",
    "SN74LVC1G123DCTR",
    "SSOP-8_2.95x2.8mm_P0.65mm",
    {
        1: "GND",
        2: "3V3",
        3: "LED_ENABLE",
        4: "GND",
        5: "LED_WINDOW",
        6: "PULSE_C",
        7: "PULSE_RC",
        8: "3V3",
    },
    [-15, -17],
    "SN74LVC1G123DCTR",
    "C123302",
    "Texas Instruments",
)
add(
    "U13",
    "SN74LVC1G04DBV",
    "SN74LVC1G04DBVR",
    "SOT-23-5",
    {2: "LED_WINDOW", 3: "GND", 4: "LED_BLANK", 5: "3V3"},
    [19, -16],
    "SN74LVC1G04DBVR",
    "C7827",
    "Texas Instruments",
)
add(
    "U14",
    "TPS259470LRPW",
    "TPS259470LRPWR",
    "TI_RPW0010A",
    {
        1: "EFUSE_EN",
        2: "OV_SENSE",
        5: "VIN_3V3",
        6: "3V3",
        7: "INRUSH_RC",
        8: "GND",
        9: "ILIM_SET",
    },
    [51, -20],
    "TPS259470LRPWR",
    "C3662793",
    "Texas Instruments",
)
for ref, net, target in [
    ("D18", "NRST_EXT", [55, -17]),
    ("D19", "NRST", [-53, -19]),
]:
    add(
        ref,
        "D_Zener",
        "PESD3V3U1UB,115",
        "D_SOD-523",
        {1: net, 2: "GND"},
        target,
        "PESD3V3U1UB,115",
        "C2443469",
        "Nexperia",
    )
add(
    "D20",
    "Status_LED",
    "GREEN / STATUS",
    "LED_0603_1608Metric",
    {1: "STATUS_LED_N", 2: "STATUS_A"},
    [-54, -26],
    "LTST-C190KGKT",
    "C125094",
    "Lite-On",
)
passive("R14", "R11", {1: "NRST_EXT", 2: "NRST"}, [53, -17])
passive("R15", "R5", {1: "3V3", 2: "PULSE_RC"}, [-16, -16])
passive("R16", "R4", {1: "LED_ENABLE", 2: "GND"}, [-11, -17])
passive("R17", "R6", {1: "3V3", 2: "STATUS_A"}, [-51, -26])
for ref, value, mpn, lcsc, nets, target, maker in [
    (
        "R18",
        "19.1k 0.1%",
        "RT0402BRD0719K1L",
        "C852587",
        {1: "VIN_3V3", 2: "OV_SENSE"},
        [50, -18],
        "Yageo",
    ),
    (
        "R19",
        "10k 0.1%",
        "RT0402BRD0710KL",
        "C190095",
        {1: "OV_SENSE", 2: "GND"},
        [50, -16],
        "Yageo",
    ),
    (
        "R20",
        "6.2k",
        "0402WGF6201TCE",
        "C25915",
        {1: "ILIM_SET", 2: "GND"},
        [52, -18],
        "UNI-ROYAL",
    ),
    (
        "R21",
        "470k",
        "0402WGF4703TCE",
        "C25790",
        {1: "VIN_3V3", 2: "EFUSE_EN"},
        [52, -16],
        "UNI-ROYAL",
    ),
]:
    add(ref, "R", value, "R_0402_1005Metric", nets, target, mpn, lcsc, maker)
for ref, template, nets, target in [
    ("C32", "C17", {1: "NRST", 2: "GND"}, [-6, -17]),
    ("C33", "C29", {1: "PULSE_C", 2: "PULSE_RC"}, [-18, -16]),
    ("C34", "C29", {1: "PULSE_C", 2: "PULSE_RC"}, [-18, -14]),
    ("C35", "C17", {1: "3V3", 2: "GND"}, [-12, -16]),
    ("C36", "C17", {1: "3V3", 2: "GND"}, [20, -16]),
    ("C37", "C24", {1: "VIN_3V3", 2: "GND"}, [52, -20]),
    ("C38", "C29", {1: "INRUSH_RC", 2: "GND"}, [53, -20]),
]:
    passive(ref, template, nets, target)

changes = {
    ("U9", "21"): "LED_ENABLE",
    ("U9", "28"): "STATUS_LED_N",
    ("J1", "1"): "VIN_3V3",
    ("J1", "5"): "NRST_EXT",
    ("D17", "1"): "VIN_3V3",
    ("C29", "2"): "GND",
    ("C30", "2"): "GND",
}
for (ref, pin), net in changes.items():
    parts[ref]["nets"][pin] = net

# Copy standard lands into the self-contained project library.
for folder, name in [
    ("Package_SO", "SSOP-8_2.95x2.8mm_P0.65mm"),
    ("LED_SMD", "LED_0603_1608Metric"),
]:
    source = LIB / "footprints" / (folder + ".pretty") / (name + ".kicad_mod")
    shutil.copy2(source, ROOT / "IR_Glasses.pretty" / source.name)

# TI RPW0010A recommended land pattern, including four L-shaped corner lands.
body = """(footprint "TI_RPW0010A" (version 20260206) (generator "pcbnew")
 (layer "F.Cu") (attr smd)
 (property "Reference" "REF**" (at 0 0) (layer "F.SilkS") (hide yes)
  (effects (font (size 0.6 0.6) (thickness 0.1))))
 (property "Value" "TPS259470LRPWR" (at 0 0) (layer "F.Fab") (hide yes)
  (effects (font (size 0.6 0.6) (thickness 0.1))))
 (fp_rect (start -1 -1) (end 1 1) (stroke (width 0.05) (type solid))
  (fill no) (layer "F.Fab"))
 (fp_rect (start -1.45 -1.45) (end 1.45 1.45)
  (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
 (fp_circle (center -1.45 -1.65) (end -1.35 -1.65)
  (stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))"""
for pin, x, y, w, h in [
    (2, -0.9, -0.225, 0.6, 0.25),
    (3, -0.9, 0.225, 0.6, 0.25),
    (5, -0.25, 0, 0.3, 2.4),
    (6, 0.25, 0, 0.3, 2.4),
    (8, 0.9, 0.225, 0.6, 0.25),
    (9, 0.9, -0.225, 0.6, 0.25),
]:
    body += (
        f'(pad "{pin}" smd rect (at {x} {y}) (size {w} {h})'
        ' (layers "F.Cu" "F.Paste" "F.Mask"))'
    )
for pin, mx, my in [(1, 1, 1), (4, 1, -1), (10, -1, 1), (7, -1, -1)]:
    ax, ay = -0.725 * mx, -0.7 * my
    points = [
        (-1.2, -0.85),
        (-0.85, -0.85),
        (-0.85, -1.2),
        (-0.6, -1.2),
        (-0.6, -0.55),
        (-1.2, -0.55),
    ]
    poly = " ".join(
        f"(xy {x * mx - ax:.4f} {y * my - ay:.4f})" for x, y in points
    )
    body += (
        f'(pad "{pin}" smd custom (at {ax} {ay}) (size 0.1 0.1)'
        ' (layers "F.Cu" "F.Paste" "F.Mask")'
        " (options (clearance outline) (anchor rect))"
        f" (primitives (gr_poly (pts {poly}) (width 0) (fill yes))))"
    )
body += (
    '(model "${KIPRJMOD}/models/TI_RPW0010A.wrl"'
    " (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))"
)
write(ROOT / "IR_Glasses.pretty/TI_RPW0010A.kicad_mod", sx.loads(body))
(ROOT / "models/TI_RPW0010A.wrl").write_text(
    "#VRML V2.0 utf8\nTransform { translation 0 0 0.197 children [ Shape { "
    "appearance Appearance { material Material { diffuseColor .08 .08 .08 }}"
    " geometry Box { size .7874 .7874 .3937 } } ] }\n"
)

# Patch existing pin labels without moving any schematic graphics.
for path in ROOT.glob("*.kicad_sch"):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    title = gen.children(tree, "title_block")[0]
    gen.children(title, "rev")[0][1] = "EVT E3"
    gen.children(title, "date")[0][1] = "2026-09-08"
    for symbol in gen.children(tree, "symbol"):
        ref = next(
            p[2]
            for p in gen.children(symbol, "property")
            if p[1] == "Reference"
        )
        if ref not in parts:
            continue
        x, y, _ = gen.children(symbol, "at")[0][1:4]
        unit = gen.children(symbol, "unit")[0][1]
        name = gen.children(symbol, "lib_id")[0][1].split(":")[1]
        for pin, px, py, angle in gen.pin_data(name, unit):
            if (ref, pin) not in changes:
                continue
            pos = (x + px, y - py)

            def near(p):
                return math.dist(p, pos) < 0.0001

            wires = [
                w
                for w in gen.children(tree, "wire")
                if near(gen.children(w, "pts")[0][1][1:3])
            ]
            if wires:
                end = gen.children(wires[0], "pts")[0][2][1:3]
                label = next(
                    g
                    for g in gen.children(tree, "global_label")
                    if math.dist(gen.children(g, "at")[0][1:3], end) < 0.0001
                )
                label[1] = changes[ref, pin]
            else:
                nc = next(
                    n
                    for n in gen.children(tree, "no_connect")
                    if near(gen.children(n, "at")[0][1:3])
                )
                tree.remove(nc)
                dummy = dict(parts[ref], nets={pin: changes[ref, pin]})
                nodes = sx.loads(
                    "("
                    + gen.instance(ref, dummy, x, y, unit, "/" + gen.ROOT_ID)
                    + ")"
                )
                for n in nodes:
                    if str(n[0]) == "wire" and near(n[1][1][1:3]):
                        tree.append(n)
                        end = n[1][2][1:3]
                        tree.append(
                            next(
                                g
                                for g in nodes
                                if str(g[0]) == "global_label"
                                and math.dist(
                                    gen.children(g, "at")[0][1:3], end
                                )
                                < 0.0001
                            )
                        )
    if path.stem == "ir_glasses":
        tree.append(
            sx.loads(
                f"(sheet (at 295 246) (size 82 16)"
                f' (uuid "{gen.uid("sheet/protection")}")'
                ' (property "Sheetname" "Protection/status" (at 295 244.5 0)'
                " (effects (font (size 1.27 1.27)) (justify left bottom)))"
                ' (property "Sheetfile" "protection.kicad_sch" (at 295 263 0)'
                " (effects (font (size 1.27 1.27)) (justify left top)))"
                f' (instances (project "ir_glasses" (path "/{gen.ROOT_ID}"'
                ' (page "6")))))'
            )
        )
    write(path, tree)

embedded = []
for symbol in gen.SYMBOLS.values():
    node = copy.deepcopy(symbol)
    node[1] = "IR_Glasses:" + node[1]
    embedded.append(sx.dumps(node))
sheet_path = f"/{gen.ROOT_ID}/{gen.uid('sheet/protection')}"
schematic = (
    f'(kicad_sch (version 20250114) (generator "eeschema")'
    f' (uuid "{gen.uid("protection")}") (paper "A3")'
    ' (title_block (title "Protection and status") (date "2026-09-08")'
    ' (rev "EVT E3")) (lib_symbols ' + " ".join(embedded) + ")"
)
for index, ref in enumerate(new_refs):
    x, y = 42 + (index % 5) * 78, 50 + (index // 5) * 49
    parts[ref]["sch"] = [x, y]
    schematic += gen.instance(ref, parts[ref], x, y, 1, sheet_path)
schematic += gen.text("PB2: high = bounded LED pulse; low = force off", 25, 20)
schematic += gen.text("PA8: low = green status LED on", 25, 26)
schematic += ")"
write(ROOT / "protection.kicad_sch", sx.loads(schematic))
library = library[:3] + list(gen.SYMBOLS.values())
write(ROOT / "IR_Glasses.kicad_sym", library)

board = pcb.LoadBoard(str(ROOT / "ir_glasses.kicad_pcb"))
for net in {n for p in parts.values() for n in p["nets"].values()}:
    if not board.FindNet(net):
        board.Add(pcb.NETINFO_ITEM(board, net))
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for (ref, pin), net in changes.items():
    for pad in fps[ref].Pads():
        if pad.GetNumber() == pin:
            pad.SetNet(board.FindNet(net))
for ref in new_refs:
    part = parts[ref]
    name = part["footprint"].split(":")[1]
    fp = pcb.FootprintLoad(str(ROOT / "IR_Glasses.pretty"), name)
    fp.SetReference(ref)
    fp.SetValue(part["value"])
    fp.SetFPID(pcb.LIB_ID("IR_Glasses", name))
    fp.SetPath(pcb.KIID_PATH(sheet_path + "/" + gen.uid(ref + "/1")))
    fp.SetPosition(gen.mm(part["xy"][0] + 110, part["xy"][1] + 85))
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    for pad in fp.Pads():
        net = part["nets"].get(pad.GetNumber())
        if net:
            pad.SetNet(board.FindNet(net))
    board.Add(fp)
board.GetTitleBlock().SetRevision("EVT E3")
pcb.SaveBoard(str(ROOT / "ir_glasses.kicad_pcb"), board)
(ROOT / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
(ROOT / "new_refs.json").write_text(json.dumps(new_refs))
print("E3 source created:", len(new_refs), "new populated references")
