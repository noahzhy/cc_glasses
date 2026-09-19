"""Audit the saved E7 PCB without modifying the design."""

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / f"{ROOT.name}.kicad_pcb"
OLD = ROOT.parent / "ir_glasses_EVT_E6_F302"


def position(item):
    point = item.GetPosition()
    return [pcb.ToMM(point.x), pcb.ToMM(point.y)]


def outline(board):
    rows = []
    for item in board.GetDrawings():
        if item.GetLayer() != pcb.Edge_Cuts:
            continue
        points = [item.GetStart(), item.GetEnd()]
        if item.GetShape() == pcb.SHAPE_T_ARC:
            points.append(item.GetArcMid())
        rows.append((item.GetShape(), tuple((p.x, p.y) for p in points)))
    return sorted(rows)


def audit():
    board = pcb.LoadBoard(str(PATH))
    baseline = pcb.LoadBoard(
        str(OLD / "carrier" / "ir_glasses_EVT_E6_F302_carrier.kicad_pcb")
    )
    baseline_parts = {f.GetReference(): f for f in baseline.GetFootprints()}
    tree = ET.parse(ROOT / "netlist.xml").getroot()
    parts = {c.get("ref"): c for c in tree.findall("components/comp")}
    pins = {
        (n.get("ref"), n.get("pin")): net.get("name")
        for net in tree.findall("nets/net")
        for n in net.findall("node")
    }
    observed = {}
    placement = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        placement[ref] = dict(
            xy=position(fp),
            angle=fp.GetOrientationDegrees(),
            layer=board.GetLayerName(fp.GetLayer()),
        )
        if ref in parts:
            assert fp.GetLayer() == pcb.F_Cu, ref
            for pad in fp.Pads():
                key = (ref, pad.GetNumber())
                if key in pins:
                    observed[key] = pad.GetNetname()
                    assert observed[key] == pins[key], key
    assert observed == pins, "Pad-to-net mismatch"
    assert board.GetCopperLayerCount() == 4
    assert (
        abs(pcb.ToMM(board.GetDesignSettings().GetBoardThickness()) - 1.6)
        < 1e-6
    )
    assert outline(board) == outline(baseline), "Mechanical outline changed"
    fixed = {}
    for fp in baseline.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith(("PD", "J", "H", "FID")) or ref in {
            f"D{i}" for i in range(1, 17)
        }:
            before = dict(
                xy=position(fp),
                angle=fp.GetOrientationDegrees(),
                layer=baseline.GetLayerName(fp.GetLayer()),
            )
            assert before == placement[ref], (ref, before, placement[ref])
            fixed[ref] = before
    tracks = board.GetTracks()
    vias = [
        tracks[i]
        for i in range(len(tracks))
        if isinstance(tracks[i], pcb.PCB_VIA)
    ]
    min_drill = min(pcb.ToMM(v.GetDrillValue()) for v in vias)
    min_ring = min(
        pcb.ToMM(v.GetWidth(pcb.F_Cu) - v.GetDrillValue()) / 2 for v in vias
    )
    assert min_drill >= 0.2 - 1e-6, "Via drill below 0.20 mm"
    assert min_ring >= 0.1 - 1e-6, "Via annular ring below 0.10 mm"
    assert all(v.GetViaType() == pcb.VIATYPE_THROUGH for v in vias)
    facts = dict(
        minimum_via_drill_mm=min_drill,
        minimum_via_annular_ring_mm=min_ring,
        board_sha256=hashlib.sha256(PATH.read_bytes()).hexdigest(),
        electrical_components=len(parts),
        front_components=len(parts),
        copper_layers=4,
        thickness_mm=1.6,
        matched_pins=len(pins),
        outline_unchanged=True,
        fixed_components=fixed,
        segments=sum(
            not isinstance(tracks[i], pcb.PCB_VIA) for i in range(len(tracks))
        ),
        vias=sum(
            isinstance(tracks[i], pcb.PCB_VIA) for i in range(len(tracks))
        ),
    )
    (ROOT / "review/pcb_facts.json").write_text(
        json.dumps(facts, indent=2) + "\n"
    )
    (ROOT / "review/placement.json").write_text(
        json.dumps(placement, indent=2) + "\n"
    )
    with (ROOT / "review/placement_comparison.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as output:
        writer = csv.writer(output)
        writer.writerow(
            [
                "Reference",
                "E6_X",
                "E6_Y",
                "E6_Angle",
                "E6_Layer",
                "E7_X",
                "E7_Y",
                "E7_Angle",
                "E7_Layer",
                "Status",
            ]
        )
        for ref, fp in sorted(baseline_parts.items()):
            old = [
                *position(fp),
                fp.GetOrientationDegrees(),
                baseline.GetLayerName(fp.GetLayer()),
            ]
            new = placement.get(ref)
            values = [*new["xy"], new["angle"], new["layer"]] if new else []
            writer.writerow(
                [
                    ref,
                    *old,
                    *(values or [""] * 4),
                    "fixed"
                    if ref in fixed
                    else "retained"
                    if new
                    else "removed",
                ]
            )
    print({k: v for k, v in facts.items() if k != "fixed_components"})


if __name__ == "__main__":
    audit()
