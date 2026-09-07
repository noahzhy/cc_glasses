"""Refresh assembly coordinates and dimensions for the narrow rim."""

import csv
import json
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Point, Polygon, box

root = Path("hardware/ir_glasses/EVT_D")
parts = json.loads((root / "parts.json").read_text())
geometry = json.loads((root / "geometry.json").read_text())
shape = Polygon(geometry["outer"], geometry["holes"])
holes = [Polygon(h) for h in geometry["holes"]]
rows = list(csv.DictReader((root / "bom.csv").open(encoding="utf-8-sig")))
for row in rows:
    part = parts[row["Reference"]]
    row.update(
        X_mm=part["xy"][0] + 110,
        Y_mm=part["xy"][1] + 85,
        Rotation_deg=part["angle"],
        Side=part["side"],
    )
with (root / "bom.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

records = []
for number in range(1, 17):
    led, pd = (parts[f"{prefix}{number}"] for prefix in ["D", "PD"])
    record = {"LED": f"D{number}", "PD": f"PD{number}"}
    for prefix, part, copper in [
        ("LED", led, box(-1.7, -0.65, 1.7, 0.65)),
        ("PD", pd, box(-2.25, -1.2, 2.25, 1.2)),
    ]:
        center = Point(part["xy"])
        hole = min(holes, key=lambda h: h.distance(center))
        pads = translate(
            rotate(copper, -part["angle"], origin=(0, 0)), *part["xy"]
        )
        record[f"{prefix}_center_to_hole_mm"] = round(center.distance(hole), 4)
        record[f"{prefix}_pad_to_hole_mm"] = round(pads.distance(hole), 4)
        record[f"{prefix}_pad_to_outer_mm"] = round(
            pads.distance(shape.exterior), 4
        )
        record[f"{prefix}_rotation_deg"] = part["angle"]
    record["center_spacing_mm"] = round(
        Point(led["xy"]).distance(Point(pd["xy"])), 4
    )
    records.append(record)
with (root / "optical_placement.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(records[0]))
    writer.writeheader()
    writer.writerows(records)
(root / "optical_orientation.json").write_text(
    json.dumps({"rim_width_mm": 3.7, "pairs": records}, indent=2)
)

x0, y0, x1, y1 = shape.bounds
report = {
    "width_mm": x1 - x0,
    "height_mm": y1 - y0,
    "material_area_mm2": shape.area,
    "area_reduction_vs_evt_c_percent": (1 - shape.area / 2774.36) * 100,
    "nominal_rim_width_mm": 3.7,
    "optical_positions_unchanged": False,
    "eye_openings_unchanged": True,
    "bottom_amplifiers": 0,
    "populated_side_counts": {"front": 77, "back": 45},
}
(root / "mechanical_validation.json").write_text(json.dumps(report, indent=2))

for path in [root / "README.md", Path("docs/smart_glasses_ir_sensor_bom.md")]:
    text = path.read_text(encoding="utf-8")
    text = text.replace("135.535 × 53.853", "133.136 × 52.653")
    text = text.replace("5.5 mm 收到 4.9 mm", "5.5 mm 收到 3.7 mm")
    text = text.replace("2587.97 mm²", "2291.77 mm²")
    text = text.replace("约 6.7%", "约 17.4%")
    text = text.replace(
        "两个眼部开孔和 16 组 LED/PD 位置不变，继续沿框边并排。",
        "两个眼部开孔不变；16 组 LED/PD 沿局部曲线切向并排，"
        "重新调整中心位置和旋转角度，使较窄方向横跨镜框。"
        "器件仍在朝眼面，旋转是在 PCB 平面内进行。",
    )
    if path.name != "README.md":
        marker = "- PCB 外形约 133.136 × 52.653 mm"
        note = "- LED/PD 沿局部镜框切向旋转并靠近开孔，侧边及下沿名义框宽约 3.7 mm；两个眼部开孔不变。\n"
        if note not in text:
            text = text.replace(marker, note + marker)
    path.write_text(text, encoding="utf-8")
(root / "source_bom.md").write_text(
    Path("docs/smart_glasses_ir_sensor_bom.md").read_text(encoding="utf-8"),
    encoding="utf-8",
)
print(json.dumps(report, indent=2))
