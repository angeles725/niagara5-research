#!/usr/bin/env python3
"""B119 census of *.map files under organized/ (excluding _best/).
Usage: census_maps.py ORGANIZED_DIR  -> prints JSON to stdout."""
import hashlib, json, os, sys
org = sys.argv[1]
paths = []
for d, dn, fn in os.walk(org):
    if d == org:
        dn[:] = [x for x in dn if x != "_best"]
    for f in fn:
        if f.endswith(".map"):
            paths.append(os.path.join(d, f))
paths.sort()
by_sha = {}
for p in paths:
    b = open(p, "rb").read()
    by_sha.setdefault(hashlib.sha256(b).hexdigest(), []).append(os.path.relpath(p, org))
uniq = []
for sha, ps in sorted(by_sha.items()):
    b = open(os.path.join(org, ps[0]), "rb").read()
    rec = {"sha256": sha, "n_paths": len(ps), "first_path": ps[0], "bytes": len(b)}
    try:
        j = json.loads(b.decode("utf-8-sig"))
        if not isinstance(j, dict) or "sources" not in j and "mappings" not in j:
            raise ValueError("not a sourcemap")
        sc = j.get("sourcesContent")
        rec.update(json=True, version=j.get("version"), file=j.get("file"),
                   sources=j.get("sources", []), n_sources=len(j.get("sources", [])),
                   sourcesContent=bool(sc), n_sc=sum(1 for x in (sc or []) if x),
                   sourceRoot=j.get("sourceRoot"), mappings_len=len(j.get("mappings", "")))
    except Exception as e:
        rec.update(json=False, err=str(e)[:80])
    uniq.append(rec)
tops = {}
for p in paths:
    rel = os.path.relpath(p, org).split(os.sep)
    tops.setdefault(rel[0] + "/" + (rel[1] if len(rel) > 1 else ""), 0)
summary = {"paths": len(paths), "unique_sha": len(uniq),
           "json": sum(1 for u in uniq if u["json"]),
           "nonjson": [u["first_path"] for u in uniq if not u["json"]],
           "json_with_sc": sum(1 for u in uniq if u["json"] and u["sourcesContent"]),
           "json_without_sc": sum(1 for u in uniq if u["json"] and not u["sourcesContent"]),
           "sources_entries": sum(u.get("n_sources", 0) for u in uniq if u["json"]),
           "sc_nonempty_entries": sum(u.get("n_sc", 0) for u in uniq if u["json"])}
print(json.dumps({"summary": summary, "maps": uniq}, indent=1))
