"""Verify E3 connectivity, assembly identity and preserved optical geometry."""

import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew as pcb

ROOT = Path("hardware/ir_glasses/EVT_E3")
board_path = ROOT / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(board_path))
source = pcb.LoadBoard(str(ROOT.parent / "EVT_E2/ir_glasses.kicad_pcb"))
fps = {f.GetReference(): f for f in board.GetFootprints()}
old = {f.GetReference(): f for f in source.GetFootprints()}
parts = json.loads((ROOT / "parts.json").read_text(encoding="utf-8"))
populated = {
    r for r in parts if not r.startswith("TP") and r not in {"J2", "NT1"}
}
assert set(fps) == set(parts)
assert len(populated) == 142
assert board.GetCopperLayerCount() == 4
assert (
    abs(pcb.ToMM(board.GetDesignSettings().GetBoardThickness()) - 1.6) < 1e-6
)


def xy(point):
    return [pcb.ToMM(point.x), pcb.ToMM(point.y)]


def pad(ref, number):
    return next(p for p in fps[ref].Pads() if p.GetNumber() == number)


def nets(fp):
    return {p.GetNumber(): p.GetNetname() for p in fp.Pads()}


for ref in populated:
    assert fps[ref].GetLayer() == pcb.F_Cu, ref
for index in range(1, 17):
    for prefix in ["D", "PD"]:
        ref = f"{prefix}{index}"
        assert fps[ref].GetPosition() == old[ref].GetPosition(), ref
        assert (
            abs(
                fps[ref].GetOrientationDegrees()
                - old[ref].GetOrientationDegrees()
            )
            < 1e-6
        ), ref
        expected = {
            pin: "GND" if net == "AGND" else net
            for pin, net in nets(old[ref]).items()
        }
        assert nets(fps[ref]) == expected, ref
    assert nets(fps[f"PD{index}"]) == {"1": "GND", "2": f"PD_IN{index}"}
assert "NT1" not in fps
assert not any(
    p.GetNetname() == "AGND" for f in fps.values() for p in f.Pads()
)
assert fps["U10"].GetPosition() == old["U10"].GetPosition()
for ref, expected in {
    "U12": {
        "1": "GND",
        "2": "3V3",
        "3": "LED_ENABLE",
        "4": "GND",
        "5": "LED_WINDOW",
        "6": "PULSE_C",
        "7": "PULSE_RC",
        "8": "3V3",
    },
    "U13": {"2": "LED_WINDOW", "3": "GND", "4": "LED_BLANK", "5": "3V3"},
    "U14": {
        "1": "VIN_3V3",
        "2": "OV_SENSE",
        "5": "VIN_3V3",
        "6": "3V3",
        "7": "INRUSH_RC",
        "8": "GND",
        "9": "ILIM_SET",
    },
    "U9": {"21": "LED_ENABLE", "28": "STATUS_LED_N"},
    "D20": {"1": "STATUS_LED_N", "2": "STATUS_A"},
    "R17": {"1": "3V3", "2": "STATUS_A"},
    "C32": {"1": "NRST", "2": "GND"},
    "C29": {"1": "ADC_L", "2": "GND"},
    "C30": {"1": "ADC_R", "2": "GND"},
}.items():
    actual = nets(fps[ref])
    assert all(actual.get(pin) == net for pin, net in expected.items()), ref
assert parts["D20"]["mpn"] == "LTST-C190KGKT"
assert parts["R17"]["value"] == "4.7k"
assert parts["R18"]["mpn"] == "RT0402BRD0719K1L"
assert parts["R19"]["mpn"] == "RT0402BRD0710KL"

xml = ET.parse(ROOT / "netlist.xml").getroot()
components = {c.attrib["ref"]: c for c in xml.findall("components/comp")}
assert set(components) == set(parts)
for ref, component in components.items():
    assert component.findtext("value") == fps[ref].GetValue(), ref
    assert component.findtext("footprint") == fps[ref].GetFPIDAsString(), ref
for net in xml.findall("nets/net"):
    for node in net.findall("node"):
        ref, pin = node.attrib["ref"], node.attrib["pin"]
        assert nets(fps[ref])[pin] == net.attrib["name"], (ref, pin)

rows = list(csv.DictReader((ROOT / "bom.csv").open(encoding="utf-8-sig")))
assert {r["Reference"] for r in rows} == populated
for row in rows:
    part, fp = parts[row["Reference"]], fps[row["Reference"]]
    assert row["MPN"] == part["mpn"]
    assert row["LCSC"] == part["lcsc"]
    assert (
        math.dist(
            [float(row["X_mm"]), float(row["Y_mm"])], xy(fp.GetPosition())
        )
        < 1e-5
    )

outline = pcb.SHAPE_POLY_SET()
assert board.GetBoardPolygonOutlines(outline, False)
assert outline.OutlineCount() == 1 and outline.HoleCount(0) == 2
old_outline = pcb.SHAPE_POLY_SET()
assert source.GetBoardPolygonOutlines(old_outline, False)


def rings(shape):
    return sorted(
        sorted(
            (shape.CHole(0, i).CPoint(j).x, shape.CHole(0, i).CPoint(j).y)
            for j in range(shape.CHole(0, i).PointCount())
        )
        for i in range(shape.HoleCount(0))
    )


assert rings(outline) == rings(old_outline), "Eye opening geometry changed"
old_vias = {
    t.m_Uuid.AsString()
    for t in source.GetTracks()
    if isinstance(t, pcb.PCB_VIA)
}
via_ids = {
    t.m_Uuid.AsString()
    for t in board.GetTracks()
    if isinstance(t, pcb.PCB_VIA)
}
assert not via_ids & {
    "bf5f8978-1448-4d99-9f9f-2477ed86f099",
    "26a255da-0175-4e9e-8a5c-aded2dabc975",
}
capacitor_distances = []
for cap, chip, number in [
    ("C3", "U2", "4"),
    ("C4", "U3", "4"),
    ("C5", "U4", "4"),
    ("C6", "U5", "4"),
    ("C17", "U9", "6"),
    ("C32", "U9", "10"),
    ("C29", "U9", "11"),
    ("C30", "U9", "12"),
    ("C25", "U14", "6"),
]:
    capacitor_distances.append(
        {
            "capacitor": cap,
            "chip": chip,
            "power_or_signal_pin": number,
            "pad_center_distance_mm": math.dist(
                xy(pad(cap, "1").GetPosition()),
                xy(pad(chip, number).GetPosition()),
            ),
        }
    )
for ref, part in parts.items():
    fp = fps[ref]
    part.update(
        xy=[v - o for v, o in zip(xy(fp.GetPosition()), [110, 85])],
        angle=fp.GetOrientationDegrees(),
        nets=nets(fp),
    )
land_count = sum(
    p.IsOnLayer(pcb.F_Cu) for r in populated for p in fps[r].Pads()
)
paste_count = sum(
    p.IsOnLayer(pcb.F_Paste) for r in populated for p in fps[r].Pads()
)
report = {
    "assembly_references": len(populated),
    "footprints": len(fps),
    "assembly_copper_lands": land_count,
    "expected_paste_openings": paste_count,
    "via_count": len(via_ids),
    "new_via_uuids": sorted(via_ids - old_vias),
    "all_assembly_front": True,
    "optical_position_angle_polarity_preserved": True,
    "eye_openings_preserved": True,
    "central_imu_preserved": True,
    "ground_architecture": "Common GND; former AGND merged; NT1 removed",
    "schematic_pcb_bom_identity": True,
    "capacitor_pad_center_distances": capacitor_distances,
    "board_sha256": hashlib.sha256(board_path.read_bytes()).hexdigest(),
}
(ROOT / "physical_summary.json").write_text(json.dumps(report, indent=2))
print(
    json.dumps(
        {
            k: v
            for k, v in report.items()
            if k not in {"new_via_uuids", "capacitor_pad_center_distances"}
        },
        indent=2,
    )
)
