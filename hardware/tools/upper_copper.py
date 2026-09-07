"""Export copper geometry for ground stitching checks."""

import json
from pathlib import Path

import pcbnew as pcb

b = pcb.LoadBoard("hardware/ir_glasses/EVT_D/ir_glasses.kicad_pcb")


def point(p):
    return [pcb.ToMM(p.x), pcb.ToMM(p.y)]


items = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        rect = pad.GetBoundingBox()
        items.append(
            {
                "type": "pad",
                "net": pad.GetNetname(),
                "box": [*point(rect.GetPosition()), *point(rect.GetEnd())],
            }
        )
for t in b.GetTracks():
    items.append(
        {
            "type": "via" if isinstance(t, pcb.PCB_VIA) else "track",
            "net": t.GetNetname(),
            "a": point(t.GetStart()),
            "b": point(t.GetEnd()),
            "width": pcb.ToMM(
                t.GetWidth(pcb.F_Cu)
                if isinstance(t, pcb.PCB_VIA)
                else t.GetWidth()
            ),
            "layer": t.GetLayerName(),
        }
    )
Path("hardware/ir_glasses/EVT_D/copper.json").write_text(json.dumps(items))
