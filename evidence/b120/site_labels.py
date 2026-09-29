#!/usr/bin/env python3
"""B120: ground-truth label list per typeSwitch/enumSwitch site, straight from the shipped class's
BootstrapMethods (javap -c -p -v).  Output: TSV  class<TAB>method<TAB>kind<TAB>labels(ordered)<TAB>guard_loop
guard_loop=yes when a branch AFTER the indy jumps back to an offset <= the indy (javac's restart-index loop
that re-enters typeSwitch after a failed `when` guard or a failed nested record-pattern component)."""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_sites as g

def sites(classfile):
    text = subprocess.run([g.JAVAP, "-c", "-p", "-v", str(classfile)], capture_output=True, text=True, timeout=120).stdout
    ann, bsm = g.annotated_javap(classfile)
    lines = text.splitlines()
    method, out, insns = None, [], []
    def flush():
        for (off, kind, idx, nm) in [i for i in insns if i[0] == "indy"][:0]:
            pass
    cur_method, cur = None, []
    per = []  # (method, [(off, line)])
    for ln in lines:
        if re.match(r"^  \S.*\(.*\).*;$", ln) or re.match(r"^  static \{\};", ln):
            cur_method = ln.strip(); cur = []; per.append((cur_method, cur, None))
        md = re.match(r"^\s+descriptor: (\S+)$", ln)
        if md and per and per[-1][2] is None:
            per[-1] = (per[-1][0], per[-1][1], md.group(1))
        m = re.match(r"^\s+(\d+): (\S+)\s*(.*)$", ln)
        if m and cur_method is not None:
            cur.append((int(m.group(1)), m.group(2), m.group(3)))
    for meth, ins, desc in per:
        for off, op, rest in ins:
            m = re.search(r"InvokeDynamic #(\d+):(typeSwitch|enumSwitch)", rest)
            if op == "invokedynamic" and m and "SwitchBootstraps" in bsm[int(m.group(1))]["bsm"]:
                back = any(o2 > off and re.match(r"(goto|if\w+)$", op2) and (t := re.match(r"(\d+)", r2)) and int(t.group(1)) <= off
                           for o2, op2, r2 in ins)
                out.append((re.sub(r"\(.*", "", meth).split()[-1] + desc, m.group(2), bsm[int(m.group(1))]["args"], back))
    return out

if __name__ == "__main__":
    c = json.load(open(sys.argv[1]))
    seen = set()
    rows = []
    for grp in ("typeSwitch_sites", "enumSwitch_sites"):
        for s in c[grp]:
            if s["class"] in seen:
                continue
            seen.add(s["class"])
            for meth, kind, args, back in sites(g.ORG / s["class"]):
                rows.append((s["class"].split("extracted/")[1][:-6], meth, kind, " | ".join(args), "yes" if back else "no"))
    for r in rows:
        print("\t".join(r))
