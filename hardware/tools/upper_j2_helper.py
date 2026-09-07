from pathlib import Path
p=Path('hardware/tools/upper_finish_signals.py'); s=p.read_text(); a=s.index('for net in ['); z=s.index(']:',a); s=s[:a]+'for net in ["3V3"'+s[z:]
s=s.replace('rotate(copper, -item["angle"], origin=(0, 0))', 'rotate(copper.buffer(.1) if item.get("npth") else copper, -item["angle"], origin=(0, 0))'); p.write_text(s)
