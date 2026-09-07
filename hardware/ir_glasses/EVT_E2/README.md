# IR Glasses EVT E2

本版将 16 颗感光器件改为 **Everlight PD15-21B/TR8 / C2921391**，完成专用两脚封装、原理图与布线更新。侧边和下沿名义框宽缩至 **3.0 mm**，双眼开孔保持不变，LED/PD 沿框边并排，LED 更靠近眼部开孔。全部 **122 颗器件在正面**，IMU 保持中央位置和轴向丝印。

批次为 **5 块 PCB，其中 2 块同配置贴装**。两板均使用 100 kΩ / 22 pF，TLV9064IPWR 和接口定义保持不变。工程资料已准备完成；国内实时库存、平台损耗、自备料入库、工厂 DFM 和物理光学测试尚未确认。

## 交付入口

| 文件 / 目录 | 用途 |
|---|---|
| `ir_glasses.kicad_pro`、`ir_glasses.kicad_sch`、`ir_glasses.kicad_pcb` | 可编辑 KiCad 成品工程；符号、封装及模型库随目录提供 |
| `schematic.pdf` | 控制、供电、左右传感及去耦原理图 |
| `pcb_3d.png`、`pcb_routed.png`、`pcb_back.png` | 三维、正反面走线预览 |
| `assembly_front.svg`、`assembly_back.svg`、`optical_assembly.pdf` | 装配位置；光学详图单独标出全部 PD/LED 位号、焊盘编号和 PD 阴极 |
| `mechanical_dimensions.pdf`、`mechanical_validation.json` | 成品尺寸及 3.0 mm 框宽记录 |
| `manufacturing/` | **成品外形版** Gerber、钻孔及贴片坐标，用于成品尺寸/工程对照 |
| `carrier/ir_glasses_carrier.kicad_pcb`、`carrier/manufacturing/` | **本批计划下单的带载框版本**及其 Gerber/钻孔 |
| `carrier/ir_glasses_carrier_fabrication.zip` | 可单独上传的载框加工 ZIP，只含 10 层 Gerber、Job 和 PTH/NPTH 钻孔 |
| `material_freeze/bom_smt_all_122.csv` | 完整 25 类、122 位号的贴片导入表；J1 编码留空，实际配单时指定自备物料 |
| `carrier/positions.csv` | 载框对应的 122 行正面贴装坐标；载框未平移元件，坐标与成品版一致 |
| `carrier/positions_jlc.csv` | 嘉立创字段格式的坐标表，单位 mm；与原生坐标逐项相同 |
| `carrier_design.md`、`carrier/carrier_review.svg` | 工艺边、连接桥、定位与最终铣断路径说明 |
| `fabrication_notes.md` | 发给工厂的制造、贴装及文件配套要求 |
| `material_freeze/`、`procurement/` | 完整采购主表、JLC 匹配、自备料及实时库存待核对清单 |
| `first_board_test.md`、`cost_estimate.md` | 首板测试记录模板及 5 裸板/2 贴装预算 |

不要混用成品版与载框版的外形、钻孔和 Gerber。每个制造目录均使用分离的 `*PTH.drl` 和 `*NPTH.drl`，两份一起导入；不导入审查目录中的旧参考钻孔文件。载框版用于本批加工；成品版定义去框后的轮廓。E1 及更早版本仅保留历史用途。

完整交付 ZIP 用于工程审阅，上传 PCB 制作时选择其中单独的载框加工 ZIP；`ir_glasses_unit_reference.zip` 是去框后的成品参考版本。

## 已验证的工程结果

- KiCad 10 原生检查：**ERC 0、DRC 0、未连接 0、原理图/PCB 一致性问题 0**，详见 `erc.json`、`drc.json`；报告记录了所用检查配置。载框检查见 `carrier/drc.json` 和 `carrier/carrier_validation.json`。
- 采购主表为 **25 类、每板 122 颗、两板净用 244 颗**。24 类 JLC 导入表涵盖每板 121 颗，另加 J1 自备 1 颗；两表合并才是完整贴装范围。
- PD1–PD16 均为两焊盘：**1=A 接 AGND，2=K 接对应 PD_IN**；32 个光学器件均满足至少 0.35 mm 的铜焊盘到成品板边目标。光学几何和网络检查见 `optical_validation.json`，不代表已通过光学性能测试。
- 成品板约 **132.305145 × 51.955477 mm**，载框约 **152.305 × 71.955 mm**。载框保持元件位号、位置、旋转角、网络和贴片坐标不变，增加的定位孔和 Mark 不进入 BOM。

工程 DRC 和坐标检查用于确认设计文件一致性，工厂仍需确认窄镜框支撑、钻孔/阻焊公差、光学器件贴装方向和分板工装。长 PD 输入线路的寄生、噪声及采样建立时间列入首板实测。

`validation.json` 汇总原理图、PCB、完整 BOM 和两份 CPL 的交叉检查；`SHA256SUMS.txt` 列出本次交付文件校验值。ZIP 只收录 E2 最终工程与报告，未收录中间布线文件或旧 PD 封装。打开可编辑 3D 视图需安装 KiCad 10 的标准模型库；PD、LED 和 J1 的项目模型已附带。

## 下单参数与当前待办

四层 FR-4、名义厚度 1.6 mm、沉金 ENIG、外层 1 oz/内层 0.5 oz、绿油白字、无阻抗控制、单面钢网和正面贴装。载框四周 8 mm 工艺边，至少 2 mm 铣槽间隔，8 个名义 3 mm 实心连接桥，4 个 Ø2 mm 非金属化定位孔和 3 个不对称正面 Mark。5 块均用治具支撑铣断去框，其中 2 块在贴装检验后分板，3 块裸板分板。

国内 24 个有编码页面本次均返回校验页，**未知库存不等于缺货**。J1 已选择 TE 2492111-5 自备，实际采购和工厂入库未执行；其余料只有在国内短缺得到确认后才启用同厂家、同完整 MPN 的自备方案。贴片损耗和最终供料量留待实际配单填写。

标准型预算约 **1,000–1,700 元**；若工厂确认可按经济型接单，条件预算约 **650–1,350 元**。正式报价、齐料、工厂 DFM、首板功能和光学实测分别记录状态，目前不标记为已生产放行。
