"""Adopt the supplied workbook and refresh E4 delivery archives."""

import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import openpyxl


BASE = Path("hardware/ir_glasses")
ROOT = BASE / "ir_glasses_EVT_E4"
SOURCE = BASE / "bom.xlsx"
TARGET = ROOT / "material_freeze/bom.xlsx"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rewrite_zip(path, updates, removed=()):
    with ZipFile(path) as archive:
        entries = {n: archive.read(n) for n in archive.namelist()}
    for name in removed:
        entries.pop(name, None)
    entries.update(updates)
    manifest = next(n for n in entries if n.endswith("SHA256SUMS.txt"))
    prefix = manifest.removesuffix("SHA256SUMS.txt")
    entries[manifest] = "".join(
        f"{digest(data)}  {name.removeprefix(prefix)}\n"
        for name, data in sorted(entries.items())
        if name != manifest
    ).encode()
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        for name, data in entries.items():
            assert archive.read(name) == data
    return entries[manifest]


def main():
    workbook = openpyxl.load_workbook(SOURCE, read_only=True, data_only=True)
    rows = list(workbook.active.iter_rows(values_only=True))[1:]
    mapped = {}
    for row in rows:
        refs = row[0].split(",")
        assert len(refs) == row[6] and row[7] == 2 * row[6]
        for ref in refs:
            assert ref not in mapped
            mapped[ref] = row
    with (ROOT / "carrier/positions_jlc.csv").open(
        encoding="utf-8-sig", newline=""
    ) as stream:
        cpl = list(csv.DictReader(stream))
    assert len(rows) == 33 and len(mapped) == 142
    assert set(mapped) == {r["Designator"] for r in cpl}
    assert all(r["Layer"] == "Top" for r in cpl)
    with (ROOT / "bom.csv").open(encoding="utf-8-sig", newline="") as stream:
        engineering = list(csv.DictReader(stream))
    changes = []
    for part in engineering:
        new = mapped[part["Reference"]]
        assert str(new[5]) == part["Footprint"]
        if part["MPN"] != new[3] or part["LCSC"] != (new[4] or ""):
            changes.append(
                {
                    "reference": part["Reference"],
                    "previous_mpn": part["MPN"],
                    "mpn": new[3],
                    "lcsc": new[4],
                }
            )
    assert {r["reference"] for r in changes} == {"R11", "R12", "R14"}
    backup = BASE / "archive" / datetime.now().strftime("bom_before_%Y%m%d_%H%M%S")
    backup.mkdir(parents=True)
    shutil.copytree(ROOT / "material_freeze", backup / "material_freeze")
    for path in BASE.glob("ir_glasses_EVT_E4*.zip*"):
        shutil.copy2(path, backup / path.name)
    shutil.copy2(SOURCE, TARGET)
    for name in ["bom_smt_all.csv", "bom_jlc_import.csv", "bom_frozen_2pcs.csv"]:
        path = ROOT / "material_freeze" / name
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, records = reader.fieldnames, list(reader)
        for record in records:
            new = mapped[record["Designator"].split(",")[0]]
            for key, value in {
                "Comment": new[3],
                "MPN": new[3],
                "Manufacturer": new[2],
                "LCSC": new[4] or "",
                "LCSC Part #": new[4] or "",
            }.items():
                if key in record:
                    record[key] = value
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    note = (
        "# 当前生产 BOM\n\n"
        "以用户提供的 [bom.xlsx](bom.xlsx) 为准，原文件格式和内容完整保留。\n"
        "33 类物料、142 个正面贴装位号；5 块裸板，其中 2 块贴片，净用 284 颗。\n"
        "R11/R12/R14 采购替换为 YAGEO RC0402FR-07100RL / C106232，"
        "100 Ω、1%、0402；原工程中的旧订货属性仅作设计历史参考，"
        "采购以本工作簿为准。PCB 焊盘、布线和电阻阻值未改动。\n"
        "同目录 CSV 是由本表同步的兼容副本，不是独立采购来源。\n"
        "J1 仍为自备料；库存是工作簿内快照，实时锁料、损耗和工厂接收待确认。\n"
        "平台导入时将元件位号、制造商料号、立创商城料号、封装、单板数量"
        "映射到对应列，订单选 2 块贴片；不要用两块板净用量作为单板数量。\n"
    )
    (ROOT / "material_freeze/README.md").write_text(note, encoding="utf-8")
    (BASE / "material_freeze/CURRENT.md").write_text(
        "# 当前采购版本：ir_glasses_EVT_E4\n\n"
        "当前主表：[用户提供的嘉立创 BOM]"
        "(../ir_glasses_EVT_E4/material_freeze/bom.xlsx)。\n"
        "33 类物料、142 位号；5 块裸板、2 块贴片。\n",
        encoding="utf-8",
    )
    report = {
        "source": str(SOURCE),
        "sha256": digest(SOURCE.read_bytes()),
        "groups": 33,
        "references": 142,
        "two_board_quantity": 284,
        "cpl_identity": True,
        "procurement_overrides": changes,
        "pcb_modified": False,
        "live_stock": "NOT RECHECKED",
    }
    (ROOT / "material_freeze/bom_adoption.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    check = ROOT / "pre_smt_final_check.md"
    text = check.read_text(encoding="utf-8").replace("02_BOM.csv", "02_BOM.xlsx")
    text = text.split("\n\n# 当前生产 BOM")[0] + "\n\n" + note
    check.write_text(text, encoding="utf-8")
    upload = BASE / "ir_glasses_EVT_E4_JLC_upload.zip"
    rewrite_zip(
        upload,
        {"02_BOM.xlsx": TARGET.read_bytes(), "README.md": check.read_bytes()},
        ["02_BOM.csv"],
    )
    shutil.copy2(upload, ROOT / "JLC_upload.zip")
    validation_path = ROOT / "validation.json"
    validation = json.loads(validation_path.read_text())
    validation["jlc_upload_sha256"] = digest(upload.read_bytes())
    validation["production_bom"] = report
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    changed = [
        check,
        ROOT / "JLC_upload.zip",
        validation_path,
        *[p for p in (ROOT / "material_freeze").iterdir() if p.is_file()],
    ]
    complete = BASE / "ir_glasses_EVT_E4.zip"
    manifest = rewrite_zip(
        complete,
        {
            ROOT.name + "/" + p.relative_to(ROOT).as_posix(): p.read_bytes()
            for p in changed
        },
    )
    (ROOT / "SHA256SUMS.txt").write_bytes(manifest)
    review = BASE / "ir_glasses_EVT_E4_production_review.zip"
    shutil.copy2(complete, review)
    for path in [upload, complete, review]:
        path.with_suffix(".zip.sha256").write_text(
            f"{digest(path.read_bytes())}  {path.name}\n", encoding="utf-8"
        )
    with ZipFile(complete) as archive:
        archived_bom = archive.read(ROOT.name + "/material_freeze/bom.xlsx")
        assert archived_bom == SOURCE.read_bytes()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
