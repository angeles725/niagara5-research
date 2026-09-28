#!/usr/bin/env python3
"""Bytecode census over every shipped class under organized/*/extracted and organized/_bin-ext/*/extracted."""
import os, sys, glob, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import CF
from collections import Counter, defaultdict
O='/home/cristian/niagara5-research/organized'
dirs=[d for d in glob.glob(f'{O}/*/extracted')+glob.glob(f'{O}/_bin-ext/*/extracted') if '/docSource/' not in d]
c=Counter(); ex=defaultdict(list)
for d in dirs:
    mod=d.split('/')[-2]
    for root,_,fs in os.walk(d):
        for f in fs:
            if not f.endswith('.class'): continue
            p=os.path.join(root,f)
            try: k=CF(open(p,'rb').read())
            except Exception as e: c['parse-error']+=1; ex['parse-error'].append(p); continue
            c['classes']+=1
            c[f'major{k.major}']+=1
            if k.minor==65535: c['preview-minor-65535']+=1; ex['preview'].append(p)
            tags=[e[0] for e in k.cp if e]
            if 'dyn' in tags: c['classes-with-CONSTANT_Dynamic']+=1; ex['condy'].append(p)
            if any(m['name'].startswith('$$$reportNull$$$') for m in k.methods): c['idea-notnull-instrumented']+=1; ex['notnull'].append(p)
            if any(e[0]=='utf8' and 'Argument for @NotNull parameter' in e[1] for e in k.cp if e): c['idea-notnull-string']+=1
            has_lvt=False; code_methods=0
            for m in k.methods:
                cd=k.code(m)
                if cd is None: continue
                code_methods+=1
                if 'LocalVariableTable' in cd['subattrs']: has_lvt=True
                for t in cd['ins']:
                    if t[0]==0xba:
                        s=t[1]
                        if 'SwitchBootstraps.typeSwitch' in s: c['indy-typeSwitch']+=1; ex['typeSwitch'].append(p+' '+m['name'])
                        if 'SwitchBootstraps.enumSwitch' in s: c['indy-enumSwitch']+=1
                        if 'ObjectMethods.bootstrap' in s: c['indy-ObjectMethods(record)']+=1
                if m['name']=='<init>':
                    # flexible constructor bodies: effects before the first invokespecial <init> on 'this'
                    ins=cd['ins']; depth_new=0; pre=[]
                    for t in ins:
                        if t[0]==0xbb: depth_new+=1
                        if t[0]==0xb7 and isinstance(t[1],str) and '.<init>:' in t[1]:
                            if depth_new>0: depth_new-=1; pre.append(t); continue
                            break
                        pre.append(t)
                    pf=[t for t in pre if t[0]==0xb5 and not t[1].split('.')[-1].startswith(('this$','val$'))]
                    th=[t for t in pre if t[0]==0xbf]
                    st=[t for t in pre if isinstance(t[0],int) and (0x36<=t[0]<=0x4e)]
                    if pf: c['ctor-putfield-before-super(JEP513)']+=1; ex['jep513-putfield'].append(p)
                    if th: c['ctor-athrow-before-super']+=1; ex['jep513-athrow'].append(p)
                    if st: c['ctor-localstore-before-super']+=1; ex['jep513-store'].append(p)
            if code_methods: c['classes-with-code']+=1
            if code_methods and has_lvt: c['classes-with-LVT']+=1
            if 'Record' in k.attrs: c['records']+=1
            if 'PermittedSubclasses' in k.attrs: c['sealed']+=1
            if 'NestHost' in k.attrs or 'NestMembers' in k.attrs: c['nest-attrs']+=1
            if 'SourceDebugExtension' in k.attrs: c['SourceDebugExtension(kotlin/jsp?)']+=1
            if any(e[0]=='utf8' and e[1].startswith('kotlin/') for e in k.cp if e): c['kotlin-refs']+=1
json.dump({k:v[:40] for k,v in ex.items()},open('census-examples.json','w'),indent=1)
for k,v in sorted(c.items()): print(k,v)
