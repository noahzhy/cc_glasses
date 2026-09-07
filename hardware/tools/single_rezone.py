"""Pour separate analog and digital regions around the one-face layout."""

import json
import uuid
from pathlib import Path

import sexpdata as sx
from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_E")
path = root / "ir_glasses.kicad_pcb"
board = sx.loads(path.read_text(encoding="utf-8"))
board = [n for n in board if not isinstance(n, list) or str(n[0]) != "zone"]
geometry = json.loads((root / "geometry.json").read_text())
outer = Polygon(geometry["outer"])
digital = unary_union(
    [
        box(-60, -28, -48, -21),
        box(-60, -28, 60, -27.4),
        box(-9.1, -28, 16.5, -16.8),
        box(-3.8, -17, 6, -10.9),
        box(6.8, -20, 23, -16.5),
        box(48, -28, 61.7, -15),
    ]
)
regions = []
for name, area in [
    ("GND", outer.intersection(digital)),
    ("AGND", outer.difference(digital)),
]:
    polygons = [area] if area.geom_type == "Polygon" else list(area.geoms)
    for polygon in polygons:
        polygon = polygon.buffer(-0.03)
        regions.append({"name": name, "coords": list(polygon.exterior.coords)})
        polygon = translate(polygon, 110, 85)
        points = " ".join(
            f"(xy {x:.6f} {y:.6f})" for x, y in polygon.exterior.coords[:-1]
        )
        for layer in ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]:
            zone = (
                f'(zone (net "{name}") (layer "{layer}") '
                f'(uuid "{uuid.uuid4()}") (hatch edge .5) '
                "(connect_pads yes (clearance .2)) (min_thickness .15) "
                "(fill yes (thermal_gap .2) (thermal_bridge_width .25)) "
                f"(polygon (pts {points})))"
            )
            board.append(sx.loads(zone))
path.write_text(sx.dumps(board), encoding="utf-8")
(root / "zones.json").write_text(json.dumps(regions))
