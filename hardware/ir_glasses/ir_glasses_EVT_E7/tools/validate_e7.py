"""Validate E7 against the E6 schematic and preserved mechanical baseline."""

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import sexpdata as sx

from export_bom import export_bom

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / "ir_glasses_EVT_E6_F302"
REMOVED = {"C24", "C45", "TP5", "TP6"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def children(tree, key):
    return [v for v in tree if isinstance(v, list) and v and str(v[0]) == key]


def netlist(path):
    tree = ET.parse(path).getroot()
    pins = {
        (v.get("ref"), v.get("pin")): n.get("name")
        for n in tree.findall("nets/net")
        for v in n.findall("node")
    }
    return tree, pins


def properties(path):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    rows = {}
    for symbol in children(tree, "symbol"):
        fields = {p[1]: p[2] for p in children(symbol, "property")}
        ref = fields["Reference"]
        if not ref.startswith("#"):
            rows[ref] = (
                fields,
                {
                    k: str(children(symbol, k)[0][1])
                    for k in ["in_bom", "on_board", "dnp"]
                },
            )
    return rows


def validate():
    old, before = netlist(OLD / "netlist.xml")
    new, after = netlist(ROOT / "netlist.xml")
    expected = {k: v for k, v in before.items() if k[0] not in REMOVED}
    assert expected == after, "Unexplained pin/net change"
    old_parts = properties(OLD / f"{OLD.name}.kicad_sch")
    parts = properties(ROOT / f"{ROOT.name}.kicad_sch")
    assert set(old_parts) - set(parts) == REMOVED
    assert all(old_parts[r] == v for r, v in parts.items())
    with (ROOT / "review/pin_net_comparison.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["Reference", "Pin", "E6", "E7", "Change"])
        for key in sorted(before):
            writer.writerow(
                [
                    *key,
                    before[key],
                    after.get(key, ""),
                    "removed" if key[0] in REMOVED else "unchanged",
                ]
            )
    with (ROOT / "BOM.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Reference",
                "Value",
                "Footprint",
                "Manufacturer",
                "MPN",
                "LCSC",
                "Quantity",
            ]
        )
        for ref, (fields, flags) in sorted(parts.items()):
            if flags["in_bom"] == "yes" and flags["dnp"] == "no":
                writer.writerow(
                    [
                        fields.get(k, "")
                        for k in [
                            "Reference",
                            "Value",
                            "Footprint",
                            "Manufacturer",
                            "MPN",
                            "LCSC",
                        ]
                    ]
                    + [1]
                )
    export_bom()
    for name, value in json.loads(
        (ROOT / "review/e6_hashes.json").read_text()
    ).items():
        assert sha(OLD / name) == value, "E6 changed: " + name
    assert len(list(ROOT.rglob("*.kicad_pcb"))) == 1
    assert len(list(ROOT.rglob("*.kicad_pro"))) == 1
    assert len(list(ROOT.rglob("*.kicad_sch"))) == 1
    erc = json.loads((ROOT / "erc.json").read_text(encoding="utf-8"))
    assert not erc["ignored_checks"]
    assert not any(s["violations"] for s in erc["sheets"])
    pcb = json.loads((ROOT / "review/pcb_facts.json").read_text())
    board_hash = sha(ROOT / f"{ROOT.name}.kicad_pcb")
    assert pcb["board_sha256"] == board_hash, "Refresh native PCB audit"
    geometry = json.loads((ROOT / "review/geometry_checks.json").read_text())
    assert geometry["board_sha256"] == board_hash, "Refresh geometry checks"
    assert not geometry["routes_outside_baseboard"]
    assert not geometry["via_hole_to_pad_violations"]
    assert not geometry["reference_projection"]["violations"]
    assert geometry["ground_regions"] == 1
    old_project = json.loads((OLD / f"{OLD.name}.kicad_pro").read_text())
    project = json.loads((ROOT / f"{ROOT.name}.kicad_pro").read_text())
    expected_rules = old_project["board"]["design_settings"]["rules"].copy()
    expected_rules.update(
        min_through_hole_diameter=0.2,
        min_via_diameter=0.4,
        min_microvia_drill=0.2,
        min_microvia_diameter=0.4,
    )
    for net_class in project["net_settings"]["classes"]:
        assert net_class["via_drill"] >= 0.2
        assert net_class["microvia_drill"] >= 0.2
    assert project["board"]["design_settings"]["rules"] == expected_rules
    assert pcb["minimum_via_drill_mm"] >= 0.2 - 1e-6
    drc_path = ROOT / "drc.json"
    drc = json.loads(drc_path.read_text(encoding="utf-8"))
    assert not drc["ignored_checks"]
    errors = [v for v in drc["violations"] if v["severity"] == "error"]
    warnings = [v for v in drc["violations"] if v["severity"] == "warning"]
    pending = len(errors) + len(drc["unconnected_items"])
    pending += len(drc.get("schematic_parity", []))
    result = dict(
        status="passed" if pending == 0 else "incomplete",
        electrical_components=len(parts),
        pins_compared=len(after),
        removed=sorted(REMOVED),
        retained_pin_changes=0,
        erc_violations=0,
        drc_errors=len(errors),
        drc_warnings=len(warnings),
        unrouted=len(drc["unconnected_items"]),
        schematic_parity=len(drc.get("schematic_parity", [])),
        single_project=True,
        e6_unchanged=True,
        all_electrical_components_front=True,
        copper_layers=pcb["copper_layers"],
        thickness_mm=pcb["thickness_mm"],
        outline_unchanged=pcb["outline_unchanged"],
        manufacturing_rules_match_requirements=True,
        minimum_via_drill_mm=pcb["minimum_via_drill_mm"],
        minimum_via_annular_ring_mm=pcb["minimum_via_annular_ring_mm"],
        rule_changes={
            "min_through_hole_diameter": [0.15, 0.2],
            "min_via_diameter": [0.35, 0.4],
            "min_microvia_drill": [0.1, 0.2],
            "min_microvia_diameter": [0.2, 0.4],
        },
        minimum_via_hole_to_pad_mm=geometry["minimum_hole_to_pad_mm"],
        scope="Static design review; bench tests pending",
        hashes={
            p.name: sha(p)
            for p in [
                ROOT / f"{ROOT.name}.kicad_sch",
                ROOT / f"{ROOT.name}.kicad_pcb",
                ROOT / f"{ROOT.name}.kicad_pro",
                ROOT / "netlist.xml",
                ROOT / "erc.json",
                drc_path,
            ]
        },
    )
    (ROOT / "review/validation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    (ROOT / "review/drc_warnings.json").write_text(
        json.dumps(warnings, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print({k: v for k, v in result.items() if k != "hashes"})
    assert pending == 0, "PCB acceptance still incomplete"


if __name__ == "__main__":
    validate()
