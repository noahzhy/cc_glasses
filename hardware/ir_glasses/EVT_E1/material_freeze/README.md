# EVT E1 物料冻结记录

日期：2026-09-06。批次：5 块裸板，其中 2 块贴片，3 块留作备板。

**工程料号已冻结：25 类、每板 122 颗、两板净用量 244 颗，全部 F.Cu。供货尚未齐套，不能据此宣称已锁库存或已生产放行。**

## 使用文件

- `bom_frozen_2pcs.csv`：采购主表，含完整厂家料号、规格、编码、净用量、建议备料量及供货状态。
- `bom_jlc_import.csv`：24 类有立创编码的匹配表；包含待齐料的 PD，不代表全部可立即贴装。
- `customer_supplied.csv`：J1 排线座，按 TE 2492111-5 自备，不能漏装或自动匹配旧型号。
- `..`：对应的 KiCad 工程、更新后的 Gerber、贴片坐标与检查报告。不要将 E1 的 BOM 与旧 EVT E 的 Gerber 混用。

建议备料量含少量备件或常见包装取整，是预算数量；供应商最小包装及贴片厂实际损耗量仍以配单为准。无采购、付款或库存预占操作。

## 本次已落实的变更

| 项目 | 冻结决定 | PCB / 电气影响 |
|---|---|---|
| J1 | TE **2492111-5**；DigiKey **17-2492111-5CT-ND**；净用 2、建议备 5 | 用 TE 2492111 Rev A 图纸新建封装与官方 STEP 模型。5 Pin、0.5 mm、上接触、0.3 mm 排线；保持 1=3V3、2=GND、3=模块 TX、4=模块 RX、5=NRST。 |
| R1 | Viking **ARG02FTC2671 / C284464**，2.67 kΩ、1%、0402 | 替代非优选值 2.65 kΩ。按 TI 表中 2.65 kΩ 对应 20 mA 比例估算，约 **19.85 mA**，减小约 0.75%；实际还含驱动器与电阻误差。 |
| D17 | Nexperia **PESD5V0S1BA,115 / C19224**，SOD-323 | 保留双向 ESD 功能。5 V 工作耐压覆盖 3.3 V ±5% 的 3.465 V 上限；原 3.3 V 型号的额定工作耐压没有这项裕量。新旧厂家数据表均列 14 V／12 A 钳位指标。此器件不提供直流过压稳压保护。 |
| U11 | Nexperia **PESD3V3L2BT,215 / C55440** | 补齐包装后缀，原引脚与封装不变。 |
| FB1 | Murata **BLM18AG601SN1D / C19330** | 0603、600 Ω @100 MHz、±25%、500 mA、直流电阻最大 0.38 Ω。 |
| C28 | YAGEO **CC1210KKX5R7BB476 / C596320** | 1210、47 µF、16 V、X5R、±10%；同尺寸提高耐压。47 µF 是标称值，未取得该料的 3.3 V 偏压曲线，尚不承诺有效容量为 47 µF；首板应测试 LED 电源跌落。 |
| 其余阻容 | 全部补齐品牌、完整 MPN、容差、额定电压／功率和立创编码 | 1 µF 保持 X7R；22 pF 与 1 nF 指定 C0G；四颗运放继续使用用户指定的 TLV9064IPWR。 |

J1 新焊盘按厂家推荐图：信号焊盘 0.30×1.20 mm、间距 0.50 mm；固定脚焊盘 2.20×3.30 mm。局部坐标信号排 y=-1.35，固定脚中心 x=±2.60、y=0.82。原固定脚附近的一条 GND 线改成三段避让；器件位置和所有网络对应关系保持一致。STEP 仅做刚性坐标变换；图示模型不能代替实物排线插拔验收。

## 供货结论

**PD 仍是阻止齐料的实质缺口。** Everlight PD15-22B/TR8 已被 DigiKey 标为停产；本次 LCSC 正式页面显示 10 颗，低于两板净用的 32 颗，其他缓存却显示更多，不能将这些缓存当作已确认库存。DigiKey 页面有 3000 颗，但可见报价为整卷 3000 起，不适合这次小批量。

PD 料号冻结为 **Everlight PD15-22B/TR8 / C161211**，建议备料 40 颗。本次没有把同名国产料或 EAPDST3227A0 当成自动替代；它们还需核对引脚、受光角、结电容及 TIA 响应。若国内私有库不能提供至少 32 颗加贴片损耗，应先处理 PD 采购或做单独替代变更，再提交贴片生产。

J1 的 DigiKey 公开页面显示有散带供货（本次页面 1910 颗），可作为自备料渠道。IR-LED 已找到 **C16745**；国内库存尚未确认，Everlight Americas 原厂商店列出同型号 3870 颗，可作为备选自备渠道。1 nF 电容的 JLCPCB 公开页列出 29080 颗，但不等于嘉立创国内贴片仓实时库存。这些网页信息均未预占库存，也未确认运输费用和交期。

## 检查与交付边界

- ERC、DRC、未连接、原理图一致性：均为 0。
- 122 个贴装位号的 Value、封装、Manufacturer、MPN、LCSC 已在原理图、PCB 和 BOM 间核对；贴片坐标为 122 个正面位号。
- 原有网络和器件位置不变；442 个器件铜焊盘／板，249 个过孔。J2、TP1–TP12、NT1 是 PCB 特征，不采购、不贴装。
- 保留既有的工厂 DFM、工装／工艺边、定位点、表面处理及首板功能验收待办。排线长度、主机端接触面、ST-Link、Tag-Connect 线缆和光学遮光件不在本次 PCBA 贴装物料内。
- 这是本批 EVT 的工程料号冻结；TIA 的 100 kΩ／22 pF 和光学分类参数仍需要首板验证，不是量产性能认证。

## 依据

- [TE 2492111-5 产品与图纸](https://www.te.com/en/product-2492111-5.html)、[DigiKey 散带料号](https://www.digikey.com/en/products/detail/te-connectivity-amp-connectors/2492111-5/29274746)。厂家原图与 STEP 已保存在 `evidence/`。
- [TI TLC59283 电流设置表](https://www.ti.com/lit/ds/symlink/tlc59283.pdf)。
- [Nexperia PESD5V0S1BA](https://assets.nexperia.com/documents/data-sheet/PESD5V0S1BA.pdf)、[原 PESD3V3S1BA](https://assets.nexperia.com/documents/data-sheet/PESD3V3S1BA.pdf)。
- [PD 立创页面](https://www.lcsc.com/product-detail/C161211.html)、[PD 停产与包装状态](https://www.digikey.com/en/products/detail/everlight-electronics-co-ltd/PD15-22B-TR8/2675857)。
- [IR-LED 原厂商店](https://everlightamericas.com/smd/144-ir11-21c-tr8.html)、[1 nF 的 JLCPCB 物料页](https://jlcpcb.com/partdetail/54563-0402CG102J500NT/C53547)。
- 其余物料逐项采购来源见主表 `Source` 列；编码识别与实时齐料是两项不同检查。
