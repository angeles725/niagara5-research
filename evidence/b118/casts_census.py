import importlib.util, collections, json, os
spec = importlib.util.spec_from_file_location("x", "/home/cristian/niagara5-research/tools/n5-bytecode-xref.py"); x = importlib.util.module_from_spec(spec); spec.loader.exec_module(x)
ORG = "/home/cristian/niagara5-research/organized"
idx = x.build_index(ORG)
ds = set()
for d, _, fs in os.walk(os.path.join(ORG, "docSource")):
    for f in fs:
        if f.endswith(".java"): ds.add(os.path.relpath(os.path.join(d, f), os.path.join(ORG, "docSource")).split("/", 1)[1][:-5])
tot = collections.Counter(); per = collections.defaultdict(collections.Counter); majors = collections.Counter()
for c in idx["classes"].values():
    majors[c["major"]] += 1
    top = c["name"].split("$")[0]
    grp = "docSource-covered" if top in ds else "no-docSource"
    for m in c["methods"]:
        for s in x.cast_sites(m):
            tot[(grp, s["verdict"])] += 1; per[c["module"]][s["verdict"]] += 1
print("classes", len(idx["classes"]), "parse_errors", len(idx["errors"]), "majors", dict(majors))
for k, v in sorted(tot.items()): print(k, v)
mods = sorted(per.items(), key=lambda kv: -kv[1]["pattern-or-same-line"])[:10]
print("top modules by pattern-or-same-line:", [(m, dict(c)) for m, c in mods])
