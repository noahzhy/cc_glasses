import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.affinity import rotate, translate
from shapely.geometry import Point, LineString, box

items = json.loads(
    Path("hardware/ir_glasses/EVT_D/route_geometry.json").read_text()
)
fig, axes = plt.subplots(2, 2, figsize=(14, 14))
for layer, ax in zip([3, 0, 1, 2], axes.flat):
    for t in items:
        if layer not in t["layers"]:
            continue
        if t["kind"] == "pad":
            x, y = t["size"]
            s = (
                Point(0, 0).buffer(x / 2)
                if t["circle"]
                else box(-x / 2, -y / 2, x / 2, y / 2)
            )
            s = translate(rotate(s, -t["angle"], origin=(0, 0)), *t["xy"])
        elif t["kind"] == "via":
            s = Point(t["a"]).buffer(t["width"] / 2)
        else:
            s = LineString([t["a"], t["b"]]).buffer(t["width"] / 2)
        if not s.intersects(box(116, 59, 124, 67)):
            continue
        color = (
            "red"
            if t["net"] == "LED_K9"
            else ("orange" if t["kind"] == "via" else "steelblue")
        )
        ax.add_patch(Patch(list(s.exterior.coords), fc=color, alpha=0.7))
        if t["kind"] == "pad":
            ax.text(
                *t["xy"],
                t.get("ref", "") + "." + t.get("pin", ""),
                fontsize=6,
                ha="center",
            )
    ax.set(
        xlim=(116, 124),
        ylim=(67, 59),
        aspect="equal",
        title=["F.Cu", "In1", "In2", "B.Cu"][layer],
    )
    ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig("hardware/ir_glasses/EVT_D/driver_detail.png", dpi=160)
