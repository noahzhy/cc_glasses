import sys
from pathlib import Path
sys.path.insert(0, str(Path('hardware/ir_glasses').resolve()))
import generate as g
for part in g.PARTS.values():
    part['footprint'] = 'IR_Glasses:' + part['footprint'].split(':')[1]
g.make_schematics()
