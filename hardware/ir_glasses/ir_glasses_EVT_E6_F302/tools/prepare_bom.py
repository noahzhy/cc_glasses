from pathlib import Path
import json,csv,math,collections
R=Path(__file__).resolve().parents[1]
def fitted(path):
 return {r:p for r,p in json.load(open(path)).items() if not r.startswith('TP') and r!='J2'}
new=fitted(R/'parts.json');old=fitted(R.parent/'ir_glasses_EVT_E6/parts.json')
def group(parts):
 d={}
 for r,p in parts.items():
  code=p.get('lcsc','');v=d.setdefault(code,{'refs':[],'mpn':p.get('mpn',''),'value':p['value']});v['refs'].append(r)
 return d
ng,og=group(new),group(old)
snap={p.stem:json.load(open(p)) for p in (R/'evidence/stock').glob('*.json')}
def quote(code,n):
 d=snap.get(code,{}).get('data',{});q=max(n,int(d.get('minBuyNumber') or 1));ps=sorted(d.get('productPriceList') or [],key=lambda x:x['ladder']);eligible=[p for p in ps if p['ladder']<=q and p.get('usdPrice') is not None]
 return float(eligible[-1]['usdPrice']) if eligible else None
rows=[]
for code,g in sorted(ng.items()):
 s=snap.get(code,{});d=s.get('data',{});stock=(d.get('domesticStockVO') or {}).get('total',d.get('stockNumber'));n=len(g['refs']);p=quote(code,n*10)
 rows.append([code,g['mpn'],', '.join(sorted(g['refs'])),n,stock,max(0,n*10-stock) if isinstance(stock,(int,float)) else 'UNKNOWN',p,s.get('checked_at',''),s.get('source','')])
cost=[]
for code in sorted(set(ng)|set(og)):
 a=len(og.get(code,{}).get('refs',[]));b=len(ng.get(code,{}).get('refs',[]));row=[code,ng.get(code,og.get(code))['mpn'],a,b]
 for count in [1,10,100]:row.extend([quote(code,max(1,a*count)) if a else 0,quote(code,max(1,b*count)) if b else 0])
 cost.append(row)
payload={'bom':rows,'cost':cost,'new_count':len(new),'old_count':len(old),'notes':['价格为LCSC公开美元阶梯报价；不是国内人民币贴片结算价。','成本按每板净用量计算，阶梯数量=max(板数×该料每板用量,最小起订量)，未计采购余料、损耗、运费、税及贴片费。','1/10/100板分别使用同批查询的旧、新BOM阶梯价格；零表示该版本不使用该料，缺失报价留空。','库存为查询时快照，采购前须重新确认；10板缺口列不包括贴片损耗。','STM32F302CCT6库存以BOM库存页本次查询值为准，不自动改换其他MCU；阶梯价不代表相应数量可供货。','板上155个贴装元件；J2与测试点为裸铜，不采购不贴片。']}
descriptions={
 'C262946':'32位 Cortex-M4 MCU，256KB Flash，最高72MHz，双12位ADC；LQFP-48',
 'C123302':'单路可重触发单稳态，施密特输入；用于LED硬件限时关断；SSOP-8',
 'C125094':'黄绿色状态指示LED，峰值574nm；0603',
 'C138719':'可调限流高侧电源开关，2.5～6.5V，高电平使能；WSON-6，带底部焊盘',
 'C19224':'单路双向ESD保护，反向截止电压5V；SOD-323',
 'C19269752':'940nm红外LED，视角100°；1206',
 'C19330':'磁珠，600Ω@100MHz，额定500mA；0603',
 'C2068031':'3.3V电源窗口监控器，开漏输出；TSOT-23-6',
 'C2443469':'单路单向ESD保护，反向截止电压3.3V；SOD-523',
 'C2921391':'红外光电二极管，响应波段730～1100nm；1206',
 'C3662799':'电子保险丝，工作电压2.7～23V，可调限流；2×2mm QFN-10',
 'C398356':'双路轨到轨输入/输出运放，1.8～5.5V，10MHz增益带宽；VSSOP-8',
 'C398358':'单路轨到轨输入/输出运放，1.8～5.5V，10MHz增益带宽；SOT-23-5',
 'C485815':'16路恒流LED驱动器，串行移位接口，供电3～5.5V；VQFN-24，带底部焊盘',
 'C51901197':'5P FPC连接器，0.5mm间距，上接触，卧贴，适配0.3mm排线',
 'C55440':'双路双向ESD保护，反向截止电压3.3V；SOT-23',
 'C779410':'四路轨到轨输入/输出运放，1.8～5.5V，10MHz增益带宽；TSSOP-14',
 'C7827':'单路逻辑反相器，1.65～5.5V；SOT-23-5',
 'C967633':'六轴IMU（三轴加速度计＋三轴陀螺仪），数字接口；LGA-14',
 'C970231':'单路8选1模拟开关，独立地址选择，1.62～5.5V；TSSOP-16',
}
for code in ng:
 d=snap[code]['data'];a={p['paramName']:p['paramValue'] for p in d.get('paramVOList',[])}
 if '容值' in a:
  descriptions[code]='电容，'+ '，'.join(a[k] for k in ['容值','精度','额定电压','温度系数'])+'；'+d['encapStandard']
 elif '阻值' in a:
  descriptions[code]=a['电阻类型']+'，'+'，'.join(a[k] for k in ['阻值','精度','功率'])+'；'+d['encapStandard']
assert set(descriptions)==set(ng)
payload['parameters']=descriptions
(R/'evidence/bom_data.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
with (R/'procurement_gaps.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['LCSC','MPN','References','Qty_per_board','Stock','Gap_10_boards','USD_unit_10_boards','Checked_at','Source']);w.writerows(r for r in rows if r[5]!='UNKNOWN' and r[5]>0 or r[5]=='UNKNOWN')
print('fitted',len(new),'old',len(old),'groups',len(rows),'unknown prices',sum(any(x is None for x in r[4:]) for r in cost))
