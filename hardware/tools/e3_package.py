"""Gate and package the E3 engineering deliverables with verified hashes."""

import csv
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path("hardware/ir_glasses/EVT_E3")


def read(name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


erc = read("erc.json")
assert not any(sheet["violations"] for sheet in erc["sheets"])
for name in ["drc.json", "carrier/drc.json"]:
    report = read(name)
    assert not report["violations"], name
    assert not report["unconnected_items"], name
    assert not report["schematic_parity"], name
physical = read("physical_summary.json")
assert (
    read("electrical_metrics.json")["new_via_minimum_drill_edge_to_pad_mm"]
    >= 0.1499
)
assert physical["board_sha256"] == digest(root / "ir_glasses.kicad_pcb")
assert (
    read("electrical_metrics.json")["board_sha256"] == physical["board_sha256"]
)
carrier = read("carrier/carrier_validation.json")
assert carrier["unit_sha256"] == physical["board_sha256"]
assert carrier["carrier_sha256"] == digest(
    root / "carrier/ir_glasses_carrier.kicad_pcb"
)
visual = read("visual_review.json")
assert visual["result"] == "PASS"
assert visual["unit_sha256"] == physical["board_sha256"]
assert visual["carrier_sha256"] == carrier["carrier_sha256"]
for name, value in visual["file_sha256"].items():
    assert digest(root / name) == value
for directory in [root, root / "carrier"]:
    report = json.loads(
        (directory / "manufacturing_review/gerber_validation.json").read_text()
    )
    for name, value in report["file_sha256"].items():
        assert digest(directory / "manufacturing" / name) == value

for path in [
    root / "manufacturing/positions.csv",
    root / "carrier/positions.csv",
]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 142 and all(r["Side"] == "top" for r in rows)
    mapped = [
        {
            "Designator": row["Ref"],
            "Mid X": row["PosX"],
            "Mid Y": row["PosY"],
            "Layer": "Top",
            "Rotation": row["Rot"],
        }
        for row in rows
    ]
    with path.with_name("positions_jlc.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=mapped[0])
        writer.writeheader()
        writer.writerows(mapped)

for directory, target in [
    (root / "manufacturing", root / "ir_glasses_unit_reference.zip"),
    (
        root / "carrier/manufacturing",
        root / "carrier/ir_glasses_carrier_fabrication.zip",
    ),
]:
    inputs = [
        p
        for p in directory.iterdir()
        if p.suffix
        in {
            ".gtl",
            ".gbl",
            ".g1",
            ".g2",
            ".gts",
            ".gbs",
            ".gto",
            ".gbo",
            ".gtp",
            ".gm1",
            ".gbrjob",
            ".drl",
        }
    ]
    assert len(inputs) == 13
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in sorted(inputs):
            archive.write(path, path.name)

baseline = root.parent / "EVT_E2/ir_glasses.kicad_pcb"
assert digest(baseline) == (
    "36c26f43aae805d3afd3a7bfce988f489224c2a009d85e95be4e5db28ccbac61"
)
sources = [
    *root.glob("*.kicad_sch"),
    root / "ir_glasses.kicad_pcb",
    root / "ir_glasses.kicad_pro",
    root / "IR_Glasses.kicad_sym",
    root / "netlist.xml",
    root / "bom.csv",
]
validation = {
    "revision": "EVT E3",
    "layout": "Flat upper edge; previous protruding layout superseded",
    "engineering_checks": "PASS",
    "erc_violations": 0,
    "drc_violations": 0,
    "unconnected": 0,
    "schematic_parity_issues": 0,
    "assembly_positions": 142,
    "bom_groups": 33,
    "all_assembly_front": True,
    "carrier_coordinates": "IDENTICAL TO UNIT",
    "source_sha256": {p.name: digest(p) for p in sources},
    "previous_e2_board_preserved": True,
    "inherited_ignored_erc_checks": erc["ignored_checks"],
    "inherited_ignored_drc_checks": read("drc.json")["ignored_checks"],
    "firmware_binary": "NOT PROVIDED",
    "electrical_and_optical_bench_tests": "NOT RUN",
    "domestic_inventory_and_attrition": "UNCONFIRMED",
    "factory_dfm_and_customer_supplied_j1": "PENDING",
    "production_release": "HOLD FOR FACTORY AND FIRST ARTICLE RESULTS",
}
(root / "validation.json").write_text(
    json.dumps(validation, indent=2), encoding="utf-8"
)
files = set(sources)
files.update(root.glob("*.md"))
names = """
fp-lib-table sym-lib-table parts.json geometry.json optical_map.csv
optical_placement.csv upper_power_pocket.json first_board_tests.csv
schematic.pdf pcb_3d.png pcb_back.png pcb_routed.svg pcb_routed.png
assembly_front.svg assembly_back.svg assembly_front.png assembly_back.png
optical_assembly.pdf mechanical_dimensions.pdf mechanical_dimensions.svg
physical_summary.json electrical_metrics.json visual_review.json
gerber_validation.json validation.json erc.json drc.json release_checklist.csv
ir_glasses_unit_reference.zip
""".split()
files.update(root / n for n in names)
for directory in [
    "manufacturing",
    "manufacturing_review",
    "material_freeze",
    "carrier/manufacturing",
    "carrier/manufacturing_review",
]:
    files.update(p for p in (root / directory).rglob("*") if p.is_file())
carrier_names = """
carrier_geometry.json carrier_review.svg carrier_review.png
carrier_validation.json drc.json fp-lib-table sym-lib-table
ir_glasses_carrier.kicad_pcb ir_glasses_carrier.kicad_pro
pcb_3d.png pcb_back.png positions.csv positions_jlc.csv
ir_glasses_carrier_fabrication.zip
""".split()
files.update(root / "carrier" / n for n in carrier_names)
board = (root / "ir_glasses.kicad_pcb").read_text(encoding="utf-8")
footprints = set(re.findall(r'\(footprint\s+"IR_Glasses:([^"]+)"', board))
files.update(root / "IR_Glasses.pretty" / f"{n}.kicad_mod" for n in footprints)
models = set(re.findall(r'\(model\s+"\$\{KIPRJMOD\}/([^"]+)"', board))
files.update(root / n for n in models)
assert all(p.is_file() for p in files)
lines = [
    f"{digest(p)}  {p.relative_to(root).as_posix()}" for p in sorted(files)
]
manifest = root / "SHA256SUMS.txt"
manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
files.add(manifest)
target = root.parent / "ir_glasses_EVT_E3_production_review.zip"
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, "EVT_E3/" + path.relative_to(root).as_posix())
with ZipFile(target) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(files)
    for line in lines:
        value, name = line.split("  ", 1)
        assert (
            hashlib.sha256(archive.read("EVT_E3/" + name)).hexdigest() == value
        )
target.with_suffix(".zip.sha256").write_text(
    f"{digest(target)}  {target.name}\n", encoding="utf-8"
)
print(
    json.dumps(
        {
            "zip": str(target),
            "files": len(files),
            "bytes": target.stat().st_size,
            "sha256": digest(target),
        },
        indent=2,
    )
)
