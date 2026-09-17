#!/usr/bin/env python3
"""Reproducible E4 -> E6 schematic and component-manifest generation.
Requires sexpdata. Source E4 is read-only; no manufacturing evidence is copied.
"""
from pathlib import Path
import sexpdata as sx
import json,copy,uuid,math,hashlib
ROOT=Path(__file__).resolve().parents[1]; SRC=ROOT.parent/'ir_glasses_EVT_E4'; NAME='ir_glasses_EVT_E6'
S=sx.Symbol
K=lambda e:str(e[0]) if isinstance(e,list) and e else ''
def child(e,k):return next((x for x in e if K(x)==k),None)
def children(e,k):return [x for x in e if K(x)==k]
def prop(e,k):return next((x for x in children(e,'property') if x[1]==k),None)
def uid(t):return str(uuid.uuid5(uuid.NAMESPACE_URL,'ir-glasses-evt-e6/'+t))
def parse(t):return sx.loads(t)
def write(p,e):p.write_text(sx.dumps(e)+'\n')
def q(t):return json.dumps(t,ensure_ascii=False)
def label(net,x,y,angle=0):return parse(f'(global_label {q(net)} (shape passive) (at {x} {y} {angle}) (effects (font (size 0.95 0.95)) (justify {"left" if angle==0 else "right"})) (uuid "{uid(f"label/{net}/{x}/{y}")}"))')
def wire(a,b):return parse(f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)) (uuid "{uid(str(a)+str(b))}"))')
def text(t,x,y,size=1.3):return parse(f'(text {q(t)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid "{uid(t+str(x)+str(y))}"))')
parts=json.loads((SRC/'parts.json').read_text())
board=sx.load(open(SRC/'ir_glasses_EVT_E4.kicad_pcb'))
for fp in children(board,'footprint'):
 r=prop(fp,'Reference')[2]
 if r in parts:
  at=child(fp,'at');parts[r]['pcb_xy']=at[1:3];parts[r]['angle']=at[3] if len(at)>3 else 0
  parts[r]['uuid']=child(fp,'uuid')[1]
oldparts=copy.deepcopy(parts)
# MCU SPI1 is dedicated to ADC. LED clock/data are GPIO; CS and LED use TIM1.
changes={'11':'ADC_CS_N','12':'MUX_A1','15':'MUX_A0','16':'ADC_SCLK','17':'ADC_MISO','18':'ADC_MOSI','19':'MUX_EN_N', '48':'MUX_A2','21':'IMU_INT','42':'unconnected-(U9-PB3-Pad42)','22':'LED_SCLK','23':'LED_SIN','24':'unconnected-(U9-PB12-Pad24)','26':'MUX_B2','27':'LED_ENABLE','30':'MUX_B0','31':'unconnected-(U9-PC7-Pad31)','38':'MUX_B1','47':'unconnected-(U9-PB8-Pad47)'}
parts['U9']['nets'].update(changes)
parts['U9']['nets']['25']='unconnected-(U9-PB13-Pad25)'
# Symbols are intentionally local and include physical pin numbers verified from manufacturers.
lib=sx.load(open(SRC/'libraries/S.kicad_sym'))
newdefs={}
def custom(name,pins,footprint):
 left=[p for p in pins if p[3]=='L'];right=[p for p in pins if p[3]=='R'];height=(max(len(left),len(right))+1)*2.54
 e=parse(f'(symbol {q(name)} (pin_names (offset 0.508)) (in_bom yes) (on_board yes) (property "Reference" "U" (at 0 {height/2+3.81} 0) (effects (font (size 1.27 1.27)))) (property "Value" {q(name)} (at 0 {height/2+1.27} 0) (effects (font (size 1.27 1.27)))) (property "Footprint" {q(footprint)} (at 0 0 0) (effects (font (size 1.27 1.27)) hide)) (symbol {q(name+"_0_1")} (rectangle (start -12.7 {height/2}) (end 12.7 {-height/2}) (stroke (width 0.254) (type default)) (fill (type background)))) (symbol {q(name+"_1_1")}))')
 unit=e[-1]
 for side,ps in [('L',left),('R',right)]:
  for i,(num,nm,typ,_) in enumerate(ps):
   x=-15.24 if side=='L' else 15.24;y=height/2-2.54*(i+1);angle=0 if side=='L' else 180
   unit.append(parse(f'(pin {typ} line (at {x} {y} {angle}) (length 2.54) (name {q(nm)} (effects (font (size 1.0 1.0)))) (number {q(str(num))} (effects (font (size 1 1)))))'))
 lib.append(e);newdefs[name]=e
custom('AD7386BCPZ',[(8,'AINA0','input','L'),(7,'AINA1','input','L'),(6,'AINB0','input','L'),(5,'AINB1','input','L'),(11,'REFIO','passive','L'),(9,'REFCAP','passive','L'),(3,'REGCAP','passive','L'),(4,'VCC','power_in','L'),(2,'VLOGIC','power_in','L'),(12,'CS_N','input','R'),(16,'SCLK','input','R'),(15,'SDI','input','R'),(13,'SDOA','output','R'),(14,'SDOB_ALERT','output','R'),(1,'GND','power_in','R'),(10,'GND','power_in','R'),(17,'EP','power_in','R')],'IC:LFCSP-16_3x3mm_P0.5mm_EP1.1x1.1mm')
custom('OPA2320AIDGKR',[(3,'IN_A+','input','L'),(2,'IN_A-','input','L'),(5,'IN_B+','input','L'),(6,'IN_B-','input','L'),(1,'OUT_A','output','R'),(7,'OUT_B','output','R'),(8,'V+','power_in','R'),(4,'V-','power_in','R')],'IC:VSSOP-8_3x3mm_P0.65mm')
write(ROOT/'libraries/S.kicad_sym',lib)
def add(r,value,symbol,footprint,nets,xy,page,sch,mpn=None,manufacturer=''):
 parts[r]={'symbol':symbol,'value':value,'footprint':footprint,'nets':{str(k):v for k,v in nets.items()},'pcb_xy':xy,'angle':0,'page':page,'sch':sch,'manufacturer':manufacturer,'mpn':mpn or value,'lcsc':'','side':'front','uuid':uid(r)}
# Fixed adjacent pairs: A selects odd PDs; B selects even PDs.
for r,bank,offset,xy,sch in [('U7','A',1,[95,62],[75,90]),('U8','B',2,[131,61.5],[240,90])]:
 nets={str(pin):'TIA'+str(2*i+offset) for i,pin in enumerate([13,14,15,12,1,5,2,4])}
 nets.update({'3':'MUX_'+bank,'11':f'MUX_{bank}0','10':f'MUX_{bank}1','9':f'MUX_{bank}2','6':'MUX_EN_N','16':'3V3_A','8':'GND','7':f'unconnected-({r}-NC-Pad7)'})
 add(r,'TMUX1308PWR','TMUX1308PW','IC:TSSOP-16',nets,xy,'selection',sch,manufacturer='Texas Instruments');parts[r]['lcsc']='C970231'
add('U15','AD7386BCPZ-RL7','AD7386BCPZ','IC:LFCSP-16_3x3mm_P0.5mm_EP1.1x1.1mm',{1:'GND',2:'3V3',3:'ADC_REGCAP',4:'3V3_A',5:'GND',6:'ADC_B',7:'GND',8:'ADC_A',9:'ADC_REFCAP',10:'GND',11:'ADC_REF_2V5',12:'ADC_CS_N',13:'ADC_SDO_RAW',14:'unconnected-(U15-SDOB_ALERT-Pad14)',15:'ADC_MOSI',16:'ADC_SCLK',17:'GND'},[116,70],'acquisition',[230,75],manufacturer='Analog Devices')
for r,bank,xy,sch in [('U16','A',[100,61],[70,65]),('U17','B',[126,62],[70,130])]:
 add(r,'OPA2320AIDGKR','OPA2320AIDGKR','IC:VSSOP-8_3x3mm_P0.65mm',{1:f'BUF_{bank}',2:f'BUF_{bank}',3:f'MUX_{bank}',4:'GND',5:f'SCALE_{bank}',6:f'DRIVE_{bank}',7:f'DRIVE_{bank}',8:'3V3_A'},xy,'acquisition',sch,manufacturer='Texas Instruments')
def passive(r,value,n1,n2,xy,page,sch,mpn='',maker='',fp=None):
 base=copy.deepcopy(oldparts['R11' if r.startswith('R') else 'C29'])
 base.update(value=value,nets={'1':n1,'2':n2},pcb_xy=xy,page=page,sch=sch,angle=0,uuid=uid(r),mpn=mpn,manufacturer=maker,lcsc='')
 if fp:base['footprint']=fp
 parts[r]=base
for i,bank in enumerate(['A','B']):
 y=65+65*i
 passive('R'+str(21+2*i),'10k 0.05%',f'BUF_{bank}',f'SCALE_{bank}',[100+26*i,64.5],'acquisition',[125,y-5],'RT0402BRD0710KL','Yageo')
 passive('R'+str(22+2*i),'20k 0.05%',f'SCALE_{bank}','GND',[100+26*i,66],'acquisition',[125,y+20],'RT0402BRD0720KL','Yageo')
 # MPN B is 0.1%; value corrected to actual tolerance, both paths calibrated.
 parts['R'+str(21+2*i)]['value']='10k 0.1%';parts['R'+str(22+2*i)]['value']='20k 0.1%'
 passive('R'+str(11+i),'33',f'DRIVE_{bank}',f'ADC_{bank}',[114+4*i,68],'acquisition',[170,y],'0402WGF330JTCE','UNI-ROYAL')
 passive('C'+str(29+i),'330p C0G',f'ADC_{bank}','GND',[114+4*i,69],'acquisition',[170,y+25],'GRM1555C1H331JA01D','Murata')
for r,val,n1,n2,xy,sch in [('C39','1u','3V3_A','GND',[116,67.5],[210,135]),('C40','1u','3V3','GND',[118.5,71],[240,135]),('C41','1u','ADC_REGCAP','GND',[116,72.4],[270,135]),('C42','100n','ADC_REFCAP','GND',[114,71.5],[300,135]),('C43','1u','ADC_REF_2V5','GND',[114,73],[330,135]),('C44','100n','3V3_A','GND',[100,58.5],[45,190]),('C45','100n','3V3_A','GND',[126,59],[80,190]),('C46','1u','3V3_A','GND',[99,58],[115,190]),('C47','1u','3V3_A','GND',[128,58.5],[150,190])]:
 orig=oldparts['C18' if val=='1u' else 'C11'];passive(r,val,n1,n2,xy,'acquisition',sch,orig['mpn'],orig['manufacturer'])
passive('R25','100','ADC_SDO_RAW','ADC_MISO',[117,72.5],'acquisition',[300,75],'0402WGF1000TCE','UNI-ROYAL')
passive('R26','10k','ADC_CS_N','3V3',[118.5,68],'acquisition',[300,95],'0402WGF1002TCE','UNI-ROYAL')
passive('R27','10k','MUX_EN_N','3V3',[102,59],'selection',[155,145],'0402WGF1002TCE','UNI-ROYAL')
# Library dictionary including existing multi-unit symbols.
defs={e[1]:e for e in children(lib,'symbol')}
pages={}
for f in SRC.glob('*.kicad_sch'):
 name='control' if f.stem=='ir_glasses_EVT_E4' else f.stem
 pages[name]=sx.loads(f.read_text().replace('EVT_E4','EVT_E6').replace('EVT E4','EVT E6').replace('PB2 high','PB15 high').replace('2026-09-09','2026-09-16'))
rootid=child(pages['control'],'uuid')[1]

def pinpos(inst,page):
 ln=child(inst,'lib_id')[1]; ld=next(e for e in children(child(page,'lib_symbols'),'symbol') if e[1]==ln)
 unit=child(inst,'unit')[1];a=child(inst,'at');angle=math.radians(a[3]);res={}
 for sub in children(ld,'symbol'):
  if int(sub[1].split('_')[-2]) not in (0,unit):continue
  for pin in children(sub,'pin'):
   p=child(pin,'at');x=p[1];y=-p[2]
   px=a[1]+x*math.cos(angle)+y*math.sin(angle);py=a[2]-x*math.sin(angle)+y*math.cos(angle)
   res[child(pin,'number')[1]]=(round(px,5),round(py,5),int((p[3]+a[3])%360))
 return res

def remove_instance(page,ref,keep=False):
 inst=next((e for e in children(page,'symbol') if prop(e,'Reference') and prop(e,'Reference')[2]==ref),None)
 if inst is None:return
 pins=pinpos(inst,page);points={(p[0],p[1]) for p in pins.values()};delete=[]
 # E4 uses independent short pin wires with global labels; trace their endpoints.
 changed=True
 while changed:
  changed=False
  for e in children(page,'wire'):
   if id(e) in delete:continue
   pts=child(e,'pts');xy=[tuple(round(v,5) for v in p[1:3]) for p in pts[1:]]
   if any(p in points for p in xy):points.update(xy);delete.append(id(e));changed=True
 for e in page[1:]:
  if K(e) in ('global_label','label','no_connect','junction'):
   a=child(e,'at')
   if a and tuple(round(v,5) for v in a[1:3]) in points:delete.append(id(e))
 page[:]=[e for e in page if id(e) not in delete and (keep or e is not inst)]
 return inst,pins
for page in pages.values():
 for ref in ['U7','U8','R11','R12','C29','C30']:remove_instance(page,ref)
inst,pins=remove_instance(pages['control'],'U9',True)
for num,(x,y,ang) in pins.items():
 net=parts['U9']['nets'][num]
 if net.startswith('unconnected-'):
  pages['control'].append(parse(f'(no_connect (at {x} {y}) (uuid "{uid("U9NC"+num)}"))'));continue
 dx=-3.81 if ang==0 else 3.81 if ang==180 else 0
 dy=3.81 if ang==90 else -3.81 if ang==270 else 0
 end=(round(x+dx,5),round(y+dy,5));pages['control'].append(wire((x,y),end));pages['control'].append(label(net,*end,180 if dx<0 else 0))
# New A3 pages; all symbols tied to global nets, with no hidden interconnects.
for name,title in [('selection','ADJACENT ODD / EVEN PD SELECTION'),('acquisition','DUAL SIMULTANEOUS 16-BIT ACQUISITION')]:
 pageid=uid('page/'+name)
 pages[name]=parse(f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{pageid}") (paper "A3") (title_block (title "IR Glasses EVT E6 - {title}") (date "2026-09-16") (rev "EVT E6")) (lib_symbols) (embedded_fonts no))')
 pages[name].append(text('IR GLASSES EVT E6 - '+title,20,18,2))
 y=260 if name=='selection' else 280
 sheet=parse(f'(sheet (at 295 {y}) (size 82 16) (uuid "{uid("sheet/"+name)}") (property "Sheetname" {q(name)} (at 295 {y-1} 0) (effects (font (size 1.27 1.27)) (justify left bottom))) (property "Sheetfile" {q(name+".kicad_sch")} (at 295 {y+17} 0) (effects (font (size 1.27 1.27)) (justify left top))) (instances (project "{NAME}" (path "/{rootid}" (page "{7 if name=="selection" else 8}")))))')
 # Control is A3; move sheet list into a 2-column area to fit.
 child(sheet,'at')[2]=95 if name=='selection' else 119
 child(sheet,'at')[1]=140
 for p in children(sheet,'property'):child(p,'at')[1]=140;child(p,'at')[2]=94 if p[1]=='Sheetname' and name=='selection' else 118 if p[1]=='Sheetname' else 112 if name=='selection' else 136
 pages['control'].append(sheet)
for ref,p in parts.items():
 if p['page'] not in ('selection','acquisition'):continue
 pg=pages[p['page']];ld=copy.deepcopy(defs[p['symbol']]);ld[1]='S:'+p['symbol'];ls=child(pg,'lib_symbols')
 if not any(e[1]==ld[1] for e in ls[1:]):ls.append(ld)
 x,y=p['sch'];x=round(x/1.27)*1.27;y=round(y/1.27)*1.27
 # Resistors/capacitors use original symbol geometry, ICs use local verified pin blocks.
 instid=uid('symbol/'+ref);p['sch_uuid']=instid
 inst=parse(f'(symbol (lib_id {q(ld[1])}) (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{instid}") (property "Reference" {q(ref)} (at {x} {y-5.08} 0) (effects (font (size 1.0 1.0)))) (property "Value" {q(p["value"])} (at {x} {y-2.54} 0) (effects (font (size 1.0 1.0)))) (property "Footprint" {q(p["footprint"])} (at {x} {y} 0) (effects (font (size 1 1)) hide)) (property "MPN" {q(p["mpn"])} (at {x} {y} 0) (effects (font (size 1 1)) hide)) (property "Manufacturer" {q(p["manufacturer"])} (at {x} {y} 0) (effects (font (size 1 1)) hide)) (instances (project "{NAME}" (path "/{rootid}/{uid("sheet/"+p["page"])}" (reference {q(ref)}) (unit 1)))))')
 if ref.startswith('U'):
  # Place name above the entire IC body.
  rect=next(child(unit,'rectangle') for unit in children(ld,'symbol') if child(unit,'rectangle'))
  top=child(rect,'start')[2]
  child(prop(inst,'Reference'),'at')[2]=y-top-5.08
  child(prop(inst,'Value'),'at')[2]=y-top-2.54
 if not ref.startswith('U'):
  for nm,off in [('Reference',-1.27),('Value',1.27)]:
   child(prop(inst,nm),'at')[1:3]=[x+7.62,y+off]
 pg.append(inst)
 for num,(px,py,angle) in pinpos(inst,pg).items():
  inst.append(parse(f'(pin {q(num)} (uuid "{uid(ref+"pin"+num)}"))'))
  net=p['nets'][num]
  if net.startswith('unconnected-'):
   pg.append(parse(f'(no_connect (at {px} {py}) (uuid "{uid(ref+"NC"+num)}"))'));continue
  dx=-5.08 if angle==0 else 5.08 if angle==180 else 0;dy=5.08 if angle==90 else -5.08 if angle==270 else 0
  end=(round(px+dx,5),round(py+dy,5));pg.append(wire((px,py),end));pg.append(label(net,*end,180 if dx<0 else 0))
# Engineering notes explain signal path and switching without relying on label interpretation.
pages['selection'] += [text('U7 selects odd PDs; U8 selects even PDs. LED_ID selects its two adjacent PDs using the fixed table.',25,175),text('EN_N is active low; R27 pulls high to disable both paths during reset.',25,182),text('Switch only with LED_ENABLE low. MUX address = (PD_ID - 1) / 2, integer division.',25,189)]
pages['acquisition'] += [text('Each path: MUX -> unity buffer -> 10k/20k divider -> unity buffer -> 33R / 330p -> ADC.',20,220),text('AD7386: CH=0, SEQ=0, internal 2.5V reference, 1-wire output, 16-bit, no oversampling.',20,227),text('AINA0 and AINB0 sample together on ADC_CS_N falling edge. AINx1 grounded.',20,234),text('Analog span scaled 2/3. Calibrate path offset/gain; 16-bit codes do not guarantee 16-bit ENOB.',20,241)]
for name,page in pages.items():write(ROOT/(NAME+'.kicad_sch' if name=='control' else name+'.kicad_sch'),page)
pro=json.loads((SRC/'ir_glasses_EVT_E4.kicad_pro').read_text());pro['meta']['filename']=NAME+'.kicad_pro'
# Never carry forward old rule exclusions as validation of a changed layout.
if 'board' in pro and 'design_settings' in pro['board']:pro['board']['design_settings']['drc_exclusions']=[]
rules=pro['board']['design_settings']['rules']
rules.update(min_clearance=.1,min_track_width=.1,min_copper_edge_clearance=.3,min_through_hole_diameter=.15,min_via_diameter=.35,min_via_annular_width=.1,min_hole_clearance=.2,min_hole_to_hole=.25)
for cls in pro['net_settings']['classes']:
 cls.update(clearance=.1,track_width=.127,via_diameter=.45,via_drill=.2)
(ROOT/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
(ROOT/'parts.json').write_text(json.dumps(parts,indent=2,ensure_ascii=False))
(ROOT/'source_hashes.json').write_text(json.dumps({str(p.relative_to(SRC)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SRC.rglob('*') if p.is_file()},indent=2))
print('Generated E6 schematic pages:',len(pages),'components:',len(parts))
