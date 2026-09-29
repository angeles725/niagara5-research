#!/usr/bin/env python3
"""B124 step 6: combine census/equiv/hbs/segments/controls JSON into the committed TSV tables and summary.
Usage: bundle_tally.py CENSUS EQUIV HBS SEGMENTS OUTDIR"""
import json, sys, os, collections
census, equiv, hbs, seg, out = sys.argv[1:6]
C = json.load(open(census))['bundles']; E = json.load(open(equiv)); H = json.load(open(hbs)); S = json.load(open(seg))
hbs_by = {(h['bundle'], h['id']): h for h in H}
PROVEN_JS = {'SEMANTIC-MATCH', 'IDENTICAL-AFTER-MINIFY'}
SKEL = 'SKELETON-MATCH'

def cls(r):
    if r['cls'] in ('TEMPLATE-PATH-ONLY', 'NO-READABLE-SOURCE-TEMPLATE'):
        h = hbs_by.get((r['bundle'], r['id']))
        return h['cls'] if h else r['cls']
    if r['cls'] == 'SCRIPT-NO-DEFINE':
        return 'STUB-OR-VENDOR-WRAPPER'
    return r['cls']

rows = []; per = collections.defaultdict(lambda: collections.Counter()); byt = collections.defaultdict(lambda: collections.Counter())
for r in E:
    c = cls(r); r['final'] = c
    per[r['bundle']][c] += 1; byt[r['bundle']][c] += r['bytes']
    rows.append((r['bundle'].split('/')[0], r['id'], r['bytes'], c, r.get('readable') or '', r.get('tier') or '', 'alias' if r.get('alias') else '', r.get('depsEqual', '')))
with open(os.path.join(out, 'modules.tsv'), 'w') as f:
    f.write('module\tid\tbytes\tclass\treadable\ttier\talias\tdeps_equal\n')
    for r in rows: f.write('\t'.join(str(x) for x in r) + '\n')

pre = collections.defaultdict(lambda: [0, 0, 0, 0]); oth = collections.defaultdict(lambda: [0, 0, 0, 0])
for p in S['prelude']:
    k = pre[p['bundle']]; k[0 if p['proof'] else 2] += p['bytes']; k[1 if p['proof'] else 3] += 1
for p in S['other']:
    ok = bool(p.get('equal')); k = oth[p['bundle']]; k[0 if ok else 2] += p['bytes']; k[1 if ok else 3] += 1

with open(os.path.join(out, 'hbs.tsv'), 'w') as f:
    f.write('module\tid\tbytes\tclass\treadable\n')
    for h in H: f.write('\t'.join(str(x) for x in [h['bundle'].split('/')[0], h['id'], h['bytes'], h['cls'], h.get('readable', '')]) + '\n')
with open(os.path.join(out, 'segments.tsv'), 'w') as f:
    f.write('kind\tmodule\tname_or_head\tbytes\tproof\tdetail\n')
    for p in S['prelude']:
        pr = p['proof']; nr = p.get('near')
        f.write('\t'.join(str(x) for x in ['prelude', p['bundle'].split('/')[0], p['name'], p['bytes'], (pr['how'] + ':' + pr['oracle']) if pr else 'UNPROVEN', pr['file'] if pr else (('near %s %s' % (nr['ratio'], nr['file'])) if nr else 'no same-named readable statement')]) + '\n')
    for p in S['other']:
        ch = p.get('chunks')
        f.write('\t'.join(str(x) for x in ['other', p['bundle'].split('/')[0], p['head'].replace('\t', ' ').replace('\n', ' '), p['bytes'], p.get('equal') or 'UNPROVEN', ('raw 128-byte chunks found %d/%d in %s' % (ch['hit'], ch['chunks'], ch['file'])) if ch else '']) + '\n')

tot = collections.Counter()
with open(os.path.join(out, 'bundles.tsv'), 'w') as f:
    f.write('module\tpath\tbytes\tsha256\tnewlines\tsourceMappingURL\tmodules\tproven_js_modules\tskeleton_modules\thbs_proven\tstub_or_vendor_wrapper\tother_class\tdef_bytes_proven\tdef_bytes_skeleton\tprelude_bytes_proven\tprelude_bytes_unproven\tother_bytes_proven\tother_bytes_unproven\tbytes_proven\tpct_bytes_proven\tpct_bytes_proven_or_skeleton\n')
    for b in C:
        cl = per[b['path']]; bb = byt[b['path']]
        pj = sum(cl[k] for k in PROVEN_JS); sk = cl[SKEL]; ph = cl['HBS-RECOMPILE-MATCH']; st = cl['STUB-OR-VENDOR-WRAPPER'] + cl['EMPTY-STUB']
        other = sum(v for k, v in cl.items() if k not in PROVEN_JS | {SKEL, 'HBS-RECOMPILE-MATCH', 'STUB-OR-VENDOR-WRAPPER', 'EMPTY-STUB'})
        dbp = sum(bb[k] for k in PROVEN_JS) + bb['HBS-RECOMPILE-MATCH']
        dbs = bb[SKEL]
        pp, _, pu, _ = pre[b['path']]; op, _, ou, _ = oth[b['path']]
        proven = dbp + pp + op
        f.write('\t'.join(str(x) for x in [b['module'], b['path'], b['bytes'], b['sha256'], b['newlines'], int(b['sourceMappingURL']), b['modules'], pj, sk, ph, st, other, dbp, dbs, pp, pu, op, ou, proven, round(100 * proven / b['bytes'], 2), round(100 * (proven + dbs) / b['bytes'], 2)]) + '\n')
        tot.update({'bytes': b['bytes'], 'modules': b['modules'], 'proven_js_modules': pj, 'skeleton_modules': sk, 'def_bytes_skeleton': dbs, 'hbs': ph, 'stub': st, 'other_class': other, 'def_bytes_proven': dbp,
                    'prelude_proven': pp, 'prelude_unproven': pu, 'other_proven': op, 'other_unproven': ou, 'proven': proven})
with open(os.path.join(out, 'summary.txt'), 'w') as f:
    f.write('bundles %d\n' % len(C))
    for k, v in tot.items(): f.write('%s %d\n' % (k, v))
    f.write('pct_bytes_proven %.2f\n' % (100 * tot['proven'] / tot['bytes']))
    f.write('pct_bytes_proven_or_skeleton %.2f\n' % (100 * (tot['proven'] + tot['def_bytes_skeleton']) / tot['bytes']))
    c2 = collections.Counter(r['final'] for r in E)
    f.write('skeleton ordered-equal: %d of %d\n' % (sum(1 for r in E if r.get('ordered')), sum(1 for r in E if r['final'] == SKEL)))
    f.write('module classes %s\n' % dict(c2))
    f.write('deps_equal false among matched: %d\n' % sum(1 for r in E if r.get('depsEqual') is False))
print(open(os.path.join(out, 'summary.txt')).read())
