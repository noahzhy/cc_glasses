# EVT E2 物料冻结记录

2026-09-07。5 块裸板，其中 2 块按相同配置贴装，3 块留作裸板备件。工程料号为 25 类、每板 122 颗、两板净用 244 颗，全部正面贴装。库存、平台损耗和自备料入库尚未确认，未采购或预占库存。

## E2 选型

- PD1–PD16 使用 **Everlight PD15-21B/TR8 / C2921391**，两板净用 32 颗，预算备料 40 颗。本体 3.2 × 1.5 × 1.1 mm；使用专用 `IR_Glasses:Everlight_PD15_21B` 两焊盘封装。1 脚阳极接 AGND，2 脚阴极接对应 PD_IN。旧 PD15-22B 的四焊盘封装不能混用。
- 两块板均装 RF1–RF16=100 kΩ、CF1–CF16=22 pF C0G。220 kΩ、470 kΩ 仅列于调试备料表，不进入贴片 BOM。换增益前需实测带宽、建立时间、噪声及饱和余量。
- 其余完整 MPN 延续 E1，包括 TLV9064IPWR、TE 2492111-5、R1 2.67 kΩ 及 47 µF/16 V 的 C28。J1 引脚仍为 1=3V3、2=GND、3=模块 TX、4=模块 RX、5=NRST。
- 载框版使用四层 FR-4、1.6 mm、沉金、绿油白字、正面贴装。焊盘数预计由每板 442 减少至 410；以最终 PCB 检查报告和工厂计费为准。

型号、编码与引脚依据：[Everlight 原厂数据手册](https://en.everlight.com/wp-content/plugins/ItemRelationship/product_files/pdf/PD15-21B-TR8.pdf)、[LCSC C2921391 产品身份](https://www.lcsc.com/product-detail/C2921391.html)。原厂典型 0.8 µA 的测试条件是 940 nm、1 mW/cm²、反向偏压 5 V，本板约 1.65 V 偏压下的反射信号需实测，不能将该值直接当作实际输入电流。

## 清单用途

| 文件 | 用途 |
|---|---|
| `bom_frozen_2pcs.csv` | 25 类完整采购主表，净用量、建议备量、实时库存、工厂损耗和最终供料量分列 |
| `bom_jlc_import.csv` | 24 类有立创编码的匹配表，合计每板 121 颗；需要与 J1 自备料合并完成 122 颗贴装 |
| `bom_smt_all_122.csv` | 合并 J1 后的完整贴片导入表，25 类、122 位号；J1 的 LCSC 编码为空，待实际指定自备物料 |
| `customer_supplied.csv` | 已选自备的 J1，保持 TE 2492111-5，净用 2 颗，建议备 5 颗，采购与工厂入库待完成 |
| `../procurement/customer_supply_if_short.csv` | 24 类条件性自备方案；仅在国内库存不足得到确认后启用，不表示已确认全部缺货 |
| `../procurement/domestic_inventory_check.csv` | 25 类国内配单核对表，未知库存及损耗为空白，不填 0 |
| `../procurement/debug_spares.csv` | 220 kΩ 和 470 kΩ，各建议备 100 颗，用于后续手工调试，不贴入首批两板 |

建议备量是小批量预算与备件数量，并非嘉立创要求的损耗量。平台最终供料量应满足“净用量 + 该订单确认的损耗”，并按实际最小包装取整；不能直接按建议数量确认齐套。[嘉立创损耗说明](https://www.jlc.com/portal/server_guide_42767.html)涉及器件价值、引脚数等条件，当前缺少国内成交单价，故不代填损耗。

## 供货状态

本次实际访问 24 个国内 `jlc-smt.com/lcsc/detail/` 编码页面，全部返回 JavaScript/WAF 校验页，未获得可用库存、库别或价格字段。逐条 URL、访问时间和响应摘要哈希保存在 `../procurement/domestic_inventory_observations.json`。J1 未确认国内编码，因此按已选自备处理。

国际 LCSC 页面确认 C2921391 对应 Everlight PD15-21B/TR8，且有散量销售入口，可作同型号自备的候选渠道；它不证明嘉立创国内贴片仓有料，也不等于工厂已接收该物料。旧版 PD 库存与历史缓存不用于本批齐料判断。

J1 候选采购身份为 [TE 官方 2492111-5](https://www.te.com/en/product-2492111-5.html) 和 [DigiKey 17-2492111-5CT-ND](https://www.digikey.com/en/products/detail/te-connectivity-amp-connectors/2492111-5/29274746)。实际库存、交期和邮寄备料损耗以采购与工厂配单结果为准。工厂系统提示邮寄料应先加入待邮寄备料，之后才会在 SMT 订单自动匹配，见[嘉立创下单页](https://www.jlc-smt.com/order)。

## 提交前关闭项目

1. 国内账号完成 24 类编码匹配，按两板及实际损耗生成最终供料数量；短缺料保持厂家及完整 MPN 自备。
2. J1 与条件性自备料确认编带方向、包装、入库数量、工厂内部物料编码及接收状态。
3. 工厂确认载框、分板方式、薄镜框支撑和光学器件工装，完成首件贴装角度、1 脚及丝印审核。
4. 正式报价、工厂 DFM、首板功能和光学测试分别记录实际结果。工程检查结果见 E2 检查报告，不将本清单视为生产放行记录。

J2、TP1–TP12 和 NT1 不采购、不贴装；载框 Mark 和定位孔也不进入 BOM。排线、主机、ST-Link、Tag-Connect 线缆、遮光件不在 122 颗 PCBA 物料中。E1 快照保持原样，E2 的 BOM、坐标和 Gerber 必须成套使用。
