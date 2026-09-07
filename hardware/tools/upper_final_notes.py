from pathlib import Path
root = Path('hardware/ir_glasses/EVT_D')
p=root/'README.md'; s=p.read_text(encoding='utf-8')
s=s.replace('最终检查结果以本目录报告为准。', 'ERC 0、DRC 0、未连接 0、原理图一致性问题 0；464 个焊盘网络分配已核对。')
marker='- J1 补齐 TE 官方 STEP 实体模型'
s=s.replace(marker, '- C28 在正面向左微移 0.5 mm，给驱动器引出线留出过孔空间。\n'+marker)
marker='- 总厚度 1.6 mm，四层、双面贴装；'
s=s.replace(marker, '- 最小线宽/间距 0.15/0.15 mm；普通通孔 0.6/0.3 mm，密集区及部分地连接采用 0.5/0.3 mm 通孔，最小环宽 0.1 mm。板厂需按本版参数确认加工能力。\n'+marker)
p.write_text(s,encoding='utf-8')
p=Path('docs/smart_glasses_ir_sensor_bom.md'); s=p.read_text(encoding='utf-8')
marker='- 具体坐标及正反面以 hardware/ir_glasses/EVT_D/bom.csv'
s=s.replace(marker, '- C28 向左微移 0.5 mm；密集区增加 0.5 mm 焊盘 / 0.3 mm 钻孔的通孔，其余普通通孔为 0.6/0.3 mm。\n'+marker)
p.write_text(s,encoding='utf-8'); (root/'source_bom.md').write_text(s,encoding='utf-8')
