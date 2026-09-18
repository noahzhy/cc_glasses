"""Use PA9/PA10 USART1 for runtime and boot UART; free PA2/PA3."""
from pathlib import Path
import sexpdata as sx,json,ast,uuid,math
R=Path(__file__).resolve().parents[1];SRC=R.parent/'ir_glasses_EVT_E6';K=lambda e:str(e[0]) if isinstance(e,list) and e else ''
for node in ast.parse((SRC/'tools/build_e6.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['child','children','prop','pinpos']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'helpers','exec'))
p=R/(R.name+'.kicad_sch');pg=sx.load(open(p));inst=next(e for e in children(pg,'symbol') if prop(e,'Reference')[2]=='U9');coords=pinpos(inst,pg)
for num in ['12','13']:
 x,y,a=coords[num];other=[]
 for e in list(pg):
  if K(e)!='wire':continue
  pts=child(e,'pts')[1:]
  if any(q[1:]==[x,y] for q in pts):other.extend(q[1:] for q in pts if q[1:]!=[x,y]);pg.remove(e)
 pg[:]=[e for e in pg if not(K(e) in ['label','global_label','hierarchical_label'] and child(e,'at')[1:3] in other)]
 pg.append([sx.Symbol('no_connect'),[sx.Symbol('at'),x,y],[sx.Symbol('uuid'),str(uuid.uuid4())]])
p.write_text(sx.dumps(pg)+'\n')
parts=json.load(open(R/'parts.json'));parts['U9']['nets']['12']='unconnected-(U9-PA2-Pad12)';parts['U9']['nets']['13']='unconnected-(U9-PA3-Pad13)'
p=R/(R.name+'.kicad_pcb');b=sx.load(open(p));b=[e for e in b if not(K(e) in ['segment','via'] and child(e,'net')[-1] in ['UART_TX','UART_RX'])]
for f in children(b,'footprint'):
 if prop(f,'Reference')[2]!='U9':continue
 for pad in children(f,'pad'):
  if pad[1] in ['12','13']:child(pad,'net')[1:]=[parts['U9']['nets'][pad[1]]]
p.write_text(sx.dumps(b)+'\n')
(R/'parts.json').write_text(json.dumps(parts,indent=2,ensure_ascii=False))
for p in list(R.glob('*.kicad_sch'))+[R/(R.name+'.kicad_pcb'),R/'parts.json']:
 t=p.read_text().replace('BOOT_TX_PA9','UART_TX').replace('BOOT_RX_PA10','UART_RX');p.write_text(t)
parts=json.load(open(R/'parts.json'));manifest=json.load(open(R/'evidence/change_manifest.json'))
for n,row in manifest['mcu_pin_map'].items():row['net']=parts['U9']['nets'][n]
manifest['uart_revision']='USART1 PA9/PA10 runtime and boot shared; PA2/PA3 NC'
(R/'evidence/change_manifest.json').write_text(json.dumps(manifest,indent=2))
removed=set(json.load(open(R/'evidence/uart_minrip.json'))['remove_ids']);geom=json.load(open(R/'evidence/geom26.json'));restore=[e for e in geom['items'] if e['id'] in removed and e['net']=='TIA13'];(R/'evidence/restore_tia13.json').write_text(json.dumps({'items':restore}));print('UART moved to PA9/PA10; restore TIA13 objects',len(restore))
