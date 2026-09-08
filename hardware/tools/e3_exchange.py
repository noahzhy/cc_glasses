"""Export a routing exchange with explicit via exclusion over SMD lands."""

import json
import shutil
import sys
from pathlib import Path

import pcbnew as pcb

root = Path("hardware/ir_glasses/EVT_E3")
fresh = "--fresh" in sys.argv
path = root / "ir_glasses.kicad_pcb"
if fresh:
    sys.path.insert(0, str(Path(__file__).parent / "pylib"))
    import sexpdata as sx

    tree = sx.loads(path.read_text(encoding="utf-8"))
    tree = [
        n
        for n in tree
        if not (
            isinstance(n, list)
            and (
                str(n[0]) in {"segment", "via", "zone"}
                or any(
                    isinstance(v, list)
                    and str(v[0]) == "layer"
                    and v[1] == "Edge.Cuts"
                    for v in n
                )
            )
        )
    ]
    path = root / "routing_fresh_input.kicad_pcb"
    path.write_text(sx.dumps(tree), encoding="utf-8")
    shutil.copyfile(
        root / "ir_glasses.kicad_pro", path.with_suffix(".kicad_pro")
    )
board = pcb.LoadBoard(str(path))
if fresh:
    outlines = json.loads((root / "routing_outline.json").read_text())
    for ring in outlines:
        for a, b in zip(ring, ring[1:]):
            line = pcb.PCB_SHAPE(board)
            line.SetShape(pcb.SHAPE_T_SEGMENT)
            line.SetStart(pcb.VECTOR2I(*[pcb.FromMM(v) for v in a]))
            line.SetEnd(pcb.VECTOR2I(*[pcb.FromMM(v) for v in b]))
            line.SetLayer(pcb.Edge_Cuts)
            line.SetWidth(pcb.FromMM(0.05))
            board.Add(line)
count = 0
for footprint in board.GetFootprints():
    for pad in footprint.Pads():
        if not pad.IsOnLayer(pcb.F_Cu):
            continue
        if pad.GetAttribute() == pcb.PAD_ATTRIB_NPTH:
            continue
        polygon = pad.GetEffectivePolygon(pcb.F_Cu).COutline(0)
        zone = pcb.ZONE(board)
        zone.SetIsRuleArea(True)
        zone.SetLayer(pcb.F_Cu)
        zone.SetDoNotAllowVias(True)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowFootprints(False)
        zone.SetDoNotAllowZoneFills(False)
        zone.Outline().NewOutline()
        for index in range(polygon.PointCount()):
            zone.Outline().Append(polygon.CPoint(index))
        board.Add(zone)
        count += 1
name = "routing_fresh.dsn" if fresh else "routing_keepouts.dsn"
assert pcb.ExportSpecctraDSN(board, str(root / name))
print("Exported via exclusions:", count)
