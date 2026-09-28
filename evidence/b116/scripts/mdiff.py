#!/usr/bin/env python3
"""mdiff.py REF.class NEW.class [method-key-substring] : unified diff of normalized instructions per differing method"""
import sys, os, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import CF, mkey
from cmp import slotnorm
OPN={}
try:
    import dis
except: pass
a=CF(open(sys.argv[1],'rb').read()); b=CF(open(sys.argv[2],'rb').read())
flt=sys.argv[3] if len(sys.argv)>3 else ''
bm={mkey(m):m for m in b.methods}
def fmt(ins):
    return ['%s %s'%(t[0] if not isinstance(t[0],int) else hex(t[0]), ' '.join(map(str,t[1:]))) for t in ins]
for m in a.methods:
    k=mkey(m)
    if flt not in k or k not in bm: continue
    ca=a.code(m); cb=b.code(bm[k])
    if not ca or not cb: continue
    if slotnorm(ca['ins'])==slotnorm(cb['ins']) and ca['exc']==cb['exc']: continue
    print('#####',k)
    for l in difflib.unified_diff(fmt(slotnorm(ca['ins'])),fmt(slotnorm(cb['ins'])),'ref','new',lineterm='',n=2): print(l)
    if ca['exc']!=cb['exc']: print('EXC ref',ca['exc'],'\nEXC new',cb['exc'])
