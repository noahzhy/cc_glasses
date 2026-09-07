from pathlib import Path

source = Path('hardware/ir_glasses/refinement/ir_glasses.dsn').read_text()
source = source[:source.index('  (wiring')] + '  (wiring)\n)\n'
source = source.replace('(width 180)', '(width 150)')
Path('hardware/tools/route_fresh.dsn').write_text(source)
