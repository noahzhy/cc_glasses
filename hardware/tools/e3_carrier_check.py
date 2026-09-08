"""Check native carrier transforms and assembly coordinates."""

import csv
import hashlib
import json
import math
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E3")
path = root / "ir_glasses.kicad_pcb"
target = root / "carrier/ir_glasses_carrier.kicad_pcb"
unit = pcb.LoadBoard(str(path))
carrier = pcb.LoadBoard(str(target))
original = {fp.GetReference(): fp for fp in unit.GetFootprints()}
placed = {fp.GetReference(): fp for fp in carrier.GetFootprints()}
assert set(placed) - set(original) == {
    "H1",
    "H2",
    "H3",
    "H4",
    "FID1",
    "FID2",
    "FID3",
}


def pad_record(fp):
    return sorted(
        (
            p.GetNumber(),
            p.GetPosition().x,
            p.GetPosition().y,
            p.GetOrientationDegrees(),
            p.GetNetname(),
        )
        for p in fp.Pads()
    )


for ref, fp in original.items():
    assert pad_record(fp) == pad_record(placed[ref]), ref
    assert fp.GetPosition() == placed[ref].GetPosition(), ref
    assert fp.GetOrientationDegrees() == placed[ref].GetOrientationDegrees()


def tracks(board):
    return sorted(
        (
            t.m_Uuid.AsString(),
            t.GetNetname(),
            t.GetStart().x,
            t.GetStart().y,
            t.GetEnd().x,
            t.GetEnd().y,
            t.GetLayer(),
        )
        for t in board.GetTracks()
    )


assert tracks(unit) == tracks(carrier)
outline = pcb.SHAPE_POLY_SET()
assert carrier.GetBoardPolygonOutlines(outline, False)
assert outline.OutlineCount() == 1 and outline.HoleCount(0) == 10
rows = []
for file in [
    root / "manufacturing/positions.csv",
    root / "carrier/positions.csv",
]:
    with file.open(encoding="utf-8-sig", newline="") as stream:
        table = list(csv.DictReader(stream))
    assert len(table) == 142
    for row in table:
        fp = original[row["Ref"]]
        assert row["Side"] == "top"
        assert math.isclose(
            float(row["PosX"]), pcb.ToMM(fp.GetPosition().x), abs_tol=1e-4
        )
        assert math.isclose(
            float(row["PosY"]), -pcb.ToMM(fp.GetPosition().y), abs_tol=1e-4
        )
        assert (
            abs(
                (float(row["Rot"]) - fp.GetOrientationDegrees() + 180) % 360
                - 180
            )
            < 1e-4
        )
    rows.append(sorted(table, key=lambda r: r["Ref"]))
assert rows[0] == rows[1]
report = {
    "native_pad_track_transform": "IDENTITY",
    "assembly_references": 142,
    "additional_mechanical_features": 7,
    "closed_outline_count": 1,
    "cutout_count": 10,
    "assembly_coordinates_identical": True,
    "unit_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    "carrier_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    "factory_dfm": "PENDING",
}
(root / "carrier/carrier_validation.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(json.dumps(report, indent=2))
