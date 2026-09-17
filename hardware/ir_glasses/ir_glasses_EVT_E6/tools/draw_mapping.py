import json,csv
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
root=Path(__file__).resolve().parents[1];p=json.load(open(root/'parts.json'));rows=list(csv.DictReader(open(root/'led_pd_mapping.csv')))
c=canvas.Canvas(str(root/'led_pd_mapping.pdf'),pagesize=(1000,560));c.setFont('Helvetica-Bold',22);c.drawString(40,520,'EVT E6 | One LED + its two adjacent PDs');c.setFont('Helvetica',11);c.drawString(40,497,'E4 optical positions preserved. ADC-A = odd PD; ADC-B = even PD. Both sample on the same CS edge.')
def xy(ref):
 x,y=p[ref]['pcb_xy'];return 45+(x-43)*6.8,180+(109-y)*6.8
for row in rows:
 led='D'+row['led_id'];a='PD'+row['pd_a_id'];b='PD'+row['pd_b_id'];c.setStrokeColor(HexColor('#abbcca'));c.setLineWidth(1)
 for pd in [a,b]:c.line(*xy(led),*xy(pd))
for prefix,color in [('PD','#176a91'),('D','#e27b30')]:
 for i in range(1,17):
  ref=prefix+str(i);x,y=xy(ref);c.setFillColor(HexColor(color));c.circle(x,y,4,fill=1,stroke=0);c.setFont('Helvetica-Bold',9);c.drawCentredString(x,y+9,ref)
c.setFillColor(HexColor('#15334a'));c.setFont('Helvetica',10)
for idx,row in enumerate(rows):
 col=idx//8;r=idx%8;line=f"D{row['led_id']:>2}   A: PD{row['pd_a_id']:>2}   B: PD{row['pd_b_id']:>2}   mux: {row['address_a']}/{row['address_b']}"
 c.drawString(95+col*470,150-r*15,line)
c.setFont('Helvetica',9);c.drawString(40,15,'Fixed optical-neighbor mapping; this drawing is not a PCB routing or bench-validation approval.');c.save()

