# EVT E7

**状态：静态设计验收通过，首板验证待完成。** ERC、PCB DRC 均为 0 错误、0 警告；未连接及原理图与 PCB 一致性问题均为 0。尚未进行首板实测和板厂 DFM，不能据此宣布量产放行。

唯一编辑入口：`ir_glasses_EVT_E7.kicad_pro`。

- 一张 A1 原理图：`ir_glasses_EVT_E7.kicad_sch` / `schematic.pdf`。
- 一个 PCB：`ir_glasses_EVT_E7.kicad_pcb`，已包含 carrier，无独立裸板或 carrier 工程。
- 四层、1.6 mm，所有电气元器件统一正面；光学位置、接口和机械外形沿用 E6。
- 所有过孔孔径至少 0.20 mm、外径至少 0.40 mm，单边环宽至少 0.10 mm。
- 复核及精简：`review/report.md`；验收状态：`review/validation.json`。
- 分层及装配预览：`review/pcb_layers.pdf`；采购清单：`BOM.csv`；正面贴装坐标：`assembly_positions.csv`。
- 本目录不发布制造包。E6 历史制造文件不适用于 E7。

`tools/` 为此次整改的重建和检查脚本；日常直接编辑 KiCad 工程。重建脚本会覆盖设计，不能在人工修改后直接重跑。Python 工具不引入继承类；需要 KiCad 10 的 pcbnew Python，以及 Python 3 的 sexpdata、numpy、scipy、shapely、pymupdf。

固件接口和采集协议保持 F302 版本兼容，编号 E7 不意味着更改串口协议。有效采集前等待模拟偏置稳定，首板按 `first_board_tests.csv` 验证。

量产前复核见 `review/preproduction/report.md`。工程根目录 `BOM.csv` 为逐位号明细，`BOM_采购汇总.csv` 为 39 种料号的中文采购汇总，均包含简要参数及立创商城编码；单板共 153 个装配器件。实时库存、贴片库可用性及实物验证待确认。
