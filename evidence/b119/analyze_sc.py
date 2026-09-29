#!/usr/bin/env python3
"""B119: for every unique JSON source map under organized/*/extracted with sourcesContent,
compare the recovered original with the shipped generated JS. Usage: analyze_sc.py ORGANIZED"""
import hashlib, json, os, re, sys
org = sys.argv[1]
rows = []
def mean_line(b): 
    return len(b) / max(1, b.count(b"\n") + 1)
def longest(b):
    return max(len(x) for x in b.split(b"\n"))
def norm(s):
    return re.sub(r"\s+", "", re.sub(r"/\*.*?\*/|//[^\n]*", "", s, flags=re.S))
for mod in sorted(os.listdir(org)):
    ex = os.path.join(org, mod, "extracted")
    for d, _, fn in os.walk(ex):
        for f in sorted(fn):
            if not f.endswith(".js.map"):
                continue
            p = os.path.join(d, f)
            j = json.load(open(p, encoding="utf-8"))
            if not j.get("sourcesContent"):
                continue
            gen = os.path.join(d, j.get("file") or f[:-4])
            gb = open(gen, "rb").read() if os.path.exists(gen) else None
            sc = j["sourcesContent"][0]
            sb = sc.encode("utf-8")
            tail = (gb or b"")[-200:].decode("utf-8", "replace")
            rows.append({
                "module": mod, "map": os.path.relpath(p, org), "generated_exists": gb is not None,
                "map_sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
                "source": j["sources"][0], "source_bytes": len(sb),
                "source_sha256": hashlib.sha256(sb).hexdigest(),
                "gen_bytes": len(gb) if gb else None,
                "gen_mean_line": round(mean_line(gb), 1) if gb else None,
                "gen_longest_line": longest(gb) if gb else None,
                "src_mean_line": round(mean_line(sb), 1), "src_longest_line": longest(sb),
                "gen_minified": bool(gb and (longest(gb) >= 1000 or mean_line(gb) >= 250)),
                "src_has_comments": bool(re.search(r"/\*\*|//", sc)),
                "gen_has_comments": bool(gb and re.search(rb"/\*\*|//", gb)),
                "src_amd_define": "define(" in sc, "src_es_import_export": bool(re.search(r"^\s*(import|export)\s", sc, re.M)),
                "gen_has_sourceMappingURL": "sourceMappingURL" in tail,
                "code_identical_after_comment_ws_strip": bool(gb) and norm(sc) == norm(gb.decode("utf-8", "replace")),
                "byte_identical": bool(gb) and sb == gb,
            })
print(json.dumps(rows, indent=1))
