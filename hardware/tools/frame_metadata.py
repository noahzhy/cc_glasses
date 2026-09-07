"""Update fabrication metadata for the double-sided revision."""

import csv
import json
from pathlib import Path

root = Path("hardware/ir_glasses/EVT_C")
parts = json.loads((root / "parts.json").read_text())
with (root / "bom.csv").open("w", newline="", encoding="utf-8-sig") as output:
    writer = csv.writer(output)
    writer.writerow(
        [
            "Reference",
            "Value",
            "Footprint",
            "Quantity",
            "Populate",
            "X_mm",
            "Y_mm",
            "Rotation_deg",
            "Side",
        ]
    )
    for ref, part in parts.items():
        populate = not (ref.startswith("TP") or ref in {"NT1", "J2"})
        writer.writerow(
            [
                ref,
                part["value"],
                part["footprint"],
                1,
                "Yes" if populate else "PCB pads only",
                part["xy"][0] + 110,
                part["xy"][1] + 85,
                part["angle"],
                part["side"],
            ]
        )
for path in root.glob("*.kicad_sch"):
    text = path.read_text(encoding="utf-8").replace(
        '(rev "EVT A")', '(rev "EVT C")'
    )
    path.write_text(text, encoding="utf-8")
text = Path("hardware/ir_glasses/EVT_A/README.md").read_text(encoding="utf-8")
text = text.replace("EVT A", "EVT C").replace("156 × 82 mm", "136.734 × 58 mm")
text = text.replace(
    "全部元件放在 F.Cu 面，光学器件正面朝向眼球；",
    "采用双面贴装，LED/PD 位于 F.Cu 朝眼面，主控与主要 IC 位于 B.Cu 背面；",
)
text = text.replace(
    "PD 输入网络总走线长度约 17.39–67.48 mm；",
    "PD 输入网络总走线长度见 validation.json；",
)
text += """

## 本版机械及装配修改

- 以用户最新的 `mechanical_reference.png` 为方向基准：上沿在图上方，鼻梁缺口朝下。修正了旧版导入 SVG 时的 Y 轴方向，眼部开孔尺寸与水平间距不变。
- 取消贯穿下沿的矩形电子区，只保留两处运放所需的局部加宽；外廓约 136.734 × 58 mm，扣除开孔后的板材面积约 2868.71 mm²，比 EVT B 减少约 51%。
- 16 组 LED/PD 沿镜框切向并排、同角度放置；两者中心均距开孔边缘约 2.4 mm，组内中心间距约 5 mm。它们处于同一圈，不再按内外两圈排列。测量见 `optical_placement.csv`。
- 控制器、驱动、运放、MUX、IMU、FFC 及 SWD 位于背面；光学器件、反馈阻容及部分去耦位于正面。BOM 的 Side 和 KiCad 原生贴片坐标均区分正反面，不能使用 EVT A/B 的单面贴片资料。
- 3D 顶视图显示朝眼面；背面图为从背面观察，左右视觉上会翻转。器件编号始终按顶视图定义。
- 两面安装高度、镜框内腔、鼻梁空间、光学隔离及对眼距离仍需在样机和外壳中核对；本版尚未做佩戴验证。
"""
(root / "README.md").write_text(text, encoding="utf-8")
