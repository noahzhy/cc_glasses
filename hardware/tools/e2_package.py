"""Package only final E2 deliverables and verify every archived checksum."""

import csv
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path("hardware/ir_glasses/EVT_E2")
report = json.loads((ROOT / "validation.json").read_text(encoding="utf-8"))
assert report["engineering_checks"] == "PASS"
for name, expected in report["source_sha256"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
carrier_report = json.loads(
    (ROOT / "carrier/carrier_validation.json").read_text(encoding="utf-8")
)
assert carrier_report["carrier_sha256"] == hashlib.sha256(
    (ROOT / "carrier/ir_glasses_carrier.kicad_pcb").read_bytes()
).hexdigest()
for base in [ROOT, ROOT / "carrier"]:
    gerber_report = json.loads(
        (base / "manufacturing_review/gerber_validation.json").read_text(
            encoding="utf-8"
        )
    )
    for name, expected in gerber_report["file_sha256"].items():
        actual = hashlib.sha256(
            (base / "manufacturing" / name).read_bytes()
        ).hexdigest()
        assert actual == expected, name

for source in [ROOT / "manufacturing/positions.csv",
               ROOT / "carrier/positions.csv"]:
    with source.open(encoding="utf-8-sig", newline="") as stream:
        positions = list(csv.DictReader(stream))
    assert len(positions) == 122
    mapped = [{"Designator": row["Ref"], "Mid X": row["PosX"],
               "Mid Y": row["PosY"], "Layer": "Top",
               "Rotation": row["Rot"]} for row in positions]
    with source.with_name("positions_jlc.csv").open(
            "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(mapped[0]))
        writer.writeheader()
        writer.writerows(mapped)

for directory, destination in [
    (ROOT / "manufacturing", ROOT / "ir_glasses_unit_reference.zip"),
    (ROOT / "carrier/manufacturing",
     ROOT / "carrier/ir_glasses_carrier_fabrication.zip"),
]:
    inputs = [p for p in directory.iterdir() if p.suffix in {
        ".gtl", ".gbl", ".g1", ".g2", ".gts", ".gbs", ".gto", ".gbo",
        ".gtp", ".gm1", ".gbrjob", ".drl",
    }]
    assert len(inputs) == 13, (directory, len(inputs))
    assert len([p for p in inputs if p.suffix == ".drl"]) == 2
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(inputs):
            archive.write(path, path.name)

rows = []
for name in ["bom_jlc_import.csv", "customer_supplied.csv"]:
    with (ROOT / "material_freeze" / name).open(
            encoding="utf-8-sig", newline="") as stream:
        rows.extend(csv.DictReader(stream))
assert len(rows) == 25
assert sum(len(row["Designator"].split(",")) for row in rows) == 122
for row in rows:
    row["Quantity"] = len(row["Designator"].split(","))
    row["嘉立创元件编号"] = row.pop("LCSC Part #")
for directory in [ROOT / "material_freeze", ROOT.parent / "material_freeze"]:
    with (directory / "bom_smt_all_122.csv").open(
            "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

files = set()
for pattern in ["*.kicad_sch", "*.kicad_pro", "*.kicad_pcb",
                "*.kicad_sym", "*.md"]:
    files.update(ROOT.glob(pattern))
names = """
fp-lib-table sym-lib-table ir_glasses.xml ir_glasses.net schematic.pdf
parts.json bom.csv geometry.json optical_map.csv optical_placement.csv
mechanical_validation.json optical_validation.json
manufacturing_validation.json validation.json erc.json drc.json
gerber_validation.json
pcb_3d.png pcb_back.png pcb_routed.svg pcb_routed.png
assembly_front.svg assembly_back.svg assembly_front.png assembly_back.png
optical_assembly.pdf optical_assembly_1.png optical_assembly_2.png
mechanical_dimensions.pdf mechanical_dimensions.svg
mechanical_dimensions_1.png
ir_glasses_unit_reference.zip
""".split()
files.update(ROOT / name for name in names)
for folder in ["manufacturing", "material_freeze", "procurement",
               "manufacturing_review"]:
    files.update(p for p in (ROOT / folder).rglob("*") if p.is_file())
carrier_names = """
carrier_geometry.json carrier_review.png carrier_review.svg
carrier_validation.json drc.json fp-lib-table sym-lib-table
ir_glasses_carrier.kicad_pcb ir_glasses_carrier.kicad_pro
pcb_3d.png pcb_back.png positions.csv positions_jlc.csv
ir_glasses_carrier_fabrication.zip
""".split()
files.update(ROOT / "carrier" / name for name in carrier_names)
for folder in ["carrier/manufacturing", "carrier/manufacturing_review"]:
    files.update(p for p in (ROOT / folder).rglob("*") if p.is_file())

board = (ROOT / "ir_glasses.kicad_pcb").read_text(encoding="utf-8")
footprints = re.findall(r'\(footprint\s+"IR_Glasses:([^"]+)"', board)
files.update(ROOT / "IR_Glasses.pretty" / f"{name}.kicad_mod"
             for name in set(footprints))
models = re.findall(r'\(model\s+"\$\{KIPRJMOD\}/([^"]+)"', board)
files.update(ROOT / model for model in set(models))
assert all(path.is_file() for path in files)
assert not any("PD15_22" in p.name or "EVT_E1" in str(p) for p in files)

lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  "
         f"{p.relative_to(ROOT).as_posix()}"
         for p in sorted(files)]
manifest = ROOT / "SHA256SUMS.txt"
manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
files.add(manifest)
destination = ROOT.parent / "ir_glasses_EVT_E2_production_review.zip"
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, "EVT_E2/" + path.relative_to(ROOT).as_posix())
with ZipFile(destination) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(files)
    for line in lines:
        expected, name = line.split("  ", 1)
        actual = hashlib.sha256(archive.read("EVT_E2/" + name)).hexdigest()
        assert actual == expected, name
digest = hashlib.sha256(destination.read_bytes()).hexdigest()
destination.with_suffix(".zip.sha256").write_text(
    f"{digest}  {destination.name}\n", encoding="utf-8"
)
print(json.dumps({"zip": str(destination), "files": len(files),
                  "bytes": destination.stat().st_size, "sha256": digest,
                  "all_archived_checksums_verified": True}, indent=2))
