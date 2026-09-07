from pathlib import Path
p = Path('hardware/tools/upper_via_probe.py')
s = p.read_text(); a=s.index('for xy in'); b=s.index(':\n',a)
s=s[:a]+'for xy in [(117.1,64.75),(117.0,64.8),(117.2,64.75),(117.15,64.8)]'+s[b:]
s=s.replace('LED_K9','LED_K1'); p.write_text(s)
