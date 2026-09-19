# EVT E7 固件接口约定

这是接口与初始化要求，不是可烧录固件。硬件使用 STM32F302CCT6，不能以单 ADC 的 F302 容量型号代换。

## 采集路径

16 路独立 TIA 持续工作。U7 选择奇数 PD，U8 选择偶数 PD；两者独立寻址。U16 TLV9062 的两个单位增益通道分别驱动 100 Ω 串联电阻及 ADC 端 330 pF 电容。PA0（10 脚）接 ADC1_IN1，PA4（14 脚）接 ADC2_IN1。参考是 VDDA/3V3（与 VDD 同源；前端仍用 3V3_A），VREFINT 仅用于估算 VDDA。输入码保留 0～4095，不先降为 8 位。

`led_pd_mapping.csv` 是 16 个时隙的固定相邻 PD 映射。A 始终表示奇数 PD，B 始终表示偶数 PD。单 PD 模式仍执行双 ADC 转换，只用 valid_mask 屏蔽不需要的数据。LED 必须 one-hot；不支持通过协议任意修改光学邻接关系。

## MCU 引脚和启动

当前完整 48 脚连接见 `mcu_pin_map.csv`，必须与原理图一起审核。USART1：PA9/引脚30为TX、PA10/引脚31为RX，AF7；运行通信与Bootloader共用该端口，PA2/PA3不连接。I2C1：PB6/PB7，AF4；SWD：PA13/PA14，AF0。LED_ENABLE 使用 PB15/TIM1_CH3N，**AF4**，不能沿用 C031 的 AF 编号。TLC59283 的 PB10/PB11/PB1 作为 GPIO 时钟、数据、锁存。MUX 地址和 EN 使用普通 GPIO。MUX_EN_N=1 断开两颗开关；更新 A/B 地址后拉低使能，再开始100µs建立等待。

BOOT0 由 R5 下拉，正常从 Flash 启动。PA9/PA10 的系统 Bootloader UART 测试点保留，并与J1运行UART共网；AN2606 对应 Pattern 2：BOOT0=1 且选项位 nBOOT1=1 后复位进入系统存储器；出厂先经 SWD 读取并记录选项字节，正常运行保持 BOOT0=0。R5 的 BOOT0 端供治具临时拉高；不能将其误认成 PA14/SWCLK。正常调试优先 SWD。复位阶段 LED 请求引脚不得产生高脉冲。先设置 GPIO 输出寄存器为灭灯状态，再切换模式和复用功能。未连接GPIO初始化为模拟模式，避免浮空输入。

## 上电偏置建立

R2/R3/C1 的标称时间常数约为 5 ms。电源稳定后等待至少 50 ms，再开始有效采集；等待期间 LED_ENABLE 保持低，MUX 保持禁用。首板以最坏温度和供电波形确认偏置已达到采样误差要求，必要时延长等待。此要求不改变帧内采样时序或通信协议。

## 双 ADC 初始化

1. HSI/2 经 PLL×12 得到48 MHz，AHB不分频；APB1分频2、APB2不分频，TIM2和TIM1的实际定时器时钟均为48 MHz。按供电和频率设置Flash等待周期后再切换时钟。ADC12 使用 HCLK/4，即12 MHz（CKMODE=3）。两个ADC的时钟、分辨率、采样周期及规则序列长度一致。帧率为标称值，首板量测HSI误差；若要求24fps模式的实际最低值也不低于24，必须校准时钟并相应修正调度分频。
2. 按 RM0365 规定的 ADVREGEN 状态转换分别启用 ADC1、ADC2 的内部稳压器，等待至少 20 µs；不要照搬其他 STM32 系列的深度掉电位初始化。
3. 在禁用状态分别执行单端校准，等待 ADCAL 清零，再等待至少4个ADC周期（12MHz下至少0.334µs，固件取1µs），之后才能设置ADEN。分别启用并等待 ADRDY。
4. ADC1 为主、ADC2 为从，MULTI=6（dual regular simultaneous）；MDMA=2（12/10 位 DMA 格式）。每路 SQ1=IN1、序列长度 1、12 位、右对齐、SMP=61.5 周期。禁止连续转换、自动延迟、自动注入和交错模式。
5. ADC1 EXTSEL=9（TIM1_TRGO），仅上升沿触发。ADC2 通过双模式跟随主 ADC，不配置另一个独立触发序列。
6. DMA1 Channel1 从 ADC12 公共 CDR 以 32 位宽度读出：低 16 位 ADC1，高 16 位 ADC2；每时隙 CNDTR=2，依次为背景与亮灯。内存递增、正常模式、ADC公共CCR.DMACFG=0，禁止循环 DMA；两次数据都到齐才发布一组结果。DMA完成后ADC请求停止；下一时隙在触发关闭、ADSTART清零的状态重新装载DMA并按RM0365重新使能多ADC DMA请求，不能只写CNDTR就假定ADC端已重新准备好。

采样获取期为 61.5/12 MHz=5.125 µs，转换总计 (61.5+12.5)/12 MHz=6.1667 µs，另计外部触发同步延迟。两个采样保持窗口由双模式硬件对齐；DMA 串行搬运不改变采样同时性。禁止以先启动 ADC1、再启动 ADC2 的软件调用替代双模式。

## 单时隙时序

|相对时间|动作|
|---:|---|
|0 µs|灭灯，关闭 MUX，更新 A/B 地址，启用 MUX|
|100 µs|TIM1_TRGO 上升沿，双路背景采样|
|200 µs|LED_ENABLE 有效，点亮预先锁存的唯一 LED|
|250 µs|TIM1_TRGO 上升沿，双路亮灯采样|
|300 µs|LED_ENABLE 无效|
|1000 µs|TIM1 单次计数结束|

触发边沿不是 ADC 获取期末尾的保持时刻。数据字段 light_time_us 定义为亮灯采样**触发时刻**，沿用 E6 已定义的协议版本；需要亚微秒保持时刻时，在上位机结合 ADC 时钟及触发同步延迟解释，不伪称实测采样时刻。

TIM1 计数 1 MHz（PSC=47），ARR=999，OPM=1。CH4 内部 OC4REF 为 toggle，CCR4 初值100，DMA1 Channel4 依次写110、250、260、65535；TRGO=MMS 111（OC4REF），因此仅100、250上升沿触发。CH3N/PB15 为发光请求，CCR3 初值200，DMA1 Channel6 写300、65535。仅启用CH3N（CC3E=0、CC3NE=1），CC3NP=0，此时PB15跟随OC3REF；不要套用同时启用CH3/CH3N时的互补极性。OIS3N=0、OSSI=1、OSSR=1、DTG=0；故障首先撤销MOE，保持PB15低，再退出复用为输出低。首板用示波器验证该组合。

**必需的寄存器约束：** CH3/CH4为输出比较，OC3PE=0、OC4PE=0，使DMA写CCR立即生效；CCDS=0使DMA由比较事件触发；RCR=0、CCPC=0，禁止控制位等待COM事件。ADC DMA为32位外设/内存宽度、CNDTR=2；TIM1 CCR4和CCR3 DMA均为16位外设/内存宽度、内存递增、正常模式，CNDTR分别为4和2，目标分别为CCR4/CCR3，不能用循环DMA。若开启CCR预装载，110/250/260等比较点不会按本约定生效。

每次启动（包括故障恢复）依次执行：PB15保持GPIO输出低；禁用TIM1计数、MOE、比较DMA和ADC外触发；停止ADC规则转换并确认ADSTART清零；将OC3/OC4强制为inactive，使两个OCREF明确归零；设置PSC/ARR/RCR、CNT=0及CCR初值，产生UG加载时基并清除标志。UG期间ADC触发必须关闭。然后配置非预装载toggle、重装DMA并清标志、启用DMA及ADC请求、选择OC4REF为TRGO，最后使能ADC外触发、PB15 AF4和MOE，在确认PB15仍低后启动单次计数。禁止在采样已武装时发UG，也不能仅清CNT而沿用上次中断时残留的OC4REF电平。

DMA 地址/数量在每时隙重新装载。若 DMA 未及时更新 CCR，未允许任何周期自动重启；单次计数与独立 LED 硬件限时关断共同限制故障发光。USART1/I2C 使用中断收发；尤其禁止启用USART1 TX DMA，以免与TIM1_CH4占用的DMA1 Channel4冲突。

TIM2 为 CPU 调度节拍：48 MHz、PSC=0，30 fps 时 ARR=99999（每秒480个时隙），24 fps 时 ARR=124999（每秒384个时隙）。每帧16时隙。TIM2 只通知 CPU，不用 ITR 自动启动 TIM1。CPU 每次校验上一时隙完成、one-hot、PD 映射及 DMA 数量后提交一个令牌，再单次启动 TIM1。CPU 停止后不再续发令牌。切换帧率只改变暗态空闲时间，不延长100 µs发光请求。

## 数据和故障

保持40字节小端布局，见 `firmware_interface.h`，协议版本0xE7。背景/亮灯为 uint16，差分为 int32(light)-int32(dark)，不截断负值。每组保留帧号、时隙、样本序号、LED/PD编号、有效位与故障位。无效通道清零并清有效位；不得将上一时隙数据配到当前 LED。30 fps 原始负载为19,200字节/秒，UART建议460800 baud，另计封包及校验开销。

ADC OVR、DMA TE、缺少任一数据、配置错误或时序超时：立即撤销发光请求，禁用后续时隙，清有效位，记录故障。复位/重配/校准时默认灭灯。饱和标记是数据质量诊断，不是先判断强度才能采样的门槛。

## 参考和待验证项

- ST DS9911： https://www.st.com/resource/en/datasheet/stm32f302cc.pdf
- ST RM0365： https://www.st.com/resource/en/reference_manual/dm00094349.pdf
- ST ES0231： https://www.st.com/resource/en/errata_sheet/es0231-stm32f302xbc-device-limitations-stmicroelectronics.pdf
- ST HAL ADC 定义： https://github.com/STMicroelectronics/stm32f3xx-hal-driver/blob/master/Inc/stm32f3xx_hal_adc_ex.h

ES0231 中双 ADC 交错模式 DMA 问题不能套用为本设计规则同步模式已实测通过；本设计禁用交错/自动注入/自动延迟功能。完整适用性记录见 errata_review.md。芯片修订号、全部适用勘误、定时器 DMA 初始极性和板上实测需在固件开发与首板验收时逐项复核。

- ST AN2606 Bootloader： https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf

## 附加初始化与数据完整性约束

采用 errata_review.md 的约束。DMA1 Channel1 及时搬运ADC数据，TIM1 Channel4/6的更新必须在下一比较点前完成；验证最坏总线竞争时DMA延迟，不能只凭OVR位判定无丢样。每时隙检查背景/亮灯各一次、CNDTR归零和配对序号；禁止DMA循环重复发布旧缓冲。ADC寄存器使用独立volatile访问，避免批量结构体拷贝。

I2C1使用SYSCLK 48MHz内核时钟，IMU初始总线100kHz，TIMINGR按本板上升/下降时间计算后实测。运行采样期不使用Stop/Standby。USART1为460800、8N1，无硬件流控；关闭发送前等待TC。40字节为样本载荷，传输封装应具有数据完整性检查，不能把合法长度等同于数据未损坏。
