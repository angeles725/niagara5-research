#!/usr/bin/env python3
"""showm.py mod cls.class methkey : print docSource vs decompiled text of the method (brace-matched)"""
import sys, re, os, difflib
O='/home/cristian/niagara5-research/organized'
mod, cls, mk = sys.argv[1:4]
top = cls.split('$')[0].replace('.class','') + '.java'
name = mk.split('(')[0]
if name == '<init>': name = cls.split('/')[-1].split('$')[-1].replace('.class','')
if name == '<clinit>': name = 'static'
base = f'{O}/_bin-ext/nre' if mod=='nre' else f'{O}/{mod}'
dec = f'{base}/vineflower/{top}'
if not os.path.exists(dec): dec = f'{base}/fallback/{top}'
def grab(path):
    src = open(path, encoding='utf-8', errors='replace').read().split('\n')
    outs=[]
    for i,l in enumerate(src):
        if re.search(r'\b'+re.escape(name)+r'\s*\(', l) and not l.strip().endswith(';') and not re.search(r'[=.]\s*'+re.escape(name)+r'\s*\(', l) and not l.strip().startswith(('//','*','return','if')):
            depth=0; j=i; buf=[]; started=False
            while j < len(src):
                buf.append(src[j]); depth += src[j].count('{') - src[j].count('}')
                if '{' in src[j]: started=True
                if started and depth<=0: break
                if not started and src[j].strip().endswith(';'): break
                j+=1
            outs.append([x.strip() for x in buf if x.strip() and not x.strip().startswith(('//','*','/*'))])
    return outs
a=grab(f'{O}/docSource/{mod}/{top}'); b=grab(dec)
print('#', mod, cls, mk, '| candidates', len(a), len(b))
for x,y in zip(a,b):
    for l in difflib.unified_diff(x,y,'docSource','decompiled',lineterm='',n=1): print(l)
    print('---')
