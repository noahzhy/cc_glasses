"""Refresh assembly metadata from the final native PCB."""

import csv
import json
from pathlib import Path

import pcbnew as pcb


ROOT = Path("hardware/ir_glasses/EVT_E2")
board = pcb.LoadBoard(str(ROOT / "ir_glasses.kicad_pcb"))
parts = json.loads((ROOT / "parts.json").read_text())
footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
frozen = list(csv.DictReader((ROOT / "material_freeze/bom_frozen_2pcs.csv")
                            .open(encoding="utf-8-sig")))
selected = {ref: row for row in frozen
            for ref in row["Designator"].split(",")}
for ref, part in parts.items():
    fp = footprints[ref]
    part.update(value=fp.GetValue(), footprint=fp.GetFPIDAsString(),
                xy=[pcb.ToMM(fp.GetPosition().x) - 110,
                    pcb.ToMM(fp.GetPosition().y) - 85],
                angle=fp.GetOrientationDegrees(), side="front",
                nets={pad.GetNumber(): pad.GetNetname() for pad in fp.Pads()})
    if ref.startswith("PD"):
        part["symbol"] = "Everlight_PD15_21B"
    for field in ["Manufacturer", "MPN", "LCSC"]:
        if ref in selected:
            part[field.lower()] = selected[ref][field]
(ROOT / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")

rows = list(csv.DictReader((ROOT / "bom.csv").open(encoding="utf-8-sig")))
for row in rows:
    ref = row["Reference"]
    fp = footprints[ref]
    row.update(Value=fp.GetValue(), Footprint=fp.GetFPIDAsString(),
               X_mm=pcb.ToMM(fp.GetPosition().x),
               Y_mm=pcb.ToMM(fp.GetPosition().y),
               Rotation_deg=fp.GetOrientationDegrees(), Side="front")
    for field in ["Manufacturer", "MPN", "LCSC"]:
        row[field] = selected[ref][field] if ref in selected else ""
with (ROOT / "bom.csv").open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=rows[0])
    writer.writeheader()
    writer.writerows(rows)
print("Metadata refreshed:", len(parts), "footprints;", len(selected), "SMT")
