"""Plot native copper around a requested routing area."""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Point, Polygon, box

root = Path("hardware/ir_glasses/EVT_E")
items = json.loads((root / "route_geometry.json").read_text())
net = sys.argv[1]
bounds = list(map(float, sys.argv[2:6]))
window = box(*bounds)
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
for layer, ax in enumerate(axes.flat):
    for item in items:
        if layer not in item["layers"] and item["kind"] != "keepout":
            continue
        kind = item["kind"]
        if kind == "pad":
            x, y = item["size"]
            shape = (
                Point(0, 0).buffer(x / 2)
                if item["circle"]
                else box(-x / 2, -y / 2, x / 2, y / 2)
            )
            shape = translate(
                rotate(shape, -item["angle"], origin=(0, 0)), *item["xy"]
            )
        elif kind == "via":
            shape = Point(item["a"]).buffer(item["width"] / 2)
        elif kind == "keepout":
            shape = Polygon(item["coords"])
        else:
            shape = LineString([item["a"], item["b"]]).buffer(
                item["width"] / 2
            )
        if not shape.intersects(window):
            continue
        color = "crimson" if item["net"] == net else "#46687f"
        ax.fill(*shape.exterior.xy, color=color, alpha=0.8)
        if kind in {"pad", "via"}:
            label = (
                f"{item.get('ref', '')}.{item.get('pin', '')}\n{item['net']}"
            )
            ax.text(
                shape.centroid.x,
                shape.centroid.y,
                label,
                fontsize=5,
                ha="center",
                va="center",
            )
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[3], bounds[1])
    ax.set_aspect("equal")
    ax.set_title(["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"][layer])
    ax.grid(alpha=0.2)
fig.savefig(root / "routing_detail.png", dpi=180, bbox_inches="tight")
