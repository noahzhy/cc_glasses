"""Independently compare delivered BOM and placement against design files."""

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from validate_e7 import properties

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review/preproduction"


def read_csv(name):
    with (ROOT / name).open(encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def check():
    rows = read_csv("BOM.csv")
    bom = {r["Reference"]: r for r in rows}
    parts = properties(ROOT / f"{ROOT.name}.kicad_sch")
    fitted = {
        r: fields
        for r, (fields, flags) in parts.items()
        if flags["in_bom"] == "yes" and flags["dnp"] == "no"
    }
    assert len(bom) == len(rows) and set(bom) == set(fitted)
    for ref, row in bom.items():
        assert row["Quantity"] == "1", ref
        for key in ["Value", "Footprint", "Manufacturer", "MPN", "LCSC"]:
            assert row[key] and row[key] == fitted[ref][key], (ref, key)
        assert row["Parameters"] and row["Catalog_URL"], ref
    original = read_csv("review/preproduction/BOM_before.csv")
    for row in original:
        assert all(bom[row["Reference"]][k] == v for k, v in row.items())
    xml = ET.parse(OUT / "netlist.xml").getroot()
    def pins(tree):
        return {
            (n.get("ref"), n.get("pin")): net.get("name")
            for net in tree.findall("nets/net")
            for n in net.findall("node")
        }
    assert pins(xml) == pins(ET.parse(ROOT / "netlist.xml").getroot())
    for comp in xml.findall("components/comp"):
        ref = comp.get("ref")
        if ref in bom:
            assert comp.findtext("value") == bom[ref]["Value"]
            assert comp.findtext("footprint") == bom[ref]["Footprint"]
    cpl = read_csv("assembly_positions.csv")
    assert len(cpl) == len(bom) and {r["Ref"] for r in cpl} == set(bom)
    placement = json.loads((ROOT / "review/placement.json").read_text())
    for row in cpl:
        ref = row["Ref"]
        pos = placement[ref]
        assert row["Side"] == "top" and pos["layer"] == "F.Cu", ref
        assert abs(float(row["PosX"]) - pos["xy"][0]) < 1e-5, ref
        assert abs(float(row["PosY"]) + pos["xy"][1]) < 1e-5, ref
        delta = (float(row["Rot"]) - pos["angle"] + 180) % 360 - 180
        assert abs(delta) < 1e-5, ref
        assert row["Val"] == bom[ref]["Value"], ref
    grouped = read_csv("BOM_采购汇总.csv")
    assert sum(int(r["单板数量"]) for r in grouped) == len(bom)
    assert len(grouped) == len({r["LCSC"] for r in rows})
    catalog = json.loads(
        (ROOT / "review/bom_catalog.json").read_text(encoding="utf-8")
    )
    for row in rows:
        assert catalog[row["LCSC"]]["MPN"] == row["MPN"]
    erc = json.loads((OUT / "erc.json").read_text(encoding="utf-8"))
    drc = json.loads((OUT / "drc.json").read_text(encoding="utf-8"))
    assert not erc["ignored_checks"] and not drc["ignored_checks"]
    assert not any(s["violations"] for s in erc["sheets"])
    assert not any(
        drc[k] for k in ["violations", "unconnected_items", "schematic_parity"]
    )
    files = [
        "BOM.csv",
        "BOM_采购汇总.csv",
        "assembly_positions.csv",
        f"{ROOT.name}.kicad_sch",
        f"{ROOT.name}.kicad_pcb",
    ]
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "static_checks_passed_bench_and_factory_release_pending",
        "fitted_parts": len(bom),
        "unique_skus": len(grouped),
        "excluded_from_bom": sorted(set(parts) - set(bom)),
        "matched_pins": len(pins(xml)),
        "bom_schematic_cpl_match": True,
        "catalog_mapping": "39 archived supplier records; 2026-09-18",
        "live_stock_and_assembly_availability": "not_verified",
        "sha256": {
            n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
            for n in files
        },
    }
    (OUT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    check()
