"""F302 input load sensitivity. Typical amplifier model; no silicon/bench guarantee."""
from pathlib import Path
import subprocess,json,itertools,shutil
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'analog_validation';out.mkdir(exist_ok=True)
for n in ['TLV9062_TI_RevD.lib','TLV9062_ngspice.lib']:
 if not (out/n).exists():shutil.copyfile(root.parent/'ir_glasses_EVT_E6/analog_validation'/n,out/n)
(out/'.spiceinit').write_text('set ngbehavior=ps\n')
def run(name,body,commands):
 deck='E6 F302 '+name+'\n.include TLV9062_ngspice.lib\n.options reltol=1e-6 vntol=1e-9 abstol=1e-13\n'+body+'\n.control\nset wr_singlescale\nset wr_vecnames\nset numdgt=12\n'+commands+'\nquit\n.endc\n.end\n'
 (out/(name+'.cir')).write_text(deck);p=subprocess.run(['ngspice','-b',name+'.cir'],cwd=out,capture_output=True,text=True,timeout=120);(out/(name+'.log')).write_text(p.stdout+p.stderr)
 assert p.returncode==0 and 'Error:' not in p.stderr
 return np.loadtxt(out/(name+'.dat'),skiprows=1)
def body(v=3.3,temp=25,r=100,c=330,par=10,rs=1000,cs=5,source='DC 1.65 AC 1',loop=False):
 return f'.temp {temp}\nVdd vdd 0 {v}\nVin inp 0 {source}\nX1 inp inv vdd 0 drive TLV9062\nVfb inv drive DC 0 AC {1 if loop else 0}\nCpcb drive 0 {par}p\nRiso drive adc {r}\nCf adc 0 {c+7+par}p\nRsw adc sample {rs}\nCs sample 0 {cs}p\n'
result={'scope':'TI typical TLV9062 model, F302 CADC=5pF typical, pad=7pF approximate. Rsw=200..5000ohm and CADC=5..10pF are sensitivity assumptions, not ST guaranteed bounds. No process model, no PCB field extraction, no real PD/TIA model.','loop':[],'steps':[]}
for i,(v,t,c,par,rs,cs) in enumerate(itertools.product([3.0,3.399],[-25,85],[313.5,346.5],[0,30],[200,5000],[5,10])):
 n=f'loop_{i}';x=run(n,body(v=v,temp=t,r=99,c=c,par=par,rs=rs,cs=cs,source=f'DC {v/2}',loop=True),f'ac dec 120 1 100Meg\nlet lg=-v(drive)/v(inv)\nwrdata {n}.dat real(lg) imag(lg)')
 g=x[:,1]+1j*x[:,2];m=20*np.log10(abs(g));phase=np.unwrap(np.angle(g))*180/np.pi;k=np.where((m[:-1]>=0)&(m[1:]<0))[0];assert len(k)==1;k=k[0];q=-m[k]/(m[k+1]-m[k]);pm=float(180+phase[k]+q*(phase[k+1]-phase[k]))
 result['loop'].append(dict(case=n,VDD=v,temp=t,C_pF=c,par_pF=par,Rsw_ohm=rs,Cadc_pF=cs,PM_deg=pm))
def settle(x,a,b,tol):
 z=x[(x[:,0]>=a)&(x[:,0]<=b)];target=z[z[:,0]>b-.5e-6,-1].mean();bad=np.flatnonzero(abs(z[:,-1]-target)>tol)
 return float(z[bad[-1]+1,0]-a) if len(bad) and bad[-1]+1<len(z) else (0.0 if not len(bad) else None)
for i,(v,t,lo,hi) in enumerate([(3.3,25,.15,3.1),(3.0,85,.15,2.85),(3.399,-25,.15,3.249),(3.3,25,1.64,1.66)]):
 n=f'step_{i}';x=run(n,body(v=v,temp=t,r=101,c=346.5,par=30,rs=5000,cs=10,source=f'PULSE({lo} {hi} 2u 1n 1n 8u 20u)'),f'tran 1n 18u 0 1n\nwrdata {n}.dat v(adc) v(sample)')
 result['steps'].append(dict(case=n,rise_s=settle(x,2.001e-6,9.9e-6,v/8192),fall_s=settle(x,10.002e-6,17.9e-6,v/8192)))
result['kickback']=[]
for pre in [0,3.3]:
 n='kick_'+str(pre).replace('.','p');b=body(rs=5000,cs=10,par=30,c=346.5,r=101,source='DC 1.65')
 b=b.replace('Rsw adc sample 5000','Rsw adc sw 5000\nSacq sw sample ctrl 0 SWC\nSreset sample rst invctrl 0 SWC\n.model SWC SW(Ron=.01 Roff=1e12 Vt=.5 Vh=.01)\nVctrl ctrl 0 PWL(0 0 2u 0 2.001u 1)\nBinv invctrl 0 V=1-v(ctrl)\nVrst rst 0 '+str(pre))
 x=run(n,b,f'tran 1n 10u 0 1n\nwrdata {n}.dat v(adc) v(sample)');target=x[x[:,0]>9.5e-6,-1].mean()
 result['kickback'].append(dict(precharge_V=pre,settle_s=settle(x,2.001e-6,9.9e-6,3.3/8192),error_at_acquisition_end_V=float(np.interp(7.126e-6,x[:,0],x[:,-1])-target)))
n='noise';x=run(n,body().replace('Rsw adc sample 1000','Rsw adc sample 1000 noisy=0'),f'noise v(sample) Vin dec 150 0.1 100Meg\nsetplot noise1\nwrdata {n}.dat onoise_spectrum')
result['buffer_RC_noise_RMS_V']=float(np.sqrt(np.trapezoid(x[:,1]**2,x[:,0])))
result['ideal_12bit_quantization_RMS_V']=float(3.3/4096/np.sqrt(12))
result['minimum_PM_deg']=min(z['PM_deg'] for z in result['loop'])
result['sampling_time_s']=61.5/12e6;result['conversion_time_s']=74/12e6
result['status']='typical_model_engineering_checks_passed' if result['minimum_PM_deg']>=50 and all(z[k] is not None and z[k]<5e-6 for z in result['steps'] for k in ['rise_s','fall_s']) and all(z['settle_s']<5.125e-6 for z in result['kickback']) else 'review_required'
result['noise_acceptance']='Not set; partial buffer budget only. Real ADC noise, VDDA reference noise, TIA/PD, LED interference and calibration require bench tests.'
(out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='loop'},indent=2))
