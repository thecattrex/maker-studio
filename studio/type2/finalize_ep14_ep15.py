#!/usr/bin/env python3
"""Finalize Type-2 renders to the series AAC/loudness delivery spec.
Video is stream-copied; two-pass EBU R128 normalization is targeted at
-13.5 LUFS / -4.7 dBTP to leave AAC true-peak margin, with AAC 192 kb/s at 48 kHz. Source audio was already muted in edit.
"""
import json,os,re,subprocess
FF='/tmp/vidtools/ffmpeg';OUT='/home/user/studio/type2'
INPUTS={14:'/home/user/studio/out/ep14-type2-final-2026-10-28_1028-0548.mp4',15:'/home/user/studio/out/ep15-type2-final-2026-10-28_1028-0543.mp4'}

def cmd(args):
 p=subprocess.run(args,capture_output=True,text=True)
 if p.returncode:raise RuntimeError('FAILED: '+' '.join(args)+'\n'+(p.stderr or '')[-4000:])
 return p.stderr

def final(ep,src):
 out=f'{OUT}/EP{ep}_Type2_Final_2026-10-28.mp4';tmp=out+'.part.mp4'
 filt='loudnorm=I=-13.5:TP=-4.7:LRA=11:print_format=json'
 log=cmd([FF,'-hide_banner','-nostats','-i',src,'-vn','-af',filt,'-f','null','-'])
 matches=re.findall(r'\{\s*"input_i".*?\}',log,re.S)
 if not matches:raise RuntimeError('Could not parse loudnorm measurement:\n'+log[-2000:])
 m=json.loads(matches[-1]);
 second=(f"loudnorm=I=-13.5:TP=-4.7:LRA=11:measured_I={m['input_i']}:"
         f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
         f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
         "linear=true:print_format=summary")
 cmd([FF,'-hide_banner','-v','error','-y','-i',src,'-map','0:v:0','-map','0:a:0','-c:v','copy','-af',second,'-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart','-shortest',tmp])
 # Decode both streams before publishing the stable filename.
 cmd([FF,'-hide_banner','-v','error','-i',tmp,'-map','0:v:0','-map','0:a:0','-f','null','-'])
 os.replace(tmp,out)
 print(f'EP{ep}: {out}\ninput measurement: {json.dumps(m)}')
 print(cmd([FF,'-hide_banner','-i',out,'-vn','-af','ebur128=peak=true','-f','null','-'])[-1500:])
if __name__=='__main__':
 for ep,src in INPUTS.items():final(ep,src)
