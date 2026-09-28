import json
from collections import Counter, defaultdict
F='normdiff.jsonl'
rows=[json.loads(l) for l in open(F)]
tot=Counter(); gen=defaultdict(Counter); files=Counter(); mods=set(); ftool=Counter()
order=['S0-lexical','S1-annotations','S2-qualification','S3-modifiers/generics/parens','S4-literal-form','S5-constant-inlining/folding','S6-local-names','S7-braces/increments','residual-structural']
for r in rows:
    mods.add(r['mod'])
    st=[v['stage'] for v in r['pairs'].values()]
    worst=max((order.index(s) for s in st), default=0)
    unal=len(r['only_orig'])+len(r['only_dec'])
    k='identical-after-S0' if worst==0 and not unal else ('cosmetic-only(<=S7)' if worst<8 and not unal else 'has-residual-or-unaligned')
    files[k]+=1; ftool[(r['tool'],k)]+=1
    for v in r['pairs'].values():
        tot[v['stage']]+=1; gen['generated' if v['generated'] else 'hand'][v['stage']]+=1
print('files',len(rows),'modules',len(mods)); print(files); print(ftool)
n=sum(tot.values()); print('members aligned',n)
for s in order: print(f"{s:32s} {tot[s]:6d} {100*tot[s]/n:5.1f}%  gen {gen['generated'][s]:6d} hand {gen['hand'][s]:6d}")
print('generated members',sum(gen['generated'].values()),'hand',sum(gen['hand'].values()))
print('unaligned orig',sum(len(r['only_orig']) for r in rows),'dec',sum(len(r['only_dec']) for r in rows))
print('files with $VF marker', sum(r['vf_marker'] for r in rows))
