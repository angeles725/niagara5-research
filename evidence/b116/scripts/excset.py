import json,sys,os
sys.path.insert(0,'.')
from cf import CF,mkey
O='/home/cristian/niagara5-research/organized'
ex=json.load(open('classified.json'))
out=[]
for k,rs in ex.items():
    if 'exception-table' not in k: continue
    for r in rs:
        m=r['mod']; ref=f'{O}/_bin-ext/nre/extracted' if m=='nre' else f'{O}/{m}/extracted'
        a=CF(open(f"{ref}/{r['cls']}",'rb').read()); b=CF(open(f"recompile-dec/{m}/{r['cls']}",'rb').read())
        am={mkey(x):x for x in a.methods}; bm={mkey(x):x for x in b.methods}
        ta={e[3] for e in a.code(am[r['meth']])['exc']}; tb={e[3] for e in b.code(bm[r['meth']])['exc']}
        print('SAME' if ta==tb else 'DIFF', m, r['cls'].split('/')[-1], r['meth'][:40], sorted(ta-tb), sorted(tb-ta))
