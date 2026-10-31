#!/usr/bin/env python3
import os,sys,json,concurrent.futures
sys.path.insert(0,'/home/user/studio');import discover
from util import probe
ROOT='/home/user/dl/src/ep15_remake_candidates';IDS=['xb1a01a','xayplh6','xbglpb6','xa3ft5g','xa123a8']
def fetch(i):
 d=os.path.join(ROOT,i);os.makedirs(d,exist_ok=True)
 try:
  r=discover.download(f'https://www.dailymotion.com/video/{i}',outdir=d,max_h=1080);return {'id':i,'ok':True,'path':r['path'],'info':probe(r['path'])}
 except Exception as e:return {'id':i,'ok':False,'error':str(e)}
if __name__=='__main__':
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for r in ex.map(fetch,IDS):results.append(r);print(json.dumps(r),flush=True)
 json.dump(results,open(os.path.join(ROOT,'manifest_extra2.json'),'w'),indent=2)
