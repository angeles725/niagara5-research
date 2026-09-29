#!/usr/bin/env python3
"""B120 per-site grader: does each decompiled tree render each pattern-switch method faithfully?

Ground truth = the shipped class (organized/<mod>/extracted).  For every top-level class that holds a
typeSwitch/enumSwitch indy site or a `new java/lang/MatchException` (input: census-switch.json), and for each
tree in {v1=vineflower, v2=vineflower2, cons=vineflower-cons, cfr (CFR 0.152), procyon (Procyon 0.6.0)}:
  1. take the tree's top-level .java (CFR/Procyon are run here on the shipped top-level class);
  2. recompile it with javac 25 (--release 25 -g) against the jar-mirror classpath;
  3. compare, per switch-bearing method, the NORMALIZED bytecode (tools/n5-fidelity.py functions, imported,
     not modified) of shipped vs recompiled.  Bootstrap-method arguments (= the case-label list, whose ORDER is
     semantic) are injected into the indy line first, because n5-fidelity's normalizer drops constant-pool
     indices and would otherwise never see them.
Verdicts per (class, method, tree):
  exact        normalized code identical (labels+order, guard restart loop, MatchException default all match)
  no-compile   javac rejected the tree's file (errors kept; `switch_related` when an error line lies in the
               method's line span in the decompiled file)
  mismatch     compiled, method code differs (label-diff / matchexc-diff / other, with first differing line)
  missing      recompiled class or method absent
plus `pseudo` = the tree's text contains SwitchBootstraps / typeSwitch< / invokedynamic(!) / ProcyonInvokeDynamic.
Usage: grade_sites.py --scratch DIR [--jobs N] [--only SUBSTR] [--out grades.json]
"""
import argparse, concurrent.futures, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
spec = importlib.util.spec_from_file_location("n5f", REPO / "tools" / "n5-fidelity.py")
n5f = importlib.util.module_from_spec(spec)
sys.modules["n5f"] = n5f
spec.loader.exec_module(n5f)

ORG = Path("/home/cristian/niagara5-research/organized")
MIRROR = Path("/home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28")
JAVAC = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"
JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"
JAVA = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/java"
DEC = ORG.parent / "tools" / "decompilers"
CFR = DEC / "cfr-0.152.jar"
PROCYON = DEC / "procyon-decompiler-0.6.0.jar"
SHIM = [None]
SYSTEM = [None]
SYSTEM_JRE = "/mnt/c/Program Files/Niagara/5.0.0.28/jre"
TREES = {"v1": "vineflower", "v2": "vineflower2", "cons": "vineflower-cons"}
PSEUDO_RE = re.compile(r"SwitchBootstraps|typeSwitch<|invokedynamic\(!\)|ProcyonInvokeDynamic|\$VF|Couldn't be decompiled|<unrepresentable>")

INDY_RE = re.compile(r"(//\s*InvokeDynamic\s+#(\d+):)")


def annotated_javap(classfile):
    """javap -c -p -v text with SwitchBootstraps arguments appended to each indy comment."""
    text = subprocess.run([JAVAP, "-c", "-p", "-v", str(classfile)], capture_output=True, text=True, timeout=120).stdout
    lines = text.splitlines()
    bsm, cur, in_b = {}, None, False
    for ln in lines:
        if ln.startswith("BootstrapMethods:"):
            in_b = True
            continue
        if not in_b:
            continue
        m = re.match(r"^\s+(\d+): #\d+ REF_invokeStatic (\S+)", ln)
        if m:
            cur = int(m.group(1))
            bsm[cur] = {"bsm": m.group(2), "args": []}
        elif cur is not None and re.match(r"^\s{6}#\d+ ", ln):
            bsm[cur]["args"].append(re.sub(r"^\s*#\d+ ", "", ln).strip())
        elif ln and not ln.startswith(" "):
            in_b = False
    out = []
    for ln in lines:
        m = INDY_RE.search(ln)
        if m and int(m.group(2)) in bsm and "SwitchBootstraps" in bsm[int(m.group(2))]["bsm"]:
            ln = ln + " ARGS[" + " | ".join(bsm[int(m.group(2))]["args"]) + "]"
        out.append(ln)
    return "\n".join(out) + "\n", bsm


def parsed(classfile):
    text, bsm = annotated_javap(classfile)
    return n5f.parse_javap_verbose(text), bsm


def switch_methods(p):
    """Methods of a parsed class that contain a switch indy or MatchException."""
    keys = []
    for k, v in p["methods"].items():
        code = "\n".join(v["code"])
        if "SwitchBootstraps" in code or "ARGS[" in code or "MatchException" in code or ":typeSwitch:" in code or ":enumSwitch:" in code:
            keys.append(k)
    return keys


def classpath(cache):
    """n5-fidelity's classpath (top-level module + bin-ext jars + nested LIB-INF) plus the bin-ext SUBDIRECTORY
    jars (bcfips, bcstd, jxbrowser, ...) that its top-level glob does not reach (CertUtils needs bouncycastle)."""
    base = n5f.build_classpath(Path(cache), MIRROR / "modules", MIRROR / "bin-ext")
    extra = sorted(str(p) for p in (MIRROR / "bin-ext").glob("*/*.jar"))
    return base + ":" + ":".join(extra)


SHIM_SRC = """package b120shim;
import niagara.nre.security.privileged.*;
/** Overload-pinning shim: Vineflower drops the explicit target typing that made the original
 *  SecurityUtil.doPrivileged(<lambda>) call unambiguous (B116 defect family `reference to doPrivileged is
 *  ambiguous`).  Pin the overload so the REST of the file compiles; only switch-bearing methods are compared. */
public final class B120Shim {
  public static <T> T pea(PrivilegedExceptionAction<T> a) throws PrivilegedActionException { throw new Error(); }
  public static <T> T pa(PrivilegedAction<T> a) { throw new Error(); }
  public static <T, E extends Exception> T psea(PrivilegedSingleExceptionAction<T, E> a) throws E { throw new Error(); }
}
"""


def build_shim(scratch, cp):
    d = Path(scratch) / "shim"
    (d / "src" / "b120shim").mkdir(parents=True, exist_ok=True)
    (d / "classes").mkdir(exist_ok=True)
    f = d / "src" / "b120shim" / "B120Shim.java"
    f.write_text(SHIM_SRC)
    subprocess.run([JAVAC, "--release", "25", "-nowarn", "-proc:none", "-d", str(d / "classes"), "-cp", cp, str(f)], check=True, capture_output=True)
    return str(d / "classes")


def variant_order(ship, targets):
    """Shim variants ordered by how often the shipped bytecode calls that doPrivileged overload."""
    cnt = {"pea": 0, "pa": 0, "psea": 0}
    for t0 in targets:
        for k, v in ship[t0][0]["methods"].items():
            for l in v["code"]:
                if "SecurityUtil.doPrivileged" in l or "SecurityUtil.\"doPrivileged\"" in l:
                    if "privileged/PrivilegedExceptionAction" in l:
                        cnt["pea"] += 1
                    elif "privileged/PrivilegedAction" in l:
                        cnt["pa"] += 1
                    elif "PrivilegedSingleExceptionAction" in l:
                        cnt["psea"] += 1
    return sorted(cnt, key=lambda x: -cnt[x])


def compile_tree(java_file, cp, out_dir, system=None):
    os.makedirs(out_dir, exist_ok=True)
    rel = ["--system", system] if system else ["--release", "25"]
    cmd = [JAVAC] + rel + ["-g", "-implicit:none", "-proc:none", "-nowarn", "-encoding", "UTF-8", "-Xmaxerrs", "20", "-d", str(out_dir), "-cp", cp, str(java_file)]
    try:
        pr = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return False, ["timeout"]
    errs = [l.strip() for l in pr.stderr.splitlines() if "error:" in l]
    return pr.returncode == 0, errs[:8]


def method_line_spans(java_text, name):
    """Very rough: line numbers (1-based) of declarations of method `name(`; span = to next decl-ish line."""
    spans = []
    lines = java_text.splitlines()
    for i, l in enumerate(lines):
        if re.search(r"\b" + re.escape(name) + r"\s*\(", l) and re.search(r"\)\s*(throws [\w., ]+)?\s*\{\s*$", l) and not l.strip().startswith(("return", "if", "for", "while", "switch", "else")):
            depth, j = 0, i
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth <= 0 and j >= i:
                    break
                j += 1
            spans.append((i + 1, j + 1))
    return spans


EFFECT_RE = re.compile(r"^insn\d+: (invoke\w+|new|checkcast|instanceof|getfield|putfield|getstatic|putstatic|athrow|ldc\w*|anewarray|tableswitch|lookupswitch)\b")


def effects(code):
    """Side-effecting / type-testing instruction stream, ignoring branch layout, loads/stores and offsets."""
    out = []
    for l in code:
        if EFFECT_RE.match(l):
            l = re.sub(r"^insn\d+: ", "", l)
            l = re.sub(r"\{.*", lambda m: "{" + ",".join(x.split(":")[0].strip() for x in m.group(0).strip("{}").split(",") if not x.strip().startswith("default")) + "}", l)
            out.append(l)
    return out


def effect_diff(a_code, b_code):
    """[] when both methods perform the same effect sequence; else list of ('-shipped'|'+recompiled', insn)."""
    import difflib
    ea, eb = effects(a_code), effects(b_code)
    if ea == eb:
        return []
    from collections import Counter
    if Counter(ea) == Counter(eb):
        return ["PERMUTED: same effect multiset in a different order (arm/branch layout)"]
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ea, eb, autojunk=False).get_opcodes():
        if tag != "equal":
            ops += [("-" + x) for x in ea[i1:i2]] + [("+" + x) for x in eb[j1:j2]]
    return ops


def classify_diff(a_code, b_code):
    strip = lambda l: re.sub(r"^insn\d+: ", "", l)
    a_ind = [strip(l) for l in a_code if "ARGS[" in l]
    b_ind = [strip(l) for l in b_code if "ARGS[" in l]
    a_me = sum("MatchException" in l for l in a_code)
    b_me = sum("MatchException" in l for l in b_code)
    kinds = []
    if a_me != b_me:
        kinds.append("matchexc-diff")
    if not kinds:
        kinds.append("other")
    kinds.append("labels-equal" if a_ind == b_ind else "labels-DIFFER")
    first = next(((x, y) for x, y in zip(a_code, b_code) if x != y), (None, None))
    if first[0] is None and len(a_code) != len(b_code):
        first = (f"len {len(a_code)}", f"len {len(b_code)}")
    ed = effect_diff(a_code, b_code)
    kinds.append("effects-equal" if not ed else "effects-DIFFER")
    return "+".join(kinds), first, ed[:8]


def decompile_other(tool, top_class, dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if tool == "cfr":
        cmd = [JAVA, "-jar", str(CFR), str(top_class), "--outputdir", str(dest), "--silent", "true"]
    else:
        cmd = [JAVA, "-jar", str(PROCYON), "-o", str(dest), str(top_class)]
    subprocess.run(cmd, capture_output=True, text=True, timeout=240)


def grade_unit(unit, scratch, cp):
    mod, top_rel, targets = unit["mod"], unit["top_rel"], unit["targets"]  # top_rel like com/x/Y (no ext)
    ext = ORG / mod / "extracted"
    ship = {t: parsed(ext / (t + ".class")) for t in targets}
    res = {}
    for tree in ["v1", "v2", "cons", "cfr", "procyon"]:
        if tree in TREES:
            src = ORG / mod / TREES[tree] / (top_rel + ".java")
        else:
            d = Path(scratch) / "dec" / tree / mod.replace("/", "_")
            if not (d / (top_rel + ".java")).exists():
                decompile_other(tree, ext / (top_rel + ".class"), d)
            src = d / (top_rel + ".java")
        if not src.exists():
            res[tree] = {"status": "no-source"}
            continue
        text = src.read_text(errors="replace")
        if not text.strip():
            res[tree] = {"status": "empty-output", "pseudo": [], "compiled": False}
            continue
        pseudo = sorted(set(PSEUDO_RE.findall(text)))
        out = Path(scratch) / "rc" / tree / mod.replace("/", "_") / top_rel.replace("/", "_")
        shutil.rmtree(out, ignore_errors=True)
        ok, errs = compile_tree(src, cp, out)
        entry = {"pseudo": pseudo, "compiled": ok}
        if not ok and any("doPrivileged is ambiguous" in e for e in errs) and SHIM[0]:
            order = variant_order(ship, targets)
            for variant in order:
                patched = Path(scratch) / "patched" / tree / mod.replace("/", "_") / (top_rel + ".java")
                patched.parent.mkdir(parents=True, exist_ok=True)
                patched.write_text(text.replace("SecurityUtil.doPrivileged(", f"b120shim.B120Shim.{variant}("))
                shutil.rmtree(out, ignore_errors=True)
                ok2, errs2 = compile_tree(patched, SHIM[0] + ":" + cp, out)
                if ok2:
                    ok, errs = True, []
                    entry["compiled"] = True
                    entry["shim"] = variant
                    break
            else:
                entry["shim"] = "failed"
        if not ok and SYSTEM[0] and any("javafx" in e or "cannot find symbol" in e for e in errs):
            shutil.rmtree(out, ignore_errors=True)
            ok3, errs3 = compile_tree(src, cp, out, system=SYSTEM[0])
            if ok3:
                ok, errs = True, []
                entry["compiled"] = True
                entry["system"] = SYSTEM[0]
        if not ok:
            entry["errors"] = errs
            entry["status"] = "no-compile"
            res[tree] = entry
            continue
        entry["methods"] = {}
        for t in targets:
            cand = out / (t + ".class")
            if not cand.exists():
                entry["methods"][t] = {"*": {"verdict": "missing", "why": "recompiled class absent"}}
                continue
            rp, _ = parsed(cand)
            sp, _ = ship[t]
            for k in switch_methods(sp):
                key = f"{k[0]}{k[1]}"
                if k not in rp["methods"]:
                    entry["methods"].setdefault(t, {})[key] = {"verdict": "missing", "why": "method absent"}
                    continue
                a, b = sp["methods"][k], rp["methods"][k]
                bcode = [re.sub(r"b120shim/B120Shim\.(pea|pa|psea):", "niagara/nre/util/SecurityUtil.doPrivileged:", l) for l in b["code"]]
                b = dict(b, code=bcode)
                same = a["code"] == b["code"] and a["flags"] == b["flags"] and a.get("exception_table", []) == b.get("exception_table", [])
                shim_only = (not same and entry.get("shim") and len(a["code"]) == len(b["code"]) and a["flags"] == b["flags"]
                             and all("doPrivileged" in x and "doPrivileged" in y for x, y in zip(a["code"], b["code"]) if x != y)
                             and a.get("exception_table", []) == b.get("exception_table", []))
                if same or shim_only:
                    entry["methods"].setdefault(t, {})[key] = {"verdict": "exact"} if same else {"verdict": "exact", "note": "differs only in doPrivileged overload descriptor (shim artifact)"}
                else:
                    kind, first, ed = classify_diff(a["code"], b["code"])
                    entry["methods"].setdefault(t, {})[key] = {"verdict": "mismatch", "kind": kind, "first_diff": first, "effect_diff": ed}
        entry["status"] = "compiled"
        res[tree] = entry
    return {"unit": unit, "trees": res}


def load_units(census, only=None):
    c = json.load(open(census))
    classes = {}
    for grp in ("typeSwitch_sites", "enumSwitch_sites"):
        for s in c[grp]:
            classes.setdefault(s["class"], set()).add(grp)
    for m in c["matchexception_classes"]:
        classes.setdefault(m["class"], set()).add("matchexception")
    units = {}
    for cl, grps in classes.items():
        parts = cl.split("/")
        i = parts.index("extracted")
        mod = "/".join(parts[:i])
        rel = "/".join(parts[i + 1:])[:-6]
        top = rel.split("$")[0]
        u = units.setdefault((mod, top), {"mod": mod, "top_rel": top, "targets": [], "groups": set()})
        u["targets"].append(rel)
        u["groups"] |= grps
    out = []
    for u in units.values():
        u["groups"] = sorted(u["groups"])
        if only and not any(o in u["top_rel"] for o in only.split(",")):
            continue
        out.append(u)
    return sorted(out, key=lambda u: (u["mod"], u["top_rel"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--census", default=str(HERE / "census-switch.json"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", help="comma-separated substrings of the top-level class path")
    ap.add_argument("--out", default=str(HERE / "grades.json"))
    a = ap.parse_args()
    cp = classpath(Path(a.scratch) / "cp")
    SHIM[0] = build_shim(a.scratch, cp)
    niagara_jre = Path("/mnt/c/Program Files/Niagara/5.0.0.28/jre")
    if niagara_jre.is_dir():
        SYSTEM[0] = str(niagara_jre)
    units = load_units(a.census, a.only)
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda u: grade_unit(u, a.scratch, cp), units))
    json.dump(results, open(a.out, "w"), indent=1, default=list)
    print("units", len(results), "->", a.out)


if __name__ == "__main__":
    main()
