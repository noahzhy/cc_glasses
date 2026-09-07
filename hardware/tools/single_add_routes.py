"""Insert the clearance-checked finishing routes into KiCad."""

import json
import sys
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E")
path = root / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
layers = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]


def point(xy):
    return pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1]))


routes = json.loads(
    (
        root / (sys.argv[1] if len(sys.argv) > 1 else "manual_routes.json")
    ).read_text()
)
for item in routes:
    if item["kind"] == "via":
        track = pcb.PCB_VIA(board)
        track.SetPosition(point(item["a"]))
        track.SetDrill(pcb.FromMM(0.3))
        track.SetViaType(pcb.VIATYPE_THROUGH)
        track.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
    else:
        track = pcb.PCB_TRACK(board)
        track.SetStart(point(item["a"]))
        track.SetEnd(point(item["b"]))
        track.SetLayer(layers[item["layers"][0]])
    track.SetWidth(pcb.FromMM(item["width"]))
    track.SetNet(board.FindNet(item["net"]))
    board.Add(track)
pcb.SaveBoard(str(path), board)
print("Added route items:", len(routes))
