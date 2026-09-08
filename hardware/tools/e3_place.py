"""Fit the new components into the existing upper frame without widening it."""

import json
import math
from pathlib import Path

import numpy as np
from shapely.affinity import rotate, translate
from shapely.geometry import MultiPoint, Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((ROOT / "layout_geometry.json").read_text())
parts = json.loads((ROOT / "parts.json").read_text())
geometry = json.loads((ROOT / "geometry.json").read_text())
board = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)
new = json.loads((ROOT / "new_refs.json").read_text())
moved = [
    "C3",
    "C4",
    "C5",
    "C6",
    "C17",
    "C29",
    "C30",
    "D17",
    "C24",
    "C25",
    "U11",
    "R8",
    "R9",
    "TP9",
    "TP10",
    "TP11",
]
shapes = {}
for ref, item in items.items():
    pads = []
    for pad in item["pads"]:
        w, h = pad["size"]
        shape = rotate(
            box(-w / 2, -h / 2, w / 2, h / 2), -pad["angle"], origin=(0, 0)
        )
        pads.append(translate(shape, *pad["xy"]))
    points = [p for p in item["courtyard"] if math.dist(p, item["xy"]) < 10]
    courtyard = (
        MultiPoint(points).convex_hull
        if points
        else unary_union(pads).buffer(0.25)
    )
    shapes[ref] = courtyard.union(unary_union(pads).buffer(0.10)).convex_hull

fixed = {r: p for r, p in shapes.items() if r not in new + moved}
placements = {}


def put(ref, target, radius=10, pad_pin=None):
    item = items[ref]
    local = translate(shapes[ref], -item["xy"][0], -item["xy"][1])
    if pad_pin:
        p = next(p for p in item["pads"] if p["pin"] == pad_pin)
        offset = Point(p["xy"][0] - item["xy"][0], p["xy"][1] - item["xy"][1])
    else:
        offset = Point(0, 0)
    occupied = unary_union(list(fixed.values()))
    candidates = []
    for angle in [0, 90, 180, 270]:
        rotated = rotate(local, -angle, origin=(0, 0))
        pin = rotate(offset, -angle, origin=(0, 0))
        center = (target[0] - pin.x, target[1] - pin.y)
        for dx in np.arange(-radius, radius + 0.01, 0.2):
            for dy in np.arange(-radius, radius + 0.01, 0.2):
                x, y = center[0] + dx, center[1] + dy
                if not 57.6 <= y <= 73.8:
                    continue
                candidates.append((math.hypot(dx, dy), x, y, angle, rotated))
    candidates.sort(key=lambda v: v[0])
    for distance, x, y, angle, rotated in candidates:
        shape = translate(rotated, x, y)
        if not board.buffer(-0.1).covers(shape) or shape.intersects(occupied):
            continue
        fixed[ref] = shape
        placements[ref] = [
            round(x, 4),
            round(y, 4),
            (item["angle"] + angle) % 360,
        ]
        print(
            ref,
            placements[ref],
            "target distance",
            round(distance, 3),
            flush=True,
        )
        return
    raise RuntimeError("No placement found for " + ref)


def pin(ref, number):
    return next(p["xy"] for p in items[ref]["pads"] if p["pin"] == number)


for ref, chip, number in [
    ("C3", "U2", "4"),
    ("C4", "U3", "4"),
    ("C5", "U4", "4"),
    ("C6", "U5", "4"),
    ("C17", "U9", "6"),
    ("C29", "U9", "11"),
    ("C30", "U9", "12"),
]:
    put(ref, pin(chip, number), radius=5, pad_pin="1")
    if ref == "C17":
        put("C32", pin("U9", "10"), radius=5, pad_pin="1")
put("U14", [158.5, 61.5], radius=9)
put("D17", [159, 58.7], radius=8)
put("C37", [158.0, 64], radius=5)
put("D18", pin("J1", "5"), radius=6, pad_pin="1")
put("R18", [156.5, 63.5], radius=7)
put("R19", [156.5, 64.5], radius=7)
put("U11", [167, 67], radius=9)
put("R20", [160.5, 64.5], radius=9)
put("C38", [160, 64.5], radius=15)
put("R14", [103, 66], radius=8)
put("U12", [56, 65], radius=13)
put("U13", [128, 67], radius=13)
put("D19", pin("J2", "10"), radius=7, pad_pin="1")
put("D20", [59, 58.5], radius=10)
put("C24", [112, 68.8], radius=10)
put("C25", [56.5, 65.5], radius=8)
put("R8", [114, 69], radius=10)
put("R9", [116, 70], radius=10)
for ref, anchor, dx, dy in [
    ("C35", "U12", 2, -1),
    ("C36", "U13", 2, -1),
    ("C33", "U12", 1, 2),
    ("C34", "U12", 1, 3),
    ("R15", "U12", 2, 2),
    ("R16", "U12", -2, 1),
    ("R17", "D20", 2, 0),
]:
    x, y, _ = placements[anchor]
    put(ref, [x + dx, y + dy], radius=8)
for ref in ["TP9", "TP10", "TP11"]:
    put(ref, items[ref]["xy"], radius=15)
(ROOT / "placements_e3.json").write_text(json.dumps(placements, indent=2))
