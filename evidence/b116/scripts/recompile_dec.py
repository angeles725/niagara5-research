#!/usr/bin/env python3
"""Recompile the corpus decompile (vineflower, or CFR fallback) of docSource-covered classes, iteratively
dropping files that fail, then keep the class files. usage: recompile_dec.py <module>"""
import os, sys, subprocess, re, shutil
S=os.path.dirname(os.path.abspath(__file__)); O='/home/cristian/niagara5-research/organized'
J='/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac'
m=sys.argv[1]
ds=f'{O}/docSource/{m}'
base=f'{O}/_bin-ext/nre' if m=='nre' else f'{O}/{m}'
files=[]
for root,_,fs in os.walk(ds):
    for f in fs:
        if not f.endswith('.java') or f=='package-info.java': continue
        rel=os.path.relpath(os.path.join(root,f),ds)
        for sub in ('vineflower','fallback'):
            p=f'{base}/{sub}/{rel}'
            if os.path.exists(p): files.append((rel,sub,p)); break
out=f'{S}/recompile-dec/{m}'; shutil.rmtree(out,ignore_errors=True); os.makedirs(out)
cp=open(f'{S}/cp3.txt').read().strip()
alive={p:(rel,sub) for rel,sub,p in files}; dropped={}
for it in range(12):
    lst=f'{out}.files'; open(lst,'w').write('\n'.join(alive)+'\n')
    r=subprocess.run([J,'--release','25','-g','-proc:none','-nowarn','-encoding','UTF-8','-Xmaxerrs','100000','-cp',cp,'-d',out,'@'+lst],capture_output=True,text=True)
    errs=set(re.findall(r'^(/[^:]+\.java):\d+: error:',r.stderr,re.M))
    if r.returncode==0: break
    if not errs: dropped['?']=r.stderr[-500:]; break
    for e in errs:
        if e in alive: dropped[e]=alive.pop(e)
    shutil.rmtree(out); os.makedirs(out)
src={sub for _,sub,_ in files}
open(f'{out}.dropped','w').write('\n'.join(f'{v[1]}\t{v[0]}' if isinstance(v,tuple) else str(v) for k,v in dropped.items())+'\n')
print(m,'files',len(files),'decompiler',sorted(src),'compiled',len(alive),'dropped',len(dropped),'iters',it+1)
