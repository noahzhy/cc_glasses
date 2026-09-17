#!/usr/bin/env python3
"""Read exported CAM independently and compare drill/CPL/BOM/outline content."""
from pathlib import Path
import json,csv,re,math,hashlib,sexpdata as sx
from gerbonara import LayerStack
from gerbonara.utils import MM
ROOT=Path(__file__).resolve().parents[1];checks=[]
def check(name,value):
 checks.append({'check':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
bom=list(csv.DictReader(open(ROOT/'bom.csv',encoding='utf-8-sig')));refs={r['Reference'] for r in bom}
check('167 unique fitted BOM references',len(bom)==len(refs)==167)
counts={}
for sub in ['', 'carrier']:
 folder=ROOT/sub;name='ir_glasses_EVT_E6'+('_carrier' if sub else '');b=sx.load(open(folder/(name+'.kicad_pcb')))
 stack=LayerStack.open(folder/'manufacturing');copper=[k for k in stack.graphic_layers if k[1]=='copper'];check(sub+' four CAM copper layers',len(copper)==4)
 for k in [('top','mask'),('bottom','mask'),('top','paste'),('top','silk'),('bottom','silk')]:check(sub+' '+str(k),k in stack.graphic_layers)
 edge=stack.outline;check(sub+' outline nonempty',edge is not None and len(edge.objects)>0)
 native_edges=[e for e in b if K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts']
 check(sub+' contour segment count',len(edge.objects)==len(native_edges))
 # Exporter emits each mechanical segment; compare endpoints independent of direction.
 norm=lambda a,bb:tuple(sorted((tuple(round(v,5) for v in a),tuple(round(v,5) for v in bb))))
 source=sorted(norm(C(e,'start')[1:3],C(e,'end')[1:3]) for e in native_edges)
 cam=sorted(norm([o.x1,o.y1*-1],[o.x2,o.y2*-1]) for o in edge.objects)
 check(sub+' contour coordinates',source==cam)
 cpl=list(csv.DictReader(open(folder/'manufacturing/positions_jlc.csv',encoding='utf-8-sig')))
 check(sub+' CPL exactly matches fitted BOM',len(cpl)==167 and {r['Designator'] for r in cpl}==refs)
 check(sub+' CPL front only',all(r['Layer']=='Top' for r in cpl))
 adc=next(f for f in b if K(f)=='footprint' and any(K(x)=='property' and x[1:3]==['Reference','U15'] for x in f));ax,ay=C(adc,'at')[1:3]
 paste=stack.graphic_layers['top','paste'];ep_paste=[o for o in paste.objects if hasattr(o,'x') and abs(o.x-ax)<1e-5 and abs(o.y+ay)<1e-5]
 check(sub+' ADC exposed-pad paste flash exists',len(ep_paste)==1)
 box=ep_paste[0].aperture.bounding_box(MM)
 check(sub+' ADC exposed-pad paste 0.9mm square',all(abs(box[1][i]-box[0][i]-.9)<1e-5 for i in [0,1]))

 for ref,wanted_count in [('U18',2),('U19',6)]:
  fp=next(f for f in b if K(f)=='footprint' and any(K(x)=='property' and x[1:3]==['Reference',ref] for x in f))
  at=C(fp,'at');theta=math.radians(at[3] if len(at)>3 else 0)
  apertures=[p for p in fp if K(p)=='pad' and C(p,'layers') and ('F.Paste' in C(p,'layers')[1:]) and ((ref=='U18' and p[1]=='') or (ref=='U19' and p[1] in ['1','2','3','4','5','6']))]
  check(sub+' '+ref+' stencil aperture count',len(apertures)==wanted_count)
  for idx,pad in enumerate(apertures):
   x,y=C(pad,'at')[1:3];xx=at[1]+x*math.cos(theta)+y*math.sin(theta);yy=at[2]-x*math.sin(theta)+y*math.cos(theta)
   flashes=[o for o in paste.objects if hasattr(o,'x') and abs(o.x-xx)<1e-5 and abs(o.y+yy)<1e-5]
   check(sub+' '+ref+' stencil flash '+str(idx),len(flashes)==1)
   box=flashes[0].aperture.bounding_box(MM);dims=sorted(box[1][j]-box[0][j] for j in [0,1]);expected=sorted(C(pad,'size')[1:3])
   check(sub+' '+ref+' stencil dimensions '+str(idx),all(abs(a-z)<1e-5 for a,z in zip(dims,expected)))
  if ref=='U19':check(sub+' U19 no central paste',not any(hasattr(o,'x') and abs(o.x-at[1])<1e-5 and abs(o.y+at[2])<1e-5 for o in paste.objects))

 poses={next(x[2] for x in f if K(x)=='property' and x[1]=='Reference'):C(f,'at')[1:] for f in b if K(f)=='footprint'}
 for row in cpl:
  at=poses[row['Designator']];ang=at[2] if len(at)>2 else 0
  check(sub+' CPL position '+row['Designator'],abs(float(row['Mid X'])-at[0])<1e-5 and abs(float(row['Mid Y'])+at[1])<1e-5)
  check(sub+' CPL rotation '+row['Designator'],abs((float(row['Rotation'])-ang+180)%360-180)<1e-5)
 drills=stack.drill_layers;actual=sum(len(d.objects) for d in drills);expected=sum(K(e)=='via' for e in b)
 for f in b:
  if K(f)=='footprint':expected+=sum(K(p)=='pad' and C(p,'drill') is not None for p in f)
 check(sub+' drill count',actual==expected)
 expected_holes={'PTH':[],'NPTH':[]}
 for e in b:
  if K(e)=='via':expected_holes['PTH'].append((*C(e,'at')[1:3],C(e,'drill')[1]))
  if K(e)=='footprint':
   at=C(e,'at')[1:];angle=math.radians(at[2] if len(at)>2 else 0)
   for pad in e:
    if K(pad)!='pad' or C(pad,'drill') is None:continue
    hole=C(pad,'drill');check(sub+' round drill '+str(pad[1]),isinstance(hole[1],(int,float)))
    x,y=C(pad,'at')[1:3];xy=(at[0]+x*math.cos(angle)+y*math.sin(angle),at[1]-x*math.sin(angle)+y*math.cos(angle))
    expected_holes['NPTH' if str(pad[2])=='np_thru_hole' else 'PTH'].append((*xy,hole[1]))
 normalize=lambda rows:sorted(tuple(round(v,3) for v in r) for r in rows)
 for kind in ['PTH','NPTH']:
  layer=next(d for d in stack.drill_layers if str(d.original_path).endswith('-'+kind+'.drl'))
  header='TF.FileFunction,'+('NonPlated' if kind=='NPTH' else 'Plated')+',1,4,'+kind
  check(sub+' '+kind+' plating header',any(header in c for c in layer.comments))
  holes=[(o.x,-o.y,o.aperture.diameter) for o in layer.objects]
  remaining=list(holes);matched=True
  for wanted in expected_holes[kind]:
   matches=[i for i,r in enumerate(remaining) if max(abs(a-z) for a,z in zip(r,wanted))<=.000501]
   if not matches:matched=False;break
   remaining.pop(matches[0])
  check(sub+' '+kind+' drill coordinates and diameters within 0.000501mm export rounding',matched and not remaining)
 counts[sub or 'unit']={'copper_layers':list(copper),'drills':actual,'outline_segments':len(edge.objects),'fitted_parts':167}
 for side in ['top','bottom']:(folder/(side+'_cam.svg')).write_text(str(stack.to_pretty_svg(side=side)))
 # Every linked local model and footprint must resolve.
 for f in b:
  if K(f)!='footprint':continue
  lib,foot=f[1].split(':',1);fp=ROOT/'libraries'/f'{lib}.pretty'/f'{foot}.kicad_mod'
  # Frame mechanical footprints must also resolve locally.
  r=next(x[2] for x in f if K(x)=='property' and x[1]=='Reference')
  check(sub+' local footprint '+r,fp.is_file())
  for m in [e for e in f if K(e)=='model']:
   path=Path(m[1].replace('${KIPRJMOD}',str(folder)));check(sub+' model path '+r,path.is_file())
(ROOT/'manufacturing_validation.json').write_text(json.dumps({'status':'passed','checks':checks,'counts':counts,'board_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'ir_glasses_EVT_E6.kicad_pcb',ROOT/'carrier/ir_glasses_EVT_E6_carrier.kicad_pcb']},'cam_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in [ROOT/'manufacturing',ROOT/'carrier/manufacturing'] for p in folder.iterdir() if p.is_file()},'not_tested':['factory DFM','SMT platform rotation corrections','bench optical/electrical performance']},indent=2));print(len(checks),'CAM/BOM/CPL/library checks passed')
