"""Store the ENIG finish with the nominal standard four-layer stackup."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "pylib"))
import sexpdata as sx  # noqa: E402


path = Path("hardware/ir_glasses/EVT_E2/ir_glasses.kicad_pcb")
tree = sx.loads(path.read_text(encoding="utf-8"))
setup = next(n for n in tree if isinstance(n, list) and n
             and str(n[0]) == "setup")
setup[:] = [n for n in setup if not (
    isinstance(n, list) and n and str(n[0]) == "stackup")]
setup.append(sx.loads('''
(stackup
  (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
  (layer "F.Paste" (type "Top Solder Paste"))
  (layer "F.Mask" (type "Top Solder Mask") (color "Green")
    (thickness 0.01))
  (layer "F.Cu" (type "copper") (thickness 0.035))
  (layer "dielectric 1" (type "prepreg") (thickness 0.2104)
    (material "FR4"))
  (layer "In1.Cu" (type "copper") (thickness 0.0152))
  (layer "dielectric 2" (type "core") (thickness 1.065)
    (material "FR4"))
  (layer "In2.Cu" (type "copper") (thickness 0.0152))
  (layer "dielectric 3" (type "prepreg") (thickness 0.2104)
    (material "FR4"))
  (layer "B.Cu" (type "copper") (thickness 0.035))
  (layer "B.Mask" (type "Bottom Solder Mask") (color "Green")
    (thickness 0.01))
  (layer "B.Paste" (type "Bottom Solder Paste"))
  (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
  (copper_finish "ENIG")
  (dielectric_constraints no))
'''))
path.write_text(sx.dumps(tree), encoding="utf-8")
print("ENIG; nominal standard 1.6 mm four-layer stackup")
