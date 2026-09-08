# 智能眼镜 EVT E3

本版基于 E2 增加状态灯和保护电路，仍为四层 FR-4、1.6 mm、沉金、正面贴装。
侧边和下沿细框、双眼开孔、16 组光学器件的位置与极性、中央 IMU 保持不变。
上沿电源区已重新排紧 C25、D17、U14、C37，取消原 1.5 mm 凸起，恢复平直上沿。
本次为 E3 平顶布局更新；电路和物料选型不变，旧凸起版交付包保存在上级 archive 目录。
计划 5 块 PCB，其中 2 块相同配置贴片。

工程检查的最终结果见 `validation.json`、`erc.json`、`drc.json`；
这些检查不代替首板实测、工厂 DFM 或齐料确认。

## 本次修改

| 项目 | E3 实施内容 |
|---|---|
| 状态灯 | D20：Lite-On LTST-C190KGKT，0603 绿色；R17：4.7 kΩ；PA8 低电平点亮，丝印 S。需要固件驱动，空片上电不保证亮灯。 |
| 复位保护 | MCU 近端增加 C32 100 nF；J1 / J2 入口增加 D18 / D19 PESD3V3U1UB；J1 复位信号经 R14 100 Ω 接入 NRST。 |
| IR 发光限时 | U12 SN74LVC1G123 + U13 SN74LVC1G04；R15 100 kΩ 与 C33 / C34 两颗 1 nF C0G 定时；R16 10 kΩ 将请求脚默认拉低。 |
| 供电保护 | U14 TPS259470LRPWR 将 J1 的 VIN_3V3 与板内 3V3 分开；增加持续正向过压关断、输入限流和软启动。D17 仍只承担输入瞬态抑制。 |
| 内层参考铜 | 四层统一铺 GND，原 AGND 并入 GND，移除 NT1 铜桥及其符号。模拟、数字器件按区域布局。内层仍有部分走线，不能视为完全无切割的专用地层；噪声和串扰仍需首板验证。 |
| 局部布局 | 调整 C3–C6、C17 去耦；C29 / C30 移近 ADC，引脚 2 改接 MCU 的 GND。重布受影响线路，处理审查指出的两颗近焊盘过孔。 |

TLV9064IPWR、PD15-21B/TR8、100 kΩ / 22 pF TIA 参数及 IR 电流设定保持不变。
PD 阳极在 E3 最终版本接共同 GND；原理图中的 AGND 网络已合并。
长 PD 输入线仍需以暗态噪声、串扰及建立时间实测定版。

## 供电与固件变化

**J1 仍是 3.3 V 供电接口，不是 5 V 工作接口。板端输入范围改为 3.20–3.40 V。**

- U14 标称过压门限约 3.492 V。R18 = 19.1 kΩ / 0.1%，R19 = 10 kΩ / 0.1%。
- 计入 IC 门限、两只电阻 0.1% 公差及输入漏电，估算门限为 3.436–3.566 V；
  再保守计入各电阻 100 °C 温差、25 ppm/°C 漂移，约 3.425–3.577 V。
  这不是实测值，也不包含瞬态过冲。原来的宽松 ±5% 电源可能在上限触发保护。
- R20 = 6.2 kΩ，输入限流标称约 0.54 A；这是整板故障限流，不是单颗 IR-LED 的限流。
- C38 = 1 nF，按原厂典型公式，3.3 V 输出上升时间约 1.65 ms；实际启动需测量。
- 保护触发后按断电重启处理；本版未承诺反接耐受，也不能将原接口当作任意电源输入。
- **PB2 从 E2 的低有效 LED_BLANK 改为高有效 LED_ENABLE。旧版固件不能直接沿用。**
- PA8 用作 STATUS_LED_N；采样背景和 IR 响应期间暂时熄灭状态灯，避免引入可见光干扰。

详细时序与故障边界见 `firmware_contract.md`。尚未提供可量产烧录的 HEX / BIN。

## 交付与下单

- 原理图入口：`ir_glasses.kicad_sch`；PCB：`ir_glasses.kicad_pcb`。
- BOM：`material_freeze/bom_smt_all.csv`；供料状态：`material_freeze/bom_frozen_2pcs.csv`。
- 载框加工文件、坐标与分板图集中在 `carrier/`；单板文件放在 `manufacturing/` 供核对。
- 正式下单采用同一版本的载框 Gerber、载框坐标与 E3 BOM，不混用 E2 文件。
- 新版为 142 个实装位号、33 类物料，两板净用 284 颗。J1 继续指定 TE 2492111-5 自备。
- 国内可贴库存、平台损耗、J1 接收、钢网与分板 DFM 尚需工厂确认。
- 增加了保护器件和物料种类，原 E2 报价不能直接作为 E3 的确定报价；按本版 BOM 重新询价。
- 先完成两块 EVT 的 `first_board_tests.csv`，再决定是否进入量产。

## 原厂依据

- [ST STM32C031：NRST 与 GPIO](https://www.st.com/resource/en/datasheet/stm32c031c6.pdf)
- [TI SN74LVC1G123：触发真值表与定时](https://www.ti.com/lit/ds/symlink/sn74lvc1g123.pdf)
- [TI SN74LVC1G04：DBV 引脚](https://www.ti.com/lit/ds/symlink/sn74lvc1g04.pdf)
- [TI TPS25947：RPW0010A、OVLO、限流与 dVdt](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
- [Nexperia PESD3V3U1UB：SOD523 与极性](https://assets.nexperia.com/documents/data-sheet/PESD3V3U1UB.pdf)
- [Lite-On LTST-C190KGKT：封装及光电参数](https://optoelectronics.liteon.com/upload/download/DS22-2000-074/LTST-C190KGKT.PDF)

回流布局参考 [TI 混合信号 PCB 接地说明](https://e2e.ti.com/support/data-converters-group/data-converters/f/data-converters-forum/755516/faq-pcb-layout-guidelines-and-grounding-recommendations-for-high-resolution-adcs)。本板改用共同参考地，并保留模拟电源滤波；这是结合细框结构的工程调整，不代表原厂对本板性能的认可。另见 [ADI 混合信号接地说明](https://www.analog.com/en/resources/analog-dialogue/articles/what-are-the-basic-guidelines-for-layout-design-of-mixed-signal-pcbs.html)。
