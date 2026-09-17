#!/usr/bin/env python3
"""Run using KiCad bundled Python (pcbnew); initial E6 board generation. OVERWRITES final routing; use a copy."""
from pathlib import Path
import pcbnew as p,json,xml.etree.ElementTree as ET,uuid,math
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT.parent/'ir_glasses_EVT_E4';NAME='ir_glasses_EVT_E6'
parts=json.load(open(ROOT/'parts.json'));board=p.LoadBoard(str(SRC/'ir_glasses_EVT_E4.kicad_pcb'))
netlist=ET.parse(ROOT/'netlist.xml').getroot();comp={e.attrib['ref']:e for e in netlist.findall('components/comp')}
padnets={}
for n in netlist.findall('nets/net'):
 name=n.attrib['name']
 for v in n.findall('node'):padnets[v.attrib['ref'],v.attrib['pin']]=name
allnets={n for n in padnets.values()}
for n in allnets:
 if not board.FindNet(n):board.Add(p.NETINFO_ITEM(board,n))
# Make changed positions explicit and reproducible. Fixed optical devices remain untouched.
positions={}
# To be adjusted against rendered layout and DRC; tracked here as the placement source.
if (ROOT/'placement.json').exists():positions=json.load(open(ROOT/'placement.json'))
changed_nets=set();changed_refs=[]
for ref,part in parts.items():
 f=board.FindFootprintByReference(ref)
 repl=ref in ('U7','U8') or f is None
 if f:
  old={pad.GetNumber():pad.GetNetname() for pad in f.Pads()}
  for num,n in old.items():
   if padnets.get((ref,num),'')!=n:changed_nets.add(n);changed_nets.add(padnets.get((ref,num),''))
 if repl:
  if f:
   changed_nets.update(pad.GetNetname() for pad in f.Pads());board.Remove(f)
  lib,nm=part['footprint'].split(':');f=p.FootprintLoad(str(ROOT/'libraries'/f'{lib}.pretty'),nm)
  if f is None:raise RuntimeError('Missing footprint '+part['footprint'])
  board.Add(f);f.SetReference(ref);f.SetFPIDAsString(part['footprint'])
  changed_refs.append(ref)
 else:
  if ref in ('R11','R12','C29','C30') or ref in positions:
   changed_nets.update(pad.GetNetname() for pad in f.Pads());changed_refs.append(ref)
 if ref.startswith('TP') and f.GetLayer()==p.F_Cu:
  f.Flip(f.GetPosition(),False);changed_nets.update(pad.GetNetname() for pad in f.Pads());changed_refs.append(ref)
 xy=positions.get(ref,part['pcb_xy']);angle=xy[2] if len(xy)>2 else part['angle']
 f.SetPosition(p.VECTOR2I(round(xy[0]*1e6),round(xy[1]*1e6)));f.SetOrientationDegrees(angle)
 f.SetValue(part['value']);f.Value().SetVisible(False);f.Reference().SetVisible(False)
 # The actual schematic path is required for parity checks and future updates.
 c=comp[ref]
 for fld in c.findall('fields/field'):
  if fld.attrib['name'] not in ('Footprint','Datasheet','Description'):f.SetField(fld.attrib['name'],fld.text or '');f.GetField(fld.attrib['name']).SetVisible(False)
 path=c.find('sheetpath').attrib['tstamps']+c.find('tstamps').text.strip().split()[0]
 f.SetPath(p.KIID_PATH(path))
 for pad in f.Pads():
  name=padnets.get((ref,pad.GetNumber()),'')
  if name:pad.SetNet(board.FindNet(name))
  else:pad.SetNetCode(0)
 if repl:changed_nets.update(pad.GetNetname() for pad in f.Pads())
# Remove changed signal routes and obstructing routes. Power/GND are restored from planes.
changed_nets.discard('GND');changed_nets.discard('3V3');changed_nets.discard('3V3_A');changed_nets.discard('')
changed_nets={n for n in changed_nets if not n.startswith('PD_IN')}
rects=[]
for ref in changed_refs:
 f=board.FindFootprintByReference(ref);box=f.GetBoundingBox(False,False);box.Inflate(p.FromMM(.2));rects.append(box)
removed=0
for t in list(board.GetTracks()):
 if t.GetNetname() in changed_nets or any(r.Intersects(t.GetBoundingBox()) for r in rects):board.Remove(t);removed+=1


board.BuildConnectivity();board.SanitizeNetcodes()
p.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),board)
fn=ROOT/(NAME+'.kicad_pcb');fn.write_text(fn.read_text().replace('EVT E4','EVT E6').replace('EVT_E4','EVT_E6'))
print('Board footprints',len(board.GetFootprints()),'removed track/via items',removed,'changed nets',len(changed_nets))
