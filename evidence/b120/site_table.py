#!/usr/bin/env python3
"""B120: join grades.json (grade_sites.py) + recon-results.json (reconstruct.py) + site-labels.tsv into the per-site table.

Per (tree, method) code:
  X       normalized bytecode identical to the shipped method (labels, order, guard restart loop, default/MatchException)
  S       compiles; labels equal; same effects but different branch layout (or same effect multiset, arms permuted)
  U       compiles; labels equal; ONLY difference = extra `checkcast` for an UNUSED pattern binding (shipped uses the
          unnamed pattern `_`); confirmed exact by reconstruct.py when a recon row exists
  D       compiles; effects differ (see grades.json effect_diff) -> reviewed by hand in the block
  PSEUDO  javac rejects the file AND the text holds SwitchBootstraps/typeSwitch</.../invokedynamic(!) pseudo-Java
  NC      javac rejects the file, no pseudo-Java token (cause is elsewhere in the file; listed per unit)
  EMPTY   the decompiler wrote an empty file
Usage: site_table.py grades.json recon-results.json site-labels.tsv > site-table.tsv
"""
import json, sys
from collections import Counter, defaultdict

grades = json.load(open(sys.argv[1]))
recon = {r["name"]: r for r in json.load(open(sys.argv[2]))}
labels = {}
for ln in open(sys.argv[3]):
    cls, meth, kind, labs, guard = ln.rstrip("\n").split("\t")
    labels[(cls, meth)] = (kind, labs, guard)

TREES = ["v1", "v2", "cons", "cfr", "procyon"]


def code(entry, cls, meth):
    st = entry.get("status")
    if st == "empty-output":
        return "EMPTY"
    if st == "no-source":
        return "-"
    if st == "no-compile":
        return "PSEUDO" if entry.get("pseudo") else "NC"
    m = entry.get("methods", {}).get(cls, {}).get(meth) or entry.get("methods", {}).get(cls, {}).get("*")
    if m is None:
        return "?"
    if m["verdict"] == "exact":
        return "X"
    if m["verdict"] == "missing":
        return "MISSING"
    ed = m.get("effect_diff", [])
    if not ed or ed[0].startswith("PERMUTED"):
        return "S"
    if ed and all(x.startswith("+checkcast") for x in ed):
        return "U"
    return "D"


rows = []
for u in grades:
    for cls in u["unit"]["targets"]:
        methods = set()
        for t in TREES:
            e = u["trees"][t]
            methods |= set(e.get("methods", {}).get(cls, {}).keys())
        # methods known from the shipped labels table too (needed when every tree failed to compile)
        for (c, m), v in labels.items():
            if c == cls:
                methods.add(m)
        for meth in sorted(methods):
            if meth == "*":
                continue
            kind, labs, guard = labels.get((cls, meth), ("MatchException", "-", "-"))
            rows.append({"class": cls, "method": meth, "kind": kind, "labels": labs, "guard_loop": guard,
                         **{t: code(u["trees"][t], cls, meth) for t in TREES}})

for r in rows:
    r["recon"] = ""
    key_short = r["class"].split("/")[-1].split("$")[0] + "." + r["method"].split("(")[0]
    for name, rr in recon.items():
        if name.startswith(key_short):
            mv = [v["verdict"] for k, v in rr.get("methods", {}).items() if k.startswith(r["method"].split("(")[0])]
            r["recon"] = "exact" if mv and all(x == "exact" for x in mv) else ("effects-equal" if rr.get("compiled") else "no-compile")

print("\t".join(["kind", "class", "method", "guard_loop", "labels"] + TREES + ["recon"]))
for r in rows:
    print("\t".join([r["kind"], r["class"], r["method"], r["guard_loop"], r["labels"]] + [r[t] for t in TREES] + [r["recon"]]))

tally = defaultdict(lambda: defaultdict(Counter))
for r in rows:
    for t in TREES:
        tally[r["kind"]][t][r[t]] += 1
print("\n# tally (rows = methods; typeSwitch rows equal sites, one indy per method)", file=sys.stderr)
for kind, d in tally.items():
    print(kind, sum(d["v2"].values()), "methods", file=sys.stderr)
    for t in TREES:
        print("  ", t, dict(d[t]), file=sys.stderr)
