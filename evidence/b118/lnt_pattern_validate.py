#!/usr/bin/env python3
"""Validate a LineNumberTable discriminator for instanceof-pattern vs classic cast
against Tridium docSource originals. Read-only over organized/."""
import os, re, subprocess, sys, json, collections
ORG = "/home/cristian/niagara5-research/organized"
JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"
DS = os.path.join(ORG, "docSource")

def classes_for(mod):
    root = os.path.join(DS, mod)
    out = []
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".java"):
                rel = os.path.relpath(os.path.join(d, f), root)[:-5]
                cf = os.path.join(ORG, mod, "extracted", rel + ".class")
                if os.path.exists(cf):
                    out.append((rel, os.path.join(d, f), cf))
    return out

INS = re.compile(r"^\s+(\d+): (\w+)\s*(.*)$")
def parse_javap(text):
    """yield (method, instrs[(pc,op,arg)], lnt[(line,pc)])"""
    meth = None; instrs = []; lnt = []; mode = None
    for ln in text.splitlines():
        if re.match(r"^  \S.*\);$", ln) or re.match(r"^  \S.*\) throws .*;$", ln) or ln.startswith("  static {}"):
            if meth: yield meth, instrs, lnt
            meth = ln.strip(); instrs = []; lnt = []; mode = None; continue
        s = ln.strip()
        if s == "Code:": mode = "code"; continue
        if s == "LineNumberTable:": mode = "lnt"; continue
        if s.startswith("LocalVariableTable") or s.startswith("StackMapTable") or s.startswith("Exception table"): mode = None; continue
        if mode == "code":
            m = INS.match(ln)
            if m: instrs.append((int(m.group(1)), m.group(2), m.group(3)))
        elif mode == "lnt":
            m = re.match(r"line (\d+): (\d+)", s)
            if m: lnt.append((int(m.group(1)), int(m.group(2))))
    if meth: yield meth, instrs, lnt

def line_at(lnt, pc):
    best = None
    for line, start in lnt:
        if start <= pc and (best is None or start >= best[1]): best = (line, start)
    return best[0] if best else None

def sites(instrs, lnt):
    starts = {pc: line for line, pc in lnt}
    for i, (pc, op, arg) in enumerate(instrs):
        if op != "instanceof": continue
        cp = arg.split()[0]
        # find checkcast same cp within next 5 instrs followed by astore
        for j in range(i + 1, min(i + 6, len(instrs) - 1)):
            if instrs[j][1] == "checkcast" and instrs[j][2].split()[0] == cp and instrs[j + 1][1].startswith("astore"):
                iline = line_at(lnt, pc)
                cc_pc = instrs[j][0]
                own = None
                for line, st in lnt:
                    if pc < st <= cc_pc and line != iline: own = line
                typ = arg.split("class ")[-1].split("/")[-1].split("$")[-1] if "class" in arg else "?"
                yield dict(pc=pc, iline=iline, cast_line=own, typ=typ)
                break

def truth(src_lines, iline, typ):
    """pattern if original line (or next 2) contains 'instanceof <typ> <ident>'."""
    if iline is None or iline > len(src_lines): return "unknown"
    txt = " ".join(src_lines[iline - 1: iline + 2])
    if re.search(r"instanceof\s+[\w.]*\b" + re.escape(typ) + r"(<[^>]*>)?\s+[a-z_]\w*\s*[)&|;?:]", txt): return "pattern"
    if re.search(r"instanceof\s+[\w.]*\b" + re.escape(typ) + r"\b", txt): return "classic"
    return "unknown"

def main():
    mods = sorted(m for m in os.listdir(DS) if os.path.isdir(os.path.join(DS, m)) and m not in ("META-INF", "doc"))
    conf = collections.Counter(); ex = collections.defaultdict(list)
    for mod in mods:
        cl = classes_for(mod)
        for k in range(0, len(cl), 200):
            chunk = cl[k:k + 200]
            names = [c[0].replace("/", ".") for c in chunk]
            r = subprocess.run([JAVAP, "-c", "-l", "-p", "-cp", os.path.join(ORG, mod, "extracted")] + names,
                               capture_output=True, text=True)
            # split per class by "Compiled from"
            blocks = re.split(r"(?m)^Compiled from ", r.stdout)[1:]
            for (rel, src, cf), blk in zip(chunk, blocks):
                src_lines = open(src, encoding="utf-8", errors="replace").read().splitlines()
                for meth, ins, lnt in parse_javap(blk):
                    for s in sites(ins, lnt):
                        t = truth(src_lines, s["iline"], s["typ"])
                        pred = "classic" if (s["cast_line"] is not None and s["cast_line"] > s["iline"]) else "pattern-or-sameline"
                        conf[(t, pred)] += 1
                        if len(ex[(t, pred)]) < 5: ex[(t, pred)].append(f"{mod}:{rel}:{s['iline']}")
    for k, v in sorted(conf.items()): print(k, v)
    print(json.dumps({f"{a}|{b}": v for (a, b), v in ex.items()}, indent=1))
main()
