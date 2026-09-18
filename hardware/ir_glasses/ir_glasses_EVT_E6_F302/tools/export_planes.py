import pcbnew as p,json,sys
b=p.LoadBoard(sys.argv[1]);out=[]
xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 poly=z.GetFilledPolysList(z.GetLayer());rings=[]
 for i in range(poly.OutlineCount()):
  ch=poly.Outline(i);a=[xy(ch.CPoint(k)) for k in range(ch.PointCount())];holes=[]
  for j in range(poly.HoleCount(i)):
   ch=poly.Hole(i,j);holes.append([xy(ch.CPoint(k)) for k in range(ch.PointCount())])
  rings.append({'outer':a,'holes':holes})
 out.append({'net':z.GetNetname(),'layer':int(z.GetLayer()),'polys':rings})
json.dump(out,open(sys.argv[2],'w'));print([(z['net'],len(z['polys'])) for z in out])
