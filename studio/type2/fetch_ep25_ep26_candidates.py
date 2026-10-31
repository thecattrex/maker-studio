import os,sys,json,concurrent.futures
sys.path.insert(0,'/home/user/studio')
import discover
from util import probe
ROOT='/home/user/dl/src/ep25_26_candidates'
DM=['xbp3jtu','xbb5aru','x8e61d1','x8o67k3','x8bwurz','xaa6p8k','x8ltgj2','x9tu0gq','x92r1ps','x9zya8w','x8qaxw6','x9ml96s','x9kr59u','x9n4i08','xb9f0a6','x8ulr0w','x8lk3gv','x85zjwf','x7ufzbp','xa1uxzu','x9msgts','xbkcxk2','x9tqvnu','x77y27u','x7xankg','xa8bdo8','x8l7iki','x8ufmso','x8klzby','x9ts4w2','x9pulw4','x8aav70','x9qhpia']
YT=['Fs8chkh76gU','i-VmXYSxD3c','xNVs6rF72N4']
os.makedirs(ROOT,exist_ok=True)
def fetch(item):
 i,platform=item;d=os.path.join(ROOT,i);os.makedirs(d,exist_ok=True)
 url=(f'https://www.dailymotion.com/video/{i}' if platform=='Dailymotion' else f'https://www.youtube.com/shorts/{i}')
 try:
  r=discover.download(url,outdir=d,max_h=720)
  return {'id':i,'platform':platform,'url':url,'ok':True,'path':r['path'],'info':probe(r['path'])}
 except Exception as e:return {'id':i,'platform':platform,'url':url,'ok':False,'error':str(e)[:600]}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: out=list(ex.map(fetch,[(i,'Dailymotion') for i in DM]+[(i,'YouTube Shorts') for i in YT]))
 for r in out: print(json.dumps(r),flush=True)
 json.dump(out,open(os.path.join(ROOT,'download_manifest.json'),'w'),indent=2)
