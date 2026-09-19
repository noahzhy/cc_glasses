"""Export actual copper polygons for local route checks."""

import hashlib
import json
from pathlib import Path

import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
LAYERS = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]


def point(p):
    return [pcb.ToMM(p.x), pcb.ToMM(p.y)]


def export():
    path = ROOT / f"{ROOT.name}.kicad_pcb"
    board = pcb.LoadBoard(str(path))
    (ROOT / "review/geometry_source.json").write_text(
        json.dumps(
            {"board_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    )
    rows = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            polygons = []
            for layer in LAYERS:
                if not pad.IsOnLayer(layer):
                    continue
                p = pad.GetEffectivePolygon(layer)
                for i in range(p.OutlineCount()):
                    ring = p.COutline(i)
                    polygons.append(
                        [
                            LAYERS.index(layer),
                            [
                                point(ring.CPoint(j))
                                for j in range(ring.PointCount())
                            ],
                        ]
                    )
            rows.append(
                dict(
                    kind="pad",
                    ref=fp.GetReference(),
                    pin=pad.GetNumber(),
                    net=pad.GetNetname(),
                    id=pad.m_Uuid.AsString(),
                    xy=point(pad.GetPosition()),
                    polygons=polygons,
                    drill=max(point(pad.GetDrillSize())),
                )
            )
    tracks = board.GetTracks()
    for i in range(len(tracks)):
        t = tracks[i]
        via = isinstance(t, pcb.PCB_VIA)
        rows.append(
            dict(
                kind="via" if via else "track",
                net=t.GetNetname(),
                id=t.m_Uuid.AsString(),
                a=point(t.GetStart()),
                b=point(t.GetEnd()),
                width=pcb.ToMM(t.GetWidth(pcb.F_Cu) if via else t.GetWidth()),
                layers=list(range(4)) if via else [LAYERS.index(t.GetLayer())],
                drill=pcb.ToMM(t.GetDrill()) if via else 0,
            )
        )
    (ROOT / "review/copper_geometry.json").write_text(json.dumps(rows))
    route_rows = []
    for row in rows:
        item = dict(row, uuid=row["id"])
        if row["kind"] == "pad":
            front = [p for layer, p in row["polygons"] if layer == 0]
            if not front:
                continue
            item.update(
                coords=front[0],
                layers=[p[0] for p in row["polygons"]],
                npth=not row["net"] and row["drill"] > 0,
            )
        route_rows.append(item)
    (ROOT / "review/route_geometry.json").write_text(json.dumps(route_rows))
    regions = []
    zones = board.Zones()
    for index in range(len(zones)):
        zone = zones[index]
        if zone.GetIsRuleArea():
            continue
        polygons = zone.GetFilledPolysList(zone.GetLayer())
        for i in range(polygons.OutlineCount()):
            outer = polygons.Outline(i)
            holes = []
            for j in range(polygons.HoleCount(i)):
                hole = polygons.Hole(i, j)
                holes.append(
                    [point(hole.CPoint(k)) for k in range(hole.PointCount())]
                )
            regions.append(
                dict(
                    net=zone.GetNetname(),
                    layer=board.GetLayerName(zone.GetLayer()),
                    coords=[
                        point(outer.CPoint(k))
                        for k in range(outer.PointCount())
                    ],
                    holes=holes,
                )
            )
    (ROOT / "review/filled_regions.json").write_text(json.dumps(regions))
    print("Exported", len(rows), "copper objects")


if __name__ == "__main__":
    export()
