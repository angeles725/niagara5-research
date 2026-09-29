#!/usr/bin/env python3
"""B125 step 3c/4: assemble evidence/b125/wall-sites.tsv (the durable index) and the failure-kind tally.
Inputs (all in this directory): wall-sites-map.tsv, java-grades.tsv (raw recompile), java-grades-patched.tsv (placeholders -> null probe),
java-body-metrics.tsv. Also writes javap -c -p -l -s ground truth per wall class to organized/_evidence/b125/javap/<jar>/<class>.javap.txt.
Usage: build_index.py   (run from evidence/b125)"""
import csv, collections, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b125_lib import *
JAVAP = f"{JAVA_BIN}/javap"
rd = lambda f: list(csv.DictReader(open(f), delimiter="\t"))
sites, raw, pat, jbm = rd("wall-sites-map.tsv"), rd("java-grades.tsv"), rd("java-grades-patched.tsv"), rd("java-body-metrics.tsv")
key = lambda r: (r["jar"], r["cls"], r["method"], r["desc"])
keyd = lambda r: (r["jar"], r["cls"], r["method"], r["desc"] if "desc" in r else r["descriptor"])
raw, pat, jbm = ({key(r): r for r in t} for t in (raw, pat, jbm))
_jp = {}
def javap_file(jar, cls):
    p = f"{EV}/javap/{jar}/{cls}.javap.txt"
    if (jar, cls) not in _jp:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        txt = subprocess.run([JAVAP, "-c", "-p", "-l", "-s", f"{extracted(jar)}/{cls}.class"], capture_output=True, text=True).stdout
        open(p, "w").write(txt); _jp[(jar, cls)] = txt
    return p, _jp[(jar, cls)]

def block(txt, name, desc):
    lines, out, on = txt.splitlines(), [], False
    for n, l in enumerate(lines):
        if re.match(r"^  \S", l):
            on = n + 1 < len(lines) and lines[n + 1].strip() == f"descriptor: {desc}" and (name + "(") in l
        if on: out.append(l)
    return "\n".join(out)

def trigger(body, meth):
    """what the failing anonymous-class expression is, from the classes the shipped method instantiates/loads"""
    news = set(re.findall(r"(?:new|getstatic\s+#?\d*)\s+#?\d*\s*// (?:class|Field) ([\w/$]+)", body))
    news |= set(re.findall(r"// (?:class|Field) ([\w/$]+)\$[\w$]*\.INSTANCE", body))
    names = {n for n in re.findall(r"[\w/]+\$[\w$]+", body) if re.search(r"\$\d+$|inlined|\$sam\$", n)}
    tags = []
    if any("$sam$" in n for n in names): tags.append("sam-wrapper")
    if any("$inlined$" in n and "$sam$" not in n for n in names): tags.append("inline-fun-object")
    if any(re.search(r"\$\d+$", n) and "inlined" not in n for n in names): tags.append("lambda-class")
    if "invokedynamic" in body: tags.append("indy-lambda")
    if "lambda$" in body: tags.append("lambda-body-method")
    return tags

out_rows, tally, tri = [], collections.Counter(), collections.Counter()
for r in sites:
    k = key(r); jar, cls, name, desc = r["jar"], r["cls"], r["method"], r["desc"]
    jp, jtxt = javap_file(jar, cls)
    body = jtxt if name == "*" else block(jtxt, name, desc)
    tags = trigger(body, name) if r["note"] != "class-wall" else []
    exc = re.sub(r"^java\.lang\.", "", r["exc"].split(":")[0]) + (": anonymous-class-without-metadata" if "Anonymous" in r["exc"] else (": " + r["exc"].split(":", 1)[1].strip()[:40] if ":" in r["exc"] else ""))
    fk = f"{exc} @ {re.sub(r'^org.vineflower.kotlin.', '', r['frame']).split('(')[0]}"
    g, p, m = raw[k], pat[k], jbm[k]
    # best representation: javap -c is the only verified one (no Java-mode class recompiles); the Java-mode text is the readable companion
    java_ok = g["grade"] in ("exact", "equivalent", "canonical", "canonical-t2")
    best_kind, best_path = ("java-mode", m["jm_file"]) if java_ok else ("javap", os.path.relpath(jp, ORG))
    readable = m["jm_file"] if (m["jm_line"] or name == "*") and m["jm_unrep"] == "0" else ""
    meta = f"_evidence/b121/kotlin-signatures/{jar}/{cls.split('$')[0]}.kt.txt"
    meta = meta if os.path.exists(f"{ORG}/{meta}") else ""
    kt = f"_evidence/b121/vf-kt/{jar}/{r['kt_file']}"
    out_rows.append(dict(wall_id=r["wall_id"], jar=jar, cls=cls, method=name, descriptor=desc, plugin_failure_kind=fk,
        trigger=",".join(tags) or "-", constructs=r["constructs"] or "-", java_grade=g["grade"], java_error_kinds=g["error_kinds"] or "-",
        m_total=g["m_total"], m_exact=g["m_exact"], m_canon=g["m_canon"], m_anon=g["m_anon"], m_mismatch=g["m_mismatch"], m_missing=g["m_missing"],
        patched_grade=p["grade"], patched_error_kinds=p["error_kinds"] or "-", jm_unrep=m["jm_unrep"], ldc_cov=f"{m['ldc_found']}/{m['ldc_total']}",
        inv_cov=f"{m['inv_found']}/{m['inv_total']}", best_representation=best_kind, best_path=best_path,
        best_sha256=sha256_file(f"{ORG}/{best_path}"), readable_companion=readable or "-", metadata_path=meta or "-",
        plugin_kt_path=kt, javap_path=os.path.relpath(jp, ORG)))
cols = list(out_rows[0])
with open("wall-sites.tsv", "w") as fh:
    fh.write("\t".join(cols) + "\n")
    for o in out_rows: fh.write("\t".join(o[c] for c in cols) + "\n")
print(len(out_rows), "rows;", len({o["wall_id"] for o in out_rows}), "wall ids")
