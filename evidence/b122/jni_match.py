#!/usr/bin/env python3
"""B122 step 3: match `native` methods declared in the ffmpeg module 1:1 against the exports of ffmpeg-wrapper.dll.

Instruments: javap -p -s (Java side); PE export directory read by pelib, cross-checked against
`objdump -p` and `rabin2 -E` (three independent parsers of the same export table).
Usage: jni_match.py <extracted-classes-dir> <dll>   -> TSV on stdout, summary on stderr
"""
import re
import subprocess
import sys
from pathlib import Path

import pelib


def esc(s):
    out = []
    for ch in s:
        if ch == "_":
            out.append("_1")
        elif ch == ";":
            out.append("_2")
        elif ch == "[":
            out.append("_3")
        elif ch == "/":
            out.append("_")
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        else:
            out.append("_0%04x" % ord(ch))
    return "".join(out)


def natives(root):
    """Yield (class, method, descriptor) for every native method under root."""
    for cf in sorted(Path(root).rglob("*.class")):
        cls = str(cf.relative_to(root))[:-6].replace("/", ".")
        p = subprocess.run(["javap", "-p", "-s", "-cp", str(root), cls], capture_output=True, text=True)
        lines = p.stdout.splitlines()
        for i, ln in enumerate(lines):
            if " native " in ln:
                name = re.search(r"(\w+)\(", ln).group(1)
                desc = lines[i + 1].split("descriptor:")[1].strip()
                yield cls, name, desc


def jni_names(cls, name, desc):
    base = "Java_" + esc(cls.replace(".", "/")) + "_" + esc(name)
    return base, base + "__" + esc(desc[1:desc.index(")")])


def tool_exports(dll):
    od = subprocess.run(["objdump", "-p", dll], capture_output=True, text=True).stdout
    a = set(re.findall(r"^\s+\[\s*\d+\]\s+\+base\[\s*\d+\]\s+[0-9a-f]{4}\s+(\S+)$", od, re.M))
    rb = subprocess.run(["rabin2", "-E", dll], capture_output=True, text=True).stdout
    b = {ln.split()[-1] for ln in rb.splitlines() if re.match(r"^\d+\s", ln)}
    return a, b


def main(root, dll):
    exp = {n for n, _, _ in pelib.PE(open(dll, "rb").read()).exports()}
    od, rb = tool_exports(dll)
    print("instrument agreement: pelib=%d objdump=%d rabin2=%d equal=%s" % (
        len(exp), len(od), len(rb), exp == od == rb), file=sys.stderr)
    used, rows = set(), []
    for cls, name, desc in natives(root):
        short, long_ = jni_names(cls, name, desc)
        hit = next((x for x in (short, long_) if x in exp), None)
        used.add(hit)
        rows.append((cls, name, desc, short, long_, hit or "", "MATCH" if hit else "NO-EXPORT"))
    print("class\tmethod\tdescriptor\tjni_short\tjni_long\texport\tstatus")
    for r in rows:
        print("\t".join(r))
    for e in sorted(exp - used):
        print("\t\t\t\t\t%s\tORPHAN-EXPORT%s" % (e, " (C++-mangled, not JNI-bindable)" if e.startswith("?") else ""))
    print("natives=%d matched=%d no_export=%d orphan_exports=%d" % (
        len(rows), sum(r[6] == "MATCH" for r in rows), sum(r[6] != "MATCH" for r in rows), len(exp - used)), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
