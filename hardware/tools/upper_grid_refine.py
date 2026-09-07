from pathlib import Path
p = Path('hardware/tools/upper_finish_signals.py')
s = p.read_text().replace('step = 0.1', 'step = 0.05').replace('.buffer(0.235)', '.buffer(0.227)')
s = s.replace('end = None\n', 'print(net, "seeds/targets", int(starts.sum()), int(targets.sum()), flush=True)\n    end = None\n')
s = s.replace('assert end is not None, net', 'assert end is not None, (net, expanded)')
p.write_text(s)
