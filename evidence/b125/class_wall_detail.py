#!/usr/bin/env python3
"""B125: per-method grades of the two whole-class walls whose Java-mode file does compile (GruntOptions, KarmaConfig).
Reuses grade_sites.py (compile_top, grade_method). Writes class-wall-methods.tsv to stdout."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grade_sites as g
from b125_lib import *
print("class\tmethod\tdescriptor\tshipped_flags\tgrade\trules\tkind")
for cls in ("com/tridium/gradle/plugins/grunt/util/GruntOptions", "com/tridium/gradle/plugins/grunt/util/KarmaConfig"):
    jf, out, err, n, kinds = g.compile_top("n-plugin", cls)
    A = g.javap_parsed(f"{extracted('n-plugin')}/{cls}.class")
    B = g.javap_parsed(glob.glob(f"{out}/**/{cls.split('/')[-1]}.class", recursive=True)[0])
    for k in sorted(A["methods"]):
        m = A["methods"][k]
        if k not in B["methods"]:
            gr, rules = "missing", []
        else:
            gr, rules = g.grade_method(m, B["methods"][k])
        kind = "synthetic" if "ACC_SYNTHETIC" in m["flags"] else "bridge" if "ACC_BRIDGE" in m["flags"] else "declared"
        print(f"{cls.split('/')[-1]}\t{k[0]}\t{k[1]}\t{','.join(m['flags'])}\t{gr}\t{','.join(rules) or '-'}\t{kind}")
