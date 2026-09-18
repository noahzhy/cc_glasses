from pathlib import Path
import sexpdata as s,json,uuid,sys
root=Path(__file__).resolve().parents[1];path=root/(root.name+'.kicad_pcb')
b=s.load(path.open());d=json.load(open(sys.argv[1]));K=lambda e:str(e[0]) if isinstance(e,list) and e else '';C=lambda e,k:next((x for x in e if K(x)==k),None)
rm=set(d.get('remove_ids',[]));b[:]=[e for e in b if not(K(e) in ['segment','via'] and C(e,'uuid')[1] in rm)]
for e in d.get('items',[]):
 n=json.dumps(e['net']);a=e['start'];z=e['end'];u=str(uuid.uuid4())
 if e['type']=='via':t=f'(via (at {a[0]} {a[1]}) (size {e["width"]}) (drill {e.get("drill",.15)}) (layers "F.Cu" "B.Cu") (tenting (front yes) (back yes)) (net {n}) (uuid "{u}"))'
 else:
  layer=['F.Cu','In1.Cu','In2.Cu','B.Cu'][e['layers'][0]];t=f'(segment (start {a[0]} {a[1]}) (end {z[0]} {z[1]}) (width {e["width"]}) (layer "{layer}") (net {n}) (uuid "{u}"))'
 b.append(s.loads(t))
path.write_text(s.dumps(b)+'\n');print('Removed',len(rm),'added',len(d.get('items',[])))
