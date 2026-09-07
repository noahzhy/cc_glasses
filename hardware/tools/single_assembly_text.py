"""Center test-point labels in the assembly drawing."""

from pathlib import Path

import sexpdata as sx

root = Path("hardware/ir_glasses/EVT_E")


def labels(footprint):
    for text in footprint:
        if not isinstance(text, list) or str(text[0]) != "fp_text":
            continue
        if text[2] != "${REFERENCE}":
            continue
        for child in text:
            if not isinstance(child, list):
                continue
            if str(child[0]) == "at":
                child[1:] = [0, 0, 0]
            if str(child[0]) == "effects":
                font = next(
                    v
                    for v in child
                    if isinstance(v, list) and str(v[0]) == "font"
                )
                for value in font:
                    if isinstance(value, list) and str(value[0]) == "size":
                        value[1:] = [0.6, 0.6]
                    if (
                        isinstance(value, list)
                        and str(value[0]) == "thickness"
                    ):
                        value[1] = 0.1


path = root / "ir_glasses.kicad_pcb"
board = sx.loads(path.read_text(encoding="utf-8"))
for fp in board:
    if isinstance(fp, list) and str(fp[0]) == "footprint":
        if str(fp[1]).endswith(":TestPoint_Pad_D1.0mm"):
            labels(fp)
path.write_text(sx.dumps(board), encoding="utf-8")
path = root / "IR_Glasses.pretty/TestPoint_Pad_D1.0mm.kicad_mod"
footprint = sx.loads(path.read_text())
labels(footprint)
path.write_text(sx.dumps(footprint))
