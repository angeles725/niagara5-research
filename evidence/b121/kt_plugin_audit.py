#!/usr/bin/env python3
"""B121 step 3b: (1) list every method the Vineflower Kotlin plugin could not decompile ('$VF: Couldn't be decompiled')
and (2) check the plugin's .kt output against the kotlin.Metadata truth recovered by KotlinAudit
(function names declared in metadata vs `fun` names printed in the .kt file).
Reads the fresh runs under organized/_evidence/b121/{vf-kt,kotlin-signatures}; writes TSVs to stdout dir given as argv[1]."""
import os, re, sys, collections
EV = "/home/cristian/niagara5-research/organized/_evidence/b121"
OUT = sys.argv[1]
JARS = ["n-plugin", "n-conv-plugin", "settings", "utils"]
FUN_KT = re.compile(r"\bfun\s+(?:<[^>]*>\s*)?(?:[\w.<>?, *]+?\.)?(\w+)\s*\(")
FUN_META = re.compile(r"\bfun\s+(?:<[^>]*>\s*)?(?:[\w.<>?, *]+?\.)?([^\s(]+)\(")
HDR = re.compile(r"(\bfun\b|\bconstructor\b|\binit\b|\bget\(\)|\bset\()")

walls = []
agree = []
for j in JARS:
    base = f"{EV}/vf-kt/{j}"
    for r, _d, fs in os.walk(base):
        for f in fs:
            if not f.endswith(".kt"):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, base)
            lines = open(p, encoding="utf8", errors="replace").read().split("\n")
            for i, l in enumerate(lines):
                if "Couldn't be decompiled" in l:
                    k = i
                    while k > 0 and not HDR.search(lines[k]):
                        k -= 1
                    hdr = re.sub(r"\s+", " ", lines[k].strip())
                    # keep only the declaration head (name + arity), not any body text
                    m = re.search(r"\bfun\s+(?:<[^>]*>\s*)?(?:[\w.<>?, *]+?\.)?(\w+)\s*\(([^)]*)\)", hdr)
                    if m:
                        head = f"fun {m.group(1)}/{0 if not m.group(2).strip() else m.group(2).count(':')}"
                    else:
                        head = re.split(r"[({]", hdr)[0][:60]
                    walls.append((j, rel, i + 1, head))
    # declaration agreement
    sigroot = f"{EV}/kotlin-signatures/{j}"
    meta_by_top = collections.defaultdict(set)
    for r, _d, fs in os.walk(sigroot):
        for f in fs:
            cls = os.path.relpath(os.path.join(r, f), sigroot)[:-len(".kt.txt")]
            top = cls.split("$")[0]
            txt = open(os.path.join(r, f), encoding="utf8").read()
            for l in txt.split("\n"):
                if "fun " in l and l.startswith("  "):
                    m = FUN_META.search(l)
                    if m:
                        nm = m.group(1).rsplit(".", 1)[-1]
                        if not nm.startswith("<"):
                            meta_by_top[top].add(nm)
    tot_meta = tot_hit = tot_kt_only = 0
    miss = []
    for top, names in meta_by_top.items():
        cand = [os.path.join(base, top + ".kt"), os.path.join(base, top + ".java")]
        path = next((c for c in cand if os.path.exists(c)), None)
        if path is None:
            # facade classes: the plugin names the file after the class, or after the source file
            d = os.path.dirname(top)
            path = None
        if path is None:
            tot_meta += len(names); miss.append((top, "NO-OUTPUT-FILE", len(names))); continue
        txt = open(path, encoding="utf8", errors="replace").read()
        kt = set(FUN_KT.findall(txt))
        hit = names & kt
        tot_meta += len(names); tot_hit += len(hit)
        tot_kt_only += len(kt - names)
        if names - kt:
            miss.append((top, ",".join(sorted(names - kt))[:120], len(names - kt)))
    agree.append((j, tot_meta, tot_hit, tot_kt_only, miss))

with open(f"{OUT}/kt-plugin-walls.tsv", "w") as fh:
    fh.write("jar\tkt_file\tline\tmember_head\n")
    for w in sorted(walls):
        fh.write("\t".join(map(str, w)) + "\n")
with open(f"{OUT}/kt-plugin-decl-agreement.tsv", "w") as fh:
    fh.write("jar\tmetadata_fun_names\tpresent_in_kt\tkt_only_fun_names\tclasses_with_missing\n")
    for j, a, b, c, miss in agree:
        fh.write(f"{j}\t{a}\t{b}\t{c}\t{len(miss)}\n")
    fh.write("\n# classes whose metadata function names are not all present as `fun` in the plugin's file (top-level class, missing names, count)\n")
    for j, a, b, c, miss in agree:
        for m in sorted(miss):
            fh.write(f"{j}\t{m[0]}\t{m[1]}\t{m[2]}\n")
print(len(walls), "walls")
for j, a, b, c, miss in agree: print(j, a, b, c, len(miss))
