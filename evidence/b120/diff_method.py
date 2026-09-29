#!/usr/bin/env python3
"""Show the normalized-bytecode diff (shipped vs recompiled) for the non-exact methods of one unit/tree.
Usage: diff_method.py <grades.json> <top-class-substring> <tree> <scratch> [context]"""
import difflib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_sites as g
grades, only, tree, scratch = sys.argv[1:5]
ctx = int(sys.argv[5]) if len(sys.argv) > 5 else 1
for u in json.load(open(grades)):
    if only not in u["unit"]["top_rel"]:
        continue
    e = u["trees"][tree]
    mod = u["unit"]["mod"]
    for t, ms in e.get("methods", {}).items():
        for key, m in ms.items():
            if m["verdict"] == "exact":
                continue
            rc = Path(scratch) / "rc" / tree / mod.replace("/", "_") / u["unit"]["top_rel"].replace("/", "_") / (t + ".class")
            a, _ = g.parsed(g.ORG / mod / "extracted" / (t + ".class"))
            b, _ = g.parsed(rc)
            for k in a["methods"]:
                if f"{k[0]}{k[1]}" == key:
                    print("==", t, key, m)
                    for l in list(difflib.unified_diff(a["methods"][k]["code"], b["methods"][k]["code"], lineterm="", n=ctx))[:80]:
                        print(l)
