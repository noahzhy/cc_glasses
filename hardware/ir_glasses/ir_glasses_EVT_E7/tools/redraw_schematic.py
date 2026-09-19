"""Rebuild the A1 review schematic from the archived R2 source."""

import copy
import json
import math
import os
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import sexpdata as sx


ROOT = Path(__file__).resolve().parents[1]
NAME = ROOT.name
REVIEW = ROOT / "schematic_review"
KICAD = Path(
    os.environ.get(
        "KICAD_SYMBOL_DIR", "D:/Program Files/KiCad/10.0/share/kicad/symbols"
    )
)
LIBRARY = {}
ITEMS = []
PLACED = {}
CONNECTED = set()
COUNTER = 0


def children(tree, key):
    return [
        item
        for item in tree
        if isinstance(item, list) and item and str(item[0]) == key
    ]


def child(tree, key):
    return children(tree, key)[0]


def uid(name):
    return str(uuid5(NAMESPACE_URL, f"cc-glasses/schematic-review/{name}"))


def add(text):
    global COUNTER
    COUNTER += 1
    item = sx.loads(text)
    item.append([sx.Symbol("uuid"), uid(f"item/{COUNTER}")])
    ITEMS.append(item)
    return item


def snap(value):
    return round(round(value / 1.27) * 1.27, 4)


def point(x, y):
    return snap(x), snap(y)


def wire(*points):
    for a, b in zip(points, points[1:]):
        a, b = point(*a), point(*b)
        if a[0] != b[0] and a[1] != b[1]:
            wire(a, (b[0], a[1]), b)
            continue
        if a != b:
            add(f"""(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]}))
                (stroke (width 0) (type default)))""")


def label(net, pos, angle=0):
    x, y = point(*pos)
    justify = "right" if angle == 180 else "left"
    add(f"""(label {json.dumps(net)} (at {x} {y} {angle})
        (effects (font (size 1.27 1.27)) (justify {justify} bottom)))""")


def note(text, x, y, size=1.52):
    add(f"""(text {json.dumps(text)} (at {snap(x)} {snap(y)} 0)
        (effects (font (size {size} {size})) (justify left)))""")


def section(text, x, y, width):
    note(text, x, y, 2.03)
    add(f"""(polyline (pts (xy {x} {y + 4}) (xy {x + width} {y + 4}))
        (stroke (width 0.254) (type default)) (fill (type none)))""")


def standard(file, name, target):
    tree = sx.loads((KICAD / f"{file}.kicad_sym").read_text())
    symbols = {s[1]: s for s in children(tree, "symbol")}

    def resolve(name):
        symbol = copy.deepcopy(symbols[name])
        parent = children(symbol, "extends")
        if parent:
            base = resolve(parent[0][1])
            symbol.remove(parent[0])
            symbol.extend(copy.deepcopy(children(base, "symbol")))
            for item in base[2:]:
                if not children(symbol, str(item[0])):
                    symbol.append(copy.deepcopy(item))
        return symbol

    symbol = resolve(name)
    symbol[1] = target
    for unit in children(symbol, "symbol"):
        unit[1] = target + "_" + "_".join(unit[1].split("_")[-2:])
    symbol[:] = [
        x
        for x in symbol
        if not (
            isinstance(x, list)
            and str(x[0]) == "property"
            and x[1] == "ki_fp_filters"
        )
    ]
    LIBRARY[target] = symbol
    return symbol


with zipfile.ZipFile(REVIEW / "baseline_R2.zip") as archive:
    original = {}
    original_units = {}
    old_lib = {}
    for filename in archive.namelist():
        if not filename.endswith(".kicad_sch"):
            continue
        tree = sx.loads(archive.read(filename).decode("utf-8"))
        if filename == "ir_glasses_EVT_E6_F302.kicad_sch":
            ROOT_ID = child(tree, "uuid")[1]
        for symbol in children(child(tree, "lib_symbols"), "symbol"):
            old_lib[symbol[1]] = symbol
        for symbol in children(tree, "symbol"):
            props = {p[1]: p[2] for p in children(symbol, "property")}
            if not props["Reference"].startswith("#"):
                original.setdefault(props["Reference"], symbol)
                original_units[
                    (props["Reference"], child(symbol, "unit")[1])
                ] = symbol

for ref in ["C24", "C45", "TP5", "TP6"]:
    del original[ref]

netlist = ET.parse(REVIEW / "before.xml").getroot()
NETS = {
    (node.get("ref"), node.get("pin")): net.get("name")
    for net in netlist.findall("nets/net")
    for node in net.findall("node")
}
for ref, number in [("U9", "9"), ("C11", "1"), ("C47", "1")]:
    NETS[(ref, number)] = "3V3"

standard("Device", "R", "R")
standard("Device", "C", "C")
standard("Device", "LED", "LED")
standard("Device", "D_Photo", "PD")
standard("Device", "D_Zener", "ESD_UNI")
standard("Amplifier_Operational", "TLV9064", "TLV9064")
standard("Amplifier_Operational", "TLV9062", "TLV9062")
standard("Amplifier_Operational", "TLV9061xDBV", "TLV9061")
for unit in children(LIBRARY["PD"], "symbol"):
    for pin in children(unit, "pin"):
        number = child(pin, "number")
        number[1] = "2" if number[1] == "1" else "1"
standard("power", "GND", "GND")
standard("power", "PWR_FLAG", "PWR_FLAG")
for net in ["3V3", "3V3_A", "VIN_HOST", "VIN_3V3", "VREF_1V65"]:
    symbol = standard("power", "VCC", net)
    for prop in children(symbol, "property"):
        if prop[1] == "Value":
            prop[2] = net


def make_ic(ref, groups, width=15.24, spacing=2.54):
    """Arrange verified pin numbers by function without changing their nets."""
    old = old_lib[child(original[ref], "lib_id")[1]]
    pins = {
        child(p, "number")[1]: copy.deepcopy(p)
        for u in children(old, "symbol")
        for p in children(u, "pin")
    }
    name = ref + "_" + child(original[ref], "lib_id")[1].split(":")[-1]
    length = max(len(groups.get("left", [])), len(groups.get("right", [])))
    height = snap(max(7.62, (length + 1) * spacing / 2))
    symbol = sx.loads(f'''(symbol "{name}" (pin_names (offset 0.762))
        (in_bom yes) (on_board yes)
        (property "Reference" "U" (at 0 {height + 5.08} 0)
            (effects (font (size 1.27 1.27))))
        (property "Value" "{name}" (at 0 {height + 2.54} 0)
            (effects (font (size 1.27 1.27))))
        (symbol "{name}_0_1"
            (rectangle (start {-width} {height}) (end {width} {-height})
                (stroke (width 0.254) (type default))
                (fill (type background)))) (symbol "{name}_1_1"))''')
    target = children(symbol, "symbol")[-1]
    for side, numbers in groups.items():
        for i, number in enumerate(numbers):
            p = pins.pop(str(number))
            d = round(snap((len(numbers) - 1) * spacing / 2) - i * spacing, 4)
            if side == "left":
                at = [-width - 2.54, d, 0]
            elif side == "right":
                at = [width + 2.54, d, 180]
            elif side == "top":
                at = [-d, height + 2.54, 270]
            else:
                at = [-d, -height - 2.54, 90]
            child(p, "at")[1:] = at
            child(p, "length")[1] = 2.54
            for key in ["name", "number"]:
                child(child(child(p, key), "effects"), "font")[1] = [
                    sx.Symbol("size"),
                    1.016,
                    1.016,
                ]
            if ref == "U9" and str(number) in {"35", "47"}:
                p[1] = sx.Symbol("power_in")
            if ref == "U9" and str(number) == "7":
                p[1] = sx.Symbol("bidirectional")
            target.append(p)
    assert not pins, (ref, pins)
    LIBRARY[name] = symbol
    return name, height


def place(ref, name, x, y, unit=1, angle=0, fields=None):
    x, y = point(x, y)
    props = (
        {p[1]: p[2] for p in children(original[ref], "property")}
        if ref in original
        else {"Reference": ref, "Value": name}
    )
    old_unit = original_units.get((ref, unit))
    symbol_id = (
        child(old_unit, "uuid")[1] if old_unit else uid(f"{ref}/{unit}")
    )
    symbol = sx.loads(f'''(symbol (lib_id "Review:{name}")
        (at {x} {y} {angle}) (unit {unit}) (in_bom yes) (on_board yes)
        (dnp no) (uuid "{symbol_id}")
        (instances (project "{NAME}" (path "/{ROOT_ID}"
            (reference "{ref}") (unit {unit})))))''')
    if ref in original:
        for key in ("in_bom", "on_board", "dnp"):
            child(symbol, key)[1] = child(original[ref], key)[1]
    else:
        child(symbol, "in_bom")[1] = sx.Symbol("no")
        child(symbol, "on_board")[1] = sx.Symbol("no")
    for key, value in props.items():
        visible = key in {"Reference", "Value"} and not ref.startswith("#")
        px, py = (x + 5.08, y + (-1.27 if key == "Reference" else 1.27))
        if fields and key in fields:
            px, py = fields[key]
        prop = sx.loads(f"""(property {json.dumps(key)} {json.dumps(value)}
            (at {snap(px)} {snap(py)} {angle % 180})
            (effects (font (size 1.27 1.27))
            {"(justify left)" if angle == 0 else ""}
            {"" if visible else "hide"}))""")
        symbol.append(prop)
    pins = {}
    for u in children(LIBRARY[name], "symbol"):
        if int(u[1].split("_")[-2]) not in (0, unit):
            continue
        for pin in children(u, "pin"):
            num = child(pin, "number")[1]
            px, py, pa = child(pin, "at")[1:]
            a = math.radians(angle)
            pos = point(
                x + px * math.cos(a) - py * math.sin(a),
                y - px * math.sin(a) - py * math.cos(a),
            )
            pins[num] = (pos, (pa + angle) % 360)
            symbol.append(
                sx.loads(f'(pin "{num}" (uuid "{uid(f"{ref}/{num}")}"))')
            )
    ITEMS.append(symbol)
    PLACED.setdefault(ref, {}).update(pins)
    return pins


def pin(ref, number):
    CONNECTED.add((ref, str(number)))
    return PLACED[ref][str(number)][0]


def power(net, pos):
    ref = f"#PWR{len(ITEMS):04}"
    place(ref, net, *pos)
    if net != "GND":
        x, y = point(*pos)
        prop = next(
            p for p in children(ITEMS[-1], "property") if p[1] == "Value"
        )
        child(prop, "at")[1:3] = [x, y - 3.81]
        prop[-1] = sx.loads("(effects (font (size 1.27 1.27)))")


def connect_power(ref, number, net, length=5.08):
    a = pin(ref, number)
    b = point(a[0], a[1] + (length if net == "GND" else -length))
    wire(a, b)
    power(net, b)


def stub(ref, number, length=7.62):
    a = pin(ref, number)
    net = NETS[(ref, str(number))]
    if net.startswith("unconnected-"):
        add(f"(no_connect (at {a[0]} {a[1]}))")
        return
    direction = PLACED[ref][str(number)][1]
    dx, dy = {
        0: (-length, 0),
        180: (length, 0),
        90: (0, length),
        270: (0, -length),
    }[direction]
    b = point(a[0] + dx, a[1] + dy)
    wire(a, b)
    if net in {"3V3", "3V3_A", "GND", "VIN_HOST", "VIN_3V3"}:
        power(net, b)
    else:
        label(net, b, 180 if direction == 0 else 0)


def capacitor(ref, x, y, net=None):
    place(ref, "C", x, y)
    a, b = pin(ref, "1"), pin(ref, "2")
    top = point(a[0], a[1] - 3.81)
    wire(top, a)
    net = net or NETS[(ref, "1")]
    if net in LIBRARY:
        power(net, top)
    else:
        label(net, top)
    wire(b, (b[0], b[1] + 2.54))
    power("GND", (b[0], b[1] + 2.54))


def cap_bank(refs, x, y, spacing=20.32):
    for i, ref in enumerate(refs):
        capacitor(ref, x + i * spacing, y)


def resistor(ref, x, y, angle=0):
    fields = None
    if angle:
        fields = {
            "Reference": (x - 2.54, y - 5.08),
            "Value": (x - 2.54, y - 2.54),
        }
    place(ref, "R", x, y, angle=angle, fields=fields)


def ic(ref, groups, x, y, width=15.24, spacing=2.54):
    name, height = make_ic(ref, groups, width, spacing)
    place(
        ref,
        name,
        x,
        y,
        fields={
            "Reference": (x - width, y - height - 7.62),
            "Value": (x - width, y - height - 5.08),
        },
    )


def link(ref1, n1, ref2, n2, via=()):
    wire(pin(ref1, n1), *via, pin(ref2, n2))


def finish_pins():
    for ref, pins in list(PLACED.items()):
        if ref.startswith("#"):
            continue
        for direction in (90, 270):
            nets = {}
            for num, (pos, side) in pins.items():
                net = NETS[(ref, num)]
                if side == direction and (ref, num) not in CONNECTED:
                    if net in {"3V3", "3V3_A", "GND", "VIN_3V3"}:
                        nets.setdefault(net, []).append(num)
            for net, nums in nets.items():
                if len(nums) < 2:
                    continue
                pts = [pin(ref, n) for n in nums]
                y = pts[0][1] + (5.08 if direction == 90 else -5.08)
                xs = sorted(p[0] for p in pts)
                for p in pts:
                    wire(p, (p[0], y))
                wire((xs[0], y), (xs[-1], y))
                end = (xs[0], y + (2.54 if direction == 90 else -2.54))
                wire((xs[0], y), end)
                power(net, end)
        for num in pins:
            if (ref, num) not in CONNECTED:
                length = (
                    3.81 if ref in {f"D{i}" for i in range(1, 17)} else 7.62
                )
                stub(ref, num, length)


def redraw():
    note("IR GLASSES / EVT E7 / SCHEMATIC REVIEW", 17, 16, 3.05)
    note(
        "Single-sheet electrical source | EVT E7 with carrier",
        17,
        23,
        1.78,
    )
    section("01  HOST INPUT / CURRENT LIMIT / OVERVOLTAGE", 18, 33, 265)
    ic("U18", {"left": [6, 4], "right": [1, 3], "bottom": [5, 7, 2]}, 65, 61)
    ic(
        "U14",
        {"left": [5, 1, 2], "right": [6, 3, 4], "bottom": [7, 8, 9, 10]},
        205,
        61,
    )
    link(
        "U18",
        6,
        "U18",
        4,
        [(43.18, pin("U18", 6)[1]), (43.18, pin("U18", 4)[1])],
    )
    power("VIN_HOST", (43.18, pin("U18", 6)[1]))
    link("U18", 1, "U14", 5)
    label("VIN_3V3", (115.57, pin("U18", 1)[1]))
    resistor("R29", 72.39, 87.63)
    link("U18", 2, "R29", 1, [(pin("U18", 2)[0], 80.01), (72.39, 80.01)])
    connect_power("R29", 2, "GND")
    label("INPUT_ILIM", (72.39, 80.01))
    ic(
        "U19",
        {"left": [3], "right": [6, 1], "top": [4, 5], "bottom": [2]},
        134.62,
        111.76,
    )
    resistor("R18", 99.06, 111.76, 90)
    resistor("R19", 111.76, 130.81)
    link("R18", 2, "U19", 3)
    link("R18", 2, "R19", 1, [(111.76, pin("R18", 2)[1])])
    connect_power("R19", 2, "GND")
    label("OV_SENSE", (111.76, 123.19))
    resistor("R28", 160.02, 93.98)
    link("R28", 2, "U19", 6, [(160.02, pin("U19", 6)[1])])
    wire(
        pin("U19", 6),
        (172.72, pin("U19", 6)[1]),
        (172.72, pin("U14", 1)[1]),
        pin("U14", 1),
    )
    label("INPUT_OK", (172.72, 87.63))
    resistor("R20", 214.63, 96.52)
    link("U14", 9, "R20", 1, [(pin("U14", 9)[0], 83.82), (214.63, 83.82)])
    connect_power("R20", 2, "GND")
    label("ILIM_SET", (214.63, 83.82))
    capacitor("C38", 190.5, 96.52, "INRUSH_RC")
    wire(
        pin("U14", 7),
        (pin("U14", 7)[0], 82.55),
        (190.5, 82.55),
        (190.5, pin("C38", 1)[1] - 3.81),
    )
    cap_bank(["C48", "C49", "C37"], 27.94, 124.46)
    old = copy.deepcopy(old_lib[child(original["D17"], "lib_id")[1]])
    old[1] = "TVS"
    for prop in children(old, "property"):
        if prop[1] == "ki_fp_filters":
            prop[2] = "sod-323 sod-523"
    for unit in children(old, "symbol"):
        unit[1] = "TVS_" + "_".join(unit[1].split("_")[-2:])
    LIBRARY["TVS"] = old
    place(
        "D17",
        "TVS",
        250.19,
        93.98,
        angle=270,
        fields={"Reference": (264.16, 92.71), "Value": (264.16, 96.52)},
    )
    note("External regulated 3.3 V; no on-board regulator", 20, 146)
    note("R29 sets input limit; U19 drives U14 EN", 20, 151)

    section("02  ANALOG SUPPLY / 1.65 V BIAS", 18, 165, 265)
    old = copy.deepcopy(old_lib[child(original["FB1"], "lib_id")[1]])
    old[1] = "FB"
    for unit in children(old, "symbol"):
        unit[1] = "FB_" + "_".join(unit[1].split("_")[-2:])
    LIBRARY["FB"] = old
    place(
        "FB1",
        "FB",
        43.18,
        191.77,
        angle=90,
        fields={"Reference": (43.18, 180.34), "Value": (43.18, 184.15)},
    )
    cap_bank(["C28", "C27"], 22.86, 224.79, 30.48)
    capacitor("C15", 77.47, 224.79)
    resistor("R2", 100.33, 194.31)
    resistor("R3", 100.33, 224.79)
    link("R2", 2, "R3", 1)
    place(
        "U6",
        "TLV9061",
        148.59,
        209.55,
        fields={"Reference": (158.75, 199.39), "Value": (158.75, 203.2)},
    )
    link("R2", 2, "U6", 3, [(100.33, pin("U6", 3)[1])])
    capacitor("C1", 120.65, 224.79, "VREF_DIV")
    wire(
        (100.33, pin("U6", 3)[1]),
        (120.65, pin("U6", 3)[1]),
        (120.65, pin("C1", 1)[1] - 3.81),
    )
    wire(
        pin("U6", 4),
        (135.89, pin("U6", 4)[1]),
        (135.89, 240.03),
        (163.83, 240.03),
        (163.83, pin("U6", 1)[1]),
        pin("U6", 1),
    )
    resistor("R13", 181.61, 209.55, 90)
    link("U6", 1, "R13", 1)
    label("VREF_BUF", (163.83, 209.55))
    wire(pin("R13", 2), (207.01, 209.55))
    capacitor("C31", 207.01, 224.79, "VREF_1V65")
    wire((207.01, 209.55), (207.01, pin("C31", 1)[1] - 3.81))
    cap_bank(["C7", "C23"], 241.3, 223.52)
    note("Divider -> U6 follower -> 47R isolation -> bias rail", 20, 255)

    section("03  LED WINDOW / CONSTANT-CURRENT DRIVER", 300, 33, 222)
    ic(
        "U12",
        {"left": [3], "right": [5, 6, 7], "top": [2, 8], "bottom": [1, 4]},
        335.28,
        64.77,
    )
    ic(
        "U13",
        {"left": [2, 1], "right": [4], "top": [5], "bottom": [3]},
        392.43,
        63.5,
        10.16,
    )
    link("U12", 5, "U13", 2)
    label("LED_WINDOW", (358.14, pin("U12", 5)[1]))
    resistor("R15", 369.57, 102.87)
    for ref, y in [("C33", 123.19), ("C34", 135.89)]:
        place(
            ref,
            "C",
            354.33,
            y,
            angle=90,
            fields={
                "Reference": (350.52, y - 5.08),
                "Value": (350.52, y - 2.54),
            },
        )
    for ref in ["C33", "C34"]:
        wire(pin(ref, 2), (363.22, pin(ref, 2)[1]))
        wire(pin(ref, 1), (340.36, pin(ref, 1)[1]))
    wire(
        pin("U12", 6),
        (355.6, pin("U12", 6)[1]),
        (355.6, 86.36),
        (340.36, 86.36),
        (340.36, 135.89),
    )
    wire(pin("U12", 7), (363.22, pin("U12", 7)[1]), (363.22, 135.89))
    wire(pin("R15", 2), (369.57, 113.03), (363.22, 113.03))
    label("PULSE_C", (340.36, 123.19))
    label("PULSE_RC", (363.22, 135.89))
    resistor("R16", 309.88, 102.87)
    wire(pin("U12", 3), (309.88, pin("U12", 3)[1]), pin("R16", 1))
    label("LED_ENABLE", (309.88, 87.63), 180)
    connect_power("R16", 2, "GND")
    ic(
        "U1",
        {
            "left": [24, 23, 1, 18, 20, 19],
            "right": list(range(2, 18)),
            "top": [21],
            "bottom": [22, 25],
        },
        480.06,
        128.27,
        15.24,
        3.81,
    )
    resistor("R10", 425.45, 90.17)
    wire(
        pin("U13", 4),
        (415.29, pin("U13", 4)[1]),
        (415.29, pin("U1", 18)[1]),
        pin("U1", 18),
    )
    wire(pin("R10", 2), (425.45, pin("U1", 18)[1]))
    label("LED_BLANK", (425.45, pin("U1", 18)[1]))
    resistor("R1", 434.34, 151.13)
    wire(pin("U1", 20), (434.34, pin("U1", 20)[1]), pin("R1", 1))
    label("IREF", (434.34, pin("U1", 20)[1]))
    connect_power("R1", 2, "GND")
    cap_bank(["C35", "C36", "C2", "C18", "C25"], 312.42, 177.8, 43.18)
    note("R1 = 2.67k: about 19.8 mA per enabled channel", 302, 203)
    note("CLR rising edge triggers; low CLR terminates the pulse", 302, 210)
    note("C33 || C34 = 2 nF; verify pulse window on hardware", 302, 217)
    for i in range(1, 17):
        x = 310 + ((i - 1) % 8) * 27.94
        y = 235 + ((i - 1) // 8) * 25.4
        # Everlight IR11 uses pad 1 as anode, unlike the generic LED.
        if "IR_LED" not in LIBRARY:
            ir_led = copy.deepcopy(LIBRARY["LED"])
            ir_led[1] = "IR_LED"
            for u in children(ir_led, "symbol"):
                u[1] = u[1].replace("LED_", "IR_LED_")
                for p in children(u, "pin"):
                    n = child(p, "number")
                    n[1] = "2" if n[1] == "1" else "1"
            LIBRARY["IR_LED"] = ir_led
        place(
            f"D{i}",
            "IR_LED",
            x,
            y,
            angle=90,
            fields={"Reference": (x + 4, y), "Value": (x + 4, y + 2.54)},
        )
        # The common part number is printed once above the array.
        child(children(ITEMS[-1], "property")[1], "effects").append(
            sx.Symbol("hide")
        )
    note("D1-D16: IR11-21C/TR8; optical positions unchanged", 302, 283)

    section("04  MCU / UART / SWD / IMU", 540, 33, 280)
    ic(
        "U9",
        {
            "left": [
                7,
                44,
                10,
                14,
                15,
                11,
                46,
                16,
                17,
                27,
                18,
                19,
                21,
                22,
                28,
                20,
                42,
                43,
                29,
                30,
                31,
                34,
                37,
            ],
            "right": [
                2,
                3,
                4,
                5,
                6,
                12,
                13,
                25,
                26,
                32,
                33,
                38,
                39,
                40,
                41,
                45,
            ],
            "top": [1, 24, 36, 48, 9],
            "bottom": [8, 23, 35, 47],
        },
        594.36,
        113.03,
        17.78,
        3.81,
    )
    cap_bank(["C10", "C12", "C13", "C14", "C19"], 546.1, 181.61)
    cap_bank(["C11", "C47", "C40"], 546.1, 207.01)
    note("VDDA = VDD = 3V3; C11 10n + C47 1u at pin 9", 542, 227)
    resistor("R4", 549.91, 248.92)
    resistor("R5", 577.85, 248.92)
    capacitor("C32", 607.06, 248.92, "NRST")
    resistor("R14", 637.54, 242.57, 90)
    for ref, x in [("D18", 622.3), ("D19", 660.4)]:
        place(ref, "ESD_UNI", x, 266.7, angle=270)
        value = next(
            p for p in children(ITEMS[-1], "property") if p[1] == "Value"
        )
        child(value, "effects").append(sx.Symbol("hide"))
    note("D18/D19: PESD3V3U1UB, 1=K / 2=A", 607, 290, 1.27)
    resistor("R17", 556.26, 275.59, 90)
    place(
        "D20",
        "LED",
        589.28,
        275.59,
        angle=180,
        fields={"Reference": (589.28, 267.97), "Value": (589.28, 270.51)},
    )
    link("R17", 2, "D20", 2)
    label("STATUS_A", (568.96, 275.59))

    ic("J1", {"left": [1, 3, 4, 5], "bottom": [2]}, 710, 57, 8.89)
    ic(
        "J2",
        {
            "left": [2, 4, 10],
            "top": [1],
            "bottom": [3],
            "right": [5, 6, 7, 8, 9],
        },
        781,
        64.77,
        8.89,
    )
    resistor("R8", 708.66, 87.63, 90)
    resistor("R9", 756.92, 87.63, 90)
    ic("U11", {"left": [1], "right": [2], "bottom": [3]}, 733.0, 113.03, 12.7)
    ic(
        "U10",
        {
            "left": [13, 14, 12],
            "right": [4, 9, 10, 11],
            "top": [5, 8],
            "bottom": [1, 2, 3, 6, 7],
        },
        744.22,
        179.07,
        13.97,
        3.81,
    )
    resistor("R6", 685.8, 161.29)
    resistor("R7", 706.12, 161.29)
    wire(pin("R6", 2), (685.8, pin("U10", 13)[1]), pin("U10", 13))
    wire(pin("R7", 2), (706.12, pin("U10", 14)[1]), pin("U10", 14))
    label("I2C_SCL", (685.8, pin("U10", 13)[1]), 180)
    label("I2C_SDA", (706.12, pin("U10", 14)[1]), 180)
    cap_bank(["C16", "C17", "C20", "C26"], 680.72, 213.36, 34.29)
    note("I2C address 0x6A; CS high, SA0 low", 680, 235)
    for i in [1, 2, 3, 4, 7, 8, 9, 10, 11, 12]:
        ref = f"TP{i}"
        if "TP" not in LIBRARY:
            a = copy.deepcopy(old_lib[child(original[ref], "lib_id")[1]])
            a[1] = "TP"
            for u in children(a, "symbol"):
                u[1] = "TP_" + "_".join(u[1].split("_")[-2:])
            LIBRARY["TP"] = a
        x, y = 680.72 + ((i - 1) % 4) * 34.29, 250.19 + ((i - 1) // 4) * 17.78
        place(ref, "TP", x, y)

    section("05  LEFT PHOTODIODES / TIA 1-8", 18, 300, 802)
    section("06  RIGHT PHOTODIODES / TIA 9-16", 18, 381, 802)
    for i in range(1, 17):
        x, y = point(
            65 + ((i - 1) % 8) * 99.06, 326.39 + ((i - 1) // 8) * 81.28
        )
        ref = f"U{2 + (i - 1) // 4}"
        unit = 1 + (i - 1) % 4
        nums = [(1, 2, 3), (7, 6, 5), (8, 9, 10), (14, 13, 12)]
        out, minus, plus = nums[unit - 1]
        place(
            ref,
            "TLV9064",
            x,
            y,
            unit,
            fields={
                "Reference": (x - 2.54, y - 11.43),
                "Value": (x + 2.54, y - 6.35),
            },
        )
        place(
            f"PD{i}",
            "PD",
            x - 30.48,
            y + 7.62,
            angle=270,
            fields={
                "Reference": (x - 30.48, y - 10.16),
                "Value": (x - 30.48, y - 6.35),
            },
        )
        link(f"PD{i}", 2, ref, minus)
        connect_power(f"PD{i}", 1, "GND", 2.54)
        p = pin(ref, plus)
        wire(p, (x - 12.7, p[1]), (x - 12.7, y - 12.7))
        power("VREF_1V65", (x - 12.7, y - 12.7))
        for component, dy, lib in [
            (f"RF{i}", 17.78, "R"),
            (f"CF{i}", 27.94, "C"),
        ]:
            place(
                component,
                lib,
                x,
                y + dy,
                angle=270,
                fields={
                    "Reference": (x - 2.54, y + dy - 5.08),
                    "Value": (x - 2.54, y + dy - 2.54),
                },
            )
            wire(pin(component, 2), (x - 17.78, y + dy))
            wire(pin(component, 1), (x + 17.78, y + dy))
        wire((x - 17.78, pin(ref, minus)[1]), (x - 17.78, y + 27.94))
        wire(pin(ref, out), (x + 17.78, y), (x + 17.78, y + 27.94))
        wire((x + 17.78, y), (x + 30.48, y))
        label(f"TIA{i}", (x + 30.48, y))
        label(f"PD_IN{i}", (x - 17.78, y + 27.94), 180)

    section("07  ODD / EVEN MUX -> DUAL BUFFER -> ADC", 18, 465, 802)
    for idx, (mux, channel, x) in enumerate(
        [("U7", "A", 58.42), ("U8", "B", 459.74)]
    ):
        y = 508.0
        ic(
            mux,
            {
                "left": [13, 14, 15, 12, 1, 5, 2, 4],
                "right": [3, 11, 10, 9, 6, 7],
                "top": [16],
                "bottom": [8],
            },
            x,
            y,
            13.97,
            3.81,
        )
        bx = x + 93.98
        by = pin(mux, 3)[1] + 2.54
        place(
            "U16",
            "TLV9062",
            bx,
            by,
            idx + 1,
            fields={"Reference": (bx, by - 10.16), "Value": (bx, by - 6.35)},
        )
        out, minus, plus = [(1, 2, 3), (7, 6, 5)][idx]
        link(mux, 3, "U16", plus)
        label(f"MUX_{channel}", (bx - 40.64, pin(mux, 3)[1]))
        wire(
            pin("U16", minus),
            (bx - 12.7, by + 2.54),
            (bx - 12.7, by + 17.78),
            (bx + 15.24, by + 17.78),
            (bx + 15.24, by),
            pin("U16", out),
        )
        r, c = f"R{11 + idx}", f"C{29 + idx}"
        resistor(r, bx + 33.02, by, 90)
        link("U16", out, r, 1)
        label(f"DRIVE_{channel}", (bx + 15.24, by + 17.78))
        capacitor(c, bx + 55.88, by + 17.78, f"ADC_{channel}")
        wire(pin(r, 2), (bx + 55.88, by), (bx + 55.88, by + 10.16))
        wire((bx + 55.88, by), (bx + 81.28, by))
        label(f"ADC_{channel}", (bx + 81.28, by))
        cap_bank([f"C{8 + idx}", f"C{21 + idx}"], x + 111.76, 551.18)
    resistor("R27", 102.87, 550, 90)

    # Package power units sit next to their dedicated bypass capacitors.
    for ref, x, y, caps, symbol, unit in [
        ("U2", 294.64, 493.0, ["C3"], "TLV9064", 5),
        ("U3", 354.33, 493.0, ["C4"], "TLV9064", 5),
        ("U4", 294.64, 544.83, ["C5"], "TLV9064", 5),
        ("U5", 354.33, 544.83, ["C6"], "TLV9064", 5),
        ("U16", 716.28, 511.81, ["C44", "C46"], "TLV9062", 3),
    ]:
        place(
            ref,
            symbol,
            x,
            y,
            unit,
            fields={"Reference": (x + 2.54, y - 2.54), "Value": (x + 2.54, y)},
        )
        cap_bank(caps, x + 27.94, y)
    note(
        "100R / 330pF ADC charge reservoir; feedback before series R", 433, 530
    )
    finish_pins()
    # Explicit flags identify externally supplied and passively filtered rails.
    for net, x in [
        ("VIN_HOST", 20.32),
        ("GND", 48.26),
        ("3V3_A", 76.2),
        ("VREF_1V65", 111.76),
    ]:
        place(f"#FLG{int(x)}", "PWR_FLAG", x, 572.77)
        power(net, (x, 572.77))
    note(
        "Review only - no new fabrication release. See review/report.md",
        166,
        574,
        1.52,
    )


def split_wires():
    """Split T connections so KiCad sees the intended junctions."""
    wires = children(ITEMS, "wire")
    endpoints = set()
    for w in wires:
        endpoints.update(tuple(p[1:]) for p in child(w, "pts")[1:])
    for item in ITEMS:
        if str(item[0]) in {"label", "symbol", "no_connect"}:
            if str(item[0]) != "symbol":
                endpoints.add(tuple(child(item, "at")[1:3]))
    for pins in PLACED.values():
        endpoints.update(pos for pos, _ in pins.values())
    segments = set()
    for w in wires:
        a, b = [tuple(p[1:]) for p in child(w, "pts")[1:]]
        assert a[0] == b[0] or a[1] == b[1], (a, b)
        pts = [
            p
            for p in endpoints
            if min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
        ]
        pts.sort()
        segments.update(zip(pts, pts[1:]))
        ITEMS.remove(w)
    counts = {}
    for a, b in sorted(segments):
        wire(a, b)
        for p in (a, b):
            counts[p] = counts.get(p, 0) + 1
    for (x, y), count in counts.items():
        if count >= 3:
            add(f"""(junction (at {x} {y}) (diameter 0.635)
                (color 0 0 0 0))""")


def write_outputs():
    library = sx.loads("""(kicad_symbol_lib (version 20250114)
        (generator "kicad_symbol_editor"))""")
    library.extend(LIBRARY.values())
    (ROOT / "libraries/Review.kicad_sym").write_text(
        sx.dumps(library) + "\n", encoding="utf-8"
    )
    tree = sx.loads(f'''(kicad_sch (version 20250114) (generator "eeschema")
        (uuid "{ROOT_ID}") (paper "A1")
        (title_block (title "IR Glasses - single-sheet electrical review")
            (date "2026-09-19") (rev "E7 REVIEW")
            (company "cc_glasses")
            (comment 1 "EVT E7 - single carrier PCB - design review"))
        (lib_symbols))''')
    for name, symbol in LIBRARY.items():
        embedded = copy.deepcopy(symbol)
        embedded[1] = "Review:" + name
        child(tree, "lib_symbols").append(embedded)
    tree.extend(ITEMS)
    tree.append(sx.loads("(embedded_fonts no)"))
    (ROOT / f"{NAME}.kicad_sch").write_text(
        sx.dumps(tree) + "\n", encoding="utf-8"
    )
    table = sx.loads((ROOT / "sym-lib-table").read_text())
    table[:] = [
        x
        for x in table
        if not (
            isinstance(x, list)
            and str(x[0]) == "lib"
            and child(x, "name")[1] == "Review"
        )
    ]
    table.append(
        sx.loads("""(lib (name "Review") (type "KiCad")
        (uri "${KIPRJMOD}/libraries/Review.kicad_sym") (options "")
        (descr "Review symbols with verified package pin numbers"))""")
    )
    (ROOT / "sym-lib-table").write_text(sx.dumps(table) + "\n")
    missing = set(original) - set(PLACED)
    assert not missing, missing
    print(f"Placed {len(original)} components on one A1 sheet")


if __name__ == "__main__":
    redraw()
    split_wires()
    write_outputs()
