"""Record public LCSC snapshots. Never infer zero stock or price on a failed fetch."""
from pathlib import Path
from urllib.request import urlopen,Request
from concurrent.futures import ThreadPoolExecutor
import json,re,datetime,sys
root=Path(__file__).resolve().parents[1];out=root/'evidence/stock';out.mkdir(exist_ok=True)
parts=json.loads((root/'parts.json').read_text());old=json.loads((root.parent/'ir_glasses_EVT_E6/parts.json').read_text())
codes=sorted({p.get('lcsc') for p in list(parts.values())+list(old.values()) if p.get('lcsc')})
if len(sys.argv)>1:codes=sys.argv[1:]
def go(code):
 url=f'https://www.lcsc.com/product-detail/{code}.html';result={'code':code,'source':url,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  html=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode()
  data=json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',html).group(1))['props']['pageProps']['webData']
  assert data['productCode']==code
  result.update(status='retrieved',data=data)
 except Exception as e:result.update(status='unconfirmed',error=str(e))
 (out/(code+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(code,result['status'],flush=True)
with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(go,codes))
