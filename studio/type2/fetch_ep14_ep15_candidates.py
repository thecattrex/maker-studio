#!/usr/bin/env python3
"""Fetch fresh Dailymotion leads for EP14/EP15 screening."""
import os,sys,json,concurrent.futures
sys.path.insert(0,'/home/user/studio')
import discover
from util import probe
ROOT='/home/user/dl/src/ep14_15_candidates'
IDS=['x8b8vre','x33gk8c','x2ebg6l','xag70ye','xa1goko','xamvx3y','x944dpo','xa0lnsm','x97c2ky','xbm4fy2','x9sg4wm','x9t48pi']
def fetch(i):
 d=os.path.join(ROOT,i);os.makedirs(d,exist_ok=True)
 try:
  r=discover.download(f'https://www.dailymotion.com/video/{i}',outdir=d,max_h=1080)
  p=r['path'];return {'id':i,'path':p,'ok':True,'info':probe(p)}
 except Exception as e:return {'id':i,'ok':False,'error':str(e)}
if __name__=='__main__':
 os.makedirs(ROOT,exist_ok=True);results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for r in ex.map(fetch,IDS):results.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
 json.dump(results,open(os.path.join(ROOT,'manifest.json'),'w'),indent=2)
