"""Build E3 assembly and procurement tables."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("hardware/ir_glasses/EVT_E3")
OUT = ROOT / "material_freeze"
OUT.mkdir(exist_ok=True)
PACKAGES = {
    "LQFP-48_7x7mm_P0.5mm": "LQFP-48(7x7)",
    "Texas_RGE0024C_VQFN-24-1EP_4x4mm_P0.5mm_EP2.1x2.1mm":
        "VQFN-24-EP(4x4)",
    "LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y": "LGA-14(2.5x3)",
    "SOT-23-5": "SOT-23-5",
    "SOT-23": "SOT-23",
    "D_SOD-323": "SOD-323",
    "D_SOD-523": "SOD-523",
    "L_0603_1608Metric": "0603",
    "R_0402_1005Metric": "0402",
    "C_0402_1005Metric": "0402",
    "C_0603_1608Metric": "0603",
    "C_1210_3225Metric": "1210",
    "LED_0603_1608Metric": "0603",
    "TSSOP-14_4.4x5mm_P0.65mm": "TSSOP-14",
    "TSSOP-16_4.4x5mm_P0.65mm": "TSSOP-16",
    "Everlight_PD15_21B": "1206",
    "Everlight_IR11_21C": "1206",
    "SSOP-8_2.95x2.8mm_P0.65mm": "SSOP-8",
    "TI_RPW0010A": "VQFN-10-HR(2x2)",
    "TE_2492111-5_1x05_P0.5mm_Horizontal": "FFC/FPC-5P-P0.5mm",
}


def package_name(library_id):
    migration = json.loads((ROOT / "library_migration.json").read_text())
    packages = {
        new: PACKAGES[old]
        for old, new in migration["mapping"].items()
        if old in PACKAGES
    }
    return packages[library_id]


parts = json.loads((ROOT / "parts.json").read_text(encoding="utf-8"))
for part in parts.values():
    if part.get("mpn") == "IR11-21C/TR8":
        part["lcsc"] = "C19269752"
populated = {
    r: p
    for r, p in parts.items()
    if not r.startswith("TP") and r not in {"J2", "NT1"}
}


def csv_file(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


groups = defaultdict(list)
rows = []
for ref, part in populated.items():
    groups[
        (
            part["manufacturer"],
            part["mpn"],
            part["lcsc"],
            part["footprint"],
            part["value"],
        )
    ].append(ref)
    rows.append(
        {
            "Reference": ref,
            "Value": part["value"],
            "Manufacturer": part["manufacturer"],
            "MPN": part["mpn"],
            "LCSC": part["lcsc"],
            "Footprint": package_name(part["footprint"]),
            "X_mm": round(part["xy"][0] + 110, 6),
            "Y_mm": round(part["xy"][1] + 85, 6),
            "Rotation_deg": part["angle"],
            "Side": "front",
        }
    )
csv_file(ROOT / "bom.csv", rows)
package_by_ref = {row["Reference"]: row["Footprint"] for row in rows}
for path in ROOT.rglob("positions.csv"):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        positions = list(csv.DictReader(stream))
    original = [{k: v for k, v in row.items() if k != "Package"}
                for row in positions]
    for row in positions:
        row["Package"] = package_by_ref[row["Ref"]]
    csv_file(path, positions)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        actual = list(csv.DictReader(stream))
    assert original == [
        {k: v for k, v in row.items() if k != "Package"} for row in actual
    ]
    if path.parent.name == "manufacturing":
        report_path = (
            path.parent.parent / "manufacturing_review/gerber_validation.json"
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if path.name in report["file_sha256"]:
            report["file_sha256"][path.name] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            report["package_name_update"] = (
                "Package labels normalized; all other CSV fields unchanged."
            )
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
frozen, imports, supplied = [], [], []
for (maker, mpn, lcsc, footprint, value), refs in groups.items():
    refs.sort(
        key=lambda r: (
            r.rstrip("0123456789"),
            int(r[len(r.rstrip("0123456789")) :]),
        )
    )
    designators = ",".join(refs)
    frozen.append(
        {
            "Designator": designators,
            "Value": value,
            "Manufacturer": maker,
            "MPN": mpn,
            "LCSC": lcsc,
            "Footprint": package_name(footprint),
            "Qty_per_board": len(refs),
            "Net_qty_2_boards": 2 * len(refs),
            "Side": "F.Cu",
            "Engineering_revision": "EVT E3",
            "Domestic_live_stock": "UNCONFIRMED",
            "Stock_lookup_attempt_date": "2026-09-08",
            "Platform_attrition_qty": "",
            "Final_supply_qty": "",
            "Factory_receipt_status": "Pending",
            "Supply_route": "Customer supplied"
            if not lcsc
            else "JLC domestic preferred; fixed MPN if unavailable",
            "Source": f"https://www.jlc-smt.com/lcsc/detail/{lcsc}.html"
            if lcsc
            else "TE 2492111-5 customer-supplied connector",
        }
    )
    imported = {
        "Comment": mpn,
        "Designator": designators,
        "Footprint": package_name(footprint),
        "LCSC Part #": lcsc,
    }
    (imports if lcsc else supplied).append(imported)
csv_file(OUT / "bom_frozen_2pcs.csv", frozen)
csv_file(OUT / "bom_jlc_import.csv", imports)
csv_file(OUT / "customer_supplied.csv", supplied)
csv_file(
    OUT / "bom_smt_all.csv",
    [
        dict(row, Quantity=len(row["Designator"].split(",")))
        for row in imports + supplied
    ],
)
csv_file(
    OUT / "debug_spares_not_fitted.csv",
    [
        {
            "Value": "220k 1% 0402",
            "MPN": "0402WGF2203TCE",
            "Purpose": "Optional TIA gain experiment",
            "Fitted_qty": 0,
        },
        {
            "Value": "470k 1% 0402",
            "MPN": "0402WGF4703TCE",
            "Purpose": "Optional TIA gain experiment",
            "Fitted_qty": 0,
        },
    ],
)
(OUT / "README.md").write_text(
    f"""# EVT E3 贴片物料

本版 {len(populated)} 个贴装位号、{len(groups)} 类物料，全部正面。
计划 5 块 PCB，
其中 2 块相同配置贴片，净用 {2 * len(populated)} 颗；PD 净用 32 颗。

- `bom_smt_all.csv`：唯一推荐上传 BOM，包含全部 142 位号及 J1 自备排线座；与载框 positions_jlc.csv 配套。
- `bom_jlc_import.csv`：仅供查询的 141 位号库存料子集，不可代替完整上传 BOM。
- `customer_supplied.csv`：J1（TE 2492111-5），尚需工厂接收确认。
- `bom_frozen_2pcs.csv`：完整型号、两板净用量及供料状态。
- 平台损耗、实时可贴库存和最终齐料数量尚未确认，不能按净用量直接寄料。
- 220 kΩ / 470 kΩ 为独立调试备料，板上 RF1–RF16 仍全部为 100 kΩ。
- 新增型号已按器件资料选定；国内可贴状态需在实际订单中逐项匹配。

E3 新增 0603 绿色状态灯、复位保护、LED 脉冲限时和输入过压关断。
R18、R19 必须使用指定 0.1% 型号，不能按普通 1% 电阻替换。
U14 是 TPS259470L 的 RPW 封装，不能换用同系列其他功能后缀或普通 QFN-10 封装。

全部 BOM 表 Footprint 已转换为常用封装规格；不再导出 KiCad 库标识列。
主工程已使用短库名与有效关联，如 C:0402、R:0402、IC:TSSOP-14；平台上传表仅保留封装规格。
PD 与 IR LED 的 1206 是目录规格，实际焊盘、极性仍以专用封装和装配图为准，不能换成通用电阻焊盘。
以完整型号及 LCSC Part # 匹配，逐项复核厂家和封装，不允许自动替换指定器件。
2026-09-08：IR LED 采购编码改用 C19269752，同厂家、同型号和 1206 封装；用户提供国内有库存信息，订单锁料与损耗待确认。
来源：https://www.lcsc.com/product-detail/C19269752.html
原理图、PCB 和采购表均已同步为 C19269752。
J1 编码留空为有意设置，需作为自备料匹配并取得工厂接收确认。
""",
    encoding="utf-8",
)
print(len(populated), "SMT positions;", len(groups), "BOM groups")
