"""Validate the final EVT E2 board, schematic, BOM and carrier exports."""

import csv
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

ROOT = Path("hardware/ir_glasses/EVT_E2")
SOURCE = ROOT.parent / "EVT_E1"
DATASHEET = (
    "https://en.everlight.com/wp-content/plugins/ItemRelationship/"
    "product_files/pdf/PD15-21B-TR8.pdf"
)
IDENTITY_FIELDS = ["Value", "Footprint", "Manufacturer", "MPN", "LCSC"]
OPTICS = {f"{prefix}{n}" for prefix in ["PD", "D"] for n in range(1, 17)}
BOUNDARY_TOLERANCE_MM = 0.00001


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and str(x[0]) == key]


def fields(node):
    entries = children(node, "property")
    result = {entry[1]: entry[2] for entry in entries}
    assert len(entries) == len(result), "Duplicate component property"
    return result


def pad_nets(footprint):
    return sorted((pad.GetNumber(), pad.GetNetname())
                  for pad in footprint.Pads())


def close(first, second):
    return abs(float(first) - float(second)) < 0.00001


def same_angle(first, second):
    return abs((float(first) - float(second) + 180) % 360 - 180) < 0.00001


def position(footprint):
    xy = footprint.GetPosition()
    return [pcb.ToMM(xy.x), pcb.ToMM(xy.y)]


def polygons(board):
    result = pcb.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(result, False), "Invalid outline"
    assert result.OutlineCount() == 1, "Board material is not contiguous"
    return result


def points(chain):
    return sorted((chain.CPoint(i).x, chain.CPoint(i).y)
                  for i in range(chain.PointCount()))


def hole_boundaries(poly):
    return [poly.CHole(0, i) for i in range(poly.HoleCount(0))]


def ordered_points(chain):
    return [(pcb.ToMM(chain.CPoint(i).x), pcb.ToMM(chain.CPoint(i).y))
            for i in range(chain.PointCount())]


def point_segment_distance(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    fraction = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy)
    fraction = max(0, min(1, fraction / (dx * dx + dy * dy)))
    return math.dist(point, (start[0] + fraction * dx,
                             start[1] + fraction * dy))


def remove_collinear_vertices(original):
    result = original.copy()
    error_bound = 0
    while len(result) > 3:
        for i, point in enumerate(result):
            deviation = point_segment_distance(
                point, result[i - 1], result[(i + 1) % len(result)])
            if deviation <= BOUNDARY_TOLERANCE_MM / 4:
                result.pop(i)
                error_bound += deviation
                break
        else:
            break
    return result, error_bound


def boundary_comparison(old_chain, new_chain):
    old_original = ordered_points(old_chain)
    new_original = ordered_points(new_chain)
    old_points, old_error = remove_collinear_vertices(old_original)
    new_points, new_error = remove_collinear_vertices(new_original)
    assert len(old_points) == len(new_points), "Changed hole vertex count"
    correspondences = [
        sequence[offset:] + sequence[:offset]
        for sequence in [new_points, list(reversed(new_points))]
        for offset in range(len(new_points))
    ]
    matched = min(correspondences, key=lambda points: max(
        math.dist(a, b) for a, b in zip(old_points, points)))
    maximum = max(math.dist(a, b) for a, b in zip(old_points, matched))
    upper_bound = maximum + old_error + new_error
    assert upper_bound <= BOUNDARY_TOLERANCE_MM, (
        "Changed eye opening", upper_bound)

    # Corresponding segment interpolation bounds the full boundary deviation.
    distances = []
    for first, second in [(old_original, new_original),
                          (new_original, old_original)]:
        segments = list(zip(second, second[1:] + second[:1]))
        distances += [min(point_segment_distance(p, a, b)
                          for a, b in segments) for p in first]
    old_shape, new_shape, difference = (
        pcb.SHAPE_POLY_SET(), pcb.SHAPE_POLY_SET(), pcb.SHAPE_POLY_SET()
    )
    old_shape.AddOutline(old_chain)
    new_shape.AddOutline(new_chain)
    difference.BooleanXor(old_shape, new_shape)
    return {
        "old_vertex_count": len(old_original),
        "new_vertex_count": len(new_original),
        "matched_vertex_count_after_collinear_removal": len(old_points),
        "collinear_removal_boundary_error_bound_mm": old_error + new_error,
        "maximum_corresponding_vertex_displacement_mm": maximum,
        "continuous_boundary_deviation_upper_bound_mm": upper_bound,
        "discrete_boundary_hausdorff_mm": max(distances),
        "maximum_coordinate_change_mm": max(
            abs(a[i] - b[i]) for a, b in zip(old_points, matched)
            for i in range(2)),
        "symmetric_difference_area_mm2": difference.Area() / 1e12,
        "area_method": "KiCad integer polygon XOR on the 1 nm grid",
    }


def compare_holes(first, second):
    candidates = hole_boundaries(second)
    result = []
    for original in hole_boundaries(first):
        center = tuple(sum(p[i] for p in ordered_points(original))
                       / original.PointCount() for i in range(2))
        match = min(candidates, key=lambda chain: math.dist(center, tuple(
            sum(p[i] for p in ordered_points(chain)) / chain.PointCount()
            for i in range(2))))
        result.append(boundary_comparison(original, match))
        candidates.remove(match)
    return result


def cpl_check(path, footprints, selected):
    rows = read_csv(path)
    assert len(rows) == 122 and {r["Ref"] for r in rows} == set(selected), path
    for row in rows:
        ref = row["Ref"]
        fp = footprints[ref]
        x, y = position(fp)
        assert row["Val"] == selected[ref]["Value"], (path, ref, "Value")
        assert row["Package"] == fp.GetFPID().GetLibItemName(), (path, ref)
        assert close(row["PosX"], x) and close(row["PosY"], -y), (path, ref)
        assert same_angle(row["Rot"], fp.GetOrientationDegrees()), (path, ref)
        assert row["Side"] == "top" and fp.GetLayer() == pcb.F_Cu, (path, ref)
    return len(rows)


def drc_check(path, pcb_path):
    report = read_json(path)
    assert path.stat().st_mtime >= pcb_path.stat().st_mtime, "Stale DRC report"
    assert {"error", "warning"} <= set(report["included_severities"]), path
    assert report["source"] == pcb_path.name, path
    for key in ["violations", "unconnected_items", "schematic_parity"]:
        assert not report[key], (path, key, len(report[key]))
    return report


frozen = read_csv(ROOT / "material_freeze/bom_frozen_2pcs.csv")
selected = {ref: row for row in frozen for ref in row["Designator"].split(",")}
assert len(frozen) == 25 and len(selected) == 122
assert sum(int(row["Qty_per_board"]) for row in frozen) == 122
for row in frozen:
    count = len(row["Designator"].split(","))
    assert int(row["Qty_per_board"]) == count
    assert int(row["Net_qty_2_boards"]) == count * 2
    assert row["Side"] == "F.Cu"

pcb_path = ROOT / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(pcb_path))
old = pcb.LoadBoard(str(SOURCE / pcb_path.name))
footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
previous = {fp.GetReference(): fp for fp in old.GetFootprints()}
assert set(footprints) == set(previous)
populated = {
    ref for ref, fp in footprints.items()
    if fp.GetAttributes() & pcb.FP_SMD
    and not fp.GetAttributes() & (pcb.FP_EXCLUDE_FROM_POS_FILES | pcb.FP_DNP)
}
assert populated == set(selected)
assert board.GetCopperLayerCount() == 4
assert close(pcb.ToMM(board.GetDesignSettings().GetBoardThickness()), 1.6)

for ref, fp in footprints.items():
    if not ref.startswith("PD"):
        assert pad_nets(fp) == pad_nets(previous[ref]), (ref, "Changed nets")
    if ref not in OPTICS:
        assert fp.GetPosition() == previous[ref].GetPosition(), (ref, "Moved")
        assert same_angle(
            fp.GetOrientationDegrees(),
            previous[ref].GetOrientationDegrees(),
        ), (ref, "Rotated")
    if ref not in selected:
        continue
    row = selected[ref]
    assert fp.GetLayer() == pcb.F_Cu, ref
    assert fp.GetValue() == row["Value"], (ref, "Value")
    assert fp.GetFPIDAsString() == row["Footprint"], (ref, "Footprint")
    for name in ["Manufacturer", "MPN", "LCSC"]:
        assert fp.GetFieldText(name) == row[name], (ref, name)
    if ref.startswith("PD"):
        assert pad_nets(fp) == [("1", "AGND"), ("2", f"PD_IN{ref[2:]}")], ref
        assert fp.GetValue() == "PD15-21B/TR8", ref
        assert fp.GetFieldText("LCSC") == "C2921391", ref
        assert fp.GetFieldText("Datasheet") == DATASHEET, (ref, "Datasheet")
        assert fp.GetFPIDAsString() == "IR_Glasses:Everlight_PD15_21B", ref
        for pad in fp.Pads():
            assert close(pcb.ToMM(pad.GetSize().x), 1.0), ref
            assert close(pcb.ToMM(pad.GetSize().y), 1.5), ref
        pad_list = list(fp.Pads())
        assert close(pcb.ToMM((pad_list[0].GetPosition()
                              - pad_list[1].GetPosition()).EuclideanNorm()),
                     2.6), ref

pcb_tree = sx.loads(pcb_path.read_text(encoding="utf-8"))
for node in children(pcb_tree, "footprint"):
    fields(node)

seen = set()
sch_paths = list(ROOT.glob("*.kicad_sch"))
for path in sch_paths:
    tree = sx.loads(path.read_text(encoding="utf-8"))
    assert children(children(tree, "title_block")[0], "rev")[0][1] == "EVT E2"
    for node in children(tree, "symbol"):
        properties = fields(node)
        ref = properties["Reference"]
        if ref not in selected:
            continue
        seen.add(ref)
        for name in IDENTITY_FIELDS:
            assert properties[name] == selected[ref][name], (path, ref, name)
        if ref.startswith("PD"):
            assert properties["Datasheet"] == DATASHEET, ref
            assert children(node, "lib_id")[0][1] == selected[ref]["Footprint"]
            assert {p[1] for p in children(node, "pin")} == {"1", "2"}, ref
assert seen == set(selected)

xml_path = ROOT / "ir_glasses.xml"
assert xml_path.stat().st_mtime >= max(p.stat().st_mtime for p in sch_paths)
netlist = ET.parse(xml_path).getroot()
netlist_components = {
    comp.attrib["ref"]: comp for comp in netlist.find("components")
}
netlist_nets = {
    (node.attrib["ref"], node.attrib["pin"]): net.attrib["name"]
    for net in netlist.find("nets") for node in net
}
for ref, component in netlist_components.items():
    assert ref in footprints, (ref, "Missing PCB component")
    if ref in selected:
        assert component.findtext("value") == selected[ref]["Value"], ref
        expected = selected[ref]["Footprint"]
        assert component.findtext("footprint") == expected, ref
    for pad in footprints[ref].Pads():
        key = (ref, pad.GetNumber())
        expected = netlist_nets.get(key, "")
        assert pad.GetNetname() == expected, (key, "Net mismatch")
for (ref, number), name in netlist_nets.items():
    assert (number, name) in pad_nets(footprints[ref]), (ref, number, name)

bom = read_csv(ROOT / "bom.csv")
populated_bom = {
    row["Reference"]: row for row in bom if row["Populate"] == "Yes"
}
assert set(populated_bom) == set(selected)
for ref, row in populated_bom.items():
    for name in IDENTITY_FIELDS:
        assert row[name] == selected[ref][name], (ref, name)
    x, y = position(footprints[ref])
    assert close(row["X_mm"], x) and close(row["Y_mm"], y), ref
    angle = footprints[ref].GetOrientationDegrees()
    assert same_angle(row["Rotation_deg"], angle), ref
    assert row["Side"] == "front", ref

assert position(footprints["U10"]) == [110.0, 71.3]
assert footprints["U10"].GetLayer() == pcb.F_Cu
lands = sum(pad.IsOnLayer(pcb.F_Cu) for ref in selected
            for pad in footprints[ref].Pads())
assert lands == 410, lands
poly = polygons(board)
assert poly.HoleCount(0) == 2
eye_opening_comparison = compare_holes(polygons(old), poly)
geometry = read_json(ROOT / "geometry.json")
outline = points(poly.COutline(0))
width = pcb.ToMM(max(p[0] for p in outline) - min(p[0] for p in outline))
height = pcb.ToMM(max(p[1] for p in outline) - min(p[1] for p in outline))
assert close(width, max(p[0] for p in geometry["outer"])
             - min(p[0] for p in geometry["outer"])), "Geometry width mismatch"
assert close(height, max(p[1] for p in geometry["outer"])
             - min(p[1] for p in geometry["outer"])), "Height mismatch"
mechanical = read_json(ROOT / "mechanical_validation.json")
assert close(width, mechanical["width_mm"])
assert close(height, mechanical["height_mm"])
assert mechanical["eye_openings_unchanged"]
assert all(item["copper_to_edge_mm"] >= 0.35 for item in mechanical["optics"])

cpl_count = cpl_check(
    ROOT / "manufacturing/positions.csv", footprints, selected,
)
carrier_path = ROOT / "carrier/ir_glasses_carrier.kicad_pcb"
carrier = pcb.LoadBoard(str(carrier_path))
carrier_fps = {fp.GetReference(): fp for fp in carrier.GetFootprints()}
for ref, fp in footprints.items():
    other = carrier_fps[ref]
    assert fp.GetPosition() == other.GetPosition(), (ref, "Carrier offset")
    assert same_angle(fp.GetOrientationDegrees(),
                      other.GetOrientationDegrees()), ref
    assert fp.GetLayer() == other.GetLayer(), ref
    assert fp.GetFPIDAsString() == other.GetFPIDAsString(), ref
    assert pad_nets(fp) == pad_nets(other), ref
    if ref in selected:
        for name in ["Manufacturer", "MPN", "LCSC"]:
            assert other.GetFieldText(name) == selected[ref][name], (ref, name)
carrier_cpl = cpl_check(ROOT / "carrier/positions.csv", carrier_fps, selected)
carrier_poly = polygons(carrier)
carrier_eye_comparison = compare_holes(poly, carrier_poly)

drc = drc_check(ROOT / "drc.json", pcb_path)
carrier_drc = drc_check(ROOT / "carrier/drc.json", carrier_path)
erc_path = ROOT / "erc.json"
erc = read_json(erc_path)
assert erc_path.stat().st_mtime >= max(p.stat().st_mtime for p in sch_paths)
assert {"error", "warning"} <= set(erc["included_severities"])
assert not any(sheet["violations"] for sheet in erc["sheets"])

report = {
    "revision": "EVT E2",
    "engineering_checks": "PASS",
    "production_release": "PENDING_LIVE_STOCK_FACTORY_DFM_AND_OPTICAL_TEST",
    "fabrication_quantity": 5,
    "assembly_quantity": 2,
    "groups": len(frozen),
    "populated_per_board": len(selected),
    "net_parts_for_assembly": 244,
    "front_populated": 122,
    "back_populated": 0,
    "component_copper_lands_per_board": lands,
    "photodiodes": 16,
    "pd_pin_mapping": "1=AGND; 2=PD_INn",
    "non_pd_pad_nets_unchanged": True,
    "non_optical_placement_unchanged": True,
    "all_122_identities_match_schematic_pcb_bom": True,
    "duplicate_properties": 0,
    "eye_openings_unchanged": True,
    "eye_opening_boundary_tolerance_mm": BOUNDARY_TOLERANCE_MM,
    "eye_opening_rounding_note": (
        "Matched vertices bound every intervening segment displacement. "
        "Collinear vertex removal errors are added to the boundary bound. "
        "The 10 nm tolerance accepts rounding and boundary resampling only. "
        "XOR area uses KiCad integer clipping with intersection rounding."
    ),
    "eye_opening_boundary_comparison_to_E1": eye_opening_comparison,
    "carrier_eye_opening_boundary_comparison": carrier_eye_comparison,
    "width_mm": width,
    "height_mm": height,
    "cpl_entries": cpl_count,
    "carrier_cpl_entries": carrier_cpl,
    "carrier_component_transform": "Identity; no translation or rotation",
    "erc_violations": 0,
    "drc_violations": 0,
    "unconnected_items": 0,
    "schematic_parity_issues": 0,
    "carrier_drc_violations": 0,
    "native_ignored_drc_checks": drc["ignored_checks"],
    "native_ignored_erc_checks": erc["ignored_checks"],
    "tracks": sum(t.GetClass() != "PCB_VIA" for t in board.GetTracks()),
    "vias": sum(track.GetClass() == "PCB_VIA" for track in board.GetTracks()),
    "source_sha256": {
        str(path.relative_to(ROOT)):
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [pcb_path, carrier_path, xml_path, *sch_paths,
                     ROOT / "material_freeze/bom_frozen_2pcs.csv"]
    },
}
(ROOT / "validation.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
