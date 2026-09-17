from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
R=Path(__file__).resolve().parents[1];W,H=landscape(A4);c=canvas.Canvas(str(R/'connector_pinout.pdf'),pagesize=(W,H))
c.setFillColor(HexColor('#183f4b'));c.setFont('Helvetica-Bold',20);c.drawString(32,H-42,'EVT E6 / J1 connector and cable orientation')
c.setFont('Helvetica',10);c.drawString(32,H-62,'GUOCONN 0.5K-AS-5PWB-RW / C51901197 / front view / dimensions in mm')
x0,y0,sc=220,325,34
# Front view of placed component: local x reversed, local positive y points toward top edge.
xy=lambda x,y:(x0-x*sc,y0+y*sc)
c.setFillColor(HexColor('#f1f4f5'));c.setStrokeColor(HexColor('#667b86'));a=xy(4.075,-.525);c.rect(a[0],a[1],8.15*sc,4.45*sc,fill=1)
c.setFillColor(HexColor('#d3a83e'))
for x in [-2.54,2.54]:
 xx,yy=xy(x,.975);c.rect(xx-sc,yy-1.5*sc,2*sc,3*sc,fill=1)
for i in range(1,6):
 xx,yy=xy(-1+(i-1)*.5,-1.35);c.rect(xx-.15*sc,yy-.625*sc,.3*sc,1.25*sc,fill=1)
 c.setFillColor(HexColor('#183f4b'));c.setFont('Helvetica-Bold',10);c.drawCentredString(xx,yy-35,str(i));c.setFillColor(HexColor('#d3a83e'))
c.setFillColor(HexColor('#183f4b'));c.setFont('Helvetica-Bold',11);c.drawCentredString(x0,y0+4.5*sc,'CABLE ENTRY / BOARD TOP EDGE (-Y)')
c.setLineWidth(1.3);c.line(x0,y0+4.25*sc,x0,y0+3.7*sc);c.line(x0,y0+3.7*sc,x0-5,y0+3.9*sc);c.line(x0,y0+3.7*sc,x0+5,y0+3.9*sc)
c.setFont('Helvetica',10);c.drawString(430,455,'Pin 1 is the rightmost signal land in this front view.')
c.drawString(430,438,'Cable exposed copper faces the upper contacts.')
c.drawString(430,421,'Do not infer cable A/B type without the host connector.')
for i,(n,net) in enumerate([(1,'VIN_HOST'),(2,'GND'),(3,'HOST_TX / board RX'),(4,'HOST_RX / board TX'),(5,'NRST_EXT')]):
 c.setFont('Helvetica-Bold',11);c.drawString(445,387-i*22,str(n));c.setFont('Helvetica',11);c.drawString(478,387-i*22,net)
c.setFont('Helvetica',10)
lines=['Signal lands: 0.30 x 1.25, pitch 0.50. Mechanical lands: 2.00 x 3.00.',
       'J1 origin: X=165.000, Y=61.700, rotation 180 deg. Pin 1: X=166.000, Y=63.050.',
       'Manufacturer drawing does not number contacts. Numbers above define this PCB cable contract.',
       'Before power-on, continuity-check all five conductors through the actual host cable.',
       'Rated current: 0.4 A/contact. U18 calculated continuous limit: 209-282 mA.',
       'U18 precedes U14 and main capacitors. Input requirement: 3.3 V +/-3%, correct polarity.',
       'C38=22nF; U19 controls U14 EN recovery. Inrush, short transients and cable require bench tests.',
       'Working current acceptance budget <=150mA; inrush, connector drop and temperature require bench tests.']
for i,t in enumerate(lines):c.drawString(32,225-i*21,t)
c.setFont('Helvetica',8);c.drawString(32,27,'Source: GUOCONN 0.5K-AS-NPWB drawing Rev.A; see connector_and_power.md for calculations and source links.')
c.save()
