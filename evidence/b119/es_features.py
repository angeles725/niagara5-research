#!/usr/bin/env python3
"""B119: ES2015+ feature census: recovered original (sourcesContent) vs shipped JS, 42 maps."""
import json, os, re, sys
org = sys.argv[1]
pats = {"arrow": r"=>", "class": r"\bclass\s+\w+\s*(extends\b|\{)", "const_let": r"(^|[\s;(])(const|let)\s+[\w{\[]", "template": r"`", "spread_rest": r"\.\.\.[\w(\[]"}
rows = json.load(open(os.path.join(os.path.dirname(__file__), "sc-analysis.json")))
out = []
for r in rows:
    mp = os.path.join(org, r["map"]); j = json.load(open(mp, encoding="utf-8"))
    sc = j["sourcesContent"][0]
    gen = open(os.path.join(os.path.dirname(mp), j["file"]), encoding="utf-8").read()
    def strip(t): return re.sub(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", "", t, flags=re.S)
    def cnt(t): t = strip(t); return {k: len(re.findall(p, t, re.M)) for k, p in pats.items()}
    a, b = cnt(sc), cnt(gen)
    out.append({"map": r["map"], "src": a, "gen": b, "src_head": [l for l in sc.splitlines() if l.strip() and not l.strip().startswith(("*", "/*", "//"))][:1],
                "src_uses_es2015": any(a.values()), "gen_uses_es2015": any(b.values()), "gen_use_strict": "use strict" in gen})
json.dump(out, open(os.path.join(os.path.dirname(__file__), "es-features.json"), "w"), indent=1)
print("src uses ES2015+:", sum(o["src_uses_es2015"] for o in out), "of", len(out))
print("gen uses ES2015+:", sum(o["gen_uses_es2015"] for o in out))
for k in pats: print(k, "src files", sum(1 for o in out if o["src"][k]), "gen files", sum(1 for o in out if o["gen"][k]))
for o in out:
    if o["map"].startswith("workbench"): print(o["map"], o["src_head"], o["src"], o["gen"])
