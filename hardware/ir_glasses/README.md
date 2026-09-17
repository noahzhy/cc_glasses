# IR Glasses EVT E6

当前修复后的设计为 **EVT E6 P3**：每颗 IR LED 同步读取相邻两个 PD，16 组固定配对。E4 原工程、原 BOM 和生产包保留。

- [E6 工程及交付说明](ir_glasses_EVT_E6/README.md)
- [P3 运放替代与模拟验证](ir_glasses_EVT_E6/analog_validation_report.md)
- [P2 完善与复核报告](ir_glasses_EVT_E6/production_refinement_report.md)
- [P1 历史修复记录](ir_glasses_EVT_E6/production_fix_report.md)
- [完整 E6 工程包](ir_glasses_EVT_E6.zip)
- [载框 Gerber 上传包](ir_glasses_EVT_E6_JLC_upload.zip)
- [贴片交付包](ir_glasses_EVT_E6/EVT_E6_SMT_handoff.zip)
- [贴好片示意图](ir_glasses_EVT_E6/populated_assembly.pdf)
- [E6 BOM](ir_glasses_EVT_E6/bom_EVT_E6.xlsx)

主板及载框 DRC、ERC、原理图一致性、CAM/BOM/CPL 静态检查已通过。正常输入要求 3.3V±3%，板上新增持续限流和过压恢复保护。工厂 DFM、备料、实际排线和首板电气/光学/固件验证仍待完成；本包不含可烧录固件，不能把静态检查视为量产实测放行。

## E4 基线与历史证据

- [E4 KiCad 工程](ir_glasses_EVT_E4/ir_glasses_EVT_E4.kicad_pro)
- [E4 完整交付包](ir_glasses_EVT_E4.zip)
- [E4 上传包](ir_glasses_EVT_E4_JLC_upload.zip)
- [E4 BOM](ir_glasses_EVT_E4/material_freeze/bom.xlsx)
- [本次修复前复核记录](EVT_E6_preproduction_audit/REVIEW.md)

E6 BOM 以两板净用量作参考，不含贴片损耗、最小起订量及备件；实际生产数量另行确定。
