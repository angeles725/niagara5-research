#!/usr/bin/env python3
"""B125 step 3d: the durable Kotlin-plugin trees (organized/_etc-m2/<jar>/vineflower2, built with dump_bytecode_on_error) keep a `// Bytecode:` listing
inside every "Couldn't be decompiled" method. Count its instruction lines and compare with the instruction count of the shipped method (javap -c).
Walls of one .kt file are paired with the file's markers in order. Writes plugin-bytecode-dump.tsv to stdout."""
import csv, os, re, subprocess, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b125_lib import *
rows = list(csv.DictReader(open("wall-sites-map.tsv"), delimiter="\t"))
bykt = collections.defaultdict(list)
seen = set()
for r in rows:
    if r["note"] == "class-wall" or r["wall_id"] in seen: continue
    seen.add(r["wall_id"]); bykt[(r["jar"], r["kt_file"])].append(r)
def icount(jar, cls, name, desc):
    txt = subprocess.run([f"{JAVA_BIN}/javap", "-c", "-p", "-s", f"{extracted(jar)}/{cls}.class"], capture_output=True, text=True).stdout.splitlines()
    n, on = 0, False
    for i, l in enumerate(txt):
        if re.match(r"^  \S", l):
            on = i + 1 < len(txt) and txt[i + 1].strip() == f"descriptor: {desc}" and (name + "(") in l
        elif on and re.match(r"^\s+\d+: \w", l): n += 1
    return n
print("wall_id\tplugin_dump_instr\tshipped_instr\tdump_complete")
for (jar, kt), ws in sorted(bykt.items()):
    p = f"{ORG}/_etc-m2/{JARS[jar]}/vineflower2/{kt}"
    lines = open(p, encoding="utf8", errors="replace").read().split("\n")
    marks = [i for i, l in enumerate(lines) if "Couldn't be decompiled" in l]
    ws = sorted(ws, key=lambda r: int(r["kt_line"]))
    for r, i in zip(ws, marks):
        n = 0; j = i
        while j < len(lines) and "Bytecode:" not in lines[j] and lines[j].strip().startswith("//"): j += 1
        j += 1
        while j < len(lines) and re.match(r"\s*// [0-9A-Fa-f]+: ", lines[j]): n += 1; j += 1
        s = icount(jar, r["cls"], r["method"], r["desc"])
        print(f"{r['wall_id']}\t{n}\t{s}\t{'yes' if n == s else 'no'}")
