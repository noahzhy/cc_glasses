"""Record the completed visual inspection and engineering release checks."""

import csv
import hashlib
import json
from pathlib import Path


root = Path("hardware/ir_glasses/EVT_E3")
names = [
    "pcb_3d.png",
    "pcb_back.png",
    "assembly_front.png",
    "assembly_back.png",
    "carrier/pcb_3d.png",
]
for directory in ["", "carrier/"]:
    for view in ["top_copper", "bottom_copper", "inner_1", "inner_2", "top_paste"]:
        names.append(f"{directory}manufacturing_review/{view}.png")


def digest(name):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()


report = {
    "result": "PASS",
    "scope": "Exported geometry and assembly visual inspection only",
    "unit_sha256": digest("ir_glasses.kicad_pcb"),
    "carrier_sha256": digest("carrier/ir_glasses_carrier.kicad_pcb"),
    "file_sha256": {name: digest(name) for name in names},
    "checked": [
        "Correct frame orientation and two eye openings",
        "Front-only assembly and central IMU",
        "Status LED and straight upper edge; power pocket removed",
        "Four copper layers and front paste",
        "Carrier tabs, tooling holes and asymmetric fiducials",
    ],
    "factory_dfm": "PENDING",
    "bench_tests": "NOT RUN",
}
(root / "visual_review.json").write_text(json.dumps(report, indent=2))
path = root / "gerber_validation.json"
report = json.loads(path.read_text())
report["visual_review_status"] = "PASS: exported geometry only"
path.write_text(json.dumps(report, indent=2))
path = root / "release_checklist.csv"
with path.open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))
for row in rows:
    if row["ID"] == "P11":
        row["当前状态"] = "工程文件检查通过；工厂及首板验证仍待完成"
        row["完成日期"] = "2026-09-08"
with path.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0])
    writer.writeheader()
    writer.writerows(rows)
