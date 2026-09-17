#!/usr/bin/env python3
"""Refresh manifest placement from the authoritative PCB; does not move footprints."""
from pathlib import Path
import json,sexpdata as sx
root=Path(__file__).resolve().parents[1]
key=lambda x:str(x[0]) if isinstance(x,list) and x else ''
child=lambda x,k:next((e for e in x if key(e)==k),None)
b=sx.load(open(root/'ir_glasses_EVT_E6.kicad_pcb'));parts=json.load(open(root/'parts.json'));placement=json.load(open(root/'placement.json'))
for fp in b:
 if key(fp)!='footprint':continue
 ref=next(e[2] for e in fp if key(e)=='property' and e[1]=='Reference')
 at=child(fp,'at');angle=at[3] if len(at)>3 else 0
 parts[ref].update(pcb_xy=at[1:3],angle=angle,side='front' if child(fp,'layer')[1]=='F.Cu' else 'back')
 if ref in placement:placement[ref]=at[1:3]+[angle]
(root/'parts.json').write_text(json.dumps(parts,indent=2,ensure_ascii=False))
(root/'placement.json').write_text(json.dumps(placement,indent=2))
print(len(parts),'placements synchronized')
