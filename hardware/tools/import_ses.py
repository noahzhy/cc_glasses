from pathlib import Path
import pcbnew as pcb

root = Path('hardware/ir_glasses')
board = pcb.LoadBoard(str(root / 'ir_glasses.kicad_pcb'))
print('Import:', pcb.ImportSpecctraSES(board, str(root / 'ir_glasses.ses')))
pcb.SaveBoard(str(root / 'ir_glasses.kicad_pcb'), board)
