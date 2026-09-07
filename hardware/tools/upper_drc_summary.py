"""Print compact KiCad DRC diagnostics."""

import json
from pathlib import Path

p = Path("hardware/ir_glasses/EVT_D/drc.json")
r = json.loads(p.read_text(encoding="utf-8"))
for name in ["violations", "unconnected_items", "schematic_parity"]:
    print(name, len(r[name]))
    for item in r[name][:30]:
        print(item["type"], item["description"])
        for detail in item["items"]:
            print(
                " ",
                detail["description"],
                detail["pos"],
                detail.get("uuid", ""),
            )
