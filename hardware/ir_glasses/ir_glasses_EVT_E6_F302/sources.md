# 资料与证据索引

- [STM32F302xB/C 数据手册 DS9911](https://www.st.com/resource/en/datasheet/stm32f302cc.pdf)：具体型号、LQFP48引脚、ADC电气参数及复用功能。
- [RM0365](https://www.st.com/resource/en/reference_manual/dm00094349.pdf)：双ADC、触发、DMA、定时器和启动配置。
- [ES0231](https://www.st.com/resource/en/errata_sheet/es0231-stm32f302xbc-device-limitations-stmicroelectronics.pdf)：适用性见 errata_review.md。
- [AN2606](https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf)：F302xB/C 系统Bootloader及Pattern 2。
- [TI TMUX1308](https://www.ti.com/lit/gpn/tmux1308)：地址/低有效使能及模拟开关规格。
- [TI TLV906x](https://www.ti.com/lit/ds/symlink/tlv9064.pdf)：单位增益驱动、噪声及电流规格；模拟文件及厂商模型见 analog_validation。
- [ST HAL ADC定义](https://github.com/STMicroelectronics/stm32f3xx-hal-driver/blob/master/Inc/stm32f3xx_hal_adc_ex.h)：常量交叉核查，不是本项目固件实现。
- evidence/stock/*.json：LCSC同日公开页面快照，含来源、UTC查询时间、型号、库存、起订数量、美元阶梯价。

所有静态检查只针对本次输出的文件。没有代工厂DFM结论、采购订单、烧录固件或首板测量结果。
