"""Align the manufacturer's FPC model to the existing KiCad footprint."""

from pathlib import Path

import FreeCAD as App
import Part

root = Path("hardware/ir_glasses/EVT_D/models").resolve()
shape = Part.read(str(root / "c-1734839-5-c-3d.stp"))
shape.Placement = App.Placement(
    App.Vector(0, -3.75, 1.05), App.Rotation(App.Vector(1, 0, 0), 90)
)
shape.exportStep(str(root / "TE_1734839-5_aligned.step"))
