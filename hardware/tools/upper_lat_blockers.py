from pathlib import Path
exec(Path('hardware/tools/upper_finish_signals.py').read_text().split('shapes = ')[0])
line=LineString([(110.75,60.8375),(110.65,60.9375),(110.65,62.6496),(111.0036,63.0032),(111.6787,63.0032),(112.2055,62.4764)]).buffer(.075)
for t in items:
    if t['net']!='LED_LAT' and 3 in t['layers'] and shape(t).distance(line)<.15:
        print(round(shape(t).distance(line),4),t)
print('VIA')
for t in items:
    if t['net']!='LED_LAT' and t['layers'] and shape(t).distance(Point(112.2055,62.4764))<.41:
        print(round(shape(t).distance(Point(112.2055,62.4764)),4),t)
