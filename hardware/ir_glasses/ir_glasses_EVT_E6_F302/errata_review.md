# STM32F302CCT6 勘误适用性

依据 [ST ES0231 Rev 6](https://www.st.com/resource/en/errata_sheet/es0231-stm32f302xbc-device-limitations-stmicroelectronics.pdf)。这是设计/固件约束审核，尚未验证实物修订号或固件执行。

| 条目 | 本版约束 |
|---|---|
| 2.1 / 内核 | 不使用手写 SP 加载；采集 ISR 不做浮点除法/开方。引入 RTOS/汇编时重新审核。 |
| 2.2 / 系统 | 使用 SWD；采集期不进 Stop/Standby；不依赖可被复位清除的配置锁保护 LED。 |
| 2.3.1–3 | 规则同步、单次触发；不使用交错、注入队列或自动延迟。 |
| 2.3.4 | ADC 寄存器逐个 volatile 访问，禁止批量寄存器拷贝；DMA 单次读32位 CDR。 |
| 2.3.5 | 校准结束后等待1µs再 ADEN，检查 ADRDY，带超时。 |
| 2.3.6 | 不能仅依赖 OVR；DMA及时读出，核对两次传输数量与期限。 |
| 2.3.7–8 | 仅单端输入；记录日期码，VREFINT供电估算须与电表比对。 |
| 2.4 / SPI | 本版不用硬件 SPI，TLC59283 用 GPIO。 |
| 2.5 / I2C | 仅7位地址主模式；IMU先用100kHz，I2C内核时钟48MHz；不在事务中休眠。孤立 BERR 清除后按 ST 规定继续处理，真实超时另行恢复。 |
| 2.6 / USART | 8N1、无流控/Smartcard/Break；关 TE 前等 TC；协议层须能检出损坏数据。 |
| 2.7–10 | 不用 I2S、BRK2、GPIO锁及片内COMP；LED关断依靠外部硬件。 |

首板记录 DBGMCU_IDCODE、芯片日期码；完成 DMA 负载、UART 干扰和电源估算测试。更改上述模式需重新审核对应勘误。
