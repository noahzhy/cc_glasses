from pathlib import Path
p=Path('hardware/tools/upper_via_probe.py'); s=p.read_text(); a=s.index('for xy in'); b=s.index(':\n',a)
s=s[:a]+'for xy in [(117.5,65.8),(117.5,66.0),(117.4,65.85),(117.7,65.7)]'+s[b:]
s=s.replace('LED_K1','LED_LAT').replace('< 0.46','< 0.41').replace('<.46','<.41'); p.write_text(s)
