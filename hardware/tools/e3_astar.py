"""Accelerate the clearance-grid search without changing copper rules."""

import heapq
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "routerlib"))
from numba import njit  # noqa: E402


@njit(cache=True)
def search(
    starts,
    goals,
    blocked,
    via_blocked,
    rip_cost,
    via_rip_cost,
    distances,
    width,
    height,
):
    plane = width * height
    costs = np.full(4 * plane, np.inf)
    previous = np.full(4 * plane, -1, dtype=np.int32)
    queue = [(0.0, 0.0, 0)]
    queue.pop()
    for node in np.flatnonzero(starts):
        costs[node] = 0
        heapq.heappush(queue, (distances[node % plane], 0.0, int(node)))
    expanded = 0
    while queue:
        _, cost, node = heapq.heappop(queue)
        if cost > costs[node] + 0.0001:
            continue
        if goals[node]:
            return node, previous, expanded
        layer = node // plane
        local = node % plane
        y, x = local // width, local % width
        for move in range(12):
            if move < 8:
                dx = (-1, -1, -1, 0, 0, 1, 1, 1)[move]
                dy = (-1, 0, 1, -1, 1, -1, 0, 1)[move]
                if not (0 <= x + dx < width and 0 <= y + dy < height):
                    continue
                other = node + dy * width + dx
                length = 1.41421356237 if dx and dy else 1.0
                length += 25 * rip_cost[other]
            else:
                other_layer = move - 8
                if via_blocked[local] or other_layer == layer:
                    continue
                other = other_layer * plane + local
                length = 20.0 + 50 * via_rip_cost[local]
            if blocked[other]:
                continue
            value = cost + length
            if value + 0.0001 < costs[other]:
                costs[other] = value
                previous[other] = node
                priority = value + distances[other % plane] * 2.0
                heapq.heappush(queue, (priority, value, other))
        expanded += 1
        if expanded >= 4000000:
            break
    return -1, previous, expanded
