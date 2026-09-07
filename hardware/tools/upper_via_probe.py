from pathlib import Path

s = (
    Path("hardware/tools/upper_finish_signals.py")
    .read_text()
    .split("shapes = ")[0]
)
exec(s)
for xy in [(117.5,65.8),(117.5,66.0),(117.4,65.85),(117.7,65.7)]:
    p = Point(xy)
    near = [
        (round(shape(t).distance(p), 4), t)
        for t in items
        if t["net"] != "LED_LAT" and t["layers"] and shape(t).distance(p) < 0.41
    ]
    print(xy, near)
