#!/usr/bin/env python3
"""B120 census: pattern-switch (typeSwitch / enumSwitch indy) sites and MatchException classes.

Scope = the B116 §116.6 scope: every .class under organized/*/extracted and organized/_bin-ext/*/extracted
(docSource excluded).  Two-stage, no trust in earlier counts:
  1. cheap byte prefilter: class bytes containing the UTF8 constant b'typeSwitch' / b'enumSwitch' /
     b'java/lang/MatchException';
  2. `javap -c -p -v` of each candidate: count `invokedynamic` instructions whose BootstrapMethods entry is
     java/lang/runtime/SwitchBootstraps.{typeSwitch,enumSwitch}, and classes whose constant pool holds a
     Class entry java/lang/MatchException (and whether `new java/lang/MatchException` is executed).
Usage: census_switch.py [organized_dir] [--javap PATH] [--out census-switch.json]
"""
import glob, json, os, re, subprocess, sys

JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"


def class_files(org):
    dirs = glob.glob(f"{org}/*/extracted") + glob.glob(f"{org}/_bin-ext/*/extracted")
    for d in sorted(dirs):
        if "/docSource/" in d:
            continue
        for root, _, fs in os.walk(d):
            for f in sorted(fs):
                if f.endswith(".class"):
                    yield os.path.join(root, f)


def javap_v(path, javap=JAVAP):
    return subprocess.run([javap, "-c", "-p", "-v", path], capture_output=True, text=True, timeout=120).stdout


BSM_RE = re.compile(r"^\s+(\d+): #\d+ REF_invokeStatic java/lang/runtime/SwitchBootstraps\.(typeSwitch|enumSwitch):")
INDY_RE = re.compile(r"invokedynamic #(\d+),\s+0\s+// InvokeDynamic #(\d+):(\w+):(.*)")


def analyse(text):
    """Return (bsm_kind_by_index, sites[(method, kind, bsm_idx, name, desc)], matchexc_class, matchexc_new)."""
    bsm = {}
    in_bsm = False
    for line in text.splitlines():
        if line.startswith("BootstrapMethods:"):
            in_bsm = True
            continue
        if in_bsm:
            m = BSM_RE.match(line)
            if m:
                bsm[int(m.group(1))] = m.group(2)
    sites, method = [], None
    for line in text.splitlines():
        if re.match(r"^  \S.*\(.*\).*;$", line) or re.match(r"^  static \{\};", line):
            method = line.strip()
        m = INDY_RE.search(line)
        if m and int(m.group(2)) in bsm:
            sites.append((method, bsm[int(m.group(2))], int(m.group(2)), m.group(3), m.group(4).strip()))
    has_cls = bool(re.search(r"= Class\s+#\d+\s+// java/lang/MatchException", text))
    has_new = bool(re.search(r"new\s+#\d+\s+// class java/lang/MatchException", text))
    return bsm, sites, has_cls, has_new


def main(argv):
    org = "/home/cristian/niagara5-research/organized"
    out = "census-switch.json"
    javap = JAVAP
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--javap":
            javap = args.pop(0)
        elif a == "--out":
            out = args.pop(0)
        else:
            org = a
    total = 0
    res = {"classes_scanned": 0, "typeSwitch_sites": [], "enumSwitch_sites": [], "matchexception_classes": []}
    for p in class_files(org):
        total += 1
        b = open(p, "rb").read()
        if not (b"typeSwitch" in b or b"enumSwitch" in b or b"java/lang/MatchException" in b):
            continue
        bsm, sites, has_cls, has_new = analyse(javap_v(p, javap))
        rel = os.path.relpath(p, org)
        for s in sites:
            (res["typeSwitch_sites"] if s[1] == "typeSwitch" else res["enumSwitch_sites"]).append(
                {"class": rel, "method": s[0], "bsm": s[2], "indy": f"{s[3]}:{s[4]}"})
        if has_cls:
            res["matchexception_classes"].append({"class": rel, "new_executed": has_new,
                                                  "typeSwitch_sites": sum(1 for s in sites if s[1] == "typeSwitch"),
                                                  "enumSwitch_sites": sum(1 for s in sites if s[1] == "enumSwitch")})
    res["classes_scanned"] = total
    json.dump(res, open(out, "w"), indent=1)
    ts = res["typeSwitch_sites"]
    print("classes scanned", total)
    print("typeSwitch indy sites", len(ts), "in", len({s["class"] for s in ts}), "classes")
    print("enumSwitch indy sites", len(res["enumSwitch_sites"]), "in", len({s["class"] for s in res["enumSwitch_sites"]}), "classes")
    print("MatchException-referencing classes", len(res["matchexception_classes"]),
          "(new executed in", sum(c["new_executed"] for c in res["matchexception_classes"]), ")")


if __name__ == "__main__":
    main(sys.argv[1:])
