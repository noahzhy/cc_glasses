"""Read the released board and collect production audit evidence."""

import csv
import json
from collections import Counter
from pathlib import Path

import pcbnew as pcb


ROOT = Path("hardware/ir_glasses/EVT_E")
OUT = Path("hardware/ir_glasses/production_review")
board = pcb.LoadBoard(str(ROOT / "ir_glasses.kicad_pcb"))
rows = list(csv.DictReader((ROOT / "bom.csv").open(encoding="utf-8-sig")))
populated = {row["Reference"] for row in rows if row["Populate"] == "Yes"}
pads = []
counts = {}
for footprint in board.GetFootprints():
    ref = footprint.GetReference()
    count = 0
    for pad in footprint.Pads():
        if not pad.IsOnLayer(pcb.F_Cu):
            continue
        pos = pad.GetPosition()
        size = pad.GetSize()
        pads.append({
            "ref": ref,
            "pin": pad.GetNumber(),
            "net": pad.GetNetname(),
            "xy": [pcb.ToMM(pos.x), pcb.ToMM(pos.y)],
            "size": [pcb.ToMM(size.x), pcb.ToMM(size.y)],
            "angle": pad.GetOrientationDegrees(),
            "paste": pad.IsOnLayer(pcb.F_Paste),
        })
        if ref in populated:
            count += 1
    if ref in populated:
        counts[ref] = count
groups = Counter(
    (row["Value"], row["Footprint"])
    for row in rows if row["Populate"] == "Yes"
)
report = {
    "board_sha256_note": "See input_sha256.txt for the audited release.",
    "populated_components": len(populated),
    "distinct_value_footprint_groups": len(groups),
    "physical_solder_lands_per_board": sum(counts.values()),
    "solder_lands_by_ref": counts,
    "dedicated_fiducials": [
        fp.GetReference() for fp in board.GetFootprints()
        if "fiducial" in str(fp.GetFPID()).lower()
    ],
    "vias": [
        {
            "xy": [pcb.ToMM(v.GetPosition().x), pcb.ToMM(v.GetPosition().y)],
            "drill_mm": pcb.ToMM(v.GetDrillValue()),
        }
        for v in board.GetTracks() if isinstance(v, pcb.PCB_VIA)
    ],
    "pads": pads,
}
(OUT / "board_audit.json").write_text(json.dumps(report, indent=2))
print(json.dumps({
    k: v for k, v in report.items()
    if k not in {"pads", "vias", "solder_lands_by_ref"}
}, indent=2))
