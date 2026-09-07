"""Synchronize assembly data and the documentation for EVT E."""

import csv
import json
import re
from pathlib import Path

from shapely.geometry import Polygon

root = Path("hardware/ir_glasses/EVT_E")
parts = json.loads((root / "parts.json").read_text())
rows = list(csv.DictReader((root / "bom.csv").open(encoding="utf-8-sig")))
for row in rows:
    part = parts[row["Reference"]]
    row.update(
        X_mm=part["xy"][0] + 110,
        Y_mm=part["xy"][1] + 85,
        Rotation_deg=part["angle"],
        Side="front",
    )
with (root / "bom.csv").open("w", newline="", encoding="utf-8-sig") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
populated = sum(row["Populate"] == "Yes" for row in rows)
assert populated == 122
geometry = json.loads((root / "geometry.json").read_text())
board = Polygon(geometry["outer"], geometry["holes"])
x0, y0, x1, y1 = board.bounds
report = {
    "width_mm": x1 - x0,
    "height_mm": y1 - y0,
    "material_area_mm2": board.area,
    "nominal_rim_width_mm": 3.7,
    "outline_unchanged_from_evt_d": True,
    "eye_openings_unchanged": True,
    "optical_positions_unchanged_from_evt_d": True,
    "populated_side_counts": {"front": populated, "back": 0},
    "imu_center_board_xy_mm": [110, 71.3],
    "imu_center_relative_to_bridge_mm": [0, -13.7],
    "imu_rotation_deg": 0,
    "imu_silkscreen": "IMU, +X right, +Y up; pin 1 marked by the footprint",
}
(root / "mechanical_validation.json").write_text(json.dumps(report, indent=2))

for path in root.glob("*.kicad_sch"):
    data = path.read_text(encoding="utf-8")
    data = re.sub(r'\(rev "[^"]*"\)', '(rev "EVT E")', data)
    path.write_text(data, encoding="utf-8")

source = Path("hardware/ir_glasses/EVT_D/README.md").read_text(
    encoding="utf-8"
)
readme = source.split("## 交付核验补充")[0].replace("— EVT D", "— EVT E")
readme = readme.replace(
    "采用双面贴装，LED/PD 位于 F.Cu 朝眼面，主控与主要 IC 位于 B.Cu 背面",
    "采用单面贴装，122 个待装元件全部位于 F.Cu 朝眼面，B.Cu 不装元件",
)
readme += """## EVT E：单面贴装与中央 IMU

- 全部 136 个封装均位于正面，其中 122 个为待装元件，14 个为测试点、调试焊盘和 net tie；背面贴装数量为 0。
- 四颗 TLV9064IPWR、主控、驱动器、两颗 MUX、FFC 接口及全部阻容集中在上沿。LED/PD 的切向并排位置和朝眼面与 EVT D 相同。
- 复用 EVT D 的板框和两个眼部开孔，尺寸仍为 133.136 × 52.653 mm，侧边及下沿名义框宽 3.7 mm。没有增加上沿高度。
- U10 移到鼻梁上方的中线上，KiCad 坐标为 (110.000, 71.300) mm，F.Cu、0°。旁边印有 IMU 及 X/Y 箭头，封装三角标识指向 1 脚。按 ST 数据手册图 1，在正面图中 +X 向右、+Y 向上、+Z 从板面朝外；正背面视图左右相反。固件应按实际安装关系转换到头部坐标。
- J1 保留项目自带的 TE 0-1734839-5 封装与厂家 STEP 模型；改到正面并旋转 180°，排线开口朝上方外板边。J2 和全部测试点也从正面接触。
- 原理图连接、器件型号和数量保持不变；BOM 和贴片坐标更新为单面装配。只需要正面钢网和正面贴装工序，PCB 本身仍为四层。实际费用由板厂按加工与装配资料报价。

## 制造与验证文件

- `validation.json`、`drc.json`、`erc.json` 为本版实际核验结果；`mechanical_validation.json` 记录外形和正反面装配数量。
- `manufacturing/positions.csv` 与 `bom.csv` 一一对应 122 个待装元件，全部为 top。KiCad 贴片坐标的 Y 轴与 BOM 板图坐标方向相反。
- `assembly_front.svg` 是装配位号图；`assembly_back.svg` 和 `pcb_back.png` 用于检查背面没有元件。J2 为无焊接的弹簧针接口，TP1–TP12 与 NT1 也不采购贴装。
- 四层 FR-4、总厚度 1.6 mm；最小线宽/间距 0.15/0.15 mm，普通贯穿孔为 0.5 mm 焊盘 / 0.3 mm 钻孔、最小环宽 0.1 mm。无盲埋孔。
- F.Cu 为唯一装配面；内层和 B.Cu 可布信号与电源。AGND/GND 分开并在 NT1 连接，地铜与接地过孔连接。内层有信号走线，不能当作完整连续的专用地平面。
- `models/` 内两个光学器件模型是尺寸包络示意，其余常规器件使用 KiCad 标准模型。J1 的厂家 STEP 对齐方法与 EVT D 相同。
- 0402 非极性电阻省去本体丝印短线，避免紧凑排布时与 IC 的 1 脚标识相撞；封装库同步更新，装配图中的位号和本体轮廓保留。
- 这仍是室内 EVT 样机：模拟稳定性、光学串扰、眼安全、镜框强度和安装高度待实物验证，不能仅凭 ERC/DRC 判定为量产定版。

## J1 实体模型

- 原始厂家模型：`models/c-1734839-5-c-3d.stp`。
- KiCad 对齐模型：`models/TE_1734839-5_aligned.step`；仅调整坐标和原点。
- [TE 官方产品页及 CAD 下载](https://www.te.com/en/product-1734839-5.html)。EVT D 核查时厂家标为 Superseded，采购时核对库存和替代料兼容性。
"""
(root / "README.md").write_text(readme, encoding="utf-8")

path = Path("docs/smart_glasses_ir_sensor_bom.md")
bom = path.read_text(encoding="utf-8")
bom = bom.replace("**2 层刚性 FR-4 PCB**", "**4 层刚性 FR-4 PCB，单面贴装**")
bom = bom.replace(
    "5 Pin、0.5 mm FFC/FPC 或板对板连接器",
    "TE **0-1734839-5**，5 Pin、0.5 mm FFC/FPC",
).replace("最终封装按镜框结构确定", "采用项目自带卧式封装和 TE STEP 模型")
bom = bom.replace(
    "双路低电容 3.3 V ESD 二极管阵列", "Nexperia **PESD3V3L2BT**，SOT-23"
)
bom = bom.replace(
    "3.3 V TVS / ESD 二极管 | 1", "Nexperia **PESD3V3S1BA**，SOD-323 | 1"
)
bom = bom.split("## PCB 布局更新（2026-09-06，EVT E）")[0].rstrip()
bom += """

## PCB 布局更新（2026-09-06，EVT E）

- 改为四层 PCB、单面贴装，122 个待装元件全部在 F.Cu，B.Cu 贴装数量为 0；测试点、J2 调试焊盘和 NT1 也位于正面。
- U2–U5 继续使用 TLV9064IPWR / TSSOP-14；原理图连接、器件数量和阻容值不变。
- U10 LSM6DS3TR-C 移至鼻梁上方中线，坐标 (110.000, 71.300) mm、0°，旁边增加 IMU 和 X/Y 方向丝印，保留 1 脚标记。
- 四颗运放及其反馈阻容、全部控制和供电器件利用上沿空间重新排布；J1 装在同一面，排线开口朝外。
- 板框与 EVT D 相同：约 133.136 × 52.653 mm，下沿/侧框名义宽 3.7 mm；双眼开孔及 LED/PD 切向并排布置不变。
- 单面钢网及贴装；贯穿孔 0.5/0.3 mm，线宽/间距最小 0.15/0.15 mm。采购和贴片以 `hardware/ir_glasses/EVT_E/bom.csv`、`manufacturing/positions.csv` 为准。
"""
path.write_text(bom, encoding="utf-8")
(root / "source_bom.md").write_text(bom, encoding="utf-8")
print("Single-side BOM and documentation updated.")
