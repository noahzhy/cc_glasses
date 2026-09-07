# IR Glasses EVT E1

本批物料料号已冻结：25 类、122 颗／板、全部正面；5 块裸板、2 块贴片。

**PD 尚未齐料，尚未生产放行。** 先看 [物料冻结记录](material_freeze/README.md) 和 [完整 BOM](material_freeze/bom_frozen_2pcs.csv)。

相对 EVT E：J1 更新为 TE 2492111-5 并修改焊盘及一段邻近 GND 布线；R1=2.67k；D17=PESD5V0S1BA,115；C28=47u/16V；其余补齐完整采购料号。布局、网络、单面贴装、IMU 中央位置不变。

- `ir_glasses.kicad_pro`：KiCad 工程。
- `schematic.pdf`：原理图预览。
- `manufacturing/`：Gerber、合并钻孔、原生贴片坐标。
- `drill_separated/`：分开的 PTH/NPTH 钻孔，为合并钻孔的备选交付格式，不重复导入。
- `validation.json`：原理图／PCB／BOM／坐标身份校验及规则检查。
- `material_freeze/`：25 类采购主表、24 类编码匹配表、J1 自备料表和供货说明。

贴片坐标使用 KiCad 原生角度；工厂应按引脚 1、极性和装配图校核物料库零度，不能盲用自动旋转。旧 EVT E 的制造包不与本版 BOM 混用。
