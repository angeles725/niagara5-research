#!/usr/bin/env python3
"""B119: census of minified JS (rule = tools/n5-extract-census.py is_minified_js: longest line >= 1000 B or
mean line >= 250 B) under organized/*/extracted/, and which of them have a source map.
Usage: minified_nomap.py ORGANIZED"""
import json, os, re, sys, collections
org = sys.argv[1]
def mini(b):
    ls = b.split(b"\n"); return max(len(x) for x in ls) >= 1000 or len(b) / len(ls) >= 250
tot = 0; rows = []
for mod in sorted(os.listdir(org)):
    roots = [os.path.join(org, mod, "extracted")]
    if mod.startswith("_"):
        roots = [os.path.join(org, mod, s, "extracted") for s in (os.listdir(os.path.join(org, mod)) if os.path.isdir(os.path.join(org, mod)) else [])]
    for root in roots:
        for d, _, fn in os.walk(root):
            for f in fn:
                if not f.endswith(".js"): continue
                p = os.path.join(d, f); b = open(p, "rb").read(); tot += 1
                if not mini(b): continue
                tail = b[-300:].decode("utf-8", "replace")
                m = re.search(r"sourceMappingURL=(\S+)", tail)
                sib = os.path.exists(p + ".map")
                target = os.path.join(d, m.group(1)) if m and not m.group(1).startswith("data:") else None
                rows.append({"path": os.path.relpath(p, org), "bytes": len(b), "mapref": m.group(1)[:60] if m else None,
                             "sibling_map": sib, "ref_target_exists": bool(target and os.path.exists(target)),
                             "license_only_header": False})
res = {"total_js": tot, "minified": len(rows),
       "minified_with_sourceMappingURL_comment": sum(1 for r in rows if r["mapref"]),
       "minified_with_sibling_dot_map": sum(1 for r in rows if r["sibling_map"]),
       "minified_with_existing_map_target": sum(1 for r in rows if r["ref_target_exists"]),
       "minified_no_map_at_all": sum(1 for r in rows if not r["sibling_map"] and not r["ref_target_exists"]),
       "by_module": dict(collections.Counter(r["path"].split("/")[0] for r in rows).most_common())}
json.dump({"summary": res, "files": rows}, open(os.path.join(os.path.dirname(__file__), "minified-nomap.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
