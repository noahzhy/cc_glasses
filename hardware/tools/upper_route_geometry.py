"""Export layer-aware copper geometry for finishing the remaining nets."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_D")
board = pcb.LoadBoard(str(root / "ir_glasses.kicad_pcb"))
layers = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]


def point(value):
    return [pcb.ToMM(value.x), pcb.ToMM(value.y)]


items = []
for fp in board.GetFootprints():
    for pad in fp.Pads():
        items.append(
            {
                "kind": "pad",
                "net": pad.GetNetname(),
                "ref": fp.GetReference(),
                "pin": pad.GetNumber(),
                "xy": point(pad.GetPosition()),
                "size": point(pad.GetSize()),
                "angle": pad.GetOrientationDegrees(),
                "circle": pad.GetShape() == pcb.PAD_SHAPE_CIRCLE,
                "npth": pad.GetAttribute() == pcb.PAD_ATTRIB_NPTH,
                "layers": [
                    i for i, layer in enumerate(layers) if pad.IsOnLayer(layer)
                ],
            }
        )
for track in board.GetTracks():
    via = isinstance(track, pcb.PCB_VIA)
    items.append(
        {
            "kind": "via" if via else "track",
            "net": track.GetNetname(),
            "uuid": track.m_Uuid.AsString(),
            "a": point(track.GetStart()),
            "b": point(track.GetEnd()),
            "width": pcb.ToMM(
                track.GetWidth(pcb.F_Cu) if via else track.GetWidth()
            ),
            "layers": list(range(4))
            if via
            else [layers.index(track.GetLayer())],
        }
    )
(root / "route_geometry.json").write_text(json.dumps(items))
