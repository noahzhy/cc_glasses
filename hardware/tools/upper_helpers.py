from pathlib import Path

for name in [
    "import",
    "fill",
    "copper",
    "filled",
    "plane_stitches",
    "add_stitches",
    "drc_summary",
]:
    text = (
        Path(f"hardware/tools/frame_{name}.py")
        .read_text(encoding="utf-8")
        .replace("EVT_C", "EVT_D")
        .replace("EVT C", "EVT D")
    )
    if name == "fill":
        text = text.replace(
            'zones += [zone.replace("In1.Cu", "In2.Cu") for zone in zones]',
            'zones = [zone.replace("In1.Cu", layer) for layer in ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"] for zone in zones]',
        )
        text = text.replace(
            "filename.read_text()", 'filename.read_text(encoding="utf-8")'
        ).replace(
            'filename.write_text(data[:-1] + "\\n".join(zones) + "\\n)")',
            'filename.write_text(data[:-1] + "\\n".join(zones) + "\\n)", encoding="utf-8")',
        )
    Path(f"hardware/tools/upper_{name}.py").write_text(text, encoding="utf-8")
p = Path("hardware/tools/upper_validate.py")
p.write_text(p.read_text().replace("135.535, 53.853", "133.136, 52.653"))
p = Path("hardware/tools/upper_package.py")
p.write_text(
    p.read_text().replace(
        '"optical_placement.csv",',
        '"optical_placement.csv",\n    "optical_orientation.json",',
    )
)
p = Path("hardware/tools/upper_export.py")
s = p.read_text().replace(
    '"svg",\n        "--mode-single",',
    '"svg",\n        *(["--mirror"] if name == "assembly_back" else []),\n        *(["--black-and-white"] if name.startswith("assembly_") else []),\n        "--mode-single",',
)
p.write_text(s)
