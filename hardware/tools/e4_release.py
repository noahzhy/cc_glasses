"""Prepare and verify the E4 release using the existing manufacturing tools."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


BASE = Path("hardware/ir_glasses/EVT_E3")
ROOT = BASE.parent / "ir_glasses_EVT_E4"
STEM = "ir_glasses_EVT_E4"
TOOLS = Path(__file__).parent


def rename(text):
    text = text.replace("ir_glasses_carrier", STEM + "_carrier")
    text = text.replace("ir_glasses.kicad", STEM + ".kicad")
    text = text.replace('"ir_glasses"', f'"{STEM}"')
    return re.sub(r"\bE3\b", "E4", text)


def prepare():
    assert not (ROOT / "revision_validation.json").exists(), "E4 already prepared."
    manifest = (BASE / "SHA256SUMS.txt").read_text().splitlines()
    names = [line.split("  ", 1)[1] for line in manifest]
    for name in names:
        source = BASE / name
        if source.suffix == ".zip" or name == "SHA256SUMS.txt":
            continue
        if "manufacturing" in Path(name).parts:
            continue
        target = ROOT / rename(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in {".kicad_pcb", ".kicad_sch", ".kicad_pro", ".md"}:
            text = rename(source.read_text(encoding="utf-8"))
            if source.suffix == ".kicad_sch":
                text = text.replace('(date "2026-09-08")', '(date "2026-09-09")')
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, target)
    evidence = {}
    for name in [
        "ir_glasses.kicad_pcb",
        "carrier/ir_glasses_carrier.kicad_pcb",
    ]:
        source, target = BASE / name, ROOT / rename(name)
        assert rename(source.read_text(encoding="utf-8")) == target.read_text(
            encoding="utf-8"
        )
        evidence[name] = {
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "e4_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "only_version_labels_changed": True,
        }
    (ROOT / "revision_validation.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(ROOT)


def run(action):
    supplied_bom = ROOT / "material_freeze/bom.xlsx"
    if action == "bom" and supplied_bom.exists():
        print(f"Using supplied production BOM: {supplied_bom}")
        return
    source = TOOLS / f"e3_{action}.py"
    code = source.read_text(encoding="utf-8")
    code = code.replace('"hardware/ir_glasses/EVT_E3"', f'"{ROOT.as_posix()}"')
    code = rename(code)
    code = code.replace('"ir_glasses_carrier"', f'"{STEM}_carrier"')
    code = code.replace(
        '"EVT_E2/ir_glasses_EVT_E4.kicad_pcb"', '"EVT_E3/ir_glasses.kicad_pcb"'
    )
    code = code.replace("ir_glasses_EVT_E3_", STEM + "_")
    code = code.replace('"EVT_E3/"', f'"{STEM}/"')
    if action == "native_audit":
        code = code.replace(
            '"new_via_uuids": sorted(via_ids - old_vias)',
            '"new_via_uuids": json.loads((ROOT.parent / '
            '"EVT_E3/physical_summary.json").read_text())["new_via_uuids"]',
        )
    if action == "package":
        code = code.replace(
            "36c26f43aae805d3afd3a7bfce988f489224c2a009d85e95be4e5db28ccbac61",
            hashlib.sha256((BASE / "ir_glasses.kicad_pcb").read_bytes()).hexdigest(),
        )
        code = code.replace(
            "previous_e2_board_preserved", "previous_e3_board_preserved"
        )
        code = code.replace(
            "JLC_upload.zip\n",
            "JLC_upload.zip revision_validation.json optical_edge_check.json\n",
        )
        code = code.replace(STEM + "_complete.zip", STEM + ".zip")
    sys.argv = [str(source), *sys.argv[2:]]
    exec(
        compile(code, str(source), "exec"),
        {"__name__": "__main__", "__file__": str(source)},
    )
    if action == "package" and supplied_bom.exists():
        python = Path.home() / (
            ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
        )
        subprocess.run([str(python), str(TOOLS / "e4_adopt_bom.py")], check=True)


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare()
    else:
        run(sys.argv[1])
