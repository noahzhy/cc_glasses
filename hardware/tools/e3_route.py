"""Connect remaining signal islands on a clearance-checked four-layer grid."""

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from e3_astar import search
import shapely
from scipy.ndimage import distance_transform_edt
from shapely.affinity import rotate, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

root = Path("hardware/ir_glasses/EVT_E3")
if os.environ.get("E3_ROUTE_LOG"):
    sys.stdout = open(os.environ["E3_ROUTE_LOG"], "w", buffering=1)
allow_ripup = os.environ.get("E3_ROUTE_RIPUP") == "1"
locked_nets = set(os.environ.get("E3_LOCK_NETS", "").split(","))
locked_nets.add("GND")
removed_tracks = set()
fanout_file = root / "u1_fanout_uuids.json"
protected = (
    set(json.loads(fanout_file.read_text())) if fanout_file.exists() else set()
)
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
step = float(os.environ.get("E3_ROUTE_GRID", "0.05"))


def shape(item):
    if item["kind"] in {"zone", "keepout"}:
        return Polygon(item["coords"]).buffer(0)
    if item["kind"] == "pad":
        if item.get("coords"):
            return Polygon(item["coords"]).buffer(0.1 if item["npth"] else 0)
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
routes = []
(root / "manual_routes.json").write_text("[]")
(root / "ripup_uuids.json").write_text("[]")
failed = set()
finished = set()
blocked_groups = set()
local_failed = set()
grid_cache = None
obstacle_cache = None
for net in [name for name in sys.argv[1:] for _ in range(96)]:
    if net in failed or net in finished:
        continue
    own = [i for i, item in enumerate(items) if item["net"] == net]
    if len(own) < 2:
        finished.add(net)
        continue
    parent = {i: i for i in own}

    def find(index):
        while parent[index] != index:
            index = parent[index]
        return index

    own_shapes = [shapes[i] for i in own]
    tree = shapely.STRtree(own_shapes)
    pairs = tree.query(own_shapes, predicate="dwithin", distance=0.001)
    for a, b in pairs.T:
        i, j = own[a], own[b]
        if a > b and set(items[i]["layers"]) & set(items[j]["layers"]):
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
        finished.add(net)
        locked_nets.add(net)
        continue
    candidates = [g for g in groups if frozenset(g) not in blocked_groups]
    if not candidates:
        failed.add(net)
        continue
    preferred_ref = os.environ.get("E3_SOURCE_REF")
    source = next(
        (
            g
            for g in candidates
            if preferred_ref
            and any(items[i].get("ref") == preferred_ref for i in g)
        ),
        candidates[0],
    )
    target = [i for group in groups if group is not source for i in group]
    extent = unary_union([shapes[i] for i in own]).buffer(12)
    extent = extent.intersection(board)
    if net.startswith(("PD_IN", "LED_K")) or net in {
        "3V3",
        "3V3_A",
        "AGND",
        "GND",
        "VREF_1V65",
    }:
        extent = board
    local_search = False
    if net in {"GND", "AGND"} and frozenset(source) not in local_failed:
        source_copper = unary_union([shapes[i] for i in source])
        bx0, by0, bx1, by1 = source_copper.bounds
        if max(bx1 - bx0, by1 - by0) < 6:
            extent = source_copper.buffer(5).intersection(board)
            local_search = True
    x0, y0, x1, y1 = extent.bounds
    xs = np.arange(math.floor(x0), math.ceil(x1) + step, step)
    ys = np.arange(math.floor(y0), math.ceil(y1) + step, step)
    xx, yy = np.meshgrid(xs, ys)
    height, width = xx.shape
    plane = height * width
    grid_key = (float(xs[0]), float(ys[0]), height, width)
    if grid_cache is None or grid_cache[0] != grid_key:
        grid_cache = (
            grid_key,
            raster(board.buffer(-0.385)),
            raster(board.buffer(-0.56)),
        )
    _, inside, via_inside = grid_cache
    foreign = [
        i
        for i, item in enumerate(items)
        if item["net"] != net and item["kind"] != "zone"
    ]
    local_pads = unary_union(
        [
            shapes[i]
            for i in source
            if items[i]["kind"] == "pad"
            or os.environ.get("E3_LOCAL_COPPER") == "1"
        ]
    )
    soft = [
        i
        for i in foreign
        if allow_ripup
        and items[i]["kind"] in {"track", "via"}
        and "uuid" in items[i]
        and items[i]["uuid"] not in protected
        and (
            items[i]["net"] not in locked_nets
            or (
                os.environ.get("E3_RIP_VIAS") == "1"
                and items[i]["kind"] == "via"
            )
            or (
                os.environ.get("E3_UNLOCK_LOCAL_PIN") == "1"
                and net in {"GND", "AGND"}
                and items[i]["kind"] == "track"
                and shapes[i].distance(local_pads) < 1.5
            )
            or (
                os.environ.get("E3_LOCAL_GROUND_RIP") == "1"
                and items[i]["net"] == "GND"
                and shapes[i].distance(local_pads) < 1.5
            )
            or (
                os.environ.get("E3_LOCAL_RIP") == "1"
                and shapes[i].distance(local_pads)
                < float(os.environ.get("E3_LOCAL_RADIUS", "1.5"))
            )
        )
    ]
    hard = [i for i in foreign if i not in soft]
    obstacle_key = (
        net,
        grid_key,
        tuple(hard),
        tuple(soft),
        len(removed_tracks),
    )
    fresh = obstacle_cache is None or obstacle_cache[0] != obstacle_key
    if fresh:
        blocked = np.empty((4, height, width), dtype=bool)
        rip_cost = np.zeros((4, height, width), dtype=bool)
        via_penalty = np.zeros((height, width), dtype=np.uint8)
    else:
        blocked = obstacle_cache[1].reshape(4, height, width)
        rip_cost = obstacle_cache[2].reshape(4, height, width)
    starts = np.zeros_like(blocked)
    targets = np.zeros_like(blocked)
    for layer in range(4):
        if fresh:
            obstacles = unary_union(
                [shapes[i] for i in hard if layer in items[i]["layers"]]
            ).buffer(0.227)
            blocked[layer] = raster(obstacles) | ~inside
            if soft:
                soft_copper = unary_union(
                    [shapes[i] for i in soft if layer in items[i]["layers"]]
                )
                rip_cost[layer] = raster(soft_copper.buffer(0.23))
                via_penalty += raster(soft_copper.buffer(0.41))
        for group, mask in [(source, starts), (target, targets)]:
            copper = unary_union(
                [shapes[i] for i in group if layer in items[i]["layers"]]
            )
            mask[layer] = raster(copper) & ~blocked[layer]
    if fresh:
        via_base = (
            raster(unary_union([shapes[i] for i in hard]).buffer(0.41))
            | ~via_inside
        )
        lands = [
            shapes[i]
            for i, item in enumerate(items)
            if item["kind"] == "pad" and not item.get("npth")
        ]
        via_base |= raster(unary_union(lands).buffer(0.31))
        obstacle_cache = (
            obstacle_key,
            blocked,
            rip_cost,
            via_base,
            via_penalty,
        )
    via_blocked = obstacle_cache[3].copy()
    via_blocked |= raster(
        unary_union(
            [
                Point(item["a"])
                for item in items
                if item["kind"] == "via" and item["net"] == net
            ]
        ).buffer(0.56)
    )
    distances = distance_transform_edt(~targets.any(axis=0)).ravel()
    blocked = blocked.ravel()
    goals = targets.ravel()
    via_blocked = via_blocked.ravel()
    via_rip_cost = obstacle_cache[4].ravel()
    rip_cost = rip_cost.ravel()
    print(
        net, "seeds/targets", int(starts.sum()), int(targets.sum()), flush=True
    )
    end, previous, expanded = search(
        starts.ravel(),
        goals,
        blocked,
        via_blocked,
        rip_cost,
        via_rip_cost,
        distances,
        width,
        height,
    )
    if end < 0:
        print(net, "needs local clearance repair:", expanded, flush=True)
        if local_search:
            local_failed.add(frozenset(source))
            continue
        blocked_groups.add(frozenset(source))
        if len(groups) == 2:
            failed.add(net)
        continue
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
        if via:
            local_x = int(round((a[1] - xs[0]) / step))
            local_y = int(round((a[2] - ys[0]) / step))
            assert not via_blocked[local_y * width + local_x], (net, a, b)
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
        for index in soft:
            if (
                set(item["layers"]) & set(items[index]["layers"])
                and shapes[-1].distance(shapes[index]) < 0.152
            ):
                removed_tracks.add(items[index]["uuid"])
                items[index]["layers"] = []
                items[index]["net"] = ""
                shapes[index] = Polygon()
    print(net, "path nodes:", len(path), "expanded:", expanded, flush=True)
    (root / "manual_routes.json").write_text(json.dumps(routes))
    if allow_ripup:
        (root / "ripup_uuids.json").write_text(
            json.dumps(sorted(removed_tracks))
        )
