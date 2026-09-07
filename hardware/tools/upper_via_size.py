import json
from pathlib import Path
p = Path('hardware/tools/upper_finish_signals.py')
s = p.read_text().replace('board.buffer(-0.61)', 'board.buffer(-0.56)').replace('.buffer(0.46)', '.buffer(0.41)').replace('0.6 if via else 0.15', '0.5 if via else 0.15')
p.write_text(s)
p = Path('hardware/ir_glasses/EVT_D/ir_glasses.kicad_pro')
d = json.loads(p.read_text()); d['board']['design_settings']['rules']['min_via_diameter'] = .5
p.write_text(json.dumps(d, indent=2))
