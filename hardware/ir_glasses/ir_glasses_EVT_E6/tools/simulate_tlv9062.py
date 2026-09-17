#!/usr/bin/env python3
"""TI typical macromodel evaluation; NOT manufacturing/process or bench qualification."""
from pathlib import Path
import subprocess,json,itertools,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'analog_validation';OUT.mkdir(exist_ok=True)
(OUT/'.spiceinit').write_text('set ngbehavior=ps\n')
# Map PSpice noiseless resistor semantics explicitly to ngspice, retaining the original model.
orig=(OUT/'TLV9062_TI_RevD.lib').read_text()
lines=[]
for line in orig.splitlines():
 if line.lower().startswith('.model r_noiseless '):line='.model R_NOISELESS R(TC1=0)'
 elif line.lstrip().upper().startswith('R') and 'R_NOISELESS' in line:line+=' noisy=0'
 lines.append(line)
(OUT/'TLV9062_ngspice.lib').write_text('\n'.join(lines)+'\n')
LSB=2.5/65536
base='.include TLV9062_ngspice.lib\n.options reltol=1e-5 vntol=1e-9 abstol=1e-13\n'
def run(name,body,commands):
 deck='EVT E6 '+name+'\n'+base+body+'\n.control\nset wr_singlescale\nset wr_vecnames\nset numdgt=12\n'+commands+'\nquit\n.endc\n.end\n'
 (OUT/(name+'.cir')).write_text(deck)
 p=subprocess.run(['ngspice','-b',name+'.cir'],cwd=OUT,capture_output=True,text=True,timeout=120)
 (OUT/(name+'.log')).write_text(p.stdout+p.stderr)
 if 'unrecognized parameter' in p.stderr:raise RuntimeError(name+' unsupported model parameter: '+p.stderr)
 if p.returncode or 'Error:' in p.stderr or 'Error:' in p.stdout:raise RuntimeError(name+' '+p.stderr[-1000:])
 return np.loadtxt(OUT/(name+'.dat'),skiprows=1)
def loop(name,r=100,c=330,par=10,v=3.3,temp=25,vin=1.1,stage=2):
 body=f'.temp {temp}\nVdd vdd 0 {v}\nVin inp 0 {vin}\nX1 inp inv vdd 0 out TLV9062\nVtest inv out DC 0 AC 1\n'
 if stage==2:body+=f'Coutpcb out 0 {par}p\nRiso out adc {r}\nCf adc 0 {c+par+3}p\nRsw adc sample 200\nCs sample 0 15p\n'
 else:body+=f'Rload out 0 30k\nCpcb out 0 {par}p\n'
 x=run(name,body,f'ac dec 120 1 100Meg\nlet lg=-v(out)/v(inv)\nwrdata {name}.dat real(lg) imag(lg)')
 f=x[:,0];g=x[:,1]+1j*x[:,2];mag=20*np.log10(abs(g));ph=np.unwrap(np.angle(g))*180/np.pi
 ids=np.where((mag[:-1]>=0)&(mag[1:]<0))[0];assert len(ids)==1,(name,ids)
 k=ids[0];q=-mag[k]/(mag[k+1]-mag[k]);pm=180+ph[k]+q*(ph[k+1]-ph[k]);fc=10**(np.log10(f[k])+q*np.log10(f[k+1]/f[k]))
 # first -180 degree crossing, if any, inside evaluated range
 ids2=np.where((ph[:-1]>-180)&(ph[1:]<=-180))[0];gm=None
 if len(ids2):
  k=ids2[0];q=(-180-ph[k])/(ph[k+1]-ph[k]);gm=-(mag[k]+q*(mag[k+1]-mag[k]))
 return dict(name=name,R_ohm=r,C_pF=c,extra_pcb_pF=par,Vcc=v,temp_C=temp,input_V=vin,stage=stage,PM_deg=pm,crossover_Hz=fc,GM_dB=gm)
def path(r=100,c=330,par=10,v=3.3,temp=25,source='DC 1.5 AC 1',tia=False):
 body=f'.temp {temp}\nVdd vdd 0 {v}\nVin source 0 {source}\n'
 if tia:body+='Rtia source tiain 100k\nCtia tiain 0 22p\nEbuf inp 0 tiain 0 1\n'
 else:body+='Rsrc source inp 100\n'
 body+=f'X1 inp buf vdd 0 buf TLV9062\nCpcb1 buf 0 {par}p\nRhi buf div 10k\nRlo div 0 20k\nCdiv div 0 5p\nX2 div drive vdd 0 drive TLV9062\nCpcb2 drive 0 {par}p\nRiso drive adc {r}\nCf adc 0 {c+3+par}p\nRsw adc sample 200\nCs sample 0 15p\n'
 return body
def settling(x,start,end):
 t=x[:,0];y=x[:,-1];sel=(t>=start)&(t<=end);a=t[sel];b=y[sel];target=np.mean(b[-max(10,len(b)//30):]);bad=np.where(abs(b-target)>LSB/2)[0];return (float(a[bad[-1]+1]-start) if len(bad) and bad[-1]+1<len(a) else None),float(target)
results={'scope':'typical TI macromodel; ADC Fig28 simplified equivalent; parasitics assumed; no process corners or bench data','model_sha256':hashlib.sha256((OUT/'TLV9062_TI_RevD.lib').read_bytes()).hexdigest(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True).splitlines()[1],'loop':[]}
for r in [33,47,68,100]:results['loop'].append(loop('loop_R'+str(r),r=r))
# sensitivity sweep, NOT transistor process corners; typical model can omit temperature effects.
for i,(v,temp,c,par) in enumerate(itertools.product([3.0,3.3,3.399],[-25,25,85],[313.5,346.5],[0,30])):
 results['loop'].append(loop('corner_'+str(i),r=99,c=c,par=par,v=v,temp=temp))
for i,(v,vin,par) in enumerate(itertools.product([3.0,3.399],[0.1,1.5],[0,30])):results['loop'].append(loop('stage1_'+str(i),v=v,vin=vin,par=par,stage=1))
# First-stage 50pF layout sensitivity, and second-stage common mode near range endpoints
results['loop'].append(loop('stage1_50p',par=50,stage=1))
for i,vin in enumerate([0.1,2.2]):results['loop'].append(loop('driver_vcm_'+str(i),vin=vin,par=30))
results['steps']=[]
for r in [33,100]:
 for amp,lo,hi in [('small',1.49,1.51),('large',0.15,3.1)]:
  name=f'step_{amp}_{r}';x=run(name,path(r=r,source=f'PULSE({lo} {hi} 2u 1n 1n 8u 20u)'),f'tran 2n 18u 0 2n\nwrdata {name}.dat v(source) v(drive) v(adc) v(sample)')
  a,high=settling(x,2.001e-6,9.9e-6);b,low=settling(x,10.002e-6,17.9e-6);sel=(x[:,0]>=2.001e-6)&(x[:,0]<9.9e-6);ov=(max(x[sel,-1])-high)/(high-low)*100
  results['steps'].append(dict(name=name,rise_settle_s=a,fall_settle_s=b,overshoot_pct=float(ov),steady_low_V=low,steady_high_V=high))
name='tia_first_order';x=run(name,path(source='PULSE(0.15 3.1 5u 1n 1n 70u 160u)',tia=True),f'tran 10n 145u 0 10n\nwrdata {name}.dat v(source) v(drive) v(adc) v(sample)');a,hi=settling(x,5.001e-6,74e-6);b,lo=settling(x,75.002e-6,144e-6);results['tia_first_order']=dict(rise_settle_s=a,fall_settle_s=b,limitation='ideal 100k/22p pole only; real PD/TIA not modeled')
# Charge-sharing stress: precharge 15pF to 0 or 2.5V, then connect through 200ohm.
results['kickback']=[]
for reset in [0,2.5]:
 name='kick_'+str(reset).replace('.','p');body=path();body=body.replace('Rsw adc sample 200','Rsw adc sw 200\nSacq sw sample ctrl 0 SAMPLE_SW\nSreset sample rst invctrl 0 SAMPLE_SW\n.model SAMPLE_SW SW(Ron=0.01 Roff=1e12 Vt=0.5 Vh=0.01)\nVctrl ctrl 0 PWL(0 0 2u 0 2.001u 1)\nBinv invctrl 0 V=1-v(ctrl)\nVrst rst 0 '+str(reset))
 x=run(name,body,f'tran 1n 8u 0 1n\nwrdata {name}.dat v(adc) v(sample)');a,final=settling(x,2.001e-6,7.9e-6);results['kickback'].append(dict(reset_V=reset,settle_s=a,error_at_110ns_V=float(np.interp(2.111e-6,x[:,0],x[:,-1])-final),error_at_5us_V=float(np.interp(7.001e-6,x[:,0],x[:,-1])-final)))
results['noise']=[]
for r in [33,100]:
 name=f'noise_{r}';noise_body=path(r=r).replace('Rsw adc sample 200','Rsw adc sample 200 noisy=0')
 x=run(name,noise_body,f'noise v(sample) Vin dec 150 0.1 100Meg\nsetplot noise1\nwrdata {name}.dat onoise_spectrum')
 total=float(np.sqrt(np.trapezoid(x[:,1]**2,x[:,0])));adc=(2.5/(2*np.sqrt(2)))/10**(85/20);combined=float(np.hypot(total,adc));diff=combined*np.sqrt(2)
 results['noise'].append(dict(R_ohm=r,buffer_divider_RMS_V=total,ADC_SNR85dB_equivalent_RMS_V=float(adc),combined_estimate_RMS_V=combined,dark_subtracted_uncorrelated_RMS_V=float(diff),diff_codes_RMS=float(diff/LSB)))
results['driver_only_steps']=[]
for r in [33,100]:
 name=f'driver_step_{r}'
 body=f'Vdd vdd 0 3.3\nVin inp 0 PULSE(1.49 1.51 2u 1n 1n 8u 20u)\nX1 inp drive vdd 0 drive TLV9062\nCpcb drive 0 10p\nRiso drive adc {r}\nCf adc 0 343p\nRsw adc sample 200\nCs sample 0 15p\n'
 x=run(name,body,f'tran 1n 18u 0 1n\nwrdata {name}.dat v(inp) v(drive) v(adc) v(sample)');a,hi=settling(x,2.001e-6,9.9e-6);b,lo=settling(x,10.002e-6,17.9e-6);sel=(x[:,0]>=2.001e-6)&(x[:,0]<9.9e-6)
 results['driver_only_steps'].append(dict(R_ohm=r,rise_settle_s=a,fall_settle_s=b,overshoot_pct=float((max(x[sel,-1])-hi)/(hi-lo)*100)))
for name,v,temp in [('step_sensitivity_low',3.0,85),('step_sensitivity_high',3.399,-25)]:
 x=run(name,path(r=101,c=346.5,par=30,v=v,temp=temp,source=f'PULSE(0.15 {v-.15} 2u 1n 1n 8u 20u)'),f'tran 2n 18u 0 2n\nwrdata {name}.dat v(source) v(drive) v(adc) v(sample)');a,hi=settling(x,2.001e-6,9.9e-6);b,lo=settling(x,10.002e-6,17.9e-6);results['steps'].append(dict(name=name,rise_settle_s=a,fall_settle_s=b,steady_low_V=lo,steady_high_V=hi))
results['gates']={'driver_PM_min_deg':50,'stage1_PM_min_deg':45,'buffer_half_LSB_settle_max_s':5e-6,'kickback_half_LSB_settle_max_s':5e-6}
selected=[x for x in results['loop'] if x['R_ohm']!=33 and not x['name'].startswith(('loop_R47','loop_R68'))]
results['selected_min_driver_PM_deg']=min(x['PM_deg'] for x in selected if x['stage']==2)
results['selected_min_stage1_PM_deg']=min(x['PM_deg'] for x in selected if x['stage']==1)
results['status']='SIMULATION_COMPLETE_NOT_BENCH_QUALIFIED'
(OUT/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in results.items() if k!='loop'},indent=2))
