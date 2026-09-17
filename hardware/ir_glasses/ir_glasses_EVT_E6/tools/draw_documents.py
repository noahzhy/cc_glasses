#!/usr/bin/env python3
"""Vector mechanical/assembly drawings taken from the actual PCB coordinates."""
from pathlib import Path
import json,math,csv
import sexpdata as sx
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3,landscape
ROOT=Path(__file__).resolve().parents[1];W,H=landscape(A3)
K=lambda x:str(x[0]) if isinstance(x,list) and x else ''
C=lambda x,k:next((e for e in x if K(e)==k),None)
b=sx.load(open(ROOT/'ir_glasses_EVT_E6.kicad_pcb'));edges=[];fps={}
for e in b:
 if K(e)=='gr_line' and C(e,'layer')[1]=='Edge.Cuts':edges.append((C(e,'start')[1:3],C(e,'end')[1:3]))
 if K(e)=='footprint':
  ref=next(x[2] for x in e if K(x)=='property' and x[1]=='Reference');a=C(e,'at');pads=[];ang=math.radians(a[3] if len(a)>3 else 0)
  for p in e:
   if K(p)!='pad':continue
   pa=C(p,'at');x,y=pa[1:3];pads.append({'n':str(p[1]),'x':a[1]+x*math.cos(ang)+y*math.sin(ang),'y':a[2]-x*math.sin(ang)+y*math.cos(ang),'net':C(p,'net')[-1] if C(p,'net') else ''})
  fps[ref]={'x':a[1],'y':a[2],'angle':a[3] if len(a)>3 else 0,'side':C(e,'layer')[1],'pads':pads}
xmin=min(p[0] for e in edges for p in e);xmax=max(p[0] for e in edges for p in e);ymin=min(p[1] for e in edges for p in e);ymax=max(p[1] for e in edges for p in e)
def header(c,title,subtitle):
 c.setFillColor(HexColor('#16324a'));c.setFont('Helvetica-Bold',22);c.drawString(42,H-48,title);c.setFont('Helvetica',10);c.drawString(42,H-69,subtitle)
 c.setStrokeColor(HexColor('#d2dce5'));c.line(42,H-82,W-42,H-82)
def footer(c,n):
 c.setFillColor(HexColor('#526575'));c.setFont('Helvetica',9);c.drawString(42,24,'EVT E6 | 2026-09-17 | All dimensions in mm | Prototype: bench validation pending');c.drawRightString(W-42,24,str(n))
def plot(c,region,rect,refs=None,mirror=False,labels=True):
 x0,y0,x1,y1=region;rx,ry,rw,rh=rect;s=min(rw/(x1-x0),rh/(y1-y0));ox=rx+(rw-(x1-x0)*s)/2;oy=ry+(rh-(y1-y0)*s)/2
 def xy(x,y):return ox+((x1-x) if mirror else (x-x0))*s,oy+(y1-y)*s
 c.saveState();p=c.beginPath();p.rect(ox,oy,(x1-x0)*s,(y1-y0)*s);c.clipPath(p,stroke=0)
 c.setStrokeColor(HexColor('#899eae'));c.setLineWidth(.7)
 for a,bb in edges:c.line(*xy(*a),*xy(*bb))
 labelboxes=[]
 for r,f in fps.items():
  if refs is not None and r not in refs:continue
  if not(x0<=f['x']<=x1 and y0<=f['y']<=y1):continue
  col='#008c91' if r.startswith('PD') else '#d87525' if r.startswith('D') and r[1:].isdigit() and int(r[1:])<=16 else '#365771'
  c.setFillColor(HexColor(col));c.setStrokeColor(HexColor(col))
  for p in f['pads']:
   px,py=xy(p['x'],p['y']);c.circle(px,py,1.3 if p['n']=='1' else .55,stroke=1,fill=p['n']=='1')
  if len(f['pads'])>1:
   pp=[xy(p['x'],p['y']) for p in f['pads']];xx=[p[0] for p in pp];yy=[p[1] for p in pp]
   c.setLineWidth(.3);c.rect(min(xx)-2,min(yy)-2,max(xx)-min(xx)+4,max(yy)-min(yy)+4,stroke=1,fill=0)
  if labels:
   px,py=xy(f['x'],f['y']);c.setFont('Helvetica-Bold',6.5);width=c.stringWidth(r,'Helvetica-Bold',6.5)
   candidates=[(px+dx,py+dy) for dy in [7,-12,15,-20,23,-28] for dx in [0,12,-12,24,-24]]
   for lx,ly in candidates:
    box=(lx-width/2-1,ly-1,lx+width/2+1,ly+7)
    if not any(box[0]<q[2] and box[2]>q[0] and box[1]<q[3] and box[3]>q[1] for q in labelboxes):break
   labelboxes.append(box);c.setLineWidth(.25);c.line(px,py,lx,ly);c.setFillColor(HexColor('#ffffff'));c.rect(box[0],box[1],box[2]-box[0],box[3]-box[1],fill=1,stroke=0);c.setFillColor(HexColor(col));c.drawCentredString(lx,ly,r)
 c.restoreState();return xy,s
optic=[r for r in fps if (r.startswith('PD') or r.startswith('D') and r[1:].isdigit() and int(r[1:])<=16)]
c=canvas.Canvas(str(ROOT/'mechanical_dimensions.pdf'),pagesize=(W,H));header(c,'EVT E6 / mechanical reference','Finished board outline and all 32 optical positions are unchanged from EVT E4.')
xy,s=plot(c,(xmin-3,ymin-4,xmax+3,ymax+4),(60,210,W-120,H-340),optic)
a=xy(xmin,ymin-2);bb=xy(xmax,ymin-2);c.setStrokeColor(HexColor('#16324a'));c.line(*a,*bb);c.setFont('Helvetica-Bold',11);c.drawCentredString((a[0]+bb[0])/2,a[1]+10,f'Overall width {xmax-xmin:.3f}')
c.setFont('Helvetica',11)
for i,line in enumerate([f'Bounding box: X {xmin:.6f} .. {xmax:.6f}; Y {ymin:.6f} .. {ymax:.6f}; height {ymax-ymin:.3f}.','4 copper layers / 1.6 mm finished thickness. Exact milling contour: PCB Edge.Cuts and Gerber.','Do not infer tolerances or mounting clearances from this overview; retain the E4 mechanical fixture.','Orange = LED; teal = photodiode. Filled dot marks pad 1. All views use actual board coordinates.','Fabrication uses the separate support-frame package; controlled routing removes solid tabs after assembly.']):c.drawString(55,165-i*20,line)
footer(c,1);c.save()
c=canvas.Canvas(str(ROOT/'optical_assembly.pdf'),pagesize=(W,H));header(c,'EVT E6 / front assembly','167 fitted components on front. Filled dot marks pad 1; verify supplier-library orientation before SMT.')
plot(c,(xmin-1,ymin-1,xmax+1,ymax+1),(40,80,W-80,H-190),[r for r in fps if not r.startswith('TP')],labels=True);footer(c,1);c.showPage()
for i,(a,z) in enumerate([(43,95),(85,142),(130,177)]):
 header(c,'EVT E6 / upper electronics '+['left','center','right'][i],'Front view. Boxes show pad envelopes; filled dots mark pad 1. Use CPL for exact coordinates.')
 plot(c,(a,55,z,77),(45,100,W-90,H-220),[r for r in fps if not r.startswith('TP')],labels=True)
 footer(c,2+i);c.showPage()
header(c,'EVT E6 / optical polarity and test access','PD pad 1 = A/GND; pad 2 = K/TIA input. Test pads are on back and are not fitted parts.')
plot(c,(xmin-2,ymin-2,xmax+2,ymax+2),(45,340,W-90,340),optic)
plot(c,(xmin-2,56,xmax+2,78),(45,100,W-90,180),[r for r in fps if r.startswith('TP')],mirror=True)
c.setFont('Helvetica-Bold',11);c.drawString(45,307,'Back view (mirrored horizontally): TP1..TP12; J2 remains front-side bare Tag-Connect pads.')
footer(c,5);c.showPage();header(c,'EVT E6 / optical coordinate table','KiCad absolute board coordinates. Angles in degrees. E4 comparison is checked independently.')
c.setFont('Helvetica-Bold',10);cols=[55,135,220,305,390,480,570,660,750,840,930,1020]
heads=['LED','X','Y','Angle','Pad1 net','PD','X','Y','Angle','Pad1 net','Pad2 net']
for x,t in zip(cols,heads):c.drawString(x,H-115,t)
rows=[]
for i in range(1,17):
 led=fps[f'D{i}'];pd=fps[f'PD{i}'];net=lambda f,n:next(p['net'] for p in f['pads'] if p['n']==n)
 values=[f'D{i}',f"{led['x']:.6f}",f"{led['y']:.6f}",str(led['angle']),net(led,'1'),f'PD{i}',f"{pd['x']:.6f}",f"{pd['y']:.6f}",str(pd['angle']),net(pd,'1'),net(pd,'2')]
 c.setFont('Helvetica',9)
 for x,t in zip(cols,values):c.drawString(x,H-145-30*(i-1),t)
 for r in [f'D{i}',f'PD{i}']:f=fps[r];rows.append({'Reference':r,'X_mm':f['x'],'Y_mm':f['y'],'Rotation_deg':f['angle'],'Pad1_net':net(f,'1'),'Pad2_net':net(f,'2')})
footer(c,6);c.save()
with (ROOT/'optical_placement.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Mechanical and six-page assembly drawings generated from PCB')
