#!/usr/bin/env python3
"""B125 step 3b: how much of each wall method survives in the Java-mode Vineflower text (recompile is impossible for most, see grade_sites.py).
Per wall row: locate the method declaration in the Java-mode file, brace-match its body, and count placeholders and how many of the shipped
method's string constants and invoked method names (javap -c) appear in the body text. A coverage proxy, not a fidelity grade.
Usage: java_body_metrics.py <wall-sites-map.tsv> <out.tsv>"""
import csv, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b125_lib import *
JAVAP = f"{JAVA_BIN}/javap"
_cache = {}

def javap_c(jar, cls):
    k = (jar, cls)
    if k not in _cache:
        _cache[k] = subprocess.run([JAVAP, "-c", "-p", "-s", f"{extracted(jar)}/{cls}.class"], capture_output=True, text=True).stdout
    return _cache[k]

def method_block(txt, name, desc):
    lines = txt.splitlines(); out = []; on = False
    for n, l in enumerate(lines):
        if re.match(r"^  \S", l):
            on = False
            if n + 1 < len(lines) and lines[n + 1].strip() == f"descriptor: {desc}" and re.search(r"\b" + re.escape(name) + r"\(", l):
                on = True
        if on: out.append(l)
    return "\n".join(out)

def nparams(desc):
    return len(re.sub(r"L[^;]*;", "X", desc[1:desc.index(")")]).replace("[", ""))

def java_body(path, name, desc):
    lines = open(path, encoding="utf8", errors="replace").read().split("\n")
    pat = re.compile(r"^\s+(?:[\w$<>\[\]?,.@ ]+\s)?" + re.escape(name) + r"\(([^)]*)\)?.*\{\s*$")
    for i, l in enumerate(lines):
        m = pat.match(l)
        if not m or ";" in l.split(name + "(")[0] or "=" in l.split(name + "(")[0] or " new " in l or " return " in l:
            continue
        depth, j = 0, i
        while j < len(lines):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0 and j > i or (depth == 0 and j == i and "}" in lines[j]): break
            j += 1
        body = "\n".join(lines[i:j + 1])
        first = l.split(name + "(", 1)[1]
        pc = first.split(")")[0]
        n_args = 0 if not pc.strip() else pc.count(",") + 1
        if n_args == nparams(desc) or n_args == 0 and nparams(desc) == 0:
            return i + 1, body
    return None, ""

rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
cols = ["wall_id", "jar", "cls", "method", "desc", "jm_file", "jm_line", "jm_lines", "jm_unrep", "jm_inline_markers", "ldc_total", "ldc_found", "inv_total", "inv_found"]
with open(sys.argv[2], "w") as fh:
    fh.write("\t".join(cols) + "\n")
    for r in rows:
        jar, cls, name, desc = r["jar"], r["cls"], r["method"], r["desc"]
        jf = f"{EV}/java-mode/{jar}/{cls}.java"
        if not os.path.isfile(jf): jf = f"{EV}/java-mode/{jar}/{cls.split('$')[0]}.java"
        rel = os.path.relpath(jf, ORG)
        txt = javap_c(jar, cls)
        if name == "*":
            body, ln = open(jf, encoding="utf8", errors="replace").read(), 1
            blk = txt
        else:
            ln, body = java_body(jf, name, desc)
            blk = method_block(txt, name, desc)
        strs = sorted(set(re.findall(r"// String (.*)$", blk, re.M)))
        invs = sorted({m for m in re.findall(r"// (?:Interface)?Method [\w/$.\[\];]*?\.?([\w$<>]+):", blk, re.M) if not m.startswith(("<init>", "checkNot", "areEqual"))})
        f_s = sum(1 for s in strs if s and s in body)
        f_i = sum(1 for m in invs if (m + "(") in body or ("::" + m) in body)
        vals = [r["wall_id"], jar, cls, name, desc, rel, ln or "", body.count("\n") + 1 if body else 0, body.count("<unrepresentable>"),
                body.count("$i$f$") + body.count("$i$a$"), len(strs), f_s, len(invs), f_i]
        fh.write("\t".join(map(str, vals)) + "\n")
