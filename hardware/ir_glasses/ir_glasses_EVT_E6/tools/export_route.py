from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];b=p.LoadBoard(str(ROOT/'ir_glasses_EVT_E6.kicad_pcb'))
# Remove copper planes from the routing exchange only; keep original PCB pours.
for z in list(b.Zones()):
 if not z.GetIsRuleArea():b.Remove(z)
print('DSN export',p.ExportSpecctraDSN(b,str(ROOT.parent/'.e6_work/e6.dsn')))
