from pathlib import Path
import json,csv,hashlib,math,sexpdata as s,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];parts=json.load(open(R/'parts.json'));K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
def board(path):
 b=s.load(open(path));fps={}
 for f in b:
  if K(f)=='footprint':fps[next(x[2] for x in f if K(x)=='property' and x[1]=='Reference')]=f
 return b,fps
b,fps=board(R/(R.name+'.kicad_pcb'));old,ofps=board(R.parent/'ir_glasses_EVT_E6/ir_glasses_EVT_E6.kicad_pcb');checks={}
checks['part_references_match']=set(parts)==set(fps)
pins={}
for net in ET.parse(R/'netlist.xml').findall('./nets/net'):
 for n in net.findall('node'):pins[(n.get('ref'),n.get('pin'))]=net.get('name')
checks['schematic_parts_nets_match']=all(pins.get((r,n))==net for r,p in parts.items() for n,net in p['nets'].items() if net and not net.startswith('unconnected-'))
checks['pcb_parts_nets_match']=all(C(pad,'net')[-1]==parts[r]['nets'][pad[1]] for r,f in fps.items() for pad in f if K(pad)=='pad' and C(pad,'net') and pad[1] in parts[r]['nets'])
optical=['D'+str(i) for i in range(1,17)]+['PD'+str(i) for i in range(1,17)]
checks['optical_32_positions_angles_unchanged']=all(C(fps[r],'at')==C(ofps[r],'at') for r in optical)
edges=lambda board:[e for e in board if K(e).startswith('gr_') and C(e,'layer') and C(e,'layer')[1]=='Edge.Cuts']
checks['unit_edge_geometry_unchanged']=edges(b)==edges(old)
checks['front_assembly']=all(C(f,'layer')[1]=='F.Cu' for r,f in fps.items() if not r.startswith('TP') and r!='J2')
checks['four_copper_layers']=sum(1 for e in C(b,'layers')[1:] if e[1].endswith('.Cu'))==4
checks['removed_components_absent']=not set(['U15','U17','R21','R22','R23','R24','R25','R26','C39','C41','C42','C43'])&set(parts)
checks['ADC1_PA0_ADC2_PA4']=parts['U9']['nets']['10']=='ADC_A' and parts['U9']['nets']['14']=='ADC_B'
checks['RC_network']=all(parts[r]['value']=='100' for r in ['R11','R12']) and all(parts[r]['value']=='330p C0G' for r in ['C29','C30'])
checks['VDDA_local_10nF']=parts['C11']['lcsc']=='C15195' and parts['C11']['value']=='10n X7R'
checks['VDD_local_bulk_0603_10uF']=parts['C40']['lcsc']=='C19702' and fps['C40'][1]=='C:0603' and C(fps['C40'],'at')[1:3]==[113.8,71.8]
rows=list(csv.DictReader(open(R/'led_pd_mapping.csv')))
checks['16_pairs_odd_even_addresses']=len(rows)==16 and all(int(r['pd_a_id'])%2==1 and int(r['pd_b_id'])%2==0 and int(r['address_a'])==(int(r['pd_a_id'])-1)//2 and int(r['address_b'])==(int(r['pd_b_id'])-1)//2 for r in rows)
checks['mapping_unchanged']=list(csv.DictReader(open(R.parent/'ir_glasses_EVT_E6/led_pd_mapping.csv')))==rows
nearest_ok=[]
for row in rows:
 led=int(row['led_id']);pd_ids=range(1,9) if led<=8 else range(9,17)
 nearest=sorted(pd_ids,key=lambda i:math.dist(C(fps['D'+str(led)],'at')[1:3],C(fps['PD'+str(i)],'at')[1:3]))[:2]
 nearest_ok.append(set(nearest)=={int(row['pd_a_id']),int(row['pd_b_id'])})
checks['mapping_matches_two_nearest_PDs_on_same_eye']=all(nearest_ok)
changes=[]
for rel,digest in json.load(open(R/'evidence/source_hashes.json')).items():
 p=R.parent/'ir_glasses_EVT_E6'/rel
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changes.append(rel)
checks['P3_source_hashes_unchanged']=not changes
report={'status':'passed' if all(checks.values()) else 'failed','scope':'Static schematic/PCB design checks only; native DRC and bench testing are separate','checks':checks,'source_changed':changes,'fitted_count':sum(not r.startswith('TP') and r!='J2' for r in parts)}
(R/'design_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));assert all(checks.values())
