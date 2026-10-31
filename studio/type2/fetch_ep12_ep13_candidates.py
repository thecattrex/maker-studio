#!/usr/bin/env python3
"""Download fresh candidate single-incident fail clips for EP12/EP13 screening."""
import os, sys, json, concurrent.futures
sys.path.insert(0, '/home/user/studio')
import discover
from util import probe

ROOT='/home/user/dl/src/ep12_13_candidates'
IDS=['x9s26xm','xa16vus','x8ihsjz','xa64o2o','xb4fq36','x9rxxiq','x8ctzxy','x9wy8kc','xa0shno','x8fx5gw','xb8cze6','x8mdbfj','x9y52lk','x9ejedo','xbfbsli','x99bals','x9p4g1k','x9yd16y']

def fetch(i):
    d=os.path.join(ROOT,i)
    os.makedirs(d,exist_ok=True)
    url=f'https://www.dailymotion.com/video/{i}'
    try:
        r=discover.download(url,outdir=d,max_h=1080)
        p=r['path'];info=probe(p)
        return {'id':i,'url':url,'path':p,'ok':True,'info':info}
    except Exception as e:
        return {'id':i,'url':url,'ok':False,'error':str(e)}

if __name__=='__main__':
    os.makedirs(ROOT,exist_ok=True)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(fetch,IDS):
            results.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
    json.dump(results,open(os.path.join(ROOT,'manifest.json'),'w'),indent=2)
