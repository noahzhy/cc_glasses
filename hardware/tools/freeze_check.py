"""Check purchasing identities against the routed EVT E1 board and schematics."""

import csv
import json
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402

base = Path("hardware/ir_glasses")
root = base / "EVT_E1"
frozen = list(csv.DictReader((base / "material_freeze/bom_frozen_2pcs.csv")
                            .open(encoding="utf-8-sig")))
selected = {ref: row for row in frozen
            for ref in row["Designator"].split(",")}
board = pcb.LoadBoard(str(root / "ir_glasses.kicad_pcb"))
old = pcb.LoadBoard(str(base / "EVT_E/ir_glasses.kicad_pcb"))
old_fps = {f.GetReference(): f for f in old.GetFootprints()}
fp_by_ref = {f.GetReference(): f for f in board.GetFootprints()}


def nets(footprint):
    return sorted((p.GetNumber(), p.GetNetname()) for p in footprint.Pads())


for ref, fp in fp_by_ref.items():
    previous = old_fps[ref]
    assert nets(fp) == nets(previous), ref
    assert fp.GetPosition() == previous.GetPosition(), ref
    assert fp.GetOrientationDegrees() == previous.GetOrientationDegrees(), ref
    if ref not in selected:
        continue
    row = selected[ref]
    assert fp.GetLayer() == pcb.F_Cu, ref
    assert fp.GetValue() == row["Value"], ref
    assert fp.GetFPIDAsString() == row["Footprint"], ref
    for name in ["Manufacturer", "MPN", "LCSC"]:
        assert fp.GetFieldText(name) == row[name], (ref, name)

seen = set()
for path in root.glob("*.kicad_sch"):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    for node in tree:
        if not isinstance(node, list) or not node or str(node[0]) != "symbol":
            continue
        fields = {x[1]: x[2] for x in node if isinstance(x, list)
                  and x and str(x[0]) == "property"}
        ref = fields["Reference"]
        if ref in selected:
            seen.add(ref)
            for name in ["Value", "Footprint", "Manufacturer", "MPN", "LCSC"]:
                assert fields[name] == selected[ref][name], (ref, name)
assert seen == set(selected)
pos = list(csv.DictReader((root / "manufacturing/positions.csv")
                         .open(encoding="utf-8-sig")))
assert {r["Ref"] for r in pos} == set(selected)
for row in pos:
    fp = fp_by_ref[row["Ref"]]
    assert row["Val"] == selected[row["Ref"]]["Value"]
    assert abs(float(row["PosX"]) - pcb.ToMM(fp.GetPosition().x)) < 1e-5
    assert abs(float(row["PosY"]) + pcb.ToMM(fp.GetPosition().y)) < 1e-5
    assert row["Side"] == "top"

drc = json.loads((root / "drc.json").read_text(encoding="utf-8"))
erc = json.loads((root / "erc.json").read_text(encoding="utf-8"))
assert not drc["violations"]
assert not drc["unconnected_items"]
assert not drc["schematic_parity"]
assert not any(s["violations"] for s in erc["sheets"])
report = {
    "revision": "EVT E1", "engineering_bom": "FROZEN",
    "production_release": "HOLD_PD_SUPPLY_AND_FACTORY_DFM",
    "groups": len(frozen), "populated_per_board": len(selected),
    "assembly_quantity": 2, "fabrication_quantity": 5,
    "net_parts_for_assembly": len(selected) * 2,
    "front_populated": len(selected), "back_populated": 0,
    "net_mapping_unchanged": True, "placement_unchanged": True,
    "all_122_identities_match_schematic_pcb_bom": True,
    "cpl_entries": len(pos), "erc_violations": 0, "drc_violations": 0,
    "unconnected_items": 0, "schematic_parity_issues": 0,
    "tracks": sum(t.GetClass() != "PCB_VIA" for t in board.GetTracks()),
    "vias": sum(t.GetClass() == "PCB_VIA" for t in board.GetTracks()),
    "component_copper_lands_per_board": sum(
        1 for ref in selected for pad in fp_by_ref[ref].Pads()
        if pad.IsOnLayer(pcb.F_Cu)),
}
(root / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
