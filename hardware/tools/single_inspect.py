import json
from pathlib import Path

p = json.loads(Path("hardware/ir_glasses/EVT_D/parts.json").read_text())
for ref, t in p.items():
    if ref.startswith(("PD", "D")) and ref not in ["D17"]:
        continue
    print(ref, t)
