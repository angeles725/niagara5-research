import json, re, subprocess, sys
ex=json.load(open('classified.json'))
sel=sys.argv[1]
for k,rs in sorted(ex.items()):
    if not re.search(sel,k): continue
    for r in rs:
        if 'overload' in k: continue
        names=set()
        for x in r['minus']+r['plus']:
            if len(x)>1:
                m=re.search(r'\.([A-Za-z_$][\w$]*):',x[1])
                if m and x[0]!='const': names.add(m.group(1))
                if x[0]=='const': names.add(x[1])
        out=subprocess.run(['python3','showm.py',r['mod'],r['cls'],r['meth']],capture_output=True,text=True).stdout
        print('=====',k,'::',r['mod'],r['cls'].split('/')[-1],r['meth'][:70])
        print('   delta -',[ '|'.join(x)[-70:] for x in r['minus'] if not x[0].endswith('return')][:5])
        print('   delta +',[ '|'.join(x)[-70:] for x in r['plus'] if not x[0].endswith('return')][:5])
        lines=[l for l in out.split('\n') if l[:1] in '+-' and not l.startswith(('---','+++'))]
        keep=[l for l in lines if any(n.strip("'S:") and n.strip("'S:").replace('S:','') in l for n in names)] or lines[:14]
        for l in keep[:14]: print('     ',l[:160])
