"""Insert the planned ground stitching vias."""

import json
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_D")
p = root / "ir_glasses.kicad_pcb"
b = pcb.LoadBoard(str(p))
for item in json.loads((root / "stitches.json").read_text()):
    v = pcb.PCB_VIA(b)
    v.SetPosition(pcb.VECTOR2I(pcb.FromMM(item["x"]), pcb.FromMM(item["y"])))
    v.SetWidth(pcb.FromMM(0.6))
    v.SetDrill(pcb.FromMM(0.3))
    v.SetViaType(pcb.VIATYPE_THROUGH)
    v.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
    v.SetNet(b.FindNet(item["net"]))
    b.Add(v)
pcb.SaveBoard(str(p), b)
