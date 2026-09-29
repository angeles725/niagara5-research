#!/usr/bin/env python3
import json, re, sys
r = json.load(open(sys.argv[1]))
for u in r:
    top = u["unit"]["top_rel"].split("/")[-1]
    row = []
    for t, e in u["trees"].items():
        st = e.get("status")
        if st == "compiled":
            vs = []
            for c in e["methods"].values():
                for m in c.values():
                    vs.append(m["verdict"] + (":" + m.get("kind", "") if m["verdict"] == "mismatch" else ""))
            s = ",".join(f"{v}x{vs.count(v)}" for v in sorted(set(vs)))
            if e.get("shim"): s += f"[shim={e['shim']}]"
            if e.get("system"): s += "[jre]"
        else:
            s = st
        row.append(f"{t}={s}{'*P' if e.get('pseudo') else ''}")
    print(top, "".join(x[0] for x in u["unit"]["groups"]), " ".join(row))
