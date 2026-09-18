# F302 R2 设计说明

本版从E6 P3独立派生。MCU更换为双ADC的STM32F302CCT6，删除AD7386及专用参考、分压和第二级缓冲。保留16路TIA、奇偶PD选择开关、单颗TLV9062双通道单位增益缓冲，以及UART、SWD、IMU、LED驱动和硬件限时关断。

运行UART与ROM Bootloader共用PA9/PA10的USART1，释放PA2/PA3。外部J1线序和40字节数据布局不变；UART使用中断收发，避免占用定时采样使用的DMA通道。

信号链：PD → 独立TIA → TMUX1308 → TLV9062 → 100Ω → ADC输入节点（330pF至地）。ADC1/ADC2的PA0/PA4由共同定时事件同时获取，读取顺序不代表采样先后。TIA以原VREF_1V65为偏置；该偏置仍用于模拟前端，不能与ADC的VDDA参考混淆。

每帧16个LED时隙，默认30fps、可选24fps。100µs是发光请求宽度；实际LED电流脉冲还受到保留的单稳态窗口限制，应实测其最短脉冲在电压、温度和RC容差下覆盖整个亮态ADC获取窗口。按请求计算，30fps总发光占空比4.8%、单颗0.30%；24fps分别3.84%、0.24%。降低帧率不增加脉宽。

输入保护链路保持J1→TPS2553→TPS259470A→3V3，3V3_A继续使用模拟滤波支路。原P3的约150mA工作峰值预算是验收预算，不是F302新板的实测功耗。19个TLV906x放大器通道（16路TIA、偏置缓冲、2路ADC缓冲）仅典型静态电流约10.2mA；还需加MCU、两个ADC、IMU、LED驱动、LED峰值及其他负载。不能凭该部分电流推断整板功耗已通过。首板验证启动、最低供电和最高温度下工作电流、参考纹波及保护动作，确认F302替换后的余量。

关于动态建立和噪声：0.5LSB目标指相对于校准后稳态值的动态残差，不能替代失调、增益和噪声预算。见analog_validation_report.md，模型通过不代替首板测试。

电气连接由本机KiCad原理图网表和PCB比较；32个光学器件坐标/角度与P3逐项比较；完整48脚MCU分配在evidence/change_manifest.json。ERC、DRC、原理图一致性、装配孔距、采购数据和首板测试分别记录，不能以某一项通过替代其他项目。

器件资料：[STM32F302xB/C](https://www.st.com/resource/en/datasheet/stm32f302cc.pdf)、[RM0365](https://www.st.com/resource/en/reference_manual/dm00094349.pdf)、[ES0231](https://www.st.com/resource/en/errata_sheet/es0231-stm32f302xbc-device-limitations-stmicroelectronics.pdf)、[TLV906x](https://www.ti.com/lit/ds/symlink/tlv9064.pdf)。
