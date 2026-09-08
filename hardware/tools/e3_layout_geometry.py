"""Export physical placement geometry using KiCad's transformed coordinates."""

import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path("hardware/ir_glasses/EVT_E3")
board = pcb.LoadBoard(str(ROOT / "ir_glasses.kicad_pcb"))


def xy(point):
    return [pcb.ToMM(point.x), pcb.ToMM(point.y)]


items = {}
for fp in board.GetFootprints():
    fp.BuildCourtyardCaches()
    courtyard = fp.GetCourtyard(pcb.F_CrtYd)
    graphics = []
    if courtyard.OutlineCount():
        outline = courtyard.COutline(0)
        graphics = [xy(outline.CPoint(i)) for i in range(outline.PointCount())]
    items[fp.GetReference()] = {
        "xy": xy(fp.GetPosition()),
        "angle": fp.GetOrientationDegrees(),
        "courtyard": graphics,
        "pads": [
            {
                "pin": p.GetNumber(),
                "xy": xy(p.GetPosition()),
                "size": xy(p.GetSize()),
                "angle": p.GetOrientationDegrees(),
                "net": p.GetNetname(),
            }
            for p in fp.Pads()
        ],
    }
(ROOT / "layout_geometry.json").write_text(json.dumps(items))
