"""Check carrier isolation, reference copper and via assembly spacing."""

import json
from collections import Counter

from check_reference import check_reference
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "review"


def check():
    geometry = json.loads((REVIEW / "geometry.json").read_text())
    board = translate(Polygon(geometry["outer"], geometry["holes"]), 110, 85)
    rows = json.loads((REVIEW / "copper_geometry.json").read_text())
    pads = [
        (f"{r['ref']}.{r['pin']}", Polygon(points))
        for r in rows
        if r["kind"] == "pad" and r["drill"] == 0
        for layer, points in r["polygons"]
        if layer in {0, 3}
    ]
    routes = [r for r in rows if r["kind"] != "pad"]
    outside = []
    gaps = []
    for row in routes:
        via = row["kind"] == "via"
        center = Point(row["a"]) if via else LineString([row["a"], row["b"]])
        copper = center.buffer(row["width"] / 2)
        if not board.buffer(0.002).covers(copper):
            outside.append(row["id"])
        if via:
            gap, pad = min(
                (center.distance(p) - row["drill"] / 2, ref) for ref, p in pads
            )
            gaps.append(
                dict(
                    uuid=row["id"],
                    net=row["net"],
                    xy=row["a"],
                    nearest_pad=pad,
                    hole_to_pad_mm=gap,
                )
            )
    gaps.sort(key=lambda row: row["hole_to_pad_mm"])
    bad_vias = [row for row in gaps if row["hole_to_pad_mm"] < 0.10 - 1e-6]
    foreign_ground_tracks = [
        r["id"]
        for r in routes
        if r["kind"] == "track" and r["layers"] == [1] and r["net"] != "GND"
    ]
    regions = json.loads((REVIEW / "filled_regions.json").read_text())
    ground = unary_union(
        [
            Polygon(r["coords"], r.get("holes", []))
            for r in regions
            if r["layer"] == "In1.Cu" and r["net"] == "GND"
        ]
    )
    reference = check_reference()
    result = dict(
        reference_projection=reference,
        board_sha256=json.loads((REVIEW / "geometry_source.json").read_text())[
            "board_sha256"
        ],
        routes_outside_baseboard=outside,
        via_hole_to_pad_violations=bad_vias,
        minimum_hole_to_pad_mm=gaps[0]["hole_to_pad_mm"],
        nearest_vias=gaps[:10],
        nonground_tracks_on_reference_layer=foreign_ground_tracks,
        ground_regions=1
        if ground.geom_type == "Polygon"
        else len(ground.geoms),
        ground_area_mm2=ground.area,
        route_objects_by_layer=dict(Counter(str(r["layers"]) for r in routes)),
        scope="Geometric checks; mask registration and tenting require DFM",
    )
    (REVIEW / "geometry_checks.json").write_text(json.dumps(result, indent=2))
    print({k: v for k, v in result.items() if k != "nearest_vias"})
    assert not outside and not bad_vias and not reference["violations"]
    assert result["ground_regions"] == 1


if __name__ == "__main__":
    check()
