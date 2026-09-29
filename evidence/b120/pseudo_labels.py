#!/usr/bin/env python3
"""B120: machine-check the label lists that the PSEUDO-Java renderings (cons / CFR / Procyon) print for each
typeSwitch/enumSwitch site against the shipped BootstrapMethods argument list (order matters).

Text forms parsed:
  cons    SwitchBootstraps.typeSwitch<"typeSwitch",A,B,C>(sel, idx)
  cfr     SwitchBootstraps.typeSwitch("typeSwitch", new Object[]{A.class, B.class}, sel, n)
  procyon SwitchBootstraps.typeSwitch(lookup, "typeSwitch", MethodType.methodType(...), A.class, B.class).dynamicInvoker()
Labels are compared by SIMPLE name (last segment after . / $), quotes and `.class` stripped.
Per top-level class, the multiset of label lists printed in the file must equal the multiset from the shipped classes.
Usage: pseudo_labels.py census-switch.json site-labels.tsv <scratch-dir> > pseudo-labels.tsv"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ORG = Path("/home/cristian/niagara5-research/organized")
census, labels_tsv, scratch = sys.argv[1], sys.argv[2], Path(sys.argv[3])


def norm(tok):
    t = tok.strip().strip('"')
    t = re.sub(r"\.class$", "", t)
    return re.split(r"[./$]", t)[-1]


def split_top(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [norm(x) for x in out if x.strip()]


CONS = re.compile(r'SwitchBootstraps\.(?:typeSwitch|enumSwitch)<"(?:typeSwitch|enumSwitch)"((?:,[^>]*?)?)>\(')
CFR = re.compile(r'SwitchBootstraps\.(?:typeSwitch|enumSwitch)\("\w+", new Object\[\]\{(.*?)\}, ')
PRO = re.compile(r'SwitchBootstraps\.(?:typeSwitch|enumSwitch)\(lookup, "\w+", MethodType\.methodType\([^)]*\), (.*?)\)\)\.dynamicInvoker')

ship = defaultdict(list)
for ln in open(labels_tsv):
    cls, meth, kind, labs, guard = ln.rstrip("\n").split("\t")
    ship[cls.split("$")[0]].append(tuple(norm(x) for x in labs.split(" | ")))

c = json.load(open(census))
units = {}
for grp in ("typeSwitch_sites", "enumSwitch_sites"):
    for s in c[grp]:
        parts = s["class"].split("/")
        i = parts.index("extracted")
        mod = "/".join(parts[:i])
        top = "/".join(parts[i + 1:])[:-6].split("$")[0]
        units[(mod, top)] = 1

print("unit\ttree\tsites_shipped\tsites_printed\tlabel_lists_equal")
tot = defaultdict(lambda: [0, 0])
for (mod, top) in sorted(units):
    want = Counter(ship[top])
    for tree, path, rx, first in [
        ("cons", ORG / mod / "vineflower-cons" / (top + ".java"), CONS, True),
        ("cfr", scratch / "dec" / "cfr" / mod.replace("/", "_") / (top + ".java"), CFR, False),
        ("procyon", scratch / "dec" / "procyon" / mod.replace("/", "_") / (top + ".java"), PRO, False),
    ]:
        if not path.exists() or not path.read_text(errors="replace").strip():
            print(f"{top}\t{tree}\t{sum(want.values())}\t-\tEMPTY")
            continue
        text = path.read_text(errors="replace")
        got = Counter()
        for m in rx.finditer(text):
            got[tuple(split_top(m.group(1)))] += 1
        eq = got == want
        print(f"{top}\t{tree}\t{sum(want.values())}\t{sum(got.values())}\t{'yes' if eq else 'NO'}")
        tot[tree][0] += 1
        tot[tree][1] += eq
for t, (n, e) in tot.items():
    print(f"# {t}: {e}/{n} classes print exactly the shipped label multiset", file=sys.stderr)
