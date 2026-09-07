# 当前物料冻结入口：EVT E2

当前版本为 **EVT E2 / Everlight PD15-21B/TR8 / C2921391**，2026-09-07。批次为 5 块裸板、其中 2 块同配置正面贴装；25 类、122 颗/板、两板净用 244 颗。

本目录的 `selections.json`、`bom_frozen_2pcs.csv`、`bom_jlc_import.csv` 和 `customer_supplied.csv` 已同步 E2。完整资料以 [EVT E2 物料冻结记录](../EVT_E2/material_freeze/README.md)和 [E2 工程入口](../EVT_E2/README.md)为准；只与 E2 的 PCB、Gerber 和贴片坐标配套使用。

PD1–PD16 净用 32 颗，建议备料 40 颗。两块首板均保持 100 kΩ / 22 pF；[220 kΩ、470 kΩ 调试备件](../EVT_E2/procurement/debug_spares.csv)不进入首批贴片 BOM。

JLC 匹配表含 24 类、每板 121 颗，另加 J1 自备表的 TE 2492111-5，每板合计 122 颗。J1 自备选型已确定，实际采购和工厂入库尚未完成。其他料只有在国内短缺得到确认后才启用[同完整 MPN 条件性自备清单](../EVT_E2/procurement/customer_supply_if_short.csv)。

下单可使用已合并的 `bom_smt_all_122.csv`，它包含完整 25 类、122 位号；J1 编码留空，等待工厂接收后指定自备料。

本次 24 个国内物料页面均返回校验页，实时库存和平台损耗未取得，相关字段保留空白；未知库存不表示缺货或齐套。详见 [E2 配单状态与访问记录](../EVT_E2/procurement/README.md)。未采购、付款、邮寄或预占库存。

[EVT E1 历史冻结记录](../EVT_E1/material_freeze/README.md)保持原样。旧根目录 `evidence/` 中的 TE 图纸等仅作为历史来源资料，不能代替 E2 的当前 BOM 和检查结论。
