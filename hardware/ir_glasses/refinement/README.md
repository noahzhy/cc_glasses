# 智能眼镜红外传感板 — EVT A

本目录是可编辑的 KiCad 10 工程。打开 `ir_glasses.kicad_pro`，再进入原理图或 PCB 编辑器。

## 设计范围

- 单块双层 FR-4，1.6 mm；外形 **156 × 82 mm**，保留两个镜片开孔。
- 开孔从 `assets/blender/topview_outline.svg` 的闭合轮廓提取，折线简化容差 0.08 mm。每孔包围框约 53.84 × 39.09 mm；外板框为经过用户同意的加宽原型电子区，不是原镜框外边的 1:1 复制。
- 16 颗 IR11-21C/TR8、16 颗 PD15-22B/TR8、4 颗 TLV9064、TLC59283、STM32C031C6T6、LSM6DS3TR-C、双 TMUX1308，以及供电、UART、SWD 和测试焊盘。
- 全部元件放在 F.Cu 面，光学器件正面朝向眼球；左右编号以 PCB 元件面图的左、右为准，装到镜框后须确认与佩戴者左右眼的对应关系。
- 不含电池、充电、无线通信、固件、光学遮罩和外壳。

## 文件

- `ir_glasses.kicad_pro`：工程及加工规则。
- `ir_glasses.kicad_pcb`：元件、双眼开孔、实际铜走线与地铜。
- `ir_glasses.kicad_sch`：控制器和接口主页；其余四页为电源/驱动、左眼、右眼、去耦。
- `IR_Glasses.kicad_sym`、`IR_Glasses.pretty`、两个 library table：项目自带完整符号与封装库。
- `schematic.pdf`：五页原理图预览。
- `bom.csv`：板上元件清单；调试焊盘和 net tie 不采购、不贴装。
- `validation.json`、`erc.json`、`drc.json`：最后一次核验结果。

## 接口

### J1：TE 0-1734839-5，0.5 mm、5 pin FFC

| Pin | 网络 | 定义 |
|---|---|---|
| 1 | 3V3 | 主机稳压 3.3 V 输入 |
| 2 | GND | 主机数字地 |
| 3 | HOST_TX | 模块 TX，接主机 RX |
| 4 | HOST_RX | 模块 RX，接主机 TX |
| 5 | NRST | 低有效复位，主机应开漏驱动或释放 |

### J2：TC2050-IDC-NL，按 TC2050-ARM2010 适配器接法

| Pin | 网络 |
|---|---|
| 1 | VTref / 3V3 |
| 2 | SWDIO |
| 3 | GND |
| 4 | SWCLK / PA14 / BOOT0 |
| 5–9 | 不连接 |
| 10 | NRST |

J2 是无焊接连接器的弹簧针焊盘。它不是直接配任意 Cortex 10-pin 线缆的保证；按所选 TC2050-ARM2010 适配器核对接法，尤其不要把适配器可选 5 V 送入板子。板子由 J1 供电。

### MCU 分配

| MCU 引脚 | 功能 |
|---|---|
| PA0、PA1 | 左、右 ADC 输入 |
| PA2、PA3 | USART2 运行 UART |
| PA5、PA7 | SPI1 SCLK、MOSI，驱动 TLC59283 |
| PB1、PB2 | LED LAT、BLANK |
| PA4、PA6、PB0 | 两颗 MUX 共用 A0、A1、A2 |
| PB6、PB7 | I²C SCL、SDA；IMU 地址 0x6A |
| PB3 | IMU INT1 |
| PA9、PA10 | USART1 系统 Bootloader 测试点 |
| PA13、PA14 | SWDIO、SWCLK；PA14 同时承担 BOOT0 |
| PF2 | NRST |

BOOT0 并非独立管脚。R5 将 PA14 以 100 kΩ 弱下拉；调试时不要把 BOOT0 测试点硬拉高。通过系统串口恢复需要先按 STM32C031 的参考手册和 AN2606 配置/核对启动 option bytes，不能假定出厂设置下一拉高即进入 Bootloader。

## 与输入 BOM 的具体化和补充

- U11 选定 Nexperia PESD3V3L2BT，SOT-23；D17 选定 PESD3V3S1BA，SOD-323。U11 的零偏电容约 101 pF，适用于这里的低速 UART，不能当作亚 pF 高速接口保护器。
- J1 选定 TE 0-1734839-5；C28 选用 1210、47 µF、6.3 V X5R MLCC，采购时核对 3.3 V 直流偏压下的有效电容。
- 增加 R10=10 kΩ，将 BLANK 默认上拉，MCU 复位时 LED 保持关闭。
- 增加 R11/R12=100 Ω、C29/C30=1 nF，隔离 ADC 采样瞬态。
- 增加 R13=47 Ω、C31=100 nF，缓冲器输出经隔离电阻后形成 VREF_1V65；反馈取电阻前端。
- 增加 NT1，明确 AGND 与 GND 的单点连接。磁珠隔离 3V3_A。
- IR11-21C 的封装按厂家 **1=A、2=K**；PD15-22B 按 **1/4=K、2/3=A** 建立，不套用不匹配的通用二极管编号。

## 上电与验证边界

这是一份待实物验证的室内 EVT 设计，不是量产或医疗用途定版。

1. 初次用限流 3.3 V 供电，确认 3V3_A 和 VREF_1V65。MCU 复位时检查所有 LED 熄灭。
2. 固件先保持 BLANK 高，清空移位寄存器；只允许单颗 LED 以 20 mA、100 µs 脉冲扫描，不得同时点亮 16 颗。
3. 每眼主通道按 1→5、2→6、3→7、4→8 及反向配对；同单元 LED/PD 仅机械相邻，不作为主接收对。
4. RF=100 kΩ、CF=22 pF 是初始值。四运放服务分散在镜框上的 PD，敏感输入线仍较长，**未满足每个 PD 都紧邻独立 TIA 的理想布局**。须测试寄生电容、稳定性、暗电流、串扰与噪声；如达不到指标，应改成分散单运放或重新选择封装/架构。
5. 遮光罩、安装方向、眼距与镜片反射尚未验证；应先在离眼台架上完成光学和眼安全评估，再开展佩戴测试。
6. ERC/DRC 与网表一致性只验证所声明的电气/几何规则，不代替样机、EMC、热、模拟稳定性和机械装配试验。

## 核对来源

- [TI TLC59283：引脚、RGE0024C、恒流设定](https://www.ti.com/lit/ds/symlink/tlc59283.pdf)
- [TI TLV906x：运放引脚与应用](https://www.ti.com/lit/ds/symlink/tlv9061.pdf)
- [TI TMUX1308：引脚、低有效 EN](https://www.ti.com/lit/ds/symlink/tmux1308.pdf)
- [ST STM32C031C6：LQFP48 管脚和复用功能](https://www.st.com/resource/en/datasheet/stm32c031c6.pdf)
- [ST LSM6DS3TR-C：LGA14 管脚和 I²C 接法](https://www.st.com/resource/en/datasheet/lsm6ds3tr-c.pdf)
- [Everlight IR11-21C/TR8：封装和焊盘](https://www.everlight.com.cn/wp-content/plugins/ItemRelationship/product_files/pdf/IR11-21C-TR8.pdf)
- [Everlight PD15-22B/TR8：四焊盘极性和建议焊盘](https://www.everlight.com.cn/wp-content/plugins/ItemRelationship/product_files/pdf/PD15-22B-TR8.pdf)
- [Nexperia PESD3V3L2BT](https://assets.nexperia.com/documents/data-sheet/PESD3V3L2BT.pdf)
- [Nexperia PESD3V3S1BA](https://assets.nexperia.com/documents/data-sheet/PESD3V3S1BA.pdf)
- [Tag-Connect TC2050-ARM2010](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2021/02/TC2050-ARM2010-2021.pdf)
