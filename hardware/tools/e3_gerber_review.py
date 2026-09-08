"""Independently parse, check and render the exported EVT E3 CAM files."""

import hashlib
import json
import sys
import warnings
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))

import pymupdf  # noqa: E402
from gerbonara import LayerStack  # noqa: E402
from shapely.geometry import LineString, Polygon  # noqa: E402
from shapely.ops import polygonize_full, unary_union  # noqa: E402


ROOT = Path("hardware/ir_glasses/EVT_E3")
physical = json.loads((ROOT / "physical_summary.json").read_text())
pad_centers = {
    (p["ref"], p["pin"]): p["xy"]
    for p in json.loads((ROOT / "route_geometry.json").read_text())
    if p["kind"] == "pad" and p["net"]
}
VIEWS = {
    "top_copper": ("top", "copper", "#b87333"),
    "bottom_copper": ("bottom", "copper", "#276eac"),
    "inner_1": ("inner_1", "copper", "#904c9a"),
    "inner_2": ("inner_2", "copper", "#24816b"),
    "top_paste": ("top", "paste", "#292929"),
}


def inspect(folder, expected_holes):
    source = folder / "manufacturing"
    review = folder / "manufacturing_review"
    review.mkdir(exist_ok=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        stack = LayerStack.open(source)
    layers = stack.graphic_layers
    copper = [side for side, use in layers if use == "copper"]
    assert set(copper) == {"top", "bottom", "inner_1", "inner_2"}
    paste = layers["top", "paste"].objects
    refs = {obj.attrs[".C"][0] for obj in paste}
    lands = [
        obj
        for obj in layers["top", "copper"].objects
        if type(obj).__name__ == "Flash"
        and ".P" in obj.attrs
        and obj.attrs[".P"][0] in refs
    ]
    assert len(refs) == physical["assembly_references"]
    assert len(lands) == physical["assembly_copper_lands"]
    for land in lands:
        key = tuple(land.attrs[".P"][:2])
        if key in pad_centers:
            x, y = pad_centers[key]
            assert abs(land.x - x) < 0.00001, key
            assert abs(land.y + y) < 0.00001, key
    assert len(paste) == physical["expected_paste_openings"]
    assert all(type(obj).__name__ == "Flash" for obj in paste)
    assert ("bottom", "paste") not in layers
    pd_pins = {}
    for obj in lands:
        ref, pin = obj.attrs[".P"][:2]
        if ref.startswith("PD"):
            pd_pins.setdefault(ref, {})[pin] = obj.attrs[".N"][0]
    for index in range(1, 17):
        assert pd_pins[f"PD{index}"] == {"1": "GND", "2": f"PD_IN{index}"}

    outline = layers["mechanical", "outline"].objects
    assert all(type(obj).__name__ == "Line" for obj in outline)
    lines = [LineString([(o.x1, o.y1), (o.x2, o.y2)]) for o in outline]
    polygons, cuts, dangles, invalid = polygonize_full(unary_union(lines))
    assert cuts.is_empty and dangles.is_empty and invalid.is_empty
    material = max(polygons.geoms, key=lambda polygon: polygon.area)
    assert len(material.interiors) == expected_holes

    drill_counts = Counter()
    for layer in stack.drill_layers:
        assert layer is stack.drill_pth or layer is stack.drill_npth
        for obj in layer.objects:
            assert type(obj).__name__ == "Flash"
            drill_counts[(layer is stack.drill_pth, obj.tool.diameter)] += 1
    assert len(list(source.glob("*.drl"))) == 2
    assert (
        "TF.FileFunction,Plated" in next(source.glob("*-PTH.drl")).read_text()
    )
    assert (
        "TF.FileFunction,NonPlated"
        in next(source.glob("*-NPTH.drl")).read_text()
    )
    expected = {(True, 0.3): physical["via_count"], (False, 0.991): 3}
    if expected_holes == 10:
        expected[False, 2.0] = 4
    assert drill_counts == expected
    job_path = next(source.glob("*-job.gbrjob"))
    job = json.loads(job_path.read_text())
    specs = job["GeneralSpecs"]
    assert specs["Finish"] == "ENIG"
    assert specs["LayerNumber"] == 4 and specs["BoardThickness"] == 1.6

    xmin, ymin, xmax, ymax = material.bounds
    for name, (side, use, color) in VIEWS.items():
        colors = {
            f"{side} {use}": color,
            "mechanical outline": "#e04925",
            "drill pth": "#ffffff",
            "drill npth": "#111111",
        }
        svg = stack.to_svg(
            margin=1,
            side_re=f"{side}|mechanical",
            colors=colors,
            drills=use != "paste",
            force_bounds=((xmin, ymin), (xmax, ymax)),
        )
        path = review / f"{name}.svg"
        path.write_text(str(svg), encoding="utf-8")
        doc = pymupdf.open(path)
        doc[0].get_pixmap(matrix=pymupdf.Matrix(4, 4), alpha=False).save(
            path.with_suffix(".png")
        )
    result = {
        "parser": "gerbonara.LayerStack.open",
        "native_pcb_geometry_used": False,
        "preview_projection": "All layers use the board top projection.",
        "graphic_layers": [" ".join(key) for key in layers],
        "copper_layer_count": len(copper),
        "assembly_references": len(refs),
        "assembly_copper_lands": len(lands),
        "gerber_pad_centers_match_pcb_and_cpl_origin": True,
        "top_paste_openings": len(paste),
        "paste_note": "U1 exposed pad: 4 paste windows, 3 extra openings.",
        "pd_pin_nets_from_gerber_attributes": pd_pins,
        "closed_outline_holes": len(material.interiors),
        "outline_dangles_cuts_invalid": 0,
        "outline_centerline_bounds_mm": material.bounds,
        "drills": [
            {"plated": key[0], "diameter_mm": key[1], "count": value}
            for key, value in drill_counts.items()
        ],
        "drill_total": sum(drill_counts.values()),
        "separate_pth_npth": True,
        "plating_source": "Separate layer roles and X2 FileFunction headers",
        "finish": specs["Finish"],
        "thickness_mm": specs["BoardThickness"],
        "parser_warnings": [str(item.message) for item in caught],
        "file_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source.iterdir())
            if p.is_file()
        },
        "previews": [f"manufacturing_review/{name}.png" for name in VIEWS],
    }
    (review / "gerber_validation.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result, material


unit, bare = inspect(ROOT, 2)
carrier, panel = inspect(ROOT / "carrier", 10)
eyes = []
for ring in bare.interiors:
    hole = Polygon(ring)
    match = min(
        (Polygon(r) for r in panel.interiors),
        key=lambda polygon: polygon.centroid.distance(hole.centroid),
    )
    distance = hole.hausdorff_distance(match)
    assert distance <= 0.00001
    eyes.append(distance)
report = {
    "unit": unit,
    "carrier": carrier,
    "eye_hole_hausdorff_mm": eyes,
    "eye_hole_acceptance_mm": 0.00001,
    "visual_review_status": "pending",
}
(ROOT / "gerber_validation.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "unit_holes": 2,
            "carrier_holes": 10,
            "eye_hole_hausdorff_mm": eyes,
            "unit_drills": unit["drill_total"],
            "carrier_drills": carrier["drill_total"],
        },
        indent=2,
    )
)
