#!/usr/bin/env python3
"""B125 step 2: recompile the Java-mode Vineflower output of every wall class with javac and grade each wall method
(or, for a whole-class wall, every method of the class) against the shipped bytecode with the tools/n5-fidelity.py normalizer
and the tools/n5_canon.py canonical comparison (imported from the frozen snapshot, unmodified).
Method grades: exact | equivalent (width allowlist) | canonical | canonical-t2 | anon-name-only (differs only in the names of
synthetic anonymous classes) | mismatch | missing (method absent in the recompiled class) | no-compile.
Usage: grade_sites.py <wall-sites-map.tsv> <out.tsv> [jobs<=4]"""
import concurrent.futures as cf, csv, glob, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b125_lib import *
fid = load_fidelity()
JAVAC, JAVAP = f"{JAVA_BIN}/javac", f"{JAVA_BIN}/javap"
GRADLE_API = os.environ.get("GRADLE_API_JAR", "/home/cristian/.gradle/caches/9.2.1/generated-gradle-jars/gradle-api-9.2.1.jar")
LIBS = sorted(glob.glob(f"{ORG}/_v2-libcache/*.jar"))
GRADLE_LIB = os.path.dirname(GRADLE_API).replace("caches", "wrapper/dists").split("/wrapper")[0]
M2 = "/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository"
EXTRA = sorted(glob.glob(f"{ORG}/_etc-m2/*/extracted")) + sorted(glob.glob(f"{ORG}/_lib/*/extracted")) \
        + glob.glob(os.path.expanduser("~/.gradle/wrapper/dists/gradle-9.2.1-bin/*/gradle-9.2.1/lib/groovy-4*.jar")) \
        + sorted(glob.glob(f"{M2}/**/*.jar", recursive=True))
CP = ":".join([extracted(j) for j in JARS] + [GRADLE_API] + LIBS + [p for p in EXTRA if p not in [extracted(j) for j in JARS]])
BUCKETS = [("placeholder-syntax", r"illegal start of|expected"), ("anon-not-implementing", r"is not abstract and does not override"),
           ("classpath-missing", r"package .* does not exist|symbol:\s+class"), ("synthetic-class-reference", r"cannot access"), ("companion-ctor", r"constructor Companion"),
           ("enclosing-instance", r"enclosing instance"), ("synthetic-symbol", r"cannot find symbol|no suitable method"),
           ("incompatible-types", r"incompatible types|cannot be converted")]
def buckets(stderr):
    from collections import Counter
    c = Counter()
    for l in stderr.splitlines():
        if "error:" in l:
            c[next((b for b, rx in BUCKETS if re.search(rx, l)), "other")] += 1
    return ";".join(f"{k}:{v}" for k, v in sorted(c.items()))
WORK = tempfile.mkdtemp(prefix="b125-javac-")
ANON = re.compile(r"[\w/]+\$[\w$]*?(?:\$\d+|inlined[\w$]*|\$sam\$[\w$]*)(?![\w])")

def norm_anon(lines):
    return [ANON.sub("ANON", l) for l in lines]

def javap_parsed(classfile):
    out = subprocess.run([JAVAP, "-v", "-p", classfile], capture_output=True, text=True, timeout=120).stdout
    return fid.parse_javap_verbose(out)

PATCH = os.environ.get("B125_PATCH_UNREP") == "1"   # probe: replace each `<unrepresentable>` placeholder by `null` before javac
UNREP = re.compile(r"<unrepresentable>(?:::[\w$]+|\.INSTANCE)?")
_compiled = {}
def compile_top(jar, cls):
    top = cls.split("$")[0]
    jf = f"{EV}/java-mode/{jar}/{cls}.java"
    if not os.path.isfile(jf):
        jf = f"{EV}/java-mode/{jar}/{top}.java"
    if jf in _compiled: return _compiled[jf]
    out = tempfile.mkdtemp(dir=WORK)
    if PATCH:
        pd = tempfile.mkdtemp(dir=WORK); pf = os.path.join(pd, os.path.basename(jf))
        open(pf, "w").write(UNREP.sub("null", open(jf, encoding="utf8", errors="replace").read()))
        jf_src = pf
    else:
        jf_src = jf
    r = subprocess.run([JAVAC, "--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn", "-d", out, "-cp", CP, jf_src],
                       capture_output=True, text=True, timeout=300)
    err = next((l for l in r.stderr.splitlines() if "error:" in l), "") if r.returncode else ""
    err = re.sub(r"^.*(/java-mode/|/b125-javac-[^/]*/[^/]*/)", "", err)[:200]
    # classpath errors show up as "symbol: class X" on the line after "cannot find symbol"
    _compiled[jf] = (jf, out if r.returncode == 0 else None, err, r.stderr.count("error:"), buckets(re.sub(r"error: cannot find symbol\n(?:.*\n)*?\s+symbol:\s+class", "error: symbol: class", r.stderr)))
    return _compiled[jf]

def grade_method(a, b):
    """a shipped, b recompiled method record -> (grade, rules)"""
    if (a["flags"] == b["flags"] and a["code"] == b["code"] and a["exceptions"] == b["exceptions"]
            and a.get("exception_table", []) == b.get("exception_table", [])
            and a.get("has_method_parameters", False) == b.get("has_method_parameters", False)):
        return "exact", []
    body_only = a["flags"] == b["flags"] and a["exceptions"] == b["exceptions"]
    if body_only:
        if any(e.predicate(a["code"], b["code"]) for e in fid.ALLOWLIST):
            return "equivalent", []
        rules = fid._canonical_resolution({"body_only": True, "a_method": a, "b_method": b})
        if rules is not None:
            return ("canonical-t2" if set(rules) & set(fid.n5_canon.TIER2_RULES) else "canonical"), rules
        if norm_anon(a["code"]) == norm_anon(b["code"]) and a.get("exception_table") == b.get("exception_table"):
            return "anon-name-only", []
    return "mismatch", []

def site(row):
    jar, cls, meth, desc = row["jar"], row["cls"], row["method"], row["desc"]
    res = dict(row)
    jf, out, err, nerr, kinds = compile_top(jar, cls)
    res.update(java_file=os.path.relpath(jf, ORG), compile_errors=nerr, error_kinds=kinds, first_error=err)
    if out is None:
        res.update(grade="no-compile", class_grade="no-compile", m_total=0, m_exact=0, m_canon=0, m_anon=0, m_mismatch=0, m_missing=0, rules="")
        return res
    cands = glob.glob(f"{out}/**/{cls.split('/')[-1]}.class", recursive=True)
    if not cands:
        res.update(grade="missing-class", class_grade="missing-class", m_total=0, m_exact=0, m_canon=0, m_anon=0, m_mismatch=0, m_missing=0, rules="")
        return res
    A = javap_parsed(f"{extracted(jar)}/{cls}.class"); B = javap_parsed(cands[0])
    diff = fid.diff_normalized_classes(A, B)
    res["class_grade"] = fid.grade_class_result(True, diff, None)["grade"]
    keys = [(meth, desc)] if meth != "*" else sorted(A["methods"])
    cnt = dict(exact=0, canon=0, anon=0, mismatch=0, missing=0); rules = set(); grades = []
    for k in keys:
        if k not in B["methods"]:
            g = "missing"
        else:
            g, rl = grade_method(A["methods"][k], B["methods"][k]); rules.update(rl)
        grades.append(g)
        cnt["exact" if g in ("exact", "equivalent") else "canon" if g.startswith("canonical") else "anon" if g == "anon-name-only" else g] += 1
    res.update(grade=grades[0] if meth != "*" else "class:" + res["class_grade"], m_total=len(keys), m_exact=cnt["exact"], m_canon=cnt["canon"],
               m_anon=cnt["anon"], m_mismatch=cnt["mismatch"], m_missing=cnt["missing"], rules=",".join(sorted(rules)))
    return res

if __name__ == "__main__":
    rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
    jobs = min(int(sys.argv[3]) if len(sys.argv) > 3 else 4, 4)
    # compile each top-level file once first (<=4 concurrent javac), then grade
    tops = sorted({(r["jar"], r["cls"]) for r in rows})
    with cf.ThreadPoolExecutor(jobs) as ex:
        list(ex.map(lambda t: compile_top(*t), tops))
    results = [site(r) for r in rows]
    cols = ["wall_id", "jar", "cls", "method", "desc", "java_file", "compile_errors", "error_kinds", "first_error", "grade", "class_grade", "m_total", "m_exact", "m_canon", "m_anon", "m_mismatch", "m_missing", "rules"]
    with open(sys.argv[2], "w") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in results:
            fh.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    print(json.dumps({g: sum(1 for r in results if r["grade"] == g) for g in sorted({r["grade"] for r in results})}))
