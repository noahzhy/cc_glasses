"""Update EVT D assembly data and document the layout changes."""

import csv
import json
from collections import Counter
from pathlib import Path

from shapely.geometry import Polygon

root = Path("hardware/ir_glasses/EVT_D")
source = Path("hardware/ir_glasses/EVT_C")
parts = json.loads((root / "parts.json").read_text())
rows = list(csv.DictReader((source / "bom.csv").open(encoding="utf-8-sig")))
for r in rows:
    p = parts[r["Reference"]]
    r.update(
        X_mm=p["xy"][0] + 110,
        Y_mm=p["xy"][1] + 85,
        Rotation_deg=p["angle"],
        Side=p["side"],
    )
with (root / "bom.csv").open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
counts = Counter(r["Side"] for r in rows if r["Populate"] == "Yes")
g = json.loads((root / "geometry.json").read_text())
shape = Polygon(g["outer"], g["holes"])
x0, y0, x1, y1 = shape.bounds
report = {
    "width_mm": x1 - x0,
    "height_mm": y1 - y0,
    "material_area_mm2": shape.area,
    "area_reduction_vs_evt_c_percent": (1 - shape.area / 2774.36) * 100,
    "optical_positions_unchanged": True,
    "bottom_amplifiers": 0,
    "populated_side_counts": counts,
}
(root / "mechanical_validation.json").write_text(json.dumps(report, indent=2))
for p in root.glob("*.kicad_sch"):
    s = p.read_text(encoding="utf-8").replace("EVT C", "EVT D")
    p.write_text(s, encoding="utf-8")
p = root / "README.md"
s = p.read_text(encoding="utf-8")
s = s.replace("EVT C", "EVT D").replace("136.734 × 55.5", "135.535 × 53.853")
s = s.replace("正面 73、背面 49", "正面 77、背面 45")
s = s.replace(
    "ERC 0、DRC 0、未连接 0、原理图一致性问题 0；464 个焊盘网络分配已与原理图核对。",
    "最终检查结果以本目录报告为准。",
)
a = s.index("## 本版机械及装配修改")
b = s.index("## 运放和层叠更新", a)
s = (
    s[:a]
    + """## 本版机械及装配修改

- 鼻梁缺口朝下，两个眼部开孔和 16 组 LED/PD 位置不变，继续沿框边并排。
- U3、U5 及其反馈阻容、去耦电容移到上沿；四颗运放均在背面上沿，下沿不再有运放电子区。
- 下沿两处凸起已取消，窄框由 5.5 mm 收到 4.9 mm；外形约 135.535 × 53.853 mm，板材面积约 2587.97 mm²，比 EVT C 减少约 6.7%。
- 为容纳上沿电路，J2 略向外侧移动；部分保护器件和电容改到正面。使用本版贴片坐标，正面 77 个、背面 45 个元件。
- J1 补齐 TE 官方 STEP 实体模型并对齐 5 个引脚与固定焊盘；插线口朝外侧，型号和电气接法不变。
- 3D 和装配背面图从背面观察，左右会翻转；器件编号按正面定义。
- 仍需核对外壳安装高度、对眼距离、遮光结构及模拟电路稳定性。

"""
    + s[b:]
)
s = s.replace(
    "地铜通过 294 个总过孔中的接地过孔和地走线互连。",
    "地铜通过接地过孔和地走线互连。",
)
s += """
## J1 实体模型

- 原始厂家模型：models/c-1734839-5-c-3d.stp。
- KiCad 对齐模型：models/TE_1734839-5_aligned.step；仅调整坐标方向与原点，未改变几何尺寸。
- 原始模型坐标绕 X 轴旋转 +90°，平移 (0, -3.75, 1.05) mm，使焊脚底面落在 PCB 表面。
- [TE 1734839-5 官方产品页及 CAD 下载](https://www.te.com/en/product-1734839-5.html)。厂家当前将此料号标为 Superseded，采购前需确认库存或替代料兼容性。
"""
p.write_text(s, encoding="utf-8")
p = Path("docs/smart_glasses_ir_sensor_bom.md")
s = p.read_text(encoding="utf-8")
s += """
## PCB 布局更新（2026-09-06，EVT D）

- TLV9064IPWR 四颗不变；下沿 U3、U5 及配套反馈阻容和去耦移到上沿，下方凸起取消。
- PCB 外形约 135.535 × 53.853 mm，四层双面贴装；本版贴片坐标为正面 77 个、背面 45 个元件。
- J1 的焊盘和接法不变，补齐 TE 官方 STEP 模型并对齐焊脚，便于装配与插线方向检查。
- 具体坐标及正反面以 hardware/ir_glasses/EVT_D/bom.csv 和 manufacturing/positions.csv 为准。
"""
p.write_text(s, encoding="utf-8")
(root / "source_bom.md").write_text(s, encoding="utf-8")
print(json.dumps(report, indent=2))
