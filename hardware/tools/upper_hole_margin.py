from pathlib import Path
p=Path('hardware/tools/upper_finish_ground.py'); s=p.read_text().replace('return translate(\n            rotate(copper, -item["angle"], origin=(0, 0)), *item["xy"]\n        )', 'return translate(\n            rotate(copper.buffer(.1) if item.get("npth") else copper, -item["angle"], origin=(0, 0)), *item["xy"]\n        )'); p.write_text(s)
