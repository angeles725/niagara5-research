#!/usr/bin/env python3
"""Compare a reference class tree with a recompiled class tree, per method (B116 scratch).

usage: cmp.py REF_DIR NEW_DIR [--classes list.txt] [--json out.json]
REF_DIR/NEW_DIR contain pkg/Name.class trees. Level per method:
  exact     : identical normalized instructions + exception table
  slotnorm  : identical after renumbering local-variable slots by first use
  differ    : otherwise
Also records LineNumberTable equality, LVT-name equality, method-set and field-set deltas.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from cf import CF, mkey

LOADS = set(range(0x15, 0x2e)) | set(range(0x36, 0x4f)) | {0xa9}


def slotnorm(ins, nargs_hint=None):
    """Renumber local slots in order of first appearance; keep param slots too (they appear first by use)."""
    out = []; mp = {}
    def S(ix):
        if ix not in mp: mp[ix] = len(mp)
        return mp[ix]
    for t in ins:
        op = t[0]
        if op in (0x15, 0x16, 0x17, 0x18, 0x19, 0x36, 0x37, 0x38, 0x39, 0x3a, 0xa9) and isinstance(t[1], tuple):
            ix = t[1][0]; out.append((op, 'L', S(ix)))
        elif isinstance(op, int) and 0x1a <= op <= 0x2d:
            base = (op - 0x1a) // 4; ix = (op - 0x1a) % 4; out.append((0x15 + base, 'L', S(ix)))
        elif isinstance(op, int) and 0x3b <= op <= 0x4e:
            base = (op - 0x3b) // 4; ix = (op - 0x3b) % 4; out.append((0x36 + base, 'L', S(ix)))
        elif op == 0x84 or op == 'iinc':
            ix, c = t[1]; out.append(('iinc', S(ix), c))
        else:
            out.append(t)
    return out


def load(d, rel):
    p = os.path.join(d, rel)
    if not os.path.exists(p): return None
    return CF(open(p, 'rb').read())


def compare_class(ref, new):
    r = {'methods': {}, 'missing_in_new': [], 'extra_in_new': [], 'fields_missing': [], 'fields_extra': []}
    rm = {mkey(m): m for m in ref.methods}; nm = {mkey(m): m for m in new.methods}
    r['missing_in_new'] = sorted(set(rm) - set(nm)); r['extra_in_new'] = sorted(set(nm) - set(rm))
    rf = {(f['name'], f['desc']) for f in ref.fields}; nf = {(f['name'], f['desc']) for f in new.fields}
    r['fields_missing'] = sorted(map(str, rf - nf)); r['fields_extra'] = sorted(map(str, nf - rf))
    for k in sorted(set(rm) & set(nm)):
        a = ref.code(rm[k]); b = new.code(nm[k])
        if a is None and b is None: lvl = 'nocode'
        elif a is None or b is None: lvl = 'differ'
        elif a['ins'] == b['ins'] and a['exc'] == b['exc']: lvl = 'exact'
        elif slotnorm(a['ins']) == slotnorm(b['ins']) and a['exc'] == b['exc']: lvl = 'slotnorm'
        else: lvl = 'differ'
        ent = {'level': lvl}
        if a and b:
            ent['lnt_equal'] = a['lnt'] == b['lnt']
            ent['lvt_names_equal'] = [x[1] for x in a['lvt']] == [x[1] for x in b['lvt']]
            ent['ref_has_lvt'] = bool(a['lvt'])
        ent['access_equal'] = rm[k]['access'] == nm[k]['access']
        r['methods'][k] = ent
    return r


def main():
    ref, new = sys.argv[1], sys.argv[2]
    classes = None; outj = None
    if '--classes' in sys.argv: classes = [l.strip() for l in open(sys.argv[sys.argv.index('--classes') + 1]) if l.strip()]
    if '--json' in sys.argv: outj = sys.argv[sys.argv.index('--json') + 1]
    if classes is None:
        classes = []
        for root, _, fs in os.walk(new):
            for f in fs:
                if f.endswith('.class') and f != 'module-info.class' and f != 'package-info.class':
                    classes.append(os.path.relpath(os.path.join(root, f), new))
    res = {}
    for rel in sorted(classes):
        a = load(ref, rel); b = load(new, rel)
        if a is None: res[rel] = {'status': 'no-ref'}; continue
        if b is None: res[rel] = {'status': 'no-new'}; continue
        c = compare_class(a, b)
        lv = [m['level'] for m in c['methods'].values() if m['level'] != 'nocode']
        if c['missing_in_new'] or c['extra_in_new'] or c['fields_missing'] or c['fields_extra']: st = 'member-delta'
        elif all(l == 'exact' for l in lv): st = 'exact'
        elif all(l in ('exact', 'slotnorm') for l in lv): st = 'slotnorm'
        else: st = 'differ'
        c['status'] = st
        c['lnt_all_equal'] = all(m.get('lnt_equal', True) for m in c['methods'].values())
        res[rel] = c
    from collections import Counter
    print(Counter(v['status'] for v in res.values()))
    print('classes with all LineNumberTables equal:', sum(1 for v in res.values() if v.get('lnt_all_equal')), '/', sum(1 for v in res.values() if 'methods' in v))
    if outj: json.dump(res, open(outj, 'w'), indent=1)


if __name__ == '__main__':
    main()
