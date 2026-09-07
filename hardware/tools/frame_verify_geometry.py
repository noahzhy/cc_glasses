"""Prepare the corrected mechanical reference and verification data."""

import csv
import json
import shutil
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_C")
geometry = json.loads((root / "geometry.json").read_text())
parts = json.loads((root / "parts.json").read_text())
holes = [Polygon(p) for p in geometry["holes"]]
outer = Polygon(geometry["outer"])
previous = json.loads(
    Path("hardware/ir_glasses/EVT_B/geometry.json").read_text()
)
previous_area = Polygon(previous["outer"]).area - sum(
    Polygon(h).area for h in previous["holes"]
)
area = outer.area - sum(h.area for h in holes)
mechanical = {
    "board_dimensions_mm": [136.734, 55.5, 1.6],
    "board_area_mm2": round(area, 2),
    "previous_board_area_mm2": round(previous_area, 2),
    "reduction_from_evt_b_percent": round(100 * (1 - area / previous_area), 2),
    "nose_notch_opens_downward": not outer.contains(Point(0, 0)),
    "coordinate_correction": "Y mirrored; opening size and spacing unchanged",
}
(root / "mechanical_validation.json").write_text(
    json.dumps(mechanical, indent=2)
)
with (root / "optical_placement.csv").open("w", newline="") as output:
    writer = csv.writer(output)
    writer.writerow(
        [
            "LED",
            "PD",
            "LED_edge_distance_mm",
            "PD_edge_distance_mm",
            "center_spacing_mm",
            "relative_angle_deg",
        ]
    )
    for index in range(1, 17):
        led, pd = parts[f"D{index}"], parts[f"PD{index}"]
        a, b = Point(led["xy"]), Point(pd["xy"])
        hole = holes[1 if index <= 8 else 0]
        distances = [hole.distance(a), hole.distance(b)]
        assert all(2.3 < distance < 2.5 for distance in distances)
        assert led["angle"] == pd["angle"]
        writer.writerow(
            [
                f"D{index}",
                f"PD{index}",
                *(round(d, 3) for d in distances),
                round(a.distance(b), 3),
                0,
            ]
        )
digital = unary_union([box(-12, -29, 15, -11), box(44, -29, 60, -18)])
zones = []
for name, shape in [
    ("GND", outer.intersection(digital)),
    ("AGND", outer.difference(digital)),
]:
    polygons = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
    zones.extend(
        {"name": name, "coords": list(p.exterior.coords)} for p in polygons
    )
(root / "zones.json").write_text(json.dumps(zones))
shutil.copy2(
    "assets/images/topview_outline.png", root / "mechanical_reference.png"
)
svg = Path("assets/blender/topview_outline.svg").read_text()
svg = svg.replace(
    'viewBox="-72.2724 -25.2117 144.3552 46.7763"',
    'viewBox="-72.2724 -21.5646 144.3552 46.7763"',
)
svg = svg.replace("  <path", '  <g transform="scale(1,-1)"><path', 1)
svg = svg.replace("</svg>", "</g></svg>")
(root / "mechanical_reference.svg").write_text(svg)
print(json.dumps(mechanical, indent=2))
