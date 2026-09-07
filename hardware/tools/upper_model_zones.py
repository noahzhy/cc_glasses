"""Attach the manufacturer's FPC model and create routing reference regions."""

import json
import uuid
from pathlib import Path

import sexpdata as sx
from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_D")
model = sx.loads(
    '(model "${KIPRJMOD}/models/TE_1734839-5_aligned.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
)
name = "TE_0-1734839-5_1x05-1MP_P0.5mm_Horizontal"
p = root / "IR_Glasses.pretty" / f"{name}.kicad_mod"
n = sx.loads(p.read_text())
n = [v for v in n if not isinstance(v, list) or str(v[0]) != "model"]
n.append(model)
p.write_text(sx.dumps(n), encoding="utf-8")
p = root / "ir_glasses.kicad_pcb"
n = sx.loads(p.read_text(encoding="utf-8"))
for fp in n:
    if (
        isinstance(fp, list)
        and str(fp[0]) == "footprint"
        and fp[1] == "IR_Glasses:" + name
    ):
        fp[:] = [
            v for v in fp if not isinstance(v, list) or str(v[0]) != "model"
        ]
        fp.append(model)
g = json.loads((root / "geometry.json").read_text())
outer = translate(Polygon(g["outer"]), 110, 85)
digital = unary_union(
    [
        box(98, 56, 125, 68.5),
        box(125, 56, 144, 60.8),
        box(135, 56, 142, 64.8),
        box(144, 56, 171, 59),
    ]
)
zones = []
for name, shape in [
    ("GND", outer.intersection(digital)),
    ("AGND", outer.difference(digital)),
]:
    polys = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
    for shape in polys:
        shape = shape.buffer(-0.03)
        coords = list(shape.exterior.coords)
        points = " ".join(f"(xy {x:.6f} {y:.6f})" for x, y in coords[:-1])
        z = f'(zone (net "{name}") (layer "In1.Cu") (uuid "{uuid.uuid4()}") (hatch edge .5) (connect_pads yes (clearance .2)) (min_thickness .15) (fill yes (thermal_gap .2) (thermal_bridge_width .25)) (polygon (pts {points})))'
        n.append(sx.loads(z))
        zones.append(
            {"name": name, "coords": [[x - 110, y - 85] for x, y in coords]}
        )
p.write_text(sx.dumps(n), encoding="utf-8")
(root / "zones.json").write_text(json.dumps(zones))
