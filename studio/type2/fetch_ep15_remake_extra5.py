#!/usr/bin/env python3
import os,sys,json
sys.path.insert(0,'/home/user/studio');import discover
from util import probe
ROOT='/home/user/dl/src/ep15_remake_candidates';i='x9o5ajg';d=os.path.join(ROOT,i);os.makedirs(d,exist_ok=True)
r=discover.download(f'https://www.dailymotion.com/video/{i}',outdir=d,max_h=1080);res={'id':i,'path':r['path'],'info':probe(r['path'])};print(json.dumps(res));json.dump(res,open(os.path.join(ROOT,'manifest_extra5.json'),'w'),indent=2)
