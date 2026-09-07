"""Omit nonpolar 0402 body silk while retaining assembly outlines."""

from pathlib import Path

import sexpdata as sx

root = Path("hardware/ir_glasses/EVT_E")
name = "R_0402_1005Metric"


def clean(node):
    return [
        item
        for item in node
        if not (
            isinstance(item, list)
            and str(item[0]) in {"fp_line", "fp_arc", "fp_rect", "fp_poly"}
            and any(
                isinstance(child, list)
                and str(child[0]) == "layer"
                and child[1] == "F.SilkS"
                for child in item
            )
        )
    ]


library = root / "IR_Glasses.pretty" / f"{name}.kicad_mod"
library.write_text(sx.dumps(clean(sx.loads(library.read_text()))))
path = root / "ir_glasses.kicad_pcb"
board = sx.loads(path.read_text(encoding="utf-8"))
for node in board:
    if isinstance(node, list) and str(node[0]) == "footprint":
        if str(node[1]) == f"IR_Glasses:{name}":
            node[:] = clean(node)
path.write_text(sx.dumps(board), encoding="utf-8")
