import os,sys,json,concurrent.futures
sys.path.insert(0,'/home/user/studio')
import discover
from util import probe
ROOT='/home/user/dl/src/ep16_17_candidates'
IDS=['xbpdexu','xbpdewm','xaw781e','xbcz1xe','xbn1i3y','xa6zmti','xa39mlm','xapqg7m','xaez7p2','xbl10cm','xbqntsi','xbrcece']
os.makedirs(ROOT,exist_ok=True)
def fetch(i):
 d=os.path.join(ROOT,i);os.makedirs(d,exist_ok=True)
 try:
  r=discover.download(f'https://www.dailymotion.com/video/{i}',outdir=d,max_h=720)
  return {'id':i,'ok':True,'path':r['path'],'info':probe(r['path'])}
 except Exception as e:return {'id':i,'ok':False,'error':str(e)}
if __name__=='__main__':
 out=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for r in ex.map(fetch,IDS): out.append(r);print(json.dumps(r),flush=True)
 json.dump(out,open(os.path.join(ROOT,'manifest.json'),'w'),indent=2)
