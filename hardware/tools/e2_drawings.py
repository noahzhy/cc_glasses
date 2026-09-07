"""Create dimensioned mechanical and optical polarity review drawings."""

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon

ROOT = Path("hardware/ir_glasses/EVT_E2")
geometry = json.loads((ROOT / "geometry.json").read_text())
parts = json.loads((ROOT / "parts.json").read_text())
items = json.loads((ROOT / "route_geometry.json").read_text())
outer = np.array(geometry["outer"]) + [110, 85]
holes = [np.array(h) + [110, 85] for h in geometry["holes"]]


def outline(ax):
    ax.add_patch(Polygon(outer, facecolor="#e0ece2", edgecolor="#294633",
                         linewidth=0.8))
    for hole in holes:
        ax.add_patch(Polygon(hole, facecolor="white", edgecolor="#294633",
                             linewidth=0.8))
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")


def rectangle(xy, size, angle):
    theta = math.radians(-angle)
    rot = np.array([[math.cos(theta), -math.sin(theta)],
                    [math.sin(theta), math.cos(theta)]])
    corners = np.array([[-1, -1], [-1, 1], [1, 1], [1, -1]])
    return corners * np.array(size) / 2 @ rot.T + xy


with PdfPages(ROOT / "optical_assembly.pdf") as pdf:
    for eye, start, limits, center in [
        ("LEFT", 1, (42, 109), np.array([78, 85])),
        ("RIGHT", 9, (111, 178), np.array([142, 85])),
    ]:
        fig, ax = plt.subplots(figsize=(9.5, 8))
        outline(ax)
        ax.set_xlim(*limits)
        ax.set_ylim(112, 56)
        refs = {f"{p}{n}" for p in ["D", "PD"]
                for n in range(start, start + 8)}
        for ref in sorted(refs):
            part = parts[ref]
            xy = np.array(part["xy"]) + [110, 85]
            is_pd = ref.startswith("PD")
            color = "#343434" if is_pd else "#2386a6"
            size = [3.2, 1.5] if is_pd else [3.2, 1.2]
            body = rectangle(xy, size, part["angle"])
            ax.add_patch(Polygon(body, facecolor=color, zorder=3))
            for pad in [p for p in items if p["kind"] == "pad"
                        and p["ref"] == ref]:
                land = rectangle(pad["xy"], pad["size"], pad["angle"])
                ax.add_patch(Polygon(land, facecolor="#c99a3d",
                                     edgecolor="white", linewidth=0.3,
                                     zorder=4))
                ax.text(*pad["xy"], pad["pin"], ha="center", va="center",
                        fontsize=6, color="black", zorder=5)
                if is_pd and pad["pin"] == "2":
                    ax.plot(*pad["xy"], "o", ms=9, mfc="none",
                            mec="#bd2032", mew=0.9, zorder=6)
            direction = center - xy
            direction /= np.linalg.norm(direction)
            label = xy + direction * (4.3 if is_pd else 2.8)
            ax.annotate(ref, xy, label, fontsize=8, ha="center",
                        va="center", color=color,
                        arrowprops={"arrowstyle": "-", "lw": 0.5,
                                    "color": color})
        fig.suptitle(f"EVT E2 | {eye} OPTICAL ASSEMBLY | TOP VIEW",
                     fontsize=14, x=0.08, ha="left")
        fig.text(0.08, 0.055,
                 "Black: PD15-21B/TR8. Red ring: pin 2 (K) to PD_INn. "
                 "Pin 1 (A) to AGND.\n"
                 "Blue: IR11-21C/TR8 LED. Pads are numbered as in PCB.\n"
                 "Use positions.csv for machine coordinates and rotation; "
                 "these are review drawings, not placement data.",
                 fontsize=9, linespacing=1.5)
        fig.subplots_adjust(left=0.06, right=0.96, top=0.91, bottom=0.16)
        pdf.savefig(fig)
        plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 7))
outline(ax)
xmin, ymin = outer.min(axis=0)
xmax, ymax = outer.max(axis=0)
for a, b in [((xmin, ymin - 5), (xmax, ymin - 5)),
             ((xmax + 5, ymin), (xmax + 5, ymax))]:
    ax.annotate("", a, b, arrowprops={"arrowstyle": "<->", "lw": 0.8})
ax.text((xmin + xmax) / 2, ymin - 6, f"{xmax - xmin:.3f} mm",
        ha="center", fontsize=11)
ax.text(xmax + 7, (ymin + ymax) / 2, f"{ymax - ymin:.3f} mm",
        rotation=90, va="center", fontsize=11)
ax.text(78, 86, "Unchanged eye opening", ha="center", fontsize=10)
ax.text(142, 86, "Unchanged eye opening", ha="center", fontsize=10)
ax.annotate("3.0 mm nominal rim", (78, 107.8), (78, 99), ha="center",
            fontsize=10, arrowprops={"arrowstyle": "->", "lw": 0.8})
ax.annotate("IMU center (110.0, 71.3)", (110, 71.3), (110, 81),
            ha="center", fontsize=8,
            arrowprops={"arrowstyle": "->", "lw": 0.8})
ax.set_xlim(xmin - 4, xmax + 15)
ax.set_ylim(ymax + 4, ymin - 11)
fig.suptitle("EVT E2 | FINISHED BOARD DIMENSIONS | mm | TOP VIEW",
             fontsize=14, x=0.065, ha="left")
fig.text(0.065, 0.05,
         "4-layer FR-4 / nominal 1.6 mm / ENIG / front assembly only.\n"
         "Rim: 3.0 mm nominal on sides and lower edges. "
         "No routing-driven local widening; upper transitions R0.8 mm.\n"
         "Upper electronics envelope retained. Dimensions refer to "
         "Edge.Cuts centerlines; this PDF is not to scale.\n"
         "Carrier and depanel details: carrier/carrier_review.svg and "
         "carrier_design.md. Factory DFM remains pending.",
         fontsize=9, linespacing=1.4)
fig.subplots_adjust(left=0.04, right=0.97, top=0.90, bottom=0.20)
fig.savefig(ROOT / "mechanical_dimensions.pdf")
fig.savefig(ROOT / "mechanical_dimensions.svg")
plt.close(fig)
