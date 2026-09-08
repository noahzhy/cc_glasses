"""Trim obsolete signal tails using KiCad's native connectivity graph."""

import json
import math
import sys
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402


ROOT = Path("hardware/ir_glasses/EVT_E3")
path = ROOT / "ir_glasses.kicad_pcb"
board = pcb.LoadBoard(str(path))
connectivity = board.GetConnectivity()
report = json.loads((ROOT / "drc.json").read_text(encoding="utf-8"))
unused = set()
if "--remove-unused-vias" in sys.argv:
    current = {t.m_Uuid.AsString() for t in board.GetTracks()}
    unused = {
        item["uuid"]
        for v in report["violations"]
        if v["type"] == "via_dangling"
        for item in v["items"]
    }
    unused &= current
actions = {uid: None for uid in unused}
for iteration in range(1):
    connectivity.Build(board)
    changed = 0
    for track in list(board.GetTracks()):
        if track.GetClass() == "PCB_VIA":
            continue
        if track.GetNetname() in {"AGND", "GND"}:
            continue
        if not connectivity.TestTrackEndpointDangling(track, False):
            continue
        a, b = track.GetStart(), track.GetEnd()
        dx, dy = b.x - a.x, b.y - a.y
        length2 = dx * dx + dy * dy
        if length2 == 0:
            actions[track.m_Uuid.AsString()] = None
            changed += 1
            continue
        anchors = []
        for pad in connectivity.GetConnectedPads(track):
            pos = pad.GetPosition()
            along = ((pos.x - a.x) * dx + (pos.y - a.y) * dy) / length2
            anchors.append(max(0.0, min(1.0, along)))
        for other in connectivity.GetConnectedTracks(track):
            width = (
                pcb.Cast_to_PCB_VIA(other).GetWidth(pcb.F_Cu)
                if other.GetClass() == "PCB_VIA"
                else other.GetWidth()
            )
            clearance = (track.GetWidth() + width) / 2 + 1000
            for pos in [other.GetStart(), other.GetEnd()]:
                along = ((pos.x - a.x) * dx + (pos.y - a.y) * dy) / length2
                along = max(0.0, min(1.0, along))
                gap = math.hypot(
                    pos.x - a.x - along * dx, pos.y - a.y - along * dy
                )
                if gap <= clearance:
                    anchors.append(along)
        if len(anchors) < 2 or max(anchors) - min(anchors) < 0.00001:
            actions[track.m_Uuid.AsString()] = None
            changed += 1
            continue
        first, last = min(anchors), max(anchors)
        start = pcb.VECTOR2I(round(a.x + first * dx), round(a.y + first * dy))
        end = pcb.VECTOR2I(round(a.x + last * dx), round(a.y + last * dy))
        if start != a or end != b:
            actions[track.m_Uuid.AsString()] = [
                [pcb.ToMM(start.x), pcb.ToMM(start.y)],
                [pcb.ToMM(end.x), pcb.ToMM(end.y)],
            ]
            changed += 1
    print("Pruning pass", iteration + 1, "changed", changed, flush=True)
    if not changed:
        break
tree = sx.loads(path.read_text(encoding="utf-8"))
for node in tree[:]:
    if (
        not isinstance(node, list)
        or not node
        or str(node[0]) not in {"segment", "via"}
    ):
        continue
    uid = next(
        x[1] for x in node if isinstance(x, list) and x and str(x[0]) == "uuid"
    )
    if uid not in actions:
        continue
    if actions[uid] is None:
        tree.remove(node)
    else:
        for key, value in zip(["start", "end"], actions[uid]):
            item = next(
                x
                for x in node
                if isinstance(x, list) and x and str(x[0]) == key
            )
            item[1:3] = value
if actions:
    path.write_text(sx.dumps(tree), encoding="utf-8")
print("Actions:", len(actions))
