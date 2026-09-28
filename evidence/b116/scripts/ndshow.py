import sys, json, difflib
sys.path.insert(0,'.')
import normdiff as N
mod, rel, key = sys.argv[1:4]
O=N.O; base=f'{O}/_bin-ext/nre' if mod=='nre' else f'{O}/{mod}'
import os
dec=f'{base}/vineflower/{rel}'
if not os.path.exists(dec): dec=f'{base}/fallback/{rel}'
ta,sa,ia=N.strip_header(N.lex(open(f'{O}/docSource/{mod}/{rel}',errors='replace').read())); tb,sb,ib=N.strip_header(N.lex(open(dec,errors='replace').read()))
own=N.class_names(ta)|N.class_names(tb)
a=N.split_members(ta)[key]; b=N.split_members(tb)[key]
vis=N.hierarchy_consts([rel[:-5]])
for f in [N.drop_annotations, lambda x:N.qualify_norm(x,own), N.generics_final_norm, N.literal_norm]:
    a,b=f(a),f(b)
a=N.const_subst(a,vis,sa,ia); b=N.const_subst(b,vis,sb,ib)
a,b=N.local_rename(a),N.local_rename(b); a,b=N.stmt_norm(a),N.stmt_norm(b)
for l in difflib.unified_diff([t[1] for t in a],[t[1] for t in b],lineterm='',n=3): print(l)
