"""Connect remaining signal islands on a clearance-checked four-layer grid."""

import heapq
import json
import math
from pathlib import Path

import numpy as np
import shapely
from scipy.ndimage import distance_transform_edt
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_D")
items = json.loads((root / "route_geometry.json").read_text())
for region in json.loads((root / "filled_regions.json").read_text()):
    items.append(
        {
            "kind": "zone",
            "net": region["net"],
            "coords": region["coords"],
            "layers": [
                ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"].index(region["layer"])
            ],
        }
    )
geometry = json.loads((root / "geometry.json").read_text())
board = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)
step = 0.1
x0, y0, x1, y1 = board.bounds
xs = np.arange(math.floor(x0), math.ceil(x1) + step, step)
ys = np.arange(math.floor(y0), math.ceil(y1) + step, step)
xx, yy = np.meshgrid(xs, ys)
height, width = xx.shape
plane = height * width


def shape(item):
    if item["kind"] == "zone":
        return Polygon(item["coords"]).buffer(0)
    if item["kind"] == "pad":
        x, y = item["size"]
        copper = (
            Point(0, 0).buffer(x / 2)
            if item["circle"]
            else box(-x / 2, -y / 2, x / 2, y / 2)
        )
        return translate(
            rotate(
                copper.buffer(0.1) if item.get("npth") else copper,
                -item["angle"],
                origin=(0, 0),
            ),
            *item["xy"],
        )
    if item["kind"] == "via":
        return Point(item["a"]).buffer(item["width"] / 2)
    return LineString([item["a"], item["b"]]).buffer(item["width"] / 2)


def raster(polygon):
    shapely.prepare(polygon)
    return shapely.contains_xy(polygon, xx, yy)


shapes = [shape(item) for item in items]
inside = raster(board.buffer(-0.385))
via_inside = raster(board.buffer(-0.56))
routes = []
for net in ["GND"] * 6 + ["AGND"] * 5:
    own = [i for i, item in enumerate(items) if item["net"] == net]
    parent = {i: i for i in own}

    def find(index):
        while parent[index] != index:
            index = parent[index]
        return index

    for k, i in enumerate(own):
        for j in own[:k]:
            if set(items[i]["layers"]) & set(items[j]["layers"]):
                if shapes[i].distance(shapes[j]) < 0.001:
                    parent[find(i)] = find(j)
    groups = {}
    for i in own:
        groups.setdefault(find(i), []).append(i)
    groups = sorted(
        groups.values(), key=lambda group: sum(shapes[i].area for i in group)
    )
    print(
        net, "connected component sizes:", [len(g) for g in groups], flush=True
    )
    if len(groups) == 1:
        continue
    source = groups[0]
    target = [i for group in groups[1:] for i in group]
    foreign = [
        i
        for i, item in enumerate(items)
        if item["net"] != net and item["kind"] != "zone"
    ]
    blocked = np.empty((4, height, width), dtype=bool)
    starts = np.zeros_like(blocked)
    targets = np.zeros_like(blocked)
    for layer in range(4):
        obstacles = unary_union(
            [shapes[i] for i in foreign if layer in items[i]["layers"]]
        ).buffer(0.227)
        blocked[layer] = raster(obstacles) | ~inside
        for group, mask in [(source, starts), (target, targets)]:
            copper = unary_union(
                [shapes[i] for i in group if layer in items[i]["layers"]]
            )
            mask[layer] = raster(copper) & ~blocked[layer]
    via_blocked = (
        raster(unary_union([shapes[i] for i in foreign]).buffer(0.41))
        | ~via_inside
    )
    for item in items:
        if item["kind"] == "via" and item["net"] == net:
            via_blocked |= raster(Point(item["a"]).buffer(0.56))
    distances = distance_transform_edt(~targets.any(axis=0)).ravel()
    costs = np.full(4 * plane, np.inf, dtype=np.float32)
    previous = np.full(4 * plane, -1, dtype=np.int32)
    blocked = blocked.ravel()
    goals = targets.ravel()
    via_blocked = via_blocked.ravel()
    queue = []
    for node in np.flatnonzero(starts):
        costs[node] = 0
        heapq.heappush(queue, (distances[node % plane], 0, int(node)))
    moves = [
        (dx, dy, math.hypot(dx, dy))
        for dx in [-1, 0, 1]
        for dy in [-1, 0, 1]
        if dx or dy
    ]
    print(
        net, "seeds/targets", int(starts.sum()), int(targets.sum()), flush=True
    )
    end = None
    expanded = 0
    while queue:
        _, cost, node = heapq.heappop(queue)
        if cost > costs[node] + 0.0001:
            continue
        if goals[node]:
            end = node
            break
        layer, local = divmod(node, plane)
        y, x = divmod(local, width)
        neighbors = []
        for dx, dy, length in moves:
            if 0 <= x + dx < width and 0 <= y + dy < height:
                other = node + dy * width + dx
                if not blocked[other]:
                    neighbors.append((other, length))
        if not via_blocked[local]:
            neighbors += [
                (other * plane + local, 20)
                for other in range(4)
                if other != layer and not blocked[other * plane + local]
            ]
        for other, length in neighbors:
            value = cost + length
            if value + 0.0001 < costs[other]:
                costs[other] = value
                previous[other] = node
                heapq.heappush(
                    queue,
                    (value + distances[other % plane] * 1.15, value, other),
                )
        expanded += 1
    assert end is not None, (net, expanded)
    path = []
    while end >= 0:
        layer, local = divmod(end, plane)
        y, x = divmod(local, width)
        path.append((layer, round(xs[x], 5), round(ys[y], 5)))
        end = int(previous[end])
    path.reverse()
    simplified = [path[0]]
    for a, b, c in zip(path, path[1:], path[2:]):
        if not (
            a[0] == b[0] == c[0]
            and abs(
                (b[1] - a[1]) * (c[2] - b[2]) - (b[2] - a[2]) * (c[1] - b[1])
            )
            < 1e-8
        ):
            simplified.append(b)
    simplified.append(path[-1])
    for a, b in zip(simplified, simplified[1:]):
        via = a[0] != b[0]
        item = {
            "kind": "via" if via else "track",
            "net": net,
            "a": list(a[1:]),
            "b": list(b[1:]),
            "width": 0.5 if via else 0.15,
            "layers": list(range(4)) if via else [a[0]],
        }
        items.append(item)
        shapes.append(shape(item))
        routes.append(item)
    print(net, "path nodes:", len(path), "expanded:", expanded, flush=True)
    (root / "ground_routes.json").write_text(json.dumps(routes))
