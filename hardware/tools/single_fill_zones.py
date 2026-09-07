"""Refill all copper regions with KiCad's native zone engine."""

from pathlib import Path

import pcbnew as pcb

path = Path("hardware/ir_glasses/EVT_E/ir_glasses.kicad_pcb")
board = pcb.LoadBoard(str(path))
pcb.ZONE_FILLER(board).Fill(board.Zones())
pcb.SaveBoard(str(path), board)
