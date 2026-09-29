#!/usr/bin/env python3
"""B119: for every niagara5-block*.md, extract cited *.js tokens, resolve each to files under
organized/*/extracted (exact path suffix, else unique basename), and classify by the B117 minified rule
and the stricter mean-line rule. Usage: block_js_cites.py REPO ORGANIZED"""
import json, os, re, sys, collections
repo, org = sys.argv[1:3]
idx = collections.defaultdict(list)
for mod in sorted(os.listdir(org)):
    roots = [os.path.join(org, mod, "extracted")]
    if mod.startswith("_"):
        base = os.path.join(org, mod)
        roots = [os.path.join(base, s, "extracted") for s in os.listdir(base)] if os.path.isdir(base) else []
    for root in roots:
        for d, _, fn in os.walk(root):
            for f in fn:
                if f.endswith(".js"): idx[f].append(os.path.join(d, f))
def cls(p):
    b = open(p, "rb").read(); ls = b.split(b"\n")
    lg = max(map(len, ls)); mn = len(b) / len(ls)
    return "minified-mean" if mn >= 250 else ("long-line-only" if lg >= 1000 else "readable")
tok = re.compile(r"[A-Za-z0-9_@./-]+\.js\b")
out = {}
for f in sorted(os.listdir(repo)):
    if not re.match(r"niagara5-block\d+\.md$", f): continue
    txt = open(os.path.join(repo, f), encoding="utf-8").read()
    toks = sorted(set(t for t in tok.findall(txt) if not t.startswith("http") and "node" not in t.lower()[:5]))
    rows = []
    for t in toks:
        bn = os.path.basename(t)
        cands = idx.get(bn, [])
        exact = [c for c in cands if c.endswith("/" + t.lstrip("./"))] if "/" in t else []
        use = exact or cands
        if not use: rows.append({"tok": t, "resolved": 0, "class": "unresolved"}); continue
        classes = sorted({cls(c) for c in use})
        rows.append({"tok": t, "resolved": len(use), "class": "/".join(classes)})
    if rows: out[f] = rows
json.dump(out, open(os.path.join(os.path.dirname(__file__), "block-js-cites.json"), "w"), indent=1)
for f, rows in out.items():
    c = collections.Counter(r["class"] for r in rows)
    print(f, dict(c))
