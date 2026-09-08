"""Plot actual copper geometry around a routing repair."""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point, Polygon, box

root = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((root / "route_geometry.json").read_text())
net = sys.argv[1]
bounds = list(map(float, sys.argv[2:6]))
window = box(*bounds)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
for layer, ax in enumerate(axes.flat):
    for item in items:
        if layer not in item["layers"] or item["kind"] == "keepout":
            continue
        kind = item["kind"]
        if kind == "pad":
            shape = Polygon(item["coords"])
        elif kind == "via":
            shape = Point(item["a"]).buffer(item["width"] / 2)
        else:
            shape = LineString([item["a"], item["b"]]).buffer(
                item["width"] / 2
            )
        if not shape.intersects(window):
            continue
        color = "crimson" if item["net"] == net else "#7391a7"
        ax.fill(*shape.exterior.xy, color=color, alpha=0.85)
        if kind == "pad":
            ax.text(
                *item["xy"],
                f"{item['ref']}.{item['pin']}",
                fontsize=6,
                ha="center",
                va="center",
            )
        if kind == "via":
            ax.plot(*item["a"], ".", color="white", markersize=3)
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[3], bounds[1])
    ax.set_aspect("equal")
    ax.set_title(["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"][layer])
    ax.grid(alpha=0.2)
fig.suptitle(net)
fig.savefig(root / "routing_detail.png", dpi=130, bbox_inches="tight")
