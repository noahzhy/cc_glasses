"""Add drawing margins and rasterize the native KiCad SVG exports."""

import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path("hardware/tools/pylib").resolve()))
import fitz

root = Path("hardware/ir_glasses/EVT_E3")
for name in ["pcb_routed", "assembly_front", "assembly_back"]:
    path = root / f"{name}.svg"
    text = path.read_text(encoding="utf-8")
    if name.startswith("assembly_"):
        match = re.search(r'viewBox="([^"]+)"', text)
        x, y, width, height = map(float, match[1].split())
        text = text.replace(
            match[0],
            f'viewBox="{x - 2} {y - 2} {width + 4} {height + 4}"',
            1,
        )
        for key, value in [("width", width + 4), ("height", height + 4)]:
            text = re.sub(
                rf'{key}="[\d.]+mm"', f'{key}="{value}mm"', text, count=1
            )
        path.write_text(text, encoding="utf-8")
    doc = fitz.open(path)
    page = doc[0]
    scale = 2000 / page.rect.width
    page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(
        root / f"{name}.png"
    )
