"""Route open nets while protecting already connected circuits."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

root = Path("hardware/ir_glasses/EVT_E3")
drc = json.loads((root / "drc.json").read_text(encoding="utf-8"))
targets = {
    re.search(r"\[([^]]+)\]", issue["items"][0]["description"])[1]
    for issue in drc["unconnected_items"]
}
targets.update(sys.argv[1:])
priority = [
    "ADC_L",
    "ADC_R",
    "MUX_A0",
    "MUX_A1",
    "LED_SCLK",
    "LED_LAT",
    "MUX_A2",
    "PULSE_C",
    "PULSE_RC",
    "INRUSH_RC",
    "LED_SIN",
    "NRST",
    "NRST_EXT",
    "SWDIO",
]
power = ["VREF_1V65", "3V3_A", "3V3", "AGND", "GND"]
priority = (
    priority[:3]
    + sorted(n for n in targets if n.startswith("PD_IN"))
    + priority[3:]
)
ordered = (
    [n for n in priority if n in targets]
    + sorted(targets - set(priority) - set(power))
    + [n for n in power if n in targets]
)
items = json.loads((root / "route_geometry.json").read_text())
env = os.environ.copy()
env["E3_ROUTE_RIPUP"] = "1"
env["E3_LOCK_NETS"] = ",".join(sorted({p["net"] for p in items} - targets))
(root / "route_targets.json").write_text(json.dumps(ordered))
subprocess.run(
    [sys.executable, str(Path(__file__).with_name("e3_route.py")), *ordered],
    env=env,
    check=True,
)
