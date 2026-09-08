"""Measure via-to-pad margins and final photodiode input routing."""

import json
import math
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((root / "route_geometry.json").read_text())
physical = json.loads((root / "physical_summary.json").read_text())
lands = unary_union(
    [
        Polygon(p["coords"])
        for p in items
        if p["kind"] == "pad" and not p["npth"]
    ]
)
new_vias = set(physical["new_via_uuids"])
margins = [
    {
        "uuid": p["uuid"],
        "net": p["net"],
        "xy": p["a"],
        "drill_edge_to_pad_mm": Point(p["a"]).distance(lands) - 0.15,
    }
    for p in items
    if p["kind"] == "via" and p["uuid"] in new_vias
]
assert min(p["drill_edge_to_pad_mm"] for p in margins) >= 0.1499
lengths = []
for number in range(1, 17):
    net = f"PD_IN{number}"
    tracks = [p for p in items if p["kind"] == "track" and p["net"] == net]
    lengths.append(
        {
            "channel": number,
            "net": net,
            "total_track_length_mm": sum(
                math.dist(p["a"], p["b"]) for p in tracks
            ),
        }
    )
report = {
    "board_sha256": physical["board_sha256"],
    "new_via_minimum_drill_edge_to_pad_mm": min(
        p["drill_edge_to_pad_mm"] for p in margins
    ),
    "new_via_margins": margins,
    "pd_input_track_lengths": lengths,
    "pd_input_noise_and_settling": "BENCH TEST REQUIRED",
}
(root / "electrical_metrics.json").write_text(json.dumps(report, indent=2))
print(
    "New via minimum pad margin:",
    report["new_via_minimum_drill_edge_to_pad_mm"],
)
print(
    "PD input length range:",
    min(p["total_track_length_mm"] for p in lengths),
    max(p["total_track_length_mm"] for p in lengths),
)
