"""Migrate the editable E3 project to short, fully linked local libraries."""

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path("hardware/ir_glasses/EVT_E3")
ARCHIVE = ROOT.parent / "archive/e3_before_library_rename.zip"
NAMES = {
    "C_0402_1005Metric": "C:0402",
    "C_0603_1608Metric": "C:0603",
    "C_1210_3225Metric": "C:1210",
    "R_0402_1005Metric": "R:0402",
    "L_0603_1608Metric": "L:0603",
    "LED_0603_1608Metric": "LED:0603",
    "D_SOD-323": "D:SOD-323",
    "D_SOD-523": "D:SOD-523",
    "Everlight_IR11_21C": "IR:1206",
    "Everlight_PD15_21B": "PD:1206",
    "LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y": "IC:LGA-14",
    "LQFP-48_7x7mm_P0.5mm": "IC:LQFP-48",
    "SOT-23-5": "IC:SOT-23-5",
    "SOT-23": "IC:SOT-23",
    "SSOP-8_2.95x2.8mm_P0.65mm": "IC:SSOP-8",
    "TSSOP-14_4.4x5mm_P0.65mm": "IC:TSSOP-14",
    "TSSOP-16_4.4x5mm_P0.65mm": "IC:TSSOP-16",
    "Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm": "IC:VQFN-24",
    "TI_RPW0010A": "IC:VQFN-10-HR",
    "Tag-Connect_TC2050-IDC-NL_2x05_P1.27mm_Vertical": "J:TC2050",
    "TE_2492111-5_1x05_P0.5mm_Horizontal": "J:FFC5-0.5",
    "TestPoint_Pad_D1.0mm": "TP:1mm",
}


def remap(text):
    text = re.sub(
        r'(\(property\s+"Footprint"\s+)"([^"]*)"',
        lambda m: m[1] + '"' + NAMES.get(m[2].split(":")[-1], m[2]) + '"',
        text,
    )
    for old, new in NAMES.items():
        text = re.sub(
            r'(\(footprint\s+|"footprint"\s*:\s*)"IR_Glasses:'
            + re.escape(old) + '"',
            lambda match: match[1] + f'"{new}"',
            text,
        )
        text = text.replace(
            f"<footprint>IR_Glasses:{old}</footprint>",
            f"<footprint>{new}</footprint>",
        )
    return text.replace("IR_Glasses:", "S:").replace("C16745", "C19269752")


sources = [
    *ROOT.glob("*.kicad_sch"),
    ROOT / "ir_glasses.kicad_pcb",
    ROOT / "carrier/ir_glasses_carrier.kicad_pcb",
    ROOT / "netlist.xml",
    ROOT / "parts.json",
    ROOT / "IR_Glasses.kicad_sym",
    ROOT / "fp-lib-table",
    ROOT / "sym-lib-table",
    ROOT / "carrier/fp-lib-table",
    ROOT / "carrier/sym-lib-table",
]
ARCHIVE.parent.mkdir(exist_ok=True)
if not ARCHIVE.exists():
    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED) as archive:
        for path in sources + list((ROOT / "IR_Glasses.pretty").glob("*.kicad_mod")):
            archive.write(path, path.relative_to(ROOT).as_posix())

for old, new in NAMES.items():
    library, name = new.split(":")
    directory = ROOT / "libraries" / f"{library}.pretty"
    directory.mkdir(parents=True, exist_ok=True)
    text = (ROOT / "IR_Glasses.pretty" / f"{old}.kicad_mod").read_text(
        encoding="utf-8"
    )
    text = text.replace(f'"{old}"', f'"{name}"')
    (directory / f"{name}.kicad_mod").write_text(text, encoding="utf-8")

for source in sources:
    if source.name in {"fp-lib-table", "sym-lib-table", "IR_Glasses.kicad_sym"}:
        continue
    with ZipFile(ARCHIVE) as archive:
        text = archive.read(source.relative_to(ROOT).as_posix()).decode("utf-8")
    source.write_text(remap(text), encoding="utf-8", newline="")
symbol = ROOT / "libraries/S.kicad_sym"
symbol.write_text(
    remap((ROOT / "IR_Glasses.kicad_sym").read_text(encoding="utf-8")),
    encoding="utf-8",
)
for directory, prefix in [(ROOT, ""), (ROOT / "carrier", "../")]:
    entries = [
        f'(lib (name "{lib}") (type "KiCad") '
        f'(uri "${{KIPRJMOD}}/{prefix}libraries/{lib}.pretty") '
        '(options "") (descr "Project local footprint library"))'
        for lib in sorted({name.split(":")[0] for name in NAMES.values()})
    ]
    (directory / "fp-lib-table").write_text(
        "(fp_lib_table (version 7)\n" + "\n".join(entries) + ")\n",
        encoding="utf-8",
    )
    (directory / "sym-lib-table").write_text(
        '(sym_lib_table (version 7) (lib (name "S") (type "KiCad") '
        f'(uri "${{KIPRJMOD}}/{prefix}libraries/S.kicad_sym") '
        '(options "") (descr "Project local symbols")))\n',
        encoding="utf-8",
    )

evidence = {}
with ZipFile(ARCHIVE) as archive:
    for name in ["ir_glasses.kicad_pcb", "carrier/ir_glasses_carrier.kicad_pcb"]:
        old = archive.read(name).decode("utf-8")
        new = (ROOT / name).read_bytes().decode("utf-8")
        assert remap(old) == new
        evidence[name] = {
            "old_sha256": hashlib.sha256(archive.read(name)).hexdigest(),
            "new_sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
            "only_library_ids_and_procurement_code_changed": True,
        }
(ROOT / "library_migration.json").write_text(
    json.dumps({"mapping": NAMES, "boards": evidence}, indent=2),
    encoding="utf-8",
)
print("Migrated", len(NAMES), "footprints and the symbol library")
