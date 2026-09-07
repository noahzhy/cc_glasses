"""Package checked EVT E sources and fabrication outputs."""

import hashlib
import json
import zipfile
from pathlib import Path

root = Path("hardware/ir_glasses/EVT_E")
report = json.loads((root / "validation.json").read_text())
assert not any(
    report[k]
    for k in [
        "erc_violations",
        "drc_violations",
        "unconnected_items",
        "schematic_parity_issues",
    ]
)
names = [
    "ir_glasses.kicad_pro",
    "ir_glasses.kicad_pcb",
    "IR_Glasses.kicad_sym",
    "fp-lib-table",
    "sym-lib-table",
    "bom.csv",
    "README.md",
    "source_bom.md",
    "schematic.pdf",
    "validation.json",
    "drc.json",
    "erc.json",
    "mechanical_reference.png",
    "mechanical_reference.svg",
    "mechanical_validation.json",
    "manufacturing_validation.json",
    "optical_placement.csv",
    "optical_orientation.json",
    "optical_map.csv",
    "pcb_3d.png",
    "pcb_back.png",
    "pcb_routed.svg",
    "pcb_routed.png",
    "assembly_front.svg",
    "assembly_back.svg",
    "assembly_front.png",
    "assembly_back.png",
]
files = [root / name for name in names]
files += list(root.glob("*.kicad_sch"))
for folder in ["IR_Glasses.pretty", "models", "manufacturing"]:
    files += [p for p in (root / folder).rglob("*") if p.is_file()]
manifest = root / "SHA256SUMS.txt"
manifest.write_text(
    "\n".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}"
        for p in sorted(files)
    )
    + "\n"
)
files.append(manifest)
out = root.parent / "ir_glasses_EVT_E.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
    for p in files:
        archive.write(p, "EVT_E/" + p.relative_to(root).as_posix())
with zipfile.ZipFile(out) as archive:
    assert archive.testzip() is None
print(out.resolve(), out.stat().st_size, "bytes;", len(files), "files")
