"""Build E3 assembly and procurement tables."""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("hardware/ir_glasses/EVT_E3")
OUT = ROOT / "material_freeze"
OUT.mkdir(exist_ok=True)
parts = json.loads((ROOT / "parts.json").read_text(encoding="utf-8"))
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
            "Footprint": part["footprint"],
            "X_mm": round(part["xy"][0] + 110, 6),
            "Y_mm": round(part["xy"][1] + 85, 6),
            "Rotation_deg": part["angle"],
            "Side": "front",
        }
    )
csv_file(ROOT / "bom.csv", rows)
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
            "Footprint": footprint,
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
        "Footprint": footprint.split(":")[1],
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

- `bom_smt_all.csv`：全部物料，包括 J1 自备排线座。
- `bom_jlc_import.csv`：带嘉立创编码的导入表。
- `customer_supplied.csv`：J1（TE 2492111-5），尚需工厂接收确认。
- `bom_frozen_2pcs.csv`：完整型号、两板净用量及供料状态。
- 平台损耗、实时可贴库存和最终齐料数量尚未确认，不能按净用量直接寄料。
- 220 kΩ / 470 kΩ 为独立调试备料，板上 RF1–RF16 仍全部为 100 kΩ。
- 新增型号已按器件资料选定；国内可贴状态需在实际订单中逐项匹配。

E3 新增 0603 绿色状态灯、复位保护、LED 脉冲限时和输入过压关断。
R18、R19 必须使用指定 0.1% 型号，不能按普通 1% 电阻替换。
U14 是 TPS259470L 的 RPW 封装，不能换用同系列其他功能后缀或普通 QFN-10 封装。
""",
    encoding="utf-8",
)
print(len(populated), "SMT positions;", len(groups), "BOM groups")
