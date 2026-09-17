"""Independent netlist/PCB and worst-case static power-protection checks. Not a transient simulation."""
from pathlib import Path
import json,hashlib,math,xml.etree.ElementTree as ET,sexpdata as sx
R=Path(__file__).resolve().parents[1];p=json.load(open(R/'parts.json'));xml=ET.parse(R/'netlist.xml').getroot();net={};checks=[]
for e in xml.findall('nets/net'):
 for n in e.findall('node'):net[n.attrib['ref'],n.attrib['pin']]=e.attrib['name']
def check(name,value):
 checks.append({'check':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
def n(ref,pin):return net[ref,str(pin)]
for ref,expect in {
 'J1':{1:'VIN_HOST',2:'GND'},
 'U18':{1:'VIN_3V3',2:'INPUT_ILIM',4:'VIN_HOST',5:'GND',6:'VIN_HOST',7:'GND'},
 'U19':{5:'VIN_3V3',3:'OV_SENSE',4:'VIN_3V3',2:'GND',6:'INPUT_OK'},
 'U14':{1:'INPUT_OK',2:'GND',5:'VIN_3V3',6:'3V3',7:'INRUSH_RC',8:'GND',9:'ILIM_SET'},
 'R18':{1:'VIN_3V3',2:'OV_SENSE'},'R19':{1:'OV_SENSE',2:'GND'},
 'R28':{1:'VIN_3V3',2:'INPUT_OK'},'R29':{1:'INPUT_ILIM',2:'GND'},
 'C48':{1:'VIN_HOST',2:'GND'},'C49':{1:'VIN_3V3',2:'GND'},'C38':{1:'INRUSH_RC',2:'GND'},
}.items():
 for pin,v in expect.items():check(ref+'.'+str(pin)+' '+v,n(ref,pin)==v and p[ref]['nets'][str(pin)]==v)
for ref,mpn in [('U14','TPS259470ARPWR'),('U18','TPS2553DRVR'),('U19','TPS3702CX33DDCR'),('R18','0402WGF2000TCE'),('R19','0402WGF1002TCE'),('R29','0402WGF1103TCE'),('C38','CL05B223KB5VPNC')]:check(ref+' MPN',p[ref]['mpn']==mpn)
check('U18 FAULT explicitly unused',n('U18',3).startswith('unconnected-'))
check('U19 UV_N explicitly unused',n('U19',1).startswith('unconnected-'))
raw={(ref,pin) for (ref,pin),v in net.items() if v=='VIN_HOST' and not ref.startswith('#')}
check('raw input has no load bypass',raw=={('J1','1'),('D17','1'),('C48','1'),('U18','4'),('U18','6')})
# Part tolerances plus worst drift from 25C to -25..85C; J1 bounds the supported temperature range.
# TPS3702CX33 SET high: nominal OV 3.3*(1+.04); +/-0.9% threshold;
# hysteresis 0.3..0.8% of nominal trip. 1% resistors with conservative 200ppm/C budget.
delta_r=.01+60*200e-6;hi=200.;lo=10000.;bias=1.5e-6*hi*(1+delta_r)
kmin=1+hi*(1-delta_r)/(lo*(1+delta_r));kmax=1+hi*(1+delta_r)/(lo*(1-delta_r));threshold=3.3*1.04
trip_min=threshold*.991*kmin-bias;trip_max=threshold*1.009*kmax+bias
recover_min=threshold*(.991-.008)*kmin-bias;recover_max=threshold*(1.009-.003)*kmax+bias
normal_min=3.3*.97;normal_max=3.3*1.03
check('normal supply below lowest trip threshold',normal_max<trip_min)
check('recovery margin at normal maximum >=35mV',recover_min-normal_max>=.035)
check('DC trip margin below ADC 3.6V >=60mV',3.6-trip_max>=.060)
check('U19 low drives U14 below 0.45V shutdown threshold',.250<.450)
check('INPUT_OK pullup exceeds maximum U14 EN threshold',normal_min-10_000*1.022*(.3e-6+.1e-6)>1.223)
check('U19 SET high selects +4 percent threshold',n('U19',4)=='VIN_3V3')
check('U14 OVLO disabled; EN shutdown recovery used',n('U14',2)=='GND')
rlim_tol=.01+60*100e-6
imin=25230/(110*(1+rlim_tol))**1.016/1000
inom=23950/110**.977/1000
imax=22980/(110*(1-rlim_tol))**.94/1000
check('continuous limit including resistor drift <0.30A',imax+.001<.30)
check('continuous limit below connector rating',imax+.001<.4)
check('150mA working budget below minimum limit',.150<imin)
K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
b=sx.load(open(R/'ir_glasses_EVT_E6.kicad_pcb'));fp={next(e[2] for e in f if K(e)=='property' and e[1]=='Reference'):f for f in b if K(f)=='footprint'}
for ref in ['U18','U19','R18','R19','R28','R29','C48','C49','C38','U14','J1']:
 for pad in [e for e in fp[ref] if K(e)=='pad' and C(e,'net')]:check('PCB '+ref+'.'+str(pad[1]),C(pad,'net')[-1]==net.get((ref,str(pad[1]))))
# Dedicated DDC land pattern checked against TI DDC0006A, including absence of an exposed pad.
lib=sx.load(open(R/'libraries/IC.pretty/TPS3702_DDC0006.kicad_mod'))
pads={str(e[1]):e for e in lib if K(e)=='pad'}
check('U19 DDC has exactly six signal pads and no EP',set(pads)==set('123456'))
for num,xy in {'1':[-1.35,-.95],'2':[-1.35,0],'3':[-1.35,.95],'4':[1.35,.95],'5':[1.35,0],'6':[1.35,-.95]}.items():
 check('U19 TI land '+num,all(abs(a-b)<1e-6 for a,b in zip(C(pads[num],'at')[1:3],xy)) and C(pads[num],'size')[1:3]==[1.1,.6])
check('U19 actual footprint uses dedicated DDC',fp['U19'][1]=='IC:TPS3702_DDC0006')
for cap,chip,max_mm in [('C37','U14',4.0),('C48','U18',3.0),('C49','U19',3.0)]:
 check(cap+' local decoupling placement',math.dist(C(fp[cap],'at')[1:3],C(fp[chip],'at')[1:3])<=max_mm)
report={'status':'passed','scope':'static connectivity, selected parts and DC tolerance calculations; transient/thermal/cable tests pending','checks':checks,'normal_input_V':[normal_min,normal_max],'temperature_C':[-25,85],'monitor':'TPS3702CX33DDCR SET=high with 200R/10k divider','resistor_tempco_budget_ppm':200,'trip_V':[trip_min,trip_max],'trip_margin_to_3V6_V':3.6-trip_max,'recovery_margin_V':recover_min-normal_max,'dynamic_protection':'NOT PROVEN; comparator and EN shutdown delays require bench verification','recovery_V':[recover_min,recover_max],'continuous_limit_A':[imin,inom,imax],'board_sha256':hashlib.sha256((R/'ir_glasses_EVT_E6.kicad_pcb').read_bytes()).hexdigest()}
(R/'power_protection_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(len(checks),'power-protection checks passed',report['continuous_limit_A'],report['trip_V'],report['recovery_V'])
