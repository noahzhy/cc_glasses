import json
import sys
from pathlib import Path
import pcbnew as pcb

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'hardware/ir_glasses')
board = pcb.LoadBoard(str(root / 'ir_glasses.kicad_pcb'))
print('Exported:', pcb.ExportSpecctraDSN(board, str(root / 'ir_glasses.dsn')))
