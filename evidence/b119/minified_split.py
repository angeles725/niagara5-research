#!/usr/bin/env python3
"""B119: split the 234 (non-underscore-prefixed) B117 'minified' JS files into truly-minified (mean line
>= 250 B) vs long-line-only (longest >= 1000 B but mean < 250 B, i.e. transpiled/readable code with a few
long lines). Usage: minified_split.py ORGANIZED"""
import json, os, sys, collections
org = sys.argv[1]
f = [x for x in json.load(open(os.path.join(os.path.dirname(__file__), "minified-nomap.json")))["files"] if not x["path"].startswith("_")]
mean_rows, long_rows = [], []
for x in f:
    b = open(os.path.join(org, x["path"]), "rb").read(); ls = b.split(b"\n")
    (mean_rows if len(b) / len(ls) >= 250 else long_rows).append({"path": x["path"], "lines": len(ls), "bytes": len(b), "mean": round(len(b) / len(ls), 1), "longest": max(map(len, ls))})
print("mean>=250 (truly minified):", len(mean_rows), " long-line-only:", len(long_rows))
print("truly minified with <=10 lines:", sum(1 for r in mean_rows if r["lines"] <= 10))
print("long-line-only median lines:", sorted(r["lines"] for r in long_rows)[len(long_rows) // 2], " median mean-line:", sorted(r["mean"] for r in long_rows)[len(long_rows) // 2])
print("truly-minified by module (top 8):", collections.Counter(r["path"].split("/")[0] for r in mean_rows).most_common(8))
json.dump({"mean_ge_250": mean_rows, "longest_only": long_rows}, open(os.path.join(os.path.dirname(__file__), "minified-split.json"), "w"), indent=1)
