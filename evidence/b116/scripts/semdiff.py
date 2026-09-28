#!/usr/bin/env python3
"""For every method whose recompiled-decompile bytecode differs from the shipped bytecode, compute the
multiset delta of *effect* instructions (invokes, field ops, allocations, casts, constants, arithmetic,
conversions, compares, throws, monitors, returns, exception-handler types). Local loads/stores, stack
shuffles and branches are ignored (they encode structure, not effects).
usage: semdiff.py  -> writes semdiff.jsonl + prints aggregated delta signatures"""
import os, sys, json, glob
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cf import CF, mkey
S = os.path.dirname(os.path.abspath(__file__)); O = '/home/cristian/niagara5-research/organized'
IGN = set(range(0x15, 0x36)) | set(range(0x36, 0x4f)) | set(range(0x57, 0x60)) | set(range(0x99, 0xaa)) | {0x00, 0xa7, 0xc8, 0xc6, 0xc7, 'tableswitch', 'lookupswitch', 'iinc', 0x84}
CONST = {0x01: 'null', 0x02: -1, 0x03: 0, 0x04: 1, 0x05: 2, 0x06: 3, 0x07: 4, 0x08: 5, 0x09: 'l0', 0x0a: 'l1', 0x0b: 'f0', 0x0c: 'f1', 0x0d: 'f2', 0x0e: 'd0', 0x0f: 'd1'}
NAMES = {0x60: 'iadd', 0x61: 'ladd', 0x62: 'fadd', 0x63: 'dadd', 0x64: 'isub', 0x65: 'lsub', 0x66: 'fsub', 0x67: 'dsub', 0x68: 'imul', 0x69: 'lmul', 0x6a: 'fmul', 0x6b: 'dmul', 0x6c: 'idiv', 0x6d: 'ldiv', 0x6e: 'fdiv', 0x6f: 'ddiv', 0x70: 'irem', 0x71: 'lrem', 0x72: 'frem', 0x73: 'drem', 0x74: 'ineg', 0x75: 'lneg', 0x76: 'fneg', 0x77: 'dneg', 0x78: 'ishl', 0x79: 'lshl', 0x7a: 'ishr', 0x7b: 'lshr', 0x7c: 'iushr', 0x7d: 'lushr', 0x7e: 'iand', 0x7f: 'land', 0x80: 'ior', 0x81: 'lor', 0x82: 'ixor', 0x83: 'lxor', 0x85: 'i2l', 0x86: 'i2f', 0x87: 'i2d', 0x88: 'l2i', 0x89: 'l2f', 0x8a: 'l2d', 0x8b: 'f2i', 0x8c: 'f2l', 0x8d: 'f2d', 0x8e: 'd2i', 0x8f: 'd2l', 0x90: 'd2f', 0x91: 'i2b', 0x92: 'i2c', 0x93: 'i2s', 0x94: 'lcmp', 0x95: 'fcmpl', 0x96: 'fcmpg', 0x97: 'dcmpl', 0x98: 'dcmpg', 0xac: 'ireturn', 0xad: 'lreturn', 0xae: 'freturn', 0xaf: 'dreturn', 0xb0: 'areturn', 0xb1: 'return', 0xb2: 'getstatic', 0xb3: 'putstatic', 0xb4: 'getfield', 0xb5: 'putfield', 0xb6: 'invokevirtual', 0xb7: 'invokespecial', 0xb8: 'invokestatic', 0xb9: 'invokeinterface', 0xba: 'invokedynamic', 0xbb: 'new', 0xbc: 'newarray', 0xbd: 'anewarray', 0xbe: 'arraylength', 0xbf: 'athrow', 0xc0: 'checkcast', 0xc1: 'instanceof', 0xc2: 'monitorenter', 0xc3: 'monitorexit', 0xc5: 'multianewarray', 0x10: 'bipush', 0x11: 'sipush', 0x12: 'ldc', 0x13: 'ldc_w', 0x14: 'ldc2_w',
         0x2e: 'iaload', 0x2f: 'laload', 0x30: 'faload', 0x31: 'daload', 0x32: 'aaload', 0x33: 'baload', 0x34: 'caload', 0x35: 'saload', 0x4f: 'iastore', 0x50: 'lastore', 0x51: 'fastore', 0x52: 'dastore', 0x53: 'aastore', 0x54: 'bastore', 0x55: 'castore', 0x56: 'sastore'}
KEEP_ARR = set(range(0x2e, 0x36)) | set(range(0x4f, 0x57))


def effects(ins):
    out = []
    for t in ins:
        op = t[0]
        if op in (0x84, 'iinc'):
            c = t[1][1] if op == 0x84 else t[2]
            out.append(('const', abs(c))); out.append(('iadd' if c > 0 else 'isub',)); continue
        if op in CONST: out.append(('const', CONST[op])); continue
        if op in (0x10, 0x11): out.append(('const', t[1])); continue
        if op in (0x12, 0x13, 0x14): out.append(('const', t[1])); continue
        if op in KEEP_ARR: out.append((NAMES[op],)); continue
        if op in IGN: continue
        if isinstance(op, int) and op in NAMES:
            out.append((NAMES[op],) + ((t[1],) if len(t) > 1 and not isinstance(t[1], tuple) else ()))
        else:
            out.append((str(op),))
    return out


def main():
    rows = []
    sig = Counter(); ncls = Counter()
    for f in sorted(glob.glob(f'{S}/cmpres/dec-*.json')):
        m = os.path.basename(f)[4:-5]
        ref = f'{O}/_bin-ext/nre/extracted' if m == 'nre' else f'{O}/{m}/extracted'
        d = json.load(open(f))
        for rel, v in d.items():
            if v.get('status') not in ('differ', 'member-delta', 'slotnorm'): continue
            a = CF(open(f'{ref}/{rel}', 'rb').read()); b = CF(open(f'{S}/recompile-dec/{m}/{rel}', 'rb').read())
            am = {mkey(x): x for x in a.methods}; bm = {mkey(x): x for x in b.methods}
            for k, e in v['methods'].items():
                if e['level'] not in ('differ',): continue
                ca = a.code(am[k]); cb = b.code(bm[k])
                if ca is None or cb is None:
                    rows.append({'mod': m, 'cls': rel, 'meth': k, 'kind': 'abstract-mismatch'}); continue
                ea = Counter(effects(ca['ins'])); eb = Counter(effects(cb['ins']))
                exa = Counter(x[3] for x in ca['exc']); exb = Counter(x[3] for x in cb['exc'])
                minus = ea - eb; plus = eb - ea
                exm = exa - exb; exp = exb - exa
                seq_equal = effects(ca['ins']) == effects(cb['ins'])
                kind = 'effects-seq-equal' if seq_equal and not exm and not exp else ('effects-multiset-equal' if not minus and not plus and not exm and not exp else 'effects-differ')
                row = {'mod': m, 'cls': rel, 'meth': k, 'kind': kind, 'minus': [list(map(str, x)) for x in minus.elements()], 'plus': [list(map(str, x)) for x in plus.elements()],
                       'exc_minus': list(exm.elements()), 'exc_plus': list(exp.elements())}
                rows.append(row); ncls[kind] += 1
                if kind == 'effects-differ':
                    s = tuple(sorted(['-' + '|'.join(x) for x in row['minus']] + ['+' + '|'.join(x) for x in row['plus']] + ['-EXC ' + x for x in row['exc_minus']] + ['+EXC ' + x for x in row['exc_plus']]))
                    sig[s] += 1
            for k in v.get('missing_in_new', []): rows.append({'mod': m, 'cls': rel, 'meth': k, 'kind': 'method-missing-in-recompile'}); ncls['method-missing'] += 1
            for k in v.get('extra_in_new', []): rows.append({'mod': m, 'cls': rel, 'meth': k, 'kind': 'method-extra-in-recompile'}); ncls['method-extra'] += 1
            for k in v.get('fields_missing', []): rows.append({'mod': m, 'cls': rel, 'meth': k, 'kind': 'field-missing'}); ncls['field-missing'] += 1
            for k in v.get('fields_extra', []): rows.append({'mod': m, 'cls': rel, 'meth': k, 'kind': 'field-extra'}); ncls['field-extra'] += 1
    with open(f'{S}/semdiff.jsonl', 'w') as o:
        for r in rows: o.write(json.dumps(r) + '\n')
    print(ncls)
    print('distinct effect-delta signatures:', len(sig))
    for s, n in sig.most_common(60): print(n, ' ; '.join(s)[:300])


if __name__ == '__main__':
    main()
