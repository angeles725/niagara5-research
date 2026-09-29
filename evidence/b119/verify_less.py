#!/usr/bin/env python3
"""B119: for every unique JSON map WITHOUT sourcesContent, locate each source in the shipped module
tree (organized/<module>/extracted/<path after /module/<module>/>) and check the map's mapped source
lines fit inside the shipped file (VLQ decode). Usage: verify_less.py ORGANIZED"""
import json, os, sys, hashlib
org = sys.argv[1]
B64 = {c: i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")}
def vlq(seg):
    out, shift, val = [], 0, 0
    for ch in seg:
        d = B64[ch]; val += (d & 31) << shift
        if d & 32: shift += 5; continue
        out.append(-(val >> 1) if val & 1 else val >> 1); shift = val = 0
    return out
def max_lines(mappings):
    src = line = 0; mx = {}
    for gl in mappings.split(";"):
        for seg in gl.split(","):
            if not seg: continue
            f = vlq(seg)
            if len(f) >= 4:
                src += f[1]; line += f[2]; mx[src] = max(mx.get(src, -1), line)
    return mx
census = json.load(open(os.path.join(os.path.dirname(__file__), "census-maps.json")))
res = []
for m in census["maps"]:
    if not m["json"] or m["sourcesContent"] or not m["sources"]: continue
    j = json.load(open(os.path.join(org, m["first_path"]), encoding="utf-8"))
    mx = max_lines(j["mappings"])
    for i, s in enumerate(j["sources"]):
        r = {"map": m["first_path"], "source": s, "found": None, "sha256": None, "lines": None, "max_mapped_line": mx.get(i)}
        if s.startswith("/module/"):
            mod, rest = s[len("/module/"):].split("/", 1)
            p = os.path.join(org, mod, "extracted", rest)
            if os.path.isfile(p):
                b = open(p, "rb").read()
                r.update(found=os.path.relpath(p, org), sha256=hashlib.sha256(b).hexdigest(), lines=b.count(b"\n") + 1)
        res.append(r)
json.dump(res, open(os.path.join(os.path.dirname(__file__), "less-locate.json"), "w"), indent=1)
less = [r for r in res if r["source"].endswith(".less")]
print("less source entries:", len(less), "unique paths:", len({r["source"] for r in less}))
print("found in extracted/:", sum(1 for r in less if r["found"]), "unique:", len({r["source"] for r in less if r["found"]}))
print("not found:", sorted({r["source"] for r in less if not r["found"]}))
print("mapped lines fit shipped file:", sum(1 for r in less if r["found"] and r["max_mapped_line"] is not None and r["max_mapped_line"] < r["lines"]),
      "exceed:", [(r["source"], r["max_mapped_line"], r["lines"]) for r in less if r["found"] and r["max_mapped_line"] is not None and r["max_mapped_line"] >= r["lines"]])
