"""Discrete compare/DMA model, not STM32 peripheral or firmware validation."""
from pathlib import Path
import json,re,subprocess,tempfile,hashlib
R=Path(__file__).resolve().parents[1]
def channel(initial,queue,preload=False,initial_ref=0,dma_loss=False):
 ref=initial_ref;ccr=initial;events=[];queue=list(queue)
 for cnt in range(1000):
  if cnt==ccr:
   ref^=1;events.append((cnt,ref))
   if queue and not dma_loss:
    new=queue.pop(0)
    if not preload:ccr=new
 return events
adc=channel(100,[110,250,260,65535]);led=channel(200,[300,65535])
checks={'two_ADC_rising_edges':[t for t,v in adc if v]==[100,250], 'LED_100us_request':led==[(200,1),(300,0)],'light_acquisition_inside_LED':200<250 and 250+61.5/12<300,'conversion_before_next_event':(61.5+12.5)/12<10,'CCR_preload_failure_detected':channel(100,[110,250,260,65535],preload=True)!=adc,'stale_OCREF_failure_detected':channel(100,[110,250,260,65535],initial_ref=1)!=adc,'lost_DMA_does_not_restart_counter':channel(200,[300,65535],dma_loss=True)==[(200,1)]}
# Each abort point requires disabled outputs + forced-inactive reference before rearming.
abort_times=[99,100,109,110,199,200,249,250,259,260,299,300,999]
restart_cases=[]
for abort in abort_times:
 prior_adc=[v for t,v in adc if t<=abort];prior_led=[v for t,v in led if t<=abort]
 state_adc=prior_adc[-1] if prior_adc else 0;state_led=prior_led[-1] if prior_led else 0
 # Record the actual stale state exposed by interrupting the sequence.
 restart_cases.append({'abort_us':abort,'stale_adc_ref':state_adc,'stale_led_ref':state_led,'unreset_restart_bad':channel(100,[110,250,260,65535],initial_ref=state_adc)!=adc or channel(200,[300,65535],initial_ref=state_led)!=led})
checks['abort_scenarios_expose_stale_state']=any(x['unreset_restart_bad'] for x in restart_cases)
checks['forced_inactive_restart_matches_normal']=channel(100,[110,250,260,65535],initial_ref=0)==adc and channel(200,[300,65535],initial_ref=0)==led
h=(R/'firmware_interface.h').read_text();doc=(R/'firmware_contract.md').read_text()
for macro in ['EVT_E6_TIM1_CCR_PRELOAD_ENABLED','EVT_E6_TIM1_DMA_ON_UPDATE','EVT_E6_TIM1_REPETITION_COUNT','EVT_E6_TIM1_CH3_MAIN_ENABLED','EVT_E6_TIM1_CH3N_POLARITY_INVERTED']:
 checks[macro]=bool(re.search(r'#define\s+'+macro+r'\s+0u',h))
checks['contract_configuration']=all(x in doc for x in ['OC3PE=0','OC4PE=0','CCDS=0','RCR=0','CC3NP=0','CC3E=0','CC3NE=1'])
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'test.c').write_text('#include "'+str(R/'firmware_interface.h')+'"\nint main(void){return evt_e6_adjacent_pd[0].pd_a_id==1 && EVT_E6_ADC_MAX_CODE==4095 ? 0:1;}\n')
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
checks['C11_header_size_and_mapping_compile']=True
report={'status':'passed' if all(checks.values()) else 'failed','scope':'Ideal discrete timer compare model and C header compile; excludes real DMA arbitration, timer register behavior, hardware one-shot tolerance and firmware execution','checks':checks,'ADC_events_us':adc,'LED_request_events_us':led,'abort_cases':restart_cases,'input_sha256':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['firmware_interface.h','firmware_contract.md']},'fault_note':'A lost LED-off DMA can leave request high until cleanup; external U12 hardware cutoff must be measured independently. OPM alone does not force OCREF low.'}
(R/'timing_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert all(checks.values())
