"""Engineering assembly guide from actual KiCad render and coordinates."""
from pathlib import Path
import json,csv,math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parents[1];W,H=1000,650
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));c=canvas.Canvas(str(R/'populated_assembly.pdf'),pagesize=(W,H));p=json.load(open(R/'parts.json'));rows=list(csv.DictReader(open(R/'led_pd_mapping.csv')))
navy=HexColor('#15334a');blue=HexColor('#176a91');orange=HexColor('#e27b30')
def txt(x,y,s,size=11):c.setFillColor(navy);c.setFont('STSong-Light',size);c.drawString(x,y,s)
def title(s,sub):txt(35,H-40,s,23);txt(35,H-65,sub,11)
def footer(n):txt(35,20,f'EVT E6 F302 R2 | 2026-09-18 | 设计示意；首板验证待完成 | {n}/4',9)
def img(name,x,y,w,h):c.drawImage(str(R/name),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
title('贴片后示意 / 正面俯视','STM32F302CCT6 + 2 × TMUX1308 + 1 × TLV9062 | 155 个实体器件，全部正面贴装')
img('populated_top.png',25,128,950,425)
txt(35,98,'采用实际 KiCad PCB 和本地 3D 模型渲染；外观、颜色及印字不代表实物。')
txt(35,76,'U9 为 LQFP-48；U16 为 VSSOP-8。U15、U17 及原 AD7386 分压/第二级缓冲已删除。')
txt(35,54,'装配以 BOM、CPL、焊盘编号及器件规格书为准；TP 和 J2 为裸焊盘，不贴装。')
footer(1);c.showPage()
title('贴片后示意 / 斜视与关键器件','光学器件、安装结构及四层板保持 P3 基准；主控与采集区域重新布局布线。')
img('populated_oblique.png',25,160,950,390)
for i,s in enumerate(['U9：STM32F302CCT6 / C262946。不能换用仅单 ADC 的其他 F302 型号。','U16：TLV9062IDGKR / C398356，双路单位增益缓冲；R11/R12 = 100Ω，C29/C30 = 330pF C0G。','U7/U8：TMUX1308PWR；奇数 PD → ADC1 / PA0，偶数 PD → ADC2 / PA4。','载框需铣断实心连接桥；不能手折或按 V-cut 分板。工厂需确认钢网、盖油和平台角度。']):txt(35,130-i*23,s)
footer(2);c.showPage()
title('16 组 LED 与相邻双 PD 映射','ADC1 与 ADC2 使用同一个硬件触发；背景和亮灯两次采样均保留两路 12 位原始值。')
def xy(ref):
 x,y=p[ref]['pcb_xy'];return 45+(x-43)*6.8,225+(109-y)*6.8
for row in rows:
 c.setStrokeColor(HexColor('#bdcbd4'));c.setLineWidth(1)
 for pd in ['PD'+row['pd_a_id'],'PD'+row['pd_b_id']]:c.line(*xy('D'+row['led_id']),*xy(pd))
for prefix,color in [('PD',blue),('D',orange)]:
 for i in range(1,17):
  ref=prefix+str(i);x,y=xy(ref);c.setFillColor(color);c.circle(x,y,4,fill=1,stroke=0);c.setFont('Helvetica-Bold',9);c.drawCentredString(x,y+9,ref)
for idx,row in enumerate(rows):
 col=idx//8;j=idx%8;txt(80+col*470,195-j*18,f"D{row['led_id']}    ADC1: PD{row['pd_a_id']}    ADC2: PD{row['pd_b_id']}    MUX A/B: {row['address_a']}/{row['address_b']}",11)
txt(35,42,'32 个光学器件的坐标和角度与当前 P3 一致；每组为同侧距离最近的两个 PD。',10)
footer(3);c.showPage()
title('J1 排线方向与上电检查','GUOCONN 0.5K-AS-5PWB-RW / C51901197 | 正面俯视 | 上接触、0.3 mm 排线')
x0,y0,sc=245,345,35;xy=lambda x,y:(x0-x*sc,y0+y*sc)
c.setFillColor(HexColor('#eef2f5'));c.setStrokeColor(HexColor('#667b86'));a=xy(4.075,-.525);c.rect(a[0],a[1],8.15*sc,4.45*sc,fill=1)
c.setFillColor(HexColor('#d3a83e'))
for x in [-2.54,2.54]:
 xx,yy=xy(x,.975);c.rect(xx-sc,yy-1.5*sc,2*sc,3*sc,fill=1)
for i in range(1,6):
 xx,yy=xy(-1+(i-1)*.5,-1.35);c.rect(xx-.15*sc,yy-.625*sc,.3*sc,1.25*sc,fill=1);txt(xx-3,yy-36,str(i),12);c.setFillColor(HexColor('#d3a83e'))
txt(120,535,'排线插入方向 / 板上边 (-Y)',13)
c.setStrokeColor(navy);c.line(x0,527,x0,500);c.line(x0,500,x0-5,507);c.line(x0,500,x0+5,507)
txt(490,505,'正面看，最右侧信号焊盘为 Pin 1。',13)
for i,(pin,net) in enumerate([(1,'VIN_HOST'),(2,'GND'),(3,'HOST_TX / 板端 RX'),(4,'HOST_RX / 板端 TX'),(5,'NRST_EXT')]):txt(505,470-i*29,f'{pin}     {net}',13)
for i,s in enumerate(['整板输入：3.3V ±3%，正确极性；首次上电前逐线核对主机与排线导通。','机械固定脚不承担电源或地回流；不能仅凭供应商 Pin 1 或排线 A/B 名称连接。','正面坐标：J1 X=165.000 mm，Y=61.700 mm，旋转 180°；Pin 1 X=166.000，Y=63.050。','U14 = TPS259470ARPWR；U18 = TPS2553DRVR（有 EP）；U19 = TPS3702CX33DDCR（无 EP）。','复位、配置错误和采样失败必须灭灯；CPU 停止后的硬件限时关断仍需示波器实测。','本交付不含可烧录固件；不能沿用 C031 固件。全部首板测试见 first_board_tests.csv。']):txt(35,235-i*29,s,11)
footer(4);c.save();print('Wrote populated_assembly.pdf (4 pages)')
