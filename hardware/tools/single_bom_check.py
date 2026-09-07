import csv
from collections import Counter
from pathlib import Path

root = Path("hardware/ir_glasses/EVT_E")
bom = list(csv.DictReader((root / "bom.csv").open(encoding="utf-8-sig")))
positions = list(csv.DictReader((root / "manufacturing/positions.csv").open()))
lookup = {r["Reference"]: r for r in bom if r["Populate"] == "Yes"}
assert {r["Ref"] for r in positions} == set(lookup)
for r in positions:
    b = lookup[r["Ref"]]
    assert abs(float(r["PosX"]) - float(b["X_mm"])) < 0.00001, r["Ref"]
    assert abs(float(r["PosY"]) + float(b["Y_mm"])) < 0.00001, r["Ref"]
    assert r["Side"] == {"front": "top", "back": "bottom"}[b["Side"]], r["Ref"]
    assert (
        abs((float(r["Rot"]) - float(b["Rotation_deg"]) + 180) % 360 - 180)
        < 0.001
    ), r["Ref"]
print(
    "Placement/BOM matched:",
    len(positions),
    dict(Counter(r["Side"] for r in positions)),
)
print(
    "Amplifiers:",
    [
        (r["Reference"], r["Value"])
        for r in bom
        if r["Reference"] in ["U2", "U3", "U4", "U5"]
    ],
)
