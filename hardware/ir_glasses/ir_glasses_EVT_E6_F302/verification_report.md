# EVT E6 F302 R2 发布检查

日期：2026-09-18。结论：**设计文件检查通过；首板性能未验收，不能视为量产批准。**

| 检查 | 结果 | 证据 |
|---|---|---|
| 原理图ERC | 启用项0违规；全严重级别报告亦0 | erc.json、evidence/erc_all.json |
| 主板DRC | 0违规、0未连接、0原理图一致性问题 | drc.json |
| 载框DRC | 0违规、0未连接 | carrier/drc.json |
| 设计与P3基准 | 16项检查通过，32个光学坐标/方向及16组映射一致 | design_validation.json |
| 载框保留/电气一致性 | 16149项检查通过，单位板铜线、过孔、元件完整保留 | carrier_validation.json |
| CAM/BOM/CPL/本地库 | 1354项检查通过，155个贴装位号，四层铜 | manufacturing_validation.json |
| 钻孔 | 主板540孔，载框544孔；坐标/直径与PCB一致 | manufacturing_validation.json |
| 贴片近孔检查 | 537个过孔；孔边到外层贴片/测试焊盘最小0.100mm | via_assembly_validation.json |
| BOM/库存/价格公式 | 39个SKU，全部型号匹配快照；公式无错误且合计独立复算一致 | bom_validation.json |
| C接口 | C11编译与40字节结构断言通过；不是MCU固件测试 | firmware_interface.h |
| 视觉复核 | 9页原理图、4页装配PDF及BOM三页预览检查 | schematic.pdf、populated_assembly.pdf、outputs/f302_bom |
| 模拟前端 | 64组环路敏感度、4组阶跃、2组采样冲击及噪声模型完成 | analog_validation/results.json |

ERC报告列出的默认关闭项为single_global_label、four_way_junction、simulation_model_issue、footprint_filter；没有把这些项宣称为通过。封装另由PCB一致性、本地库和CAM检查覆盖；原理图不是SPICE仿真源，模拟验证使用独立保存的模型网表。DRC ignored_checks为空，工程DRC排除表为空。

本轮直接核验的光学/机械基准是**当前P3**。当前工作目录没有可供重新比较的E4工程，因此没有宣称本轮完成了E4到F302的独立坐标复核。P3源文件和生产包的哈希保持不变。

## R2新增复核

C11改为10nF，C40改为0603/10µF并移近MCU。重布受影响SWCLK，重新导出并校验载框和CAM。时序约定补充CCR非预装载、DMA比较请求、故障恢复强制OCREF归零；timing_validation.json的理想事件模型通过，包含预装载/残留状态反例及C11接口编译，不等同实机固件验证。

原生报告通过native_check_provenance.json绑定当前原理图、主板/载框、工程配置、本地库、parts和网表；导出/打包拒绝改动或缺失输入，拒绝路径已测试。用户确认最小眼距25mm，温度与首批数量待定；新增光学暴露、电源时序、故障恢复测试，详见preproduction_audit.md。

## 模拟结果的适用范围

12位、3.3V时0.5LSB约402.8µV。模型最低相位裕量55.39°，阶跃最长动态建立约0.929µs，采样冲击恢复约0.427µs；配置获取期5.125µs。缓冲＋RC积分噪声约26.08µV RMS。以上不包含完整PD/TIA/MUX/VDDA/实际ADC噪声，也不证明全温全批次精度；整机噪声验收门槛尚需首板定义。

## 待完成项目

first_board_tests.csv的21项全部PENDING，未填写任何虚构测量值。重点包括双ADC窗口对齐、ADC脚建立、背景扣除、通道串扰、输入范围/饱和恢复、HSI帧率误差、30/24fps持续配对、复位灭灯、DMA故障与CPU停止后的关断、LED电流和单稳态最短窗口、电源/连接器压降及温升。

主控库存快照4件；10板净缺6件。未下单、未送厂、未生成可烧录固件。工厂DFM、贴片平台角度、钢网、X-ray和载框铣断治具确认未完成。

生产使用carrier/JLC_upload.zip及对应positions_jlc.csv、根目录bom_jlc.csv。unit_reference.zip只作裸板参考。全部发布文件由release_manifest.json记录SHA-256。

补充制造复核：可见板上字高统一到1mm，笔画至少0.1mm，启用0.15mm丝印间距检查并修正板边及局部标记间距；铜层、焊盘和光学坐标未移动。fabrication_audit.json列出小孔和线宽几何核验；工厂确认请求见factory_review_request.md，尚未发送。
