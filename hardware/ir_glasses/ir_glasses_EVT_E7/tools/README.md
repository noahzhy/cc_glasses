# E7 检查工具

日常编辑直接打开根目录 `ir_glasses_EVT_E7.kicad_pro`，不需要执行脚本。以下检查在 E7 目录执行；`kicad-cli` 和 pcbnew 使用 KiCad 10，几何检查使用 Python 3、sexpdata、numpy、scipy、shapely。

1. 导出当前网表，并运行原生 ERC、DRC：

```powershell
kicad-cli sch export netlist --format kicadxml -o netlist.xml ir_glasses_EVT_E7.kicad_sch
kicad-cli sch erc --format json --severity-all -o erc.json ir_glasses_EVT_E7.kicad_sch
kicad-cli pcb drc --refill-zones --save-board --schematic-parity --severity-all --format json -o drc.json ir_glasses_EVT_E7.kicad_pcb
```

2. 用 KiCad 自带 Python 执行 `audit_board.py`、`export_geometry.py`；用普通 Python 执行 `check_geometry.py`、`validate_e7.py`。后者生成 BOM、引脚对比和验收 JSON；未通过时返回失败。
3. `circuit_calculations.py` 重算静态限流、阈值和简化 TIA 模型。该模型不能替代首板测试。
4. `redraw_schematic.py` 从归档基线重建 A1 原理图，会覆盖当前图纸；人工修改后不要直接重跑。归档只用于追溯，不是另一个活动工程。

本地封装、符号和模型已随工程提供。检查使用 E6 历史基线进行器件、连接、机械及制造规则对比，E6 文件不会被修改。

`export_bom.py` 为根目录 BOM 明细补充参数，并生成 `BOM_采购汇总.csv`；`validate_e7.py` 会自动调用它。参数依据保存在 `review/bom_catalog.json`，其中时间为供应商资料归档时间，不代表实时库存。`check_bom.py` 核对 BOM、最新导出网表、贴装坐标及本轮 ERC/DRC，输出 `review/preproduction/result.json`；运行前需更新该目录中的网表与检查报告，并运行 `audit_board.py` 刷新 PCB 位置数据。

实际过孔钻径由 `audit_board.py` 检查，不能只检查默认过孔设置。验收同时核对最小孔径 0.20 mm、单边环宽 0.10 mm、仅通孔以及最多四层。`check_reference.py` 检查 In1 数字走线与模拟铜的投影间隔不小于 0.30 mm，`check_geometry.py` 检查地铜连通性。
