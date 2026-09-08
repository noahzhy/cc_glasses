"""Remove copper conflicting with changed pads before local rerouting."""

import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import sexpdata as sx  # noqa: E402

ROOT = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((ROOT / "route_geometry.json").read_text())
refs = set(json.loads((ROOT / "placements_e3.json").read_text()))
refs.update(["U9", "J1", "D17"])
pads = [
    (p, Polygon(p["coords"]))
    for p in items
    if p["kind"] == "pad" and p["ref"] in refs
]
removed = set()
nets = set(json.loads((ROOT / "reroute_nets.json").read_text()))
for track in items:
    if track["kind"] not in {"via", "track"}:
        continue
    via = track["kind"] == "via"
    copper = Point(track["a"]) if via else LineString([track["a"], track["b"]])
    copper = copper.buffer(track["width"] / 2)
    for pad, shape in pads:
        if not set(track["layers"]) & set(pad["layers"]):
            continue
        foreign = pad["net"] != track["net"]
        conflict = foreign and copper.distance(shape) < 0.1499
        near_hole = via and Point(track["a"]).distance(shape) < 0.301
        if conflict or near_hole:
            removed.add(track["uuid"])
            nets.add(track["net"])
            break
path = ROOT / "ir_glasses.kicad_pcb"
tree = sx.loads(path.read_text(encoding="utf-8"))
tree = [
    node
    for node in tree
    if not (
        isinstance(node, list)
        and str(node[0]) in {"segment", "via"}
        and any(
            isinstance(v, list) and str(v[0]) == "uuid" and v[1] in removed
            for v in node
        )
    )
]
path.write_text(sx.dumps(tree), encoding="utf-8")
nets.update(
    [
        "LED_BLANK",
        "LED_K5",
        "LED_ENABLE",
        "LED_WINDOW",
        "PULSE_C",
        "PULSE_RC",
        "NRST",
        "NRST_EXT",
        "STATUS_LED_N",
        "STATUS_A",
        "VIN_3V3",
        "OV_SENSE",
        "EFUSE_EN",
        "ILIM_SET",
        "INRUSH_RC",
        "3V3",
        "3V3_A",
        "GND",
        "AGND",
        "ADC_L",
        "ADC_R",
    ]
)
(ROOT / "reroute_nets.json").write_text(json.dumps(sorted(nets)))
print("Cleared", len(removed), "route items; affected nets", sorted(nets))
