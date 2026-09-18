# EVT E6 F302 R2

**设计文件检查通过；用于首板打样与贴片评审。量产放行仍待首板实测及工厂DFM确认。** 本版从当前E6 P3独立派生，原工程及生产包未改动。背面及载框标注F302 R2。

STM32F302CCT6＋两颗TMUX1308＋一颗TLV9062，删除AD7386、2/3分压及第二级缓冲。16颗LED各采同侧相邻双PD，奇数PD进入ADC1/PA0，偶数PD进入ADC2/PA4。12位同步背景/亮灯采样，默认30fps，可选24fps。UART改为PA9/PA10 USART1，外部J1线序和40字节样本布局保留。交付接口文档，不含可烧录固件。

## 交付入口

| 文件 | 用途 |
|---|---|
| ir_glasses_EVT_E6_F302.kicad_pro / .kicad_sch / .kicad_pcb | 独立KiCad工程，含本地库和模型 |
| schematic.pdf | 9页原理图 |
| populated_assembly.pdf / populated_top.png / populated_oblique.png | 4页装配示意、LED–PD映射、J1排线方向及实际PCB模型渲染 |
| bom_EVT_E6_F302.xlsx / bom.csv / bom_jlc.csv | 155个贴装器件、39个SKU，库存及同源阶梯报价比较 |
| carrier/JLC_upload.zip | **制造用载框Gerber/钻孔** |
| carrier/manufacturing/positions_jlc.csv | 与载框配套的正面贴片坐标 |
| F302_R2_SMT_package.zip | 载框CAM、BOM、CPL、装配说明及首板清单的汇总包 |
| unit_reference.zip / manufacturing | 裸板参考CAM；不能与载框文件混搭 |
| firmware_contract.md / firmware_interface.h / mcu_pin_map.csv | 初始化、定时器/DMA、40字节协议0xE7及完整48脚连接 |
| analog_validation_report.md / analog_validation | 新缓冲与ADC负载模型、日志及限制 |
| verification_report.md / release_manifest.json | 发布检查结论及文件哈希 |
| first_board_tests.csv | 21项测试，全部待实测 |

## 已完成检查

KiCad 10.0.6启用的ERC检查零问题；主板/载框DRC零违规、零未连接，主板原理图一致性零问题。DRC没有忽略项或排除项；ERC默认关闭的4类检查在检查报告中明列。

32个光学器件的坐标与方向、16组相邻PD映射和板框均与当前P3基准一致。155个BOM/CPL位号、四层CAM、钻孔、载框、封装库及模型路径完成交叉核验。最终报告是根目录和carrier目录的检查JSON；evidence中的施工中间报告不是发布凭据。

## 采购与验证边界

2026-09-18查询：C262946主控库存4件，10板净用量缺6件，未计贴片损耗；不得自动换MCU。其余本版SKU已取得公开库存和报价快照。

成本表使用LCSC公开**美元**同数量阶梯报价和每板净用量，非国内人民币贴片结算价。10板情形新BOM约15.6398 USD/板，旧P3约77.2564 USD/板；差额主要受AD7386当前公开单价影响。不能据此承诺实际降本金额，采购前需核对国内报价、MOQ余料、损耗、运费、税费与贴片费。

稳定性/建立时间是TI典型模型及参数敏感度分析，未覆盖全工艺角和整板噪声。同步采样、30/24fps、串扰、饱和恢复、LED电流、输入保护及CPU停止后的硬件关断均待首板实测。工厂仍需确认0.15mm钻孔、盖油、钢网、Pin1与平台旋转修正、铣断载框工艺。

R2复核及剩余放行门槛见preproduction_audit.md；已确认最小眼距25mm，温度与首批数量待确定。
