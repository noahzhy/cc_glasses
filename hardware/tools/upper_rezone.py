"""Keep analog decoupling inside AGND and extend GND around the FFC port."""

import json
import uuid
from pathlib import Path

import sexpdata as sx
from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_D")
path = root / "ir_glasses.kicad_pcb"
node = sx.loads(path.read_text(encoding="utf-8"))
node = [n for n in node if not isinstance(n, list) or str(n[0]) != "zone"]
g = json.loads((root / "geometry.json").read_text())
outer = translate(Polygon(g["outer"]), 110, 85)
digital = unary_union(
    [
        box(98, 56, 125, 68.5),
        box(125, 56, 144, 60.8),
        box(135, 56, 142, 64.8),
        box(144, 56, 171, 57.9),
        box(160, 56, 171, 64.5),
    ]
)
zones = []
for name, area in [
    ("GND", outer.intersection(digital)),
    ("AGND", outer.difference(digital)),
]:
    polygons = [area] if area.geom_type == "Polygon" else list(area.geoms)
    for polygon in polygons:
        coords = list(polygon.buffer(-0.03).exterior.coords)
        zones.append(
            {"name": name, "coords": [[x - 110, y - 85] for x, y in coords]}
        )
        points = " ".join(f"(xy {x:.6f} {y:.6f})" for x, y in coords[:-1])
        for layer in ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]:
            text = f'(zone (net "{name}") (layer "{layer}") (uuid "{uuid.uuid4()}") (hatch edge .5) (connect_pads yes (clearance .2)) (min_thickness .15) (fill yes (thermal_gap .2) (thermal_bridge_width .25)) (polygon (pts {points})))'
            node.append(sx.loads(text))
path.write_text(sx.dumps(node), encoding="utf-8")
(root / "zones.json").write_text(json.dumps(zones))
