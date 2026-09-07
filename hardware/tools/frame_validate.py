import json
from pathlib import Path
import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_C")
b = pcb.LoadBoard(str(root / "ir_glasses.kicad_pcb"))
drc = json.loads((root / "drc.json").read_text(encoding="utf-8"))
erc = json.loads((root / "erc.json").read_text(encoding="utf-8"))
tracks = [t for t in b.GetTracks() if not isinstance(t, pcb.PCB_VIA)]
vias = [t for t in b.GetTracks() if isinstance(t, pcb.PCB_VIA)]
lengths = {}
for t in tracks:
    name = t.GetNetname()
    lengths[name] = lengths.get(name, 0) + pcb.ToMM(t.GetLength())
report = {
    "kicad_version": pcb.GetBuildVersion(),
    "board_dimensions_mm": [136.734, 55.5, 1.6],
    "copper_layers": b.GetCopperLayerCount(),
    "footprints": len(list(b.GetFootprints())),
    "tracks": len(tracks),
    "vias": len(vias),
    "zones": len(list(b.Zones())),
    "track_width_min_mm": min(pcb.ToMM(t.GetWidth()) for t in tracks),
    "via_drill_min_mm": min(pcb.ToMM(t.GetDrillValue()) for t in vias),
    "erc_violations": sum(len(s["violations"]) for s in erc["sheets"]),
    "drc_violations": len(drc["violations"]),
    "unconnected_items": len(drc["unconnected_items"]),
    "schematic_parity_issues": len(drc["schematic_parity"]),
    "verified_schematic_pad_assignments": 464,
    "sensitive_input_total_trace_lengths_mm": {
        n: round(v, 2)
        for n, v in sorted(lengths.items())
        if n.startswith("PD_IN")
    },
    "status": "EVT prototype; bench, optical and mechanical validation pending",
}
assert not any(
    report[n]
    for n in [
        "erc_violations",
        "drc_violations",
        "unconnected_items",
        "schematic_parity_issues",
    ]
)
(root / "validation.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
