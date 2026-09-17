# IR Glasses EVT E6 P3

独立于 E4 的双 PD 同步采集硬件工程。每颗 LED 同时读取其镜圈上相邻的两颗 PD。两颗 TMUX1308 独立选择奇数与偶数 PD 的 TIA 输出，双通路缓冲/缩放后进入 AD7386 的同步采样核心。P3的U16/U17为TLV9062IDGKR，R11/R12=100Ω，C29/C30=330pF。典型模型验证及噪声预算见analog_validation_report.md。

**本版状态：设计与生产文件静态检查通过，首板电气、光学和固件运行验证待完成。** 本包不含可烧录固件；16 位是输出分辨率，不是已测有效精度。制造前须完成工厂 DFM、备料、平台 Pin1/极性与钢网确认。

## 交付入口

| 文件 | 用途 |
|---|---|
| `ir_glasses_EVT_E6.kicad_pro` | 主工程；同名 PCB、根原理图与子页均在本目录 |
| `libraries/`、`models/`、本地库表 | 自包含符号、封装及模型；U15 为按标称尺寸生成的简化外观模型 |
| `schematic.pdf` | 9 页电路图 |
| `mechanical_dimensions.pdf`、`optical_assembly.pdf` | 板框、正面装配、背面测试点、光学极性和坐标 |
| `populated_assembly.pdf`、`assembly_views/` | 贴好片的正视、斜视示意图，由 KiCad 从本版 PCB 渲染 |
| `bom.csv`、`bom_jlc.csv` | 167 个贴装器件的逐项/合并 BOM；未知供应商编号留空，按 MPN 采购 |
| `bom_EVT_E6.xlsx`、`procurement_gaps.csv` | 41 类器件、两板参考净用量、BOM 变更、库存来源与采购缺口 |
| `led_pd_mapping.pdf`、`led_pd_mapping.csv` | 16 组物理邻接映射 |
| `manufacturing_order.md`、`connector_and_power.md` | 下单参数、J1线序、排线方向及供电条件 |
| `carrier/manufacturing/positions_jlc.csv` | 167 个正面贴片坐标；工厂需复核平台零度约定 |
| `carrier/JLC_upload.zip` | 首次制造用载框 Gerber / PTH / NPTH 钻孔 |
| `ir_glasses_unit_reference.zip` | 成品裸板参考 CAM，不与载框层混用 |
| `analog_validation_report.md`、`analog_validation/` | P3运放替代、原厂模型仿真、建立时间与噪声预算 |
| `production_refinement_report.md` | P2修改记录、过压余量与待实测边界 |
| `firmware_contract.md` | 引脚、ADC 初始化/读出流水线、采样时序、数据约定和停机保护 |
| `design_notes.md`、`assembly_notes.md` | 电路计算、封装及装配要求 |
| `first_board_tests.csv`、`release_checklist.csv` | 待实测项目与设计检查证据 |

E4 的成品板框、安装几何和 32 个 LED/PD 的位置、方向、焊盘网络保持不变。4 层、1.6 mm，密集区最小线宽/间距0.10 mm，常规过孔0.45/0.20 mm，局部细间距过孔0.35/0.15 mm（外径/钻孔），须选择0.15 mm钻孔工艺并确认附加费用。In1为地铺铜、In2为3V3铺铜，内层兼有信号走线。实体器件全部正面贴装；12 个裸测试点移到背面，J2 为正面 Tag-Connect 裸焊盘。载框沿用 E4 工艺边与实心连接桥，必须用支撑治具铣断，禁止手折或 V-cut。

所选料号在各自查询时均有商城库存，本次未采购或锁库存；U14/J1尚未备料，其余自有库存待核对。J1已改为GUOCONN 0.5K-AS-5PWB-RW / C51901197，U14为TPS259470ARPWR / C3662799。U15查询时仅8件。新增U18 TPS2553DRVR提供持续限流，计算范围209～282mA；U19 TPS3702CX33DDCR控制U14使能实现过压关断与恢复，C38为22nF。正常输入要求3.3V±3%、正确极性；短路瞬态、浪涌和温升待实测；详见 connector_and_power.md。

## 固件注意事项

初始工作点为 16 时隙/帧、50 帧/秒、约 100 µs LED 请求脉冲。背景和亮灯分别由同一个 CS 下降沿同步采 A/B，AD7386 读出有一次转换延迟，必须用 pending 元数据配对，停止时补一次读出。

CPU 每次仅启动一个时隙的单次计数和非循环 DMA；不能让循环 PWM 在 CPU 停止后继续重复点灯。E4 单稳态仍负责卡高时的脉冲限时，不能限制持续重复触发。50 µs 光链路等待、100 µs 选通等待和帧率均须按首板实测确认。

## 复核与再生成

`tools/validate_design.py` 独立核对网络、光学坐标、E4 哈希和接口流水线模型；`validate_carrier.py` 比对载框；`validate_manufacturing.py` 从导出的 CAM 重新读回层、板框、钻孔、BOM/CPL 和本地库引用。报告由本版生成，没有继承 E4 的检查通过状态。

KiCad 检查版本为 10.0.6。`tools/export_manufacturing.py` 在 ERC、裸板/载框 DRC 未清零时拒绝导出。工具使用 Python 的 sexpdata / shapely / numpy / Pillow / reportlab / gerbonara 及 KiCad pcbnew；可用 `KICAD_CLI` 指定命令路径。修改设计后必须重新导出、检查并生成发布包。

原型板的准确信噪比、有效位数、满量程建立与饱和恢复、LED 电流及关断时间以首板测量为准，详见测试清单。
