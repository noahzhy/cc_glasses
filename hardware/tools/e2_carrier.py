"""Build a removable 1-up carrier around the released EVT E2 board."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path("hardware/ir_glasses/EVT_E2")
OUT = ROOT / "carrier"
KICAD = Path("D:/Program Files/KiCad/10.0")
ORIGIN = (110.0, 85.0)


def geometry():
    """Prepare the connected panel and its final router cut paths."""
    from shapely.affinity import translate
    from shapely.geometry import LineString, Polygon, box, mapping
    from shapely.ops import unary_union

    source = json.loads((ROOT / "geometry.json").read_text())
    board = translate(Polygon(source["outer"], source["holes"]),
                      xoff=ORIGIN[0], yoff=ORIGIN[1])
    left, top, right, bottom = board.bounds
    inner = box(left - 2, top - 2, right + 2, bottom + 2)
    outer = box(left - 10, top - 10, right + 10, bottom + 10)
    tabs = []
    for x in (60.0, 95.0, 125.0, 160.0):
        tabs.append(box(x - 1.5, top - 3, x + 1.5, top + 1))
    for x in (74.0, 146.0):
        edge = board.exterior.intersection(
            LineString([(x, bottom - 12), (x, bottom + 1)]))
        y = max(point.y for point in getattr(edge, "geoms", [edge]))
        tabs.append(box(x - 1.5, y - 1, x + 1.5, bottom + 3))
    tabs.extend([box(left - 3, 84.5, left + 4, 87.5),
                 box(right - 4, 84.5, right + 3, 87.5)])
    panel = unary_union([outer.difference(inner), board, *tabs])
    eye_holes = unary_union([Polygon(ring) for ring in board.interiors])
    panel = panel.difference(eye_holes)
    tabs = [tab.intersection(panel) for tab in tabs]
    assert panel.geom_type == "Polygon" and panel.is_valid
    assert len(panel.interiors) == 10
    cuts = board.exterior.intersection(unary_union(tabs))
    cut_lines = list(getattr(cuts, "geoms", [cuts]))
    keepouts = [board.exterior.intersection(tab).buffer(0.3, cap_style=3,
                                                     join_style=2)
                for tab in tabs]
    x0, y0, x1, y1 = outer.bounds
    data = {
        "origin_mm": ORIGIN,
        "board_bbox_mm": board.bounds,
        "carrier_bbox_mm": outer.bounds,
        "rail_width_mm": 8.0,
        "minimum_board_to_rail_gap_mm": 2.0,
        "tab_nominal_width_mm": 3.0,
        "outer": list(panel.exterior.coords),
        "holes": [list(ring.coords) for ring in panel.interiors],
        "bare_board": mapping(board),
        "tabs": [mapping(tab) for tab in tabs],
        "final_router_paths": [list(line.coords) for line in cut_lines],
        "cut_zone_keepouts": [list(area.exterior.coords)
                              for area in keepouts],
        "npth_centers_mm": [(x0 + 4, y0 + 4), (x1 - 4, y0 + 4),
                            (x0 + 4, y1 - 4), (x1 - 4, y1 - 4)],
        "fiducial_centers_mm": [(x0 + 16, y0 + 4), (x1 - 19, y0 + 4),
                                (x0 + 16, y1 - 4)],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "carrier_geometry.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8")
    drawing(data, board, tabs)
    dimensions = {
        "裸板外包络": f"{right - left:.3f} × {bottom - top:.3f} mm，"
        "以最终裸板 Edge.Cuts 为准",
        "载框外包络": f"{x1 - x0:.3f} × {y1 - y0:.3f} mm",
        "外框坐标": f"X {x0:.6f}～{x1:.6f}；Y {y0:.6f}～{y1:.6f} mm",
    }
    path = ROOT / "carrier_design.md"
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        for name, value in dimensions.items():
            if line.startswith(f"| {name} |"):
                lines[index] = f"| {name} | {value} |"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return data


def drawing(data, board, tabs):
    """Write a dimensioned fabrication review drawing."""
    x0, y0, x1, y1 = data["carrier_bbox_mm"]

    def path(rings):
        return " ".join("M " + " L ".join(f"{x:.4f},{y:.4f}" for x, y in ring)
                        + " Z" for ring in rings)

    board_rings = [board.exterior.coords]
    board_rings.extend(ring.coords for ring in board.interiors)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{x1 - x0 + 6:.6f}mm" '
        f'height="{y1 - y0 + 23:.6f}mm" '
        f'viewBox="{x0 - 3} {y0 - 10} {x1 - x0 + 6} {y1 - y0 + 23}">',
        '<rect x="0" y="0" width="300" height="250" fill="white"/>',
        '<g stroke-width="0.12" fill-rule="evenodd">',
        f'<path d="{path([data["outer"], *data["holes"]])}" '
        'fill="#e6e8eb" stroke="#333"/>',
        f'<path d="{path(board_rings)}" '
        'fill="#bfdcc7" stroke="#236d3b"/>',
    ]
    for tab in tabs:
        parts.append(f'<path d="{path([tab.exterior.coords])}" '
                     'fill="#f7c675" stroke="#b77d20"/>')
    for points in data["final_router_paths"]:
        coords = " ".join(f"{x:.4f},{y:.4f}" for x, y in points)
        parts.append(f'<polyline points="{coords}" fill="none" '
                     'stroke="#c92525" stroke-width="0.3"/>')
    for x, y in data["npth_centers_mm"]:
        parts.append(f'<circle cx="{x}" cy="{y}" r="1" '
                     'fill="white" stroke="#333"/>')
    for x, y in data["fiducial_centers_mm"]:
        parts.append(f'<circle cx="{x}" cy="{y}" r="1" '
                     'fill="white" stroke="#777"/>')
        parts.append(f'<circle cx="{x}" cy="{y}" r="0.5" '
                     'fill="#b08419" stroke="none"/>')
    parts.extend([
        '</g><g font-family="Arial,sans-serif" font-size="2.1" fill="#222">',
        f'<text x="{x0}" y="{y0 - 6}">'
        'EVT E2 - 1-up removable SMT carrier</text>',
        f'<text x="{x0}" y="{y0 - 2}">'
        f'{x1 - x0:.3f} x {y1 - y0:.3f} mm / '
        '8 mm rails / 2 mm minimum gap</text>',
        f'<text x="{x0}" y="{y1 + 4}">'
        'Orange: 8 solid tabs, 3 mm nominal width. '
        'Red: final router paths.</text>',
        f'<text x="{x0}" y="{y1 + 8}">'
        'Route tabs on a support fixture; retain final bare-board outline. '
        'No V-cut.</text>',
        f'<text x="{x0}" y="{y1 + 12}">'
        '4 x 2 mm NPTH; 3 asymmetric fiducials: 1 mm Cu / 2 mm mask. '
        'DFM pending.</text>',
        '</g></svg>',
    ])
    (OUT / "carrier_review.svg").write_text("\n".join(parts), encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).parent / "pylib"))
    import pymupdf

    document = pymupdf.open(OUT / "carrier_review.svg")
    document[0].get_pixmap(matrix=pymupdf.Matrix(3, 3)).save(
        OUT / "carrier_review.png")


def build_board():
    """Clone the routed board without moving components or copper."""
    import pcbnew as pcb

    sys.path.insert(0, str(Path(__file__).parent / "pylib"))
    import sexpdata as sx

    data = json.loads((OUT / "carrier_geometry.json").read_text())
    node = sx.loads((ROOT / "ir_glasses.kicad_pcb").read_text())
    node = [item for item in node if not isinstance(item, list) or not any(
        isinstance(field, list) and len(field) > 1
        and str(field[0]) == "layer" and field[1] == "Edge.Cuts"
        for field in item)]
    target = OUT / "ir_glasses_carrier.kicad_pcb"
    target.write_text(sx.dumps(node), encoding="utf-8")
    shutil.copyfile(ROOT / "ir_glasses.kicad_pro",
                    OUT / "ir_glasses_carrier.kicad_pro")
    board = pcb.LoadBoard(str(target))

    def point(x, y):
        return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))

    def segment(start, end, layer):
        shape = pcb.PCB_SHAPE(board)
        shape.SetShape(pcb.SHAPE_T_SEGMENT)
        shape.SetStart(point(*start))
        shape.SetEnd(point(*end))
        shape.SetLayer(layer)
        shape.SetWidth(pcb.FromMM(0.05 if layer == pcb.Edge_Cuts else 0.1))
        board.Add(shape)

    for ring in [data["outer"], *data["holes"]]:
        for start, end in zip(ring, ring[1:]):
            segment(start, end, pcb.Edge_Cuts)
    for path in data["final_router_paths"]:
        for start, end in zip(path, path[1:]):
            segment(start, end, pcb.Dwgs_User)
    for ring in data["cut_zone_keepouts"]:
        zone = pcb.ZONE(board)
        zone.SetIsRuleArea(True)
        zone.SetLayerSet(pcb.LSET.AllCuMask(4))
        zone.SetDoNotAllowZoneFills(True)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowFootprints(False)
        zone.Outline().NewOutline()
        for x, y in ring[:-1]:
            zone.Outline().Append(point(x, y))
        board.Add(zone)
    for fp in board.GetFootprints():
        models = fp.Models()
        for index, model in enumerate(models):
            model.m_Filename = model.m_Filename.replace(
                "${KIPRJMOD}/", "${KIPRJMOD}/../")
            models[index] = model

    library = KICAD / "share/kicad/footprints"
    for prefix, name, folder, centers in [
        ("H", "MountingHole_2mm", "MountingHole.pretty",
         data["npth_centers_mm"]),
        ("FID", "Fiducial_1mm_Mask2mm", "Fiducial.pretty",
         data["fiducial_centers_mm"]),
    ]:
        for number, center in enumerate(centers, 1):
            fp = pcb.FootprintLoad(str(library / folder), name)
            fp.SetFPID(pcb.LIB_ID(folder.removesuffix(".pretty"), name))
            fp.SetReference(f"{prefix}{number}")
            fp.SetPosition(point(*center))
            fp.SetAttributes(fp.GetAttributes() | pcb.FP_BOARD_ONLY
                             | pcb.FP_EXCLUDE_FROM_BOM
                             | pcb.FP_EXCLUDE_FROM_POS_FILES)
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
            board.Add(fp)
    label = pcb.PCB_TEXT(board)
    label.SetText("EVT E2 / TOP / 1-UP")
    label.SetPosition(point(110, data["carrier_bbox_mm"][1] + 4))
    label.SetTextSize(point(1.2, 1.2))
    label.SetTextThickness(pcb.FromMM(0.18))
    label.SetLayer(pcb.F_SilkS)
    board.Add(label)
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(target), board)
    for name in ("fp-lib-table", "sym-lib-table"):
        text = (ROOT / name).read_text(encoding="utf-8")
        (OUT / name).write_text(text.replace("${KIPRJMOD}/",
                                             "${KIPRJMOD}/../"),
                                encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board-stage", action="store_true")
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args()
    if args.board_stage:
        build_board()
        return
    geometry()
    if not args.geometry_only:
        subprocess.run([str(KICAD / "bin/python.exe"), __file__,
                        "--board-stage"], check=True)


if __name__ == "__main__":
    main()
