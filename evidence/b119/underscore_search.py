#!/usr/bin/env python3
"""B119 absence census for the 160 underscore ES modules named by js/extracted/rc/underscore/underscore-umd.js.map:
term 1 = exact filename anywhere under organized/ (excluding _best/, which only re-links); term 2 = content token
'function restArguments' / 'function isObject(' / underscore version string. Usage: underscore_search.py ORGANIZED"""
import json, os, sys, subprocess
org = sys.argv[1]
j = json.load(open(os.path.join(org, "js/extracted/rc/underscore/underscore-umd.js.map"), encoding="utf-8"))
names = {os.path.basename(s) for s in j["sources"]}
hits = {}
for d, dn, fn in os.walk(org):
    if d == org: dn[:] = [x for x in dn if x != "_best"]
    for f in fn:
        if f in names and "underscore" in os.path.join(d, f).lower():
            hits.setdefault(f, []).append(os.path.relpath(os.path.join(d, f), org))
any_name = {}
for d, dn, fn in os.walk(org):
    if d == org: dn[:] = [x for x in dn if x != "_best"]
    for f in fn:
        if f in names: any_name.setdefault(f, []).append(os.path.relpath(os.path.join(d, f), org))
print("module basenames in map:", len(names))
print("term1a: basenames found under a path containing 'underscore':", len(hits))
print("term1b: basenames found anywhere under organized/ (non-_best):", len(any_name), sorted(any_name)[:10])
for tok in ("function restArguments", "modules/_setup", "VERSION = '1.13"):
    r = subprocess.run(["grep", "-rlF", "--include=*.js", tok, org, "--exclude-dir=_best"], capture_output=True, text=True)
    files = sorted({os.path.relpath(x, org).split("/")[0] + "/" + "/".join(os.path.relpath(x, org).split("/")[1:2]) + ":" + os.path.basename(x) for x in r.stdout.split()})
    print("term2 %r ->" % tok, len(r.stdout.split()), "files; distinct tree/name:", files[:6])
