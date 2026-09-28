#!/usr/bin/env python3
"""Build a compile-time-constant table (static final fields with ConstantValue) plus a type
hierarchy index from every class on the B116 recompile classpath + JDK modules.
Output: consts.json {classname: {"super":..., "ifaces":[...], "consts": {NAME: [kind, value]}}}"""
import os, sys, json, zipfile, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import CF

S = os.path.dirname(os.path.abspath(__file__))
out = {}

def add(data):
    try: c = CF(data)
    except Exception: return
    ent = {'super': c.cls(c.sup) if c.sup else None, 'ifaces': c.ifaces, 'consts': {}}
    for f in c.fields:
        if (f['access'] & 0x18) == 0x18 and 'ConstantValue' in f['attrs']:
            i = struct.unpack('>H', f['attrs']['ConstantValue'])[0]; e = c.cp[i]
            if e[0] == 'string': v = ['string', c.utf(e[1])]
            else:
                kind = {'I': 'int', 'J': 'long', 'F': 'float', 'D': 'double', 'Z': 'boolean', 'C': 'char', 'B': 'byte', 'S': 'short'}.get(f['desc'], e[0])
                val = e[1]
                if isinstance(val, float) and (val != val or val in (float('inf'), float('-inf'))): val = repr(val)
                v = [kind, val]
            ent['consts'][f['name']] = v
    out[c.name] = ent

for p in open(f'{S}/cp3.txt').read().strip().split(':'):
    if p.endswith('.jar') and os.path.exists(p):
        try: z = zipfile.ZipFile(p)
        except Exception: continue
        for n in z.namelist():
            if n.endswith('.class') and not n.startswith('META-INF'): add(z.read(n))
    elif os.path.isdir(p):
        for root, _, fs in os.walk(p):
            for f in fs:
                if f.endswith('.class'): add(open(os.path.join(root, f), 'rb').read())
for root, _, fs in os.walk(f'{S}/jdk'):
    for f in fs:
        if f.endswith('.class'): add(open(os.path.join(root, f), 'rb').read())
json.dump(out, open(f'{S}/consts.json', 'w'))
print(len(out), 'classes', sum(len(v['consts']) for v in out.values()), 'constants')
