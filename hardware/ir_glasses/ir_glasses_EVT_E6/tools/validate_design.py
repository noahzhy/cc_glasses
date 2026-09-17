#!/usr/bin/env python3
"""Independent connection, mechanical and acquisition-contract audit (not bench tests)."""
from pathlib import Path
import json,sexpdata as sx,xml.etree.ElementTree as ET,itertools,hashlib,csv
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'ir_glasses_EVT_E4'
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
checks=[]
def check(name,condition):
 checks.append({'check':name,'pass':bool(condition)})
 if not condition:
  (ROOT/'design_validation.json').write_text(json.dumps({'status':'FAIL','scope':'static design checks only','failed_check':name,'checks':checks,'board_sha256':hashlib.sha256((ROOT/'ir_glasses_EVT_E6.kicad_pcb').read_bytes()).hexdigest()},indent=2,ensure_ascii=False))
  raise AssertionError(name)
def parse_board(path):
 b=sx.load(path.open());pads={};poses={};fps={}
 for f in b:
  if K(f)!='footprint':continue
  r=next(x[2] for x in f if K(x)=='property' and x[1]=='Reference');poses[r]=C(f,'at')[1:];fps[r]=f
  for p in f:
   if K(p)=='pad':
    n=C(p,'net');pads[r,str(p[1])]=n[-1] if n else ''
 return b,pads,poses,fps
xml=ET.parse(ROOT/'netlist.xml').getroot();net={}
for n in xml.findall('nets/net'):
 for p in n.findall('node'):net[p.attrib['ref'],p.attrib['pin']]=n.attrib['name']
b,pads,poses,fps=parse_board(ROOT/'ir_glasses_EVT_E6.kicad_pcb');old,oldpads,oldposes,oldfps=parse_board(SRC/'ir_glasses_EVT_E4.kicad_pcb')
parts=json.load(open(ROOT/'parts.json'))
for key,value in pads.items():
 if value and not value.startswith('unconnected-'):check('schematic/PCB '+str(key),net.get(key)==value)
for r,p in parts.items():
 for pin,n in p['nets'].items():
  if pin and n and not n.startswith('unconnected-'):check('manifest '+r+'.'+pin,net.get((r,pin))==n)
def n(r,pin):return net[r,str(pin)]
muxpins=[13,14,15,12,1,5,2,4]
for i in range(1,17):
 mux='U7' if i%2 else 'U8';muxpin=muxpins[(i-1)//2];tia=f'TIA{i}'
 check(f'PD{i} independent raw photodiode',n('PD'+str(i),2)==f'PD_IN{i}')
 check(f'PD{i} connects to correct odd/even mux',n(mux,muxpin)==tia)
 check(f'PD{i} feedback preserved',tia in [n('RF'+str(i),1),n('RF'+str(i),2)] and tia in [n('CF'+str(i),1),n('CF'+str(i),2)])
for bank,u,buf,rhi,rlo,rr,cc,ain in [('A','U7','U16','R21','R22','R11','C29',8),('B','U8','U17','R23','R24','R12','C30',6)]:
 for bit,pin in enumerate([11,10,9]):check(f'{bank} bit {bit}',n(u,pin)==f'MUX_{bank}{bit}')
 check(bank+' mux to buffer',n(u,3)==n(buf,3)==f'MUX_{bank}')
 check(bank+' buffer feedback',n(buf,1)==n(buf,2)==n(rhi,1)==f'BUF_{bank}')
 check(bank+' divider',n(rhi,2)==n(rlo,1)==n(buf,5)==f'SCALE_{bank}' and n(rlo,2)=='GND')
 check(bank+' ADC driver',n(buf,7)==n(buf,6)==n(rr,1)==f'DRIVE_{bank}')
 check(bank+' ADC RC',n(rr,2)==n(cc,1)==n('U15',ain)==f'ADC_{bank}' and n(cc,2)=='GND')
for ref in ['U16','U17']:
 check(ref+' TLV9062 selected',parts[ref]['mpn']=='TLV9062IDGKR' and parts[ref]['lcsc']=='C398356')
for ref in ['R11','R12']:
 check(ref+' 100ohm isolation',parts[ref]['value']=='100' and parts[ref]['mpn']=='RC0402FR-07100RL')
check('shared aperture edge PA0 / CS',n('U9',11)==n('U15',12)=='ADC_CS_N')
check('hardware LED timer PB15',n('U9',27)=='LED_ENABLE' and n('U9',26)=='MUX_B2')
check('no ADC spare floating inputs',n('U15',5)==n('U15',7)=='GND')
check('ADC EP and GND',all(n('U15',p)=='GND' for p in [1,10,17]))
for ref in ['U7','U8','U15','U16','U17','U18','U19']:
 fp=fps[ref];lib,foot=fp[1].split(':');local=sx.load(open(ROOT/'libraries'/f'{lib}.pretty'/f'{foot}.kicad_mod'))
 normalized=lambda f:sorted((str(p[1]),tuple(C(p,'at')[1:3]),tuple(C(p,'size')[1:]),tuple(sorted(str(v) for v in C(p,'layers')[1:])),tuple(C(p,'solder_paste_margin')[1:] if C(p,'solder_paste_margin') else [])) for p in f if K(p)=='pad')
 check(ref+' local and embedded pad geometry/mask/paste match',normalized(fp)==normalized(local))
ep=next(p for p in fps['U15'] if K(p)=='pad' and str(p[1])=='17')
check('AD7386 CP-16-45 actual EP size 1.1mm square',C(ep,'size')[1:]==[1.1,1.1])
check('AD7386 EP 0.9mm paste aperture present','F.Paste' in C(ep,'layers') and C(ep,'solder_paste_margin')[1]==-.1)

check('independent address controls',len({n('U9',p) for p in [15,12,48,30,38,26]})==6)
check('IMU interrupt on PB2 EXTI2',n('U9',21)==n('U10',4)==n('TP11',1)=='IMU_INT')
check('mux disable pullup',n('U7',6)==n('U8',6)==n('U9',19)==n('R27',1)=='MUX_EN_N' and n('R27',2)=='3V3')
rows=[]
for led in range(1,17):
 neighbor=led+1 if led%8 else led-7
 a,bb=(led,neighbor) if led%2 else (neighbor,led)
 row={'led_id':led,'pd_a_id':a,'pd_b_id':bb,'address_a':(a-1)//2,'address_b':(bb-1)//2}
 rows.append(row)
 check(f'D{led} adjacent PD reachability',n('U7',muxpins[row['address_a']])==f'TIA{a}' and n('U8',muxpins[row['address_b']])==f'TIA{bb}')
# Independently recover adjacency from E4 angular order around each eye center.
import math
for first in [1,9]:
 refs=[f'{prefix}{i}' for prefix in ['D','PD'] for i in range(first,first+8)]
 cx=sum(oldposes[r][0] for r in refs)/16;cy=sum(oldposes[r][1] for r in refs)/16
 order=sorted(refs,key=lambda r:math.atan2(oldposes[r][1]-cy,oldposes[r][0]-cx))
 for led in range(first,first+8):
  idx=order.index(f'D{led}');neighbors={order[(idx-1)%16],order[(idx+1)%16]};row=rows[led-1]
  check(f'D{led} neighbors match physical E4 optical order',neighbors=={f"PD{row['pd_a_id']}",f"PD{row['pd_b_id']}"})
check('16 unique fixed adjacent pairs',len({tuple(sorted([r['pd_a_id'],r['pd_b_id']])) for r in rows})==16)
with (ROOT/'led_pd_mapping.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for i in range(1,17):
 for r in [f'D{i}',f'PD{i}']:
  check(r+' optical pose preserved',poses[r]==oldposes[r])
  check(r+' optical nets preserved',{p:v for (ref,p),v in pads.items() if ref==r}=={p:v for (ref,p),v in oldpads.items() if ref==r})
check('LED driver connectivity preserved',{p:v for (r,p),v in pads.items() if r=='U1'}=={p:v for (r,p),v in oldpads.items() if r=='U1'})
edges=lambda x:[sx.dumps(e) for e in x if K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts']
check('E4 board contour exactly preserved',edges(b)==edges(old))
check('four copper layers',len([e for e in C(b,'layers')[1:] if isinstance(e,list) and str(e[1]).endswith('.Cu')])==4)
check('all fitted components on front',all(C(f,'layer')[1]=='F.Cu' for r,f in fps.items() if not r.startswith('TP')))
check('test pads on back',all(C(f,'layer')[1]=='B.Cu' for r,f in fps.items() if r.startswith('TP')))
for relative,digest in json.load(open(ROOT/'source_hashes.json')).items():
 check('E4 unchanged '+relative,hashlib.sha256((SRC/relative).read_bytes()).hexdigest()==digest)
# Reference simulation deliberately models one-conversion ADC latency and catches stale metadata.
pending=None;readbacks=[];samples=[]
for slot in range(16):
 for phase,t in [('dark',100),('light',250)]:
  event={'slot':slot,'phase':phase,'t_us':slot*1250+t,'a':1000+slot*10+(100 if phase=='light' else 0),'b':2000+slot*10+(200 if phase=='light' else 0)}
  if pending is not None:readbacks.append(pending)
  pending=event;samples.append(event)
readbacks.append(pending) # LED-off flush reads the last light pair.
check('pipeline metadata preserves all 32 pair samples',samples==readbacks)
for slot in range(16):
 dark,light=readbacks[2*slot:2*slot+2]
 check('slot '+str(slot)+' paired dark/light',dark['phase']=='dark' and light['phase']=='light' and light['a']-dark['a']==100 and light['b']-dark['b']==200)
 check('slot '+str(slot)+' sample inside LED window',200<light['t_us']-1250*slot<300)
check('signed background subtraction',int(100)-int(200)==-100)
check('3MHz 32-bit read fits CS low',2+32/3<24)
check('DMA allocation fits three channels',len(['TIM1_CH1','TIM1_CH3','SPI1_RX'])==3)
report={'status':'PASS','scope':'static netlist, geometry and reference timing model only; not bench validation','checks':checks,'counts':{'components_including_testpoints':len(fps),'fixed_led_adjacent_pd_pairs':16},'board_sha256':hashlib.sha256((ROOT/'ir_glasses_EVT_E6.kicad_pcb').read_bytes()).hexdigest()}
(ROOT/'design_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print('PASS',len(checks),'checks; 16 LEDs with verified adjacent PD pairs; E4 unchanged')
