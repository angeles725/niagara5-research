#!/usr/bin/env python3
"""B120: classify each shipped method that executes `new java/lang/MatchException`.
  record-deconstruction : the MatchException is built from a caught Throwable (`Throwable.toString` -> <init>(String,Throwable)):
                          javac's wrapper around record-pattern accessor calls;
  exhaustive-default    : `aconst_null; aconst_null; <init>` -- the synthetic default arm of an exhaustive enum/sealed switch.
Also lists the selector kind (tableswitch/lookupswitch on ordinal / $SwitchMap vs typeSwitch indy) seen in the same method.
Usage: matchexc_kinds.py census-switch.json > matchexc-kinds.tsv"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_sites as g

c = json.load(open(sys.argv[1]))
print("class\tmethod\tkind\tselector")
for m in c["matchexception_classes"]:
    p, _ = g.parsed(g.ORG / m["class"])
    for k, v in p["methods"].items():
        code = "\n".join(v["code"])
        if "MatchException" not in code:
            continue
        kind = "record-deconstruction" if "Throwable.toString" in code else "exhaustive-default"
        sel = "typeSwitch" if ":typeSwitch:" in code else ("enumSwitch" if ":enumSwitch:" in code else
              ("tableswitch/lookupswitch" if re.search(r"(table|lookup)switch", code) else "none"))
        if "$SwitchMap$" in code:
            sel += "+$SwitchMap$"
        print(f"{m['class'].split('extracted/')[1][:-6]}\t{k[0]}{k[1]}\t{kind}\t{sel}")
