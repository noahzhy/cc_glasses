import json
from pathlib import Path
import pcbnew as pcb
root = Path('hardware/ir_glasses/EVT_D')
f = root / 'ir_glasses.kicad_pcb'
b = pcb.LoadBoard(str(f))
fp = next(fp for fp in b.GetFootprints() if fp.GetReference() == 'C28')
fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(117.5), pcb.FromMM(64)))
pcb.SaveBoard(str(f), b)
p = json.loads((root / 'parts.json').read_text())
p['C28']['xy'] = [7.5, -21]
(root / 'parts.json').write_text(json.dumps(p, indent=2))
