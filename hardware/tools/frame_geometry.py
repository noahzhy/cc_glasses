"""Place a correctly oriented frame with tangential optical pairs."""

import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses")
target = root / "EVT_C"
target.mkdir(exist_ok=True)
parts = json.loads((root / "EVT_A/parts.json").read_text())
old = json.loads(Path("hardware/tools/geometry.json").read_text())
holes = [Polygon([(x, -y) for x, y in coords]) for coords in old["holes"]]
for part in parts.values():
    part["side"] = "back"
for index in range(1, 9):
    ring = holes[1].buffer(2.4, quad_segs=16).exterior
    x, y = parts[f"PD{index}"]["xy"]
    center = ring.project(Point(x, -y))
    for prefix, offset in [("D", -2.5), ("PD", 2.5)]:
        point = ring.interpolate((center + offset) % ring.length)
        a = ring.interpolate((center - 0.1) % ring.length)
        b = ring.interpolate((center + 0.1) % ring.length)
        angle = (
            round(-math.degrees(math.atan2(b.y - a.y, b.x - a.x)) / 45) * 45
        )
        for number, sign in [(index, 1), (index + 8, -1)]:
            part = parts[f"{prefix}{number}"]
            part["xy"] = [round(sign * point.x, 3), round(point.y, 3)]
            part["angle"] = sign * angle
            part["side"] = "front"
positions = {
    "U9": (0, -20),
    "U1": (10, -21),
    "U10": (28, -23),
    "U6": (-23, -23),
    "U7": (-15, -22),
    "U8": (20, -23),
    "J1": (54, -23),
    "J2": (-53, -23),
    "U11": (45, -25),
    "D17": (45, -21),
    "FB1": (-23, -18.5),
    "NT1": (-19, -19),
    "R1": (10, -17),
    "R2": (-26, -25.5),
    "R3": (-26, -20.5),
    "R4": (-7, -23),
    "R5": (6, -25),
    "R6": (26, -26.5),
    "R7": (29, -26.5),
    "R8": (45, -27),
    "R9": (45, -18.8),
    "R10": (14, -21),
    "R11": (-8, -17),
    "R12": (6, -16),
    "R13": (-23, -26),
    "C1": (-26, -23),
    "C2": (9, -25),
    "C7": (-20, -26),
    "C8": (-15, -26),
    "C9": (20, -27),
    "C10": (-6, -20),
    "C11": (-6, -18.5),
    "C12": (31, -23),
    "C13": (28, -20.5),
    "C14": (49, -26.5),
    "C15": (-20, -23.5),
    "C16": (13, -25),
    "C17": (5, -20),
    "C18": (0, -26.5),
    "C19": (-4, -26.5),
    "C20": (32, -26.5),
    "C21": (-20, -21.5),
    "C22": (-46, -23),
    "C23": (46, -23),
    "C24": (48, -20),
    "C25": (50, -27),
    "C26": (10, -14.5),
    "C27": (-27, -18.5),
    "C28": (8, -21),
    "C29": (-8, -15),
    "C30": (6, -14),
    "C31": (-23, -20.5),
}
for ref, xy in positions.items():
    parts[ref]["xy"] = list(xy)
    parts[ref]["angle"] = 90 if ref in {"U7", "U8"} else 0
parts["C28"]["side"] = "front"
for chip, first, cx, cy, cap in [
    ("U2", 1, -38, -23.3, "C3"),
    ("U3", 5, -38, 24.2, "C4"),
    ("U4", 9, 38, -23.3, "C5"),
    ("U5", 13, 38, 24.2, "C6"),
]:
    parts[chip]["xy"] = [cx, cy]
    parts[chip]["value"] = "TLV9064IPWR"
    parts[chip]["footprint"] = "IR_Glasses:TSSOP-14_4.4x5mm_P0.65mm"
    parts[chip]["angle"] = 180 if cx < 0 else 0
    parts[cap]["xy"] = [cx + (5.2 if cx < 0 else -5.2), cy]
    parts[cap]["side"] = "front"
    for offset in range(4):
        for prefix, dy in [("RF", -0.85), ("CF", 0.85)]:
            part = parts[f"{prefix}{first + offset}"]
            part["xy"] = [cx - 3 + offset * 2, cy + dy]
            part["angle"] = 0
            part["side"] = "front"
for index in range(1, 13):
    x = -18 + (index - 1) * 2 if index <= 6 else 18 + (index - 7) * 2
    parts[f"TP{index}"]["xy"] = [x, -26.5]
    parts[f"TP{index}"]["side"] = "front"
for ref, xy in {
    "C8": (-10.5, -23),
    "C9": (24.5, -22),
    "C10": (-6.7, -20),
    "C11": (-6.7, -18.5),
    "C17": (3, -26.5),
    "C25": (52, -26.5),
    "R8": (43, -27),
}.items():
    parts[ref]["xy"] = list(xy)
for ref in ["C14", "C23", "C25", "R8"]:
    parts[ref]["side"] = "front"
outer = (
    unary_union(
        [
            *(hole.buffer(5.5, quad_segs=12) for hole in holes),
            box(-59, -27, 59, -20).buffer(1, quad_segs=8),
            box(-12, -24, 12, -12).buffer(1, quad_segs=8),
            *(
                box(x - 5.5, 23, x + 5.5, 26.5).buffer(1, quad_segs=8)
                for x in [-38, 38]
            ),
        ]
    )
    .buffer(0.8, quad_segs=8)
    .buffer(-0.8, quad_segs=8)
    .simplify(0.04)
)
(target / "parts.json").write_text(json.dumps(parts, indent=2))
(target / "geometry.json").write_text(
    json.dumps(
        {
            "outer": list(outer.exterior.coords),
            "holes": [list(h.exterior.coords) for h in holes],
        }
    )
)
print("Outline bounds:", outer.bounds)
print("Material area:", outer.difference(unary_union(holes)).area)
