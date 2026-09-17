"""Package KiCad-rendered populated board views into an assembly reference PDF."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.lib.colors import HexColor
from PIL import Image
R=Path(__file__).resolve().parents[1];W,H=landscape(A3)
c=canvas.Canvas(str(R/'populated_assembly.pdf'),pagesize=(W,H))
for i,(file,title) in enumerate([('populated_top.png','EVT E6 - Populated board / front'),('populated_oblique.png','EVT E6 - Populated board / oblique')],1):
 c.setFillColor(HexColor('#183f4b'));c.setFont('Helvetica-Bold',23);c.drawString(38,H-47,title)
 c.setFont('Helvetica',11);c.drawString(38,H-69,'167 fitted components on front. J2 and rear test pads are bare copper, not fitted parts.')
 p=R/'assembly_views'/file;im=Image.open(p);scale=min((W-76)/im.width,(H-180)/im.height);ww,hh=im.width*scale,im.height*scale
 c.drawImage(str(p),(W-ww)/2,95+(H-180-hh)/2,width=ww,height=hh)
 c.setFont('Helvetica',10);c.drawString(38,64,'KiCad 10.0.6 rendering from the released PCB. Illustrative component appearance, not a photograph.')
 c.drawString(38,48,'U15 uses a nominal-dimension model. Use optical_assembly.pdf and CPL for reference IDs, Pin1 and polarity.')
 c.drawString(38,27,'2026-09-17 | J1: GUOCONN 0.5K-AS-5PWB-RW; U18 input limiter / U19 OV monitor; input 3.3 V +/-3% | Electrical / optical bench validation pending.');c.drawRightString(W-38,27,str(i));c.showPage()
c.save();print('Two-page populated assembly PDF generated')
