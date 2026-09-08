"""Give disconnected SMD lands a short, clearance-checked via escape."""

import heapq
import json
import math
from pathlib import Path

import numpy as np
import shapely
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path("hardware/ir_glasses/EVT_E3")
items = json.loads((ROOT / "route_geometry.json").read_text())
geometry = json.loads((ROOT / "geometry.json").read_text())
board = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)
targets = json.loads((ROOT / "escape_pads.json").read_text())
targets.sort(key=lambda p: (p[0] not in {"U14", "U13", "U12", "U1"}, p))
step = 0.025
routes = []


def copper(item):
    if item["kind"] in {"pad", "keepout"}:
        return Polygon(item["coords"]).buffer(0)
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


for ref, pin in targets:
    pad = next(
        p
        for p in items
        if p["kind"] == "pad" and p["ref"] == ref and p["pin"] == pin
    )
    net = pad["net"]
    x, y = pad["xy"]
    local_box = Point(x, y).buffer(5).envelope
    local = [(p, copper(p)) for p in items]
    local = [(p, s) for p, s in local if s.intersects(local_box)]
    foreign = [(p, s) for p, s in local if p["net"] != net]
    front = unary_union([s for p, s in foreign if 0 in p["layers"]])
    all_copper = unary_union([s for p, s in foreign if p["kind"] != "keepout"])
    lands = unary_union([s for p, s in local if p["kind"] == "pad"])
    keepouts = unary_union([s for p, s in local if p["kind"] == "keepout"])
    own_vias = unary_union(
        [s for p, s in local if p["kind"] == "via" and p["net"] == net]
    )
    xs = np.arange(x - 5, x + 5.001, step)
    ys = np.arange(y - 5, y + 5.001, step)
    xx, yy = np.meshgrid(xs, ys)

    def raster(shape):
        shapely.prepare(shape)
        return shapely.contains_xy(shape, xx, yy)

    blocked = raster(front.buffer(0.228)) | ~raster(board.buffer(-0.386))
    existing = raster(own_vias.buffer(-0.15)) & ~blocked
    goals = (
        ~raster(all_copper.buffer(0.405))
        & ~raster(lands.buffer(0.315))
        & ~raster(keepouts)
        & ~raster(own_vias.buffer(0.41))
        & raster(board.buffer(-0.565))
    ) | existing
    starts = raster(copper(pad)) & ~blocked
    height, width = blocked.shape
    blocked, goals, existing = blocked.ravel(), goals.ravel(), existing.ravel()
    cost = np.full(height * width, np.inf)
    previous = np.full(height * width, -1, dtype=np.int32)
    queue = []
    for node in np.flatnonzero(starts):
        cost[node] = 0
        heapq.heappush(queue, (0, int(node)))
    end = None
    while queue:
        value, node = heapq.heappop(queue)
        if value > cost[node] + 1e-8:
            continue
        if goals[node]:
            end = node
            break
        row, col = divmod(node, width)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if not (dx or dy) or not 0 <= col + dx < width:
                    continue
                if not 0 <= row + dy < height:
                    continue
                other = node + dy * width + dx
                candidate = value + math.hypot(dx, dy)
                if not blocked[other] and candidate < cost[other] - 1e-8:
                    cost[other] = candidate
                    previous[other] = node
                    heapq.heappush(queue, (candidate, other))
    if end is None:
        print(ref, pin, net, "NO ESCAPE", flush=True)
        continue
    endpoint = end
    path = []
    while end >= 0:
        row, col = divmod(end, width)
        path.append([round(xs[col], 6), round(ys[row], 6)])
        end = int(previous[end])
    path.reverse()
    simple = [path[0]]
    for a, b, c in zip(path, path[1:], path[2:]):
        if (
            abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]))
            > 1e-9
        ):
            simple.append(b)
    simple.append(path[-1])
    for a, b in zip(simple, simple[1:]):
        if a != b:
            route = dict(
                kind="track", net=net, a=a, b=b, width=0.15, layers=[0]
            )
            items.append(route)
            routes.append(route)
    if not existing[endpoint]:
        route = dict(
            kind="via",
            net=net,
            a=path[-1],
            b=path[-1],
            width=0.5,
            layers=[0, 1, 2, 3],
        )
        items.append(route)
        routes.append(route)
    print(ref, pin, net, "escape", path[-1], flush=True)
    (ROOT / "fanout_routes.json").write_text(json.dumps(routes))
