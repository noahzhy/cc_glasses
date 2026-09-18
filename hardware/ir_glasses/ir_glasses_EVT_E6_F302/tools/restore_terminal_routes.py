"""Preserve original terminal escapes; reroute only the replaced MCU region."""
from pathlib import Path
import sexpdata as s,json
from shapely.geometry import box,LineString,Point
R=Path(__file__).resolve().parents[1];p=R/(R.name+'.kicad_pcb');b=s.load(open(p));old=s.load(open(R.parent/'ir_glasses_EVT_E6/ir_glasses_EVT_E6.kicad_pcb'))
K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
nets=set(json.load(open(R/'parts.json'))['U9']['nets'].values())-{'GND','3V3','3V3_A','SWCLK','BOOT0','ADC_A','ADC_B'}
b=[e for e in b if not(K(e) in ['segment','via'] and C(e,'net')[-1] in nets)]
rect=box(104.3,57.2,115.5,68.5);n=0
for e in old:
 if K(e) not in ['segment','via'] or C(e,'net')[-1] not in nets:continue
 g=Point(C(e,'at')[1:3]) if K(e)=='via' else LineString([C(e,'start')[1:3],C(e,'end')[1:3]])
 if g.intersects(rect):continue
 b.append(e);n+=1
for z in [e for e in b if K(e)=='zone']:
 f=C(z,'fill')
 if f and C(f,'island_removal_mode'):C(f,'island_removal_mode')[1]=1
p.write_text(s.dumps(b)+'\n');print('Restored',n,'terminal copper objects')
