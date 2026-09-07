# EVT E2 配单状态

批次为 5 块裸板、2 块正面贴装。2026-09-07 实际访问 24 个有编码物料的嘉立创国内页面，均返回校验页，**未确认任何一类的国内实时库存**；J1 另按指定 TE 2492111-5 自备。未知库存不是零库存。

`domestic_inventory_check.csv` 覆盖全部 25 类，记录净用量、获取时间和来源；`domestic_inventory_observations.json` 保存访问证据摘要。库存、损耗和最终供料数量为空的格子需由实际配单填写。

`customer_supply_if_short.csv` 为保持指定 MPN 的条件性自备表，仅在工厂确认相应料无法供给时启用。该表中的国际 LCSC 链接是采购身份入口，不代表国内库现货。已选自备的 J1 单独在 `../material_freeze/customer_supplied.csv`，不能漏入贴装匹配。

`debug_spares.csv` 单独列出 UNI-ROYAL 0402WGF2203TCE / C25767 和 0402WGF4703TCE / C25790，各建议 100 颗；两块首板仍全部 100 kΩ / 22 pF。备件不计入 122 个位号、244 颗净用量或贴片坐标。

当前已完成工程采购清单及供货路径整理。实际采购、预占、邮寄及工厂入库均未执行。配单规则依据[嘉立创器件用量说明](https://www.jlc.com/portal/server_guide_42767.html)及[邮寄器件匹配入口](https://www.jlc-smt.com/order)。
