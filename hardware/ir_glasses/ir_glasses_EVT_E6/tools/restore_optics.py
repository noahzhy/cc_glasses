#!/usr/bin/env python3
"""Restore exact E4 optical poses after DSN/SES coordinate quantization; rerun DRC."""
from pathlib import Path
import pcbnew as p
root=Path(__file__).resolve().parents[1];old=p.LoadBoard(str(root.parent/'ir_glasses_EVT_E4/ir_glasses_EVT_E4.kicad_pcb'));b=p.LoadBoard(str(root/'ir_glasses_EVT_E6.kicad_pcb'));refs={f'D{i}' for i in range(1,17)}|{f'PD{i}' for i in range(1,17)};src={f.GetReference():f for f in old.GetFootprints()}
for f in b.GetFootprints():
 if f.GetReference() in refs:
  origin=src[f.GetReference()];f.SetPosition(origin.GetPosition());f.SetOrientation(origin.GetOrientation())
p.SaveBoard(str(root/'ir_glasses_EVT_E6.kicad_pcb'),b);print('Restored 32 exact E4 optical poses')
