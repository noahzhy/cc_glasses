# EVT E6 P2 — 量产复核问题修订

本文件记录P2历史修订。当前P3已更换U16/U17及R11/R12，最新模拟验证见 `analog_validation_report.md`，最终BOM为41类、首板清单30项。

2026-09-17。针对复核报告中的静态保护余量、被忽略DRC规则和量产资料缺口修改。保持E4源文件、板框、安装结构及32个光学器件坐标/方向；采集功能仍为一颗IR LED与其相邻两颗PD同步采样。

## 本次修改

- 将五类先前忽略的DRC规则全部设为启用；修正原55处过孔接入，修正本地符号封装筛选，使现有合法的本地封装名可被正确检查。此次不使用逐项排除。
- U19由TPS3700DSER改为TPS3702CX33DDCR / C2068031，使用TI DDC0006A专用TSOT-23-6焊盘，无EP；重布监控器与分压/去耦区域。
- R18改200Ω / C25087；R19改10kΩ / C25744。SET接高，感测分压比例1/1.02。U19 OV_N经INPUT_OK控制U14 EN/UVLO，U14 OVLO接地，R28保留10k上拉。
- 保留U14 TPS259470ARPWR、U18 TPS2553DRVR及110k低电流限流、C38=22nF。故障通过使能端关闭，恢复走使能启动路径，避免采用OVLO快速恢复旁路。
- 使用3.3V±3%、−25～85°C及保守电阻温漂预算重新计算：过压动作3.46590～3.53557V；恢复3.43792～3.52506V。最高DC动作门限距ADC 3.6V工作上限约64.4mV，最低恢复门限距3.399V正常输入上限约38.9mV。
- 更新BOM、贴片坐标、制造包、贴好片示意图和供电说明；全部42类实际贴装料号重新查询国内商城库存。ADC查询时仍仅8件，未锁定库存或采购。
- 首板测试新增动态过压/热插拔波形和可追溯的连续运行/每板功能测试，共27项。可烧录固件仍不属于本次交付范围。

## 验证记录

本次最终结果以同包新生成的 `erc.json`、`drc.json`、`carrier/drc.json`、`design_validation.json`、`power_protection_validation.json`、`manufacturing_validation.json`、`via_assembly_validation.json`、`review_status.json` 及 `release_checklist.csv` 为准。`SHA256SUMS.txt` 对应最终文件。

未把检查关闭或制造间距放宽来取得零违规。制造文件必须通过本版检查后重新导出；旧生产包已保存于修订前备份。

## 仍需首板和工厂完成

静态门限余量的改善不等于动态过冲保护已通过。TPS3702和U14 EN都有传播/关断延迟，该网络不是快速瞬态钳位器。实际主机型号、输出精度和纹波未获确认，仍按3.3V±3%条件设计。需要实测最坏输入、负载、线缆、启动、故障及恢复波形，并完成ADC精度/串扰/建立时间、同步配对、CPU停止后灭灯、温升、J1实物排线、工厂DFM及齐料确认。

本版状态应为EVT设计及生产文件静态验证完成，不能写为量产或实物验收通过。不得因本报告将待测项目改为通过。

## 原厂依据

- [TPS3702数据手册](https://www.ti.com/lit/ds/symlink/tps3702.pdf)：DDC针号、SET高的4%窗口、阈值精度、迟滞和焊盘。
- [TPS25947数据手册](https://www.ti.com/lit/ds/symlink/tps25947.pdf)：EN关断、启动路径及OVLO恢复旁路。
- [AD7386数据手册](https://www.analog.com/media/en/technical-documentation/data-sheets/ad7386-7387-7388.pdf)：ADC供电范围及单线同步转换读出。
