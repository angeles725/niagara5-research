#!/usr/bin/env python3
"""B125 step 3a: map every Kotlin-plugin wall site of B121 (evidence/b121/kt-plugin-walls.tsv, 67 method walls) plus the
6 whole-class walls to a JVM (class, method, descriptor) and record the plugin failure kind (exception + first plugin frame)
and the bytecode constructs of the shipped method. Writes wall-sites-map.tsv (stdout dir argv[1]).
Reads only the fresh Kotlin-plugin run under organized/_evidence/b121/vf-kt (line numbers of the walls tsv refer to it)."""
import os, re, subprocess, sys, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b125_lib import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.dirname(os.path.abspath(__file__))
HDR = re.compile(r"(\bfun\b|\bconstructor\b|\binit\b|\bget\(\)|\bset\()")
CLS = re.compile(r"^(\s*)(?:(?:public|private|internal|protected|abstract|open|final|data|enum|companion|inner|sealed|annotation|value|fun)\s+)*(class|object|interface)\b\s*(\w+)?")
fid = load_fidelity()
JP = f"{JAVA_BIN}/javap"

def enclosing(lines, k, indent):
    chain = []
    for i in range(k, -1, -1):
        m = CLS.match(lines[i])
        if not m or lines[i].lstrip().startswith("//"):
            continue
        ind = len(m.group(1))
        if ind < indent and (not chain or ind < chain[-1][0]):
            name = m.group(3)
            if m.group(2) == "object" and "companion" in lines[i].split("object")[0]:
                name = name or "Companion"
            if name in (None, "" ) or name == "object":
                continue
            chain.append((ind, name))
            if ind == 0:
                break
    return [n for _, n in reversed(chain)]

def failure(lines, i, cls_wall):
    """exception line and first plugin frame of the comment block starting at line i (0-based)"""
    exc = frame = ""
    for l in lines[i:i + 40]:
        t = l.strip().lstrip("/*/ ").strip()
        if not exc and re.match(r"java\.lang\.\w+(Exception|Error)", t):
            exc = t
        if exc and not frame and "org.vineflower.kotlin" in t:
            frame = re.sub(r"^at ", "", t)
            break
    return exc, frame

def javap_blocks(classfile):
    """javap -c -p -l -s split into {(name, descriptor): text}"""
    txt = subprocess.run([JP, "-c", "-p", "-l", "-s", classfile], capture_output=True, text=True).stdout
    blocks, cur, key = {}, [], None
    lines = txt.splitlines()
    for n, l in enumerate(lines):
        if re.match(r"^  \S.*;$", l) and n + 1 < len(lines) and lines[n + 1].strip().startswith("descriptor:"):
            if key: blocks[key] = "\n".join(cur)
            head = l.strip().rstrip(";")
            if "(" in head:
                nm = head.split("(")[0].split()[-1]
            else:
                nm = head.split()[-1]
            key, cur = (nm, lines[n + 1].split("descriptor:")[1].strip()), [l]
        elif key:
            cur.append(l)
    if key: blocks[key] = "\n".join(cur)
    return txt, blocks

def constructs(body):
    c = []
    if re.search(r"\bnew\s+#?\d*\s*// class [\w/$]+\$\d+\b|\bnew\s+#?\d*\s*// class [\w/$]*(\$\$inlined|\$sam\$)", body): c.append("new-anonymous-class")
    if re.search(r"\$i\$f\$", body): c.append("inline-fun-expansion")
    if re.search(r"\$i\$a\$", body): c.append("inline-lambda-body")
    if "invokedynamic" in body: c.append("invokedynamic")
    if "$WhenMappings" in body: c.append("when-enum-mapping")
    if "closeFinally" in body: c.append("use-closeFinally")
    if "$default" in body: c.append("default-args-call")
    if re.search(r"getstatic\s+\S+\s+// Field [\w/$]+\.INSTANCE", body) and "$" in body: c.append("object-instance")
    return c

rows = []
walls = list(csv.DictReader(open(f"{HERE}/../b121/kt-plugin-walls.tsv"), delimiter="\t"))
parsed = {}
for w in walls:
    jar, ktf, line, head = w["jar"], w["kt_file"], int(w["line"]), w["member_head"]
    kt = f"{B121}/vf-kt/{jar}/{ktf}"
    lines = open(kt, encoding="utf8", errors="replace").read().split("\n")
    i = line - 1
    assert "Couldn't be decompiled" in lines[i], (kt, line)
    k = i
    while k > 0 and not HDR.search(lines[k]): k -= 1
    hdr = lines[k]
    indent = len(hdr) - len(hdr.lstrip())
    pkg = next(re.match(r"package (\S+)", l).group(1) for l in lines if l.startswith("package "))
    stem = os.path.basename(ktf)[:-3]
    chain = enclosing(lines, k, indent) or [stem]
    cls = pkg.replace(".", "/") + "/" + "$".join(chain)
    exc, frame = failure(lines, i, False)
    m = re.match(r"\s*(?:[\w ]*?)\bfun\s+(?:<[^>]*>\s*)?(?:([\w.<>?, *]+?)\.)?(\w+)\s*\(", hdr)
    if m: kname, ext = m.group(2), bool(m.group(1))
    elif "get()" in hdr or "set(" in hdr:
        pj = k
        while pj > 0 and not re.search(r"\b(val|var)\s+\w+", lines[pj]): pj -= 1
        pn = re.search(r"\b(?:val|var)\s+(\w+)", lines[pj]).group(1)
        kname, ext = ("get" if "get()" in hdr else "set") + pn[0].upper() + pn[1:], False
    else:
        raise SystemExit(f"unparsed header {hdr!r} in {kt}:{k+1}")
    ar = re.search(r"/(\d+)$", head)
    arity = int(ar.group(1)) if ar else 0
    cf = f"{extracted(jar)}/{cls}.class"
    if not os.path.isfile(cf):
        rows.append(dict(wall_id=f"{jar}:{ktf}:{line}", jar=jar, cls=cls, method=kname, desc="?", kt_file=ktf, kt_line=line, exc=exc, frame=frame, constructs="", note="class-file-not-found")); continue
    if cf not in parsed:
        cls_txt = fid.parse_javap_verbose(subprocess.run([JP, "-v", "-p", cf], capture_output=True, text=True).stdout)
        parsed[cf] = (cls_txt["methods"],) + javap_blocks(cf)
    methods, _txt, blocks = parsed[cf]
    def nparams(desc):
        a = re.sub(r"L[^;]*;", "X", desc[1:desc.index(")")]); return len(a.replace("[", ""))
    cands = [(nm, desc) for (nm, desc), md in methods.items()
             if "ACC_SYNTHETIC" not in md["flags"] and "ACC_BRIDGE" not in md["flags"]
             and (nm == kname or (nm.startswith(kname + "$") and "lambda" not in nm and "default" not in nm))]
    fit = [c for c in cands if nparams(c[1]) in (arity, arity + 1)] or cands
    # disambiguate overloads by the simple type names printed in the .kt header (first param line only)
    ptxt = hdr[hdr.index("(") + 1:] if "(" in hdr else ""
    PRIM = {"Int": "I", "Boolean": "Z", "Long": "J", "Double": "D", "Float": "F", "Char": "C", "Short": "S", "Byte": "B"}
    def typeok(desc):
        for t in re.findall(r":\s*([A-Z]\w*)", ptxt.split(")")[0]):
            if not (("/" + t + ";") in desc or "$" + t + ";" in desc or (t in PRIM and PRIM[t] in desc)
                    or (t == "Function1" and "Function1" in desc)): return False
        return True
    fit = [c for c in fit if typeok(c[1])] or fit
    for nm, desc in fit:
        rows.append(dict(wall_id=f"{jar}:{ktf}:{line}", jar=jar, cls=cls, method=nm, desc=desc, kt_file=ktf, kt_line=line, exc=exc, frame=frame,
                         constructs=",".join(constructs(blocks.get((nm, desc), ""))),
                         note="ambiguous" if len(fit) > 1 else ""))
    if not fit:
        rows.append(dict(wall_id=f"{jar}:{ktf}:{line}", jar=jar, cls=cls, method=kname, desc="?", kt_file=ktf, kt_line=line, exc=exc, frame=frame, constructs="", note="no-jvm-candidate"))

# class walls
for jar in JARS:
    base = f"{B121}/vf-kt/{jar}"
    for r, _d, fs in os.walk(base):
        for f in fs:
            p = os.path.join(r, f)
            if not f.endswith(".kt"): continue
            lines = open(p, encoding="utf8", errors="replace").read().split("\n")
            if any("Unable to decompile class" in l for l in lines[:6]):
                rel = os.path.relpath(p, base)[:-3]
                exc, frame = failure(lines, 0, True)
                rows.append(dict(wall_id=f"{jar}:{rel}.kt:class", jar=jar, cls=rel, method="*", desc="*", kt_file=rel + ".kt", kt_line=2, exc=exc, frame=frame, constructs="", note="class-wall"))

cols = ["wall_id", "jar", "cls", "method", "desc", "kt_file", "kt_line", "exc", "frame", "constructs", "note"]
with open(f"{OUT}/wall-sites-map.tsv", "w") as fh:
    fh.write("\t".join(cols) + "\n")
    for r in sorted(rows, key=lambda r: (r["jar"], r["cls"], r["method"], r["desc"])):
        fh.write("\t".join(str(r[c]) for c in cols) + "\n")
print(len(rows), "rows")
