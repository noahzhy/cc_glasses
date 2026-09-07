from pathlib import Path
exec(Path('hardware/tools/upper_finish_signals.py').read_text().split('shapes = ')[0])
line = LineString([(117.6611,63.75),(116.424,63.75),(116.424,64.9871)]).buffer(.075)
for t in items:
    if t['net']!='LED_K3' and 3 in t['layers'] and shape(t).distance(line)<.15:
        print(shape(t).distance(line), t)
