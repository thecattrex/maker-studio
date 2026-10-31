#!/usr/bin/env python3
import os,sys,json,concurrent.futures
sys.path.insert(0,'/home/user/studio');import discover
from util import probe
ROOT='/home/user/dl/src/ep15_remake_candidates'
IDS=['xbid4im','x9y7rwe','x9ejedo','x9y52lk','x9m3tj6','xakvkte','x9wy8kc','x9si5ze']
def fetch(i):
 d=os.path.join(ROOT,i);os.makedirs(d,exist_ok=True)
 try:
  r=discover.download(f'https://www.dailymotion.com/video/{i}',outdir=d,max_h=1080)
  info=probe(r['path']);return {'id':i,'ok':True,'path':r['path'],'info':info}
 except Exception as e:return {'id':i,'ok':False,'error':str(e)}
if __name__=='__main__':
 os.makedirs(ROOT,exist_ok=True);results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for r in ex.map(fetch,IDS):results.append(r);print(json.dumps(r),flush=True)
 json.dump(results,open(os.path.join(ROOT,'manifest.json'),'w'),indent=2)
