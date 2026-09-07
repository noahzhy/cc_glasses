# 智能眼镜红外传感板 — EVT E

本目录是可编辑的 KiCad 10 工程。打开 `ir_glasses.kicad_pro`，再进入原理图或 PCB 编辑器。

## 设计范围

- 单块四层 FR-4，1.6 mm；外形 **133.136 × 52.653 mm**，保留两个镜片开孔。
- 开孔从 `assets/blender/topview_outline.svg` 的闭合轮廓提取，折线简化容差 0.08 mm。每孔包围框约 53.84 × 39.09 mm；外板框为经过用户同意的加宽原型电子区，不是原镜框外边的 1:1 复制。
- 16 颗 IR11-21C/TR8、16 颗 PD15-22B/TR8、4 颗 TLV9064、TLC59283、STM32C031C6T6、LSM6DS3TR-C、双 TMUX1308，以及供电、UART、SWD 和测试焊盘。
- 采用单面贴装，122 个待装元件全部位于 F.Cu 朝眼面，B.Cu 不装元件；左右编号以 PCB 元件面图的左、右为准，装到镜框后须确认与佩戴者左右眼的对应关系。
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


## EVT E：单面贴装与中央 IMU

- 全部 136 个封装均位于正面，其中 122 个为待装元件，14 个为测试点、调试焊盘和 net tie；背面贴装数量为 0。
- 四颗 TLV9064IPWR、主控、驱动器、两颗 MUX、FFC 接口及全部阻容集中在上沿。LED/PD 的切向并排位置和朝眼面与 EVT D 相同。
- 复用 EVT D 的板框和两个眼部开孔，尺寸仍为 133.136 × 52.653 mm，侧边及下沿名义框宽 3.7 mm。没有增加上沿高度。
- U10 移到鼻梁上方的中线上，KiCad 坐标为 (110.000, 71.300) mm，F.Cu、0°。旁边印有 IMU 及 X/Y 箭头，封装三角标识指向 1 脚。按 ST 数据手册图 1，在正面图中 +X 向右、+Y 向上、+Z 从板面朝外；正背面视图左右相反。固件应按实际安装关系转换到头部坐标。
- J1 保留项目自带的 TE 0-1734839-5 封装与厂家 STEP 模型；改到正面并旋转 180°，排线开口朝上方外板边。J2 和全部测试点也从正面接触。
- 原理图连接、器件型号和数量保持不变；BOM 和贴片坐标更新为单面装配。只需要正面钢网和正面贴装工序，PCB 本身仍为四层。实际费用由板厂按加工与装配资料报价。

## 制造与验证文件

- `validation.json`、`drc.json`、`erc.json` 为本版实际核验结果；`mechanical_validation.json` 记录外形和正反面装配数量。
- `manufacturing/positions.csv` 与 `bom.csv` 一一对应 122 个待装元件，全部为 top。KiCad 贴片坐标的 Y 轴与 BOM 板图坐标方向相反。
- `assembly_front.svg` 是装配位号图；`assembly_back.svg` 和 `pcb_back.png` 用于检查背面没有元件。J2 为无焊接的弹簧针接口，TP1–TP12 与 NT1 也不采购贴装。
- 四层 FR-4、总厚度 1.6 mm；最小线宽/间距 0.15/0.15 mm，普通贯穿孔为 0.5 mm 焊盘 / 0.3 mm 钻孔、最小环宽 0.1 mm。无盲埋孔。
- F.Cu 为唯一装配面；内层和 B.Cu 可布信号与电源。AGND/GND 分开并在 NT1 连接，地铜与接地过孔连接。内层有信号走线，不能当作完整连续的专用地平面。
- `models/` 内两个光学器件模型是尺寸包络示意，其余常规器件使用 KiCad 标准模型。J1 的厂家 STEP 对齐方法与 EVT D 相同。
- 0402 非极性电阻省去本体丝印短线，避免紧凑排布时与 IC 的 1 脚标识相撞；封装库同步更新，装配图中的位号和本体轮廓保留。
- 这仍是室内 EVT 样机：模拟稳定性、光学串扰、眼安全、镜框强度和安装高度待实物验证，不能仅凭 ERC/DRC 判定为量产定版。

## J1 实体模型

- 原始厂家模型：`models/c-1734839-5-c-3d.stp`。
- KiCad 对齐模型：`models/TE_1734839-5_aligned.step`；仅调整坐标和原点。
- [TE 官方产品页及 CAD 下载](https://www.te.com/en/product-1734839-5.html)。EVT D 核查时厂家标为 Superseded，采购时核对库存和替代料兼容性。
