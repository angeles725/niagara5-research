#!/usr/bin/env python3
"""Rule-classify effects-differ rows from semdiff.jsonl into bytecode-delta categories."""
import json, re, sys
from collections import Counter, defaultdict
rows=[json.loads(l) for l in open(sys.argv[1] if len(sys.argv)>1 else 'semdiff.jsonl')]
RET={'ireturn','lreturn','freturn','dreturn','areturn','return'}
def cat(r):
    k=r['kind']
    if k!='effects-differ': return k
    mi=[tuple(x) for x in r['minus']]; pl=[tuple(x) for x in r['plus']]
    em, ep = r['exc_minus'], r['exc_plus']
    mi2=[x for x in mi if x[0] not in RET]; pl2=[x for x in pl if x[0] not in RET]
    # boolean-return shape: const 0/1 + returns
    def strip_bool(l): return [x for x in l if not (x[0]=='const' and x[1] in ('0','1'))]
    rest_m, rest_p = mi2, pl2
    tags=[]
    if len(mi2)!=len(mi) or len(pl2)!=len(pl): tags.append('return-merge')
    if (strip_bool(rest_m)!=rest_m or strip_bool(rest_p)!=rest_p) and 'return-merge' in tags:
        rest_m, rest_p = strip_bool(rest_m), strip_bool(rest_p); tags.append('bool-shape')
    rnn=lambda x: x[0]=='invokestatic' and 'Objects.requireNonNull' in x[1]
    if any(map(rnn,rest_m+rest_p)):
        tags.append('requireNonNull'); rest_m=[x for x in rest_m if not rnn(x)]; rest_p=[x for x in rest_p if not rnn(x)]
    ind=lambda x: x[0]=='invokedynamic' and 'makeConcatWithConstants' in x[1] or (x[0] in('invokevirtual','invokespecial','new') and 'StringBuilder' in (x[1] if len(x)>1 else ''))
    if any(map(ind,rest_m+rest_p)):
        tags.append('string-concat-shape'); rest_m=[x for x in rest_m if not ind(x)]; rest_p=[x for x in rest_p if not ind(x)]
    cc=lambda x: x[0]=='checkcast'
    if any(map(cc,rest_m+rest_p)):
        tags.append('checkcast'); rest_m=[x for x in rest_m if not cc(x)]; rest_p=[x for x in rest_p if not cc(x)]
    mon=lambda x: x[0] in ('monitorexit','athrow')
    if (em or ep):
        tags.append('exception-table'+('-sameset' if set(em)==set(ep) or not set(em)^set(ep)-{'any'} else '-types'))
    if any(map(mon,rest_m+rest_p)) and (em or ep):
        tags.append('finally/sync-copy'); rest_m=[x for x in rest_m if not mon(x)]; rest_p=[x for x in rest_p if not mon(x)]
    if rest_m or rest_p:
        # overload rebinding: same owner.name, different descriptor
        def nm(x):
            if x[0].startswith('invoke') and len(x)>1:
                m=re.match(r'i?mref:([^.]+)\.([^:]+):',x[1]); return m.groups() if m else None
        mn={nm(x) for x in rest_m if nm(x)}; pn={nm(x) for x in rest_p if nm(x)}
        if mn & pn: tags.append('SEM?overload-or-receiver-change')
        box=lambda x: len(x)>1 and re.search(r'java/lang/(Integer|Long|Double|Float|Boolean|Character|Short|Byte)\.(valueOf|intValue|longValue|doubleValue|floatValue|booleanValue|charValue|shortValue|byteValue):',x[1] or '')
        if any(map(box,rest_m+rest_p)): tags.append('SEM?boxing')
        if any(x[0]=='const' for x in rest_m+rest_p): tags.append('SEM?constant')
        if any(x[0] in ('iadd','isub','imul','idiv','ladd','lsub','lmul','ldiv','dadd','dmul','ddiv','fmul','fdiv','i2d','i2f','f2d','d2i','i2l','l2i','i2c','i2b','i2s','irem','ishl','ishr','iushr','iand','ior','ixor','land','lor','lcmp','dcmpl','dcmpg','fcmpl','fcmpg') for x in rest_m+rest_p): tags.append('SEM?arith/conv')
        if any(x[0] in ('getfield','putfield','getstatic','putstatic') for x in rest_m+rest_p): tags.append('SEM?field')
        if any(x[0].startswith('invoke') for x in rest_m+rest_p) and 'SEM?overload-or-receiver-change' not in tags: tags.append('SEM?invoke')
        if any(x[0] in ('new','anewarray','newarray','instanceof','aaload','iaload','aastore','iastore','baload','bastore','caload','castore','arraylength','athrow','monitorenter','monitorexit') for x in rest_m+rest_p): tags.append('SEM?other')
        if not [t for t in tags if t.startswith('SEM')]: tags.append('SEM?unknown')
    return '+'.join(tags) if tags else 'effects-differ-empty'
c=Counter(); ex=defaultdict(list)
for r in rows:
    k=cat(r); r['cat']=k; c[k]+=1; ex[k].append(r)
for k,n in c.most_common(): print(n,k)
json.dump(ex,open('classified.json','w'))
