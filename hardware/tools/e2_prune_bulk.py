"""Remove long orphaned routing chains without disturbing their junctions."""

import sys
from collections import defaultdict
from pathlib import Path

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402


path = Path("hardware/ir_glasses/EVT_E2/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))
connectivity = board.GetConnectivity()
connectivity.Build(board)
tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()
          if t.GetClass() == "PCB_TRACK"}
ends = defaultdict(list)


def key(track, pos):
    return track.GetNetname(), track.GetLayer(), pos.x, pos.y


for uid, track in tracks.items():
    for pos in [track.GetStart(), track.GetEnd()]:
        ends[key(track, pos)].append(uid)
removed = set()
for uid, track in tracks.items():
    pos = pcb.VECTOR2I(0, 0)
    if track.GetNetname() != "LED_K3":
        continue
    if not connectivity.TestTrackEndpointDangling(track, False, pos):
        continue
    while uid not in removed:
        track = tracks[uid]
        if connectivity.GetConnectedPads(track):
            break
        a, b = track.GetStart(), track.GetEnd()
        dx, dy = b.x - a.x, b.y - a.y
        length2 = dx * dx + dy * dy
        interior = False
        for other in connectivity.GetConnectedTracks(track):
            if other.m_Uuid.AsString() in removed:
                continue
            if other.GetClass() == "PCB_VIA":
                interior = True
                break
            for candidate in [other.GetStart(), other.GetEnd()]:
                along = ((candidate.x - a.x) * dx
                         + (candidate.y - a.y) * dy) / length2
                gap2 = ((candidate.x - a.x - along * dx) ** 2
                        + (candidate.y - a.y - along * dy) ** 2)
                limit = (track.GetWidth() + other.GetWidth()) / 2 + 1000
                if 0.00001 < along < 0.99999 and gap2 < limit ** 2:
                    interior = True
        if interior:
            break
        other_end = b if pos == a else a
        removed.add(uid)
        adjacent = [value for value in ends[key(track, other_end)]
                    if value not in removed]
        if len(adjacent) != 1:
            break
        uid = adjacent[0]
        pos = other_end
tree = sx.loads(path.read_text(encoding="utf-8"))
for node in tree[:]:
    if not isinstance(node, list) or not node or str(node[0]) != "segment":
        continue
    uid = next(x[1] for x in node if isinstance(x, list)
               and x and str(x[0]) == "uuid")
    if uid in removed:
        tree.remove(node)
path.write_text(sx.dumps(tree), encoding="utf-8")
print("Removed orphaned chain segments:", len(removed))
