"""Pack all components on the optical face within the existing outline."""

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from shapely.affinity import rotate, translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_E")
parts = json.loads((root / "parts.json").read_text())
shapes = json.loads((root / "local_shapes.json").read_text())
geometry = json.loads((root / "geometry.json").read_text())
board = Polygon(geometry["outer"], geometry["holes"])
area = board.buffer(-0.18)
placed = {}
fixed = {
    "J2": (-54.5, -24, 0),
    "J1": (55, -23.3, 180),
    "U3": (-43, -23.6, 0),
    "U2": (-32.5, -24.5, 0),
    "U6": (-23, -23, 0),
    "U7": (-15, -23, 0),
    "U9": (0, -22, 0),
    "U1": (11, -23, 0),
    "U8": (21, -23.5, 0),
    "U4": (32.5, -24.5, 0),
    "U5": (43, -23.6, 0),
    "U10": (0, -13.7, 0),
    "C28": (12, -17.7, 0),
}


def courtyard(ref, xy, angle):
    return translate(
        rotate(box(*shapes[ref]["courtyard"]), -angle, origin=(0, 0)),
        *xy,
    )


def put(ref, xy, angle):
    part = parts[ref]
    part.update(xy=list(xy), angle=angle, side="front")
    placed[ref] = courtyard(ref, xy, angle)


def pin_xy(ref, pin):
    part = parts[ref]
    pad = next(p for p in shapes[ref]["pads"] if p["pin"] == str(pin))
    theta = math.radians(-part["angle"])
    x, y = pad["xy"]
    return np.array(part["xy"]) + [
        x * math.cos(theta) - y * math.sin(theta),
        x * math.sin(theta) + y * math.cos(theta),
    ]


for ref, part in parts.items():
    if ref.startswith("PD") or (ref.startswith("D") and ref != "D17"):
        put(ref, part["xy"], part["angle"])
for ref, (x, y, angle) in fixed.items():
    put(ref, (x, y), angle)

targets = {}
for amp, first in [("U2", 1), ("U3", 5), ("U4", 9), ("U5", 13)]:
    for offset, pins in enumerate([(1, 2), (7, 6), (8, 9), (14, 13)]):
        target = (pin_xy(amp, pins[0]) + pin_xy(amp, pins[1])) / 2
        for prefix in ["RF", "CF"]:
            targets[f"{prefix}{first + offset}"] = target

decoupling = {
    "C2": ("U1", 21),
    "C3": ("U2", 4),
    "C4": ("U3", 4),
    "C5": ("U4", 4),
    "C6": ("U5", 4),
    "C7": ("U6", 5),
    "C8": ("U7", 16),
    "C9": ("U8", 16),
    "C10": ("U9", 24),
    "C11": ("U9", 9),
    "C12": ("U10", 8),
    "C13": ("U10", 5),
    "C14": ("J1", 1),
    "C16": ("U1", 21),
    "C17": ("U9", 48),
}
for ref, (ic, pin) in decoupling.items():
    targets[ref] = pin_xy(ic, pin)
targets.update(
    {
        "U11": (57.5, -18),
        "D17": (49, -25),
        "R1": (13, -21),
        "R2": (-25, -25),
        "R3": (-25, -20),
        "C1": (-25, -23),
        "R4": (-6.5, -24),
        "R5": (5.8, -24),
        "R6": (3, -15),
        "R7": (3, -13),
        "R8": (52, -20),
        "R9": (53, -20),
        "R10": (13, -25),
        "R11": (-8, -18),
        "R12": (6, -18),
        "R13": (-21, -25),
        "C15": (-24, -20),
        "C18": (0, -27),
        "C19": (-4, -27),
        "C20": (3, -13),
        "C21": (-23, -20),
        "C22": (-42, -20),
        "C23": (42, -20),
        "C24": (51, -24),
        "C25": (52, -26),
        "C26": (15, -19),
        "C27": (-26, -18),
        "C29": (-6.5, -16),
        "C30": (6, -16),
        "C31": (-21, -20),
        "FB1": (-21, -18),
        "NT1": (-18, -18),
    }
)
for i in range(1, 13):
    targets[f"TP{i}"] = (-21 + (i - 1) * 4, -26.7)

order = [
    "U11",
    "D17",
    "C25",
    "C26",
    "C27",
    "FB1",
    "NT1",
    *[f"{p}{i}" for i in range(1, 17) for p in ["RF", "CF"]],
    *decoupling,
    "C25",
    "C26",
    "C27",
    "FB1",
    "NT1",
    *[r for r in parts if r not in placed and not r.startswith("TP")],
    *[f"TP{i}" for i in range(1, 13)],
]
for ref in dict.fromkeys(order):
    if ref in placed:
        continue
    tx, ty = targets[ref]
    obstacles = unary_union(list(placed.values())).buffer(0.10)
    candidates = []
    radius = 65 if ref.startswith("TP") else 18
    for dx in np.arange(-radius, radius + 0.01, 0.25):
        for dy in np.arange(-6, 15.01 if ref.startswith("TP") else 6.01, 0.25):
            x, y = round(tx + dx, 3), round(ty + dy, 3)
            if (
                y < -27.4
                or y > (-5 if ref.startswith("TP") else -11.6)
                or abs(x) > 64
            ):
                continue
            candidates.append((dx * dx + dy * dy, x, y))
    found = False
    for _, x, y in sorted(candidates):
        for angle in [0, 90]:
            shape = courtyard(ref, (x, y), angle)
            if area.covers(shape) and not shape.intersects(obstacles):
                put(ref, (x, y), angle)
                found = True
                break
        if found:
            break
    if not found:
        raise RuntimeError(f"No room for {ref}")

collisions = []
for i, (ref, shape) in enumerate(placed.items()):
    for other in list(placed)[i + 1 :]:
        if shape.intersection(placed[other]).area > 0.001:
            collisions.append([ref, other])
print("Courtyard collisions:", collisions)
assert not collisions
(root / "parts.json").write_text(json.dumps(parts, indent=2))
fig, ax = plt.subplots(figsize=(20, 8))
ax.fill(*board.exterior.xy, color="#dbe5d7")
for hole in board.interiors:
    ax.fill(*hole.xy, color="white")
for ref, shape in placed.items():
    optical = ref.startswith("PD") or (ref.startswith("D") and ref != "D17")
    ax.fill(
        *shape.exterior.xy,
        alpha=0.55,
        color="orange" if optical else "steelblue",
    )
    ax.text(*parts[ref]["xy"], ref, ha="center", va="center", fontsize=5)
ax.set_aspect("equal")
ax.invert_yaxis()
fig.savefig(root / "single_placement.png", dpi=180, bbox_inches="tight")
print("Placed", len(parts), "footprints on front.")
