#!/usr/bin/env python3
"""B122: which shipped native files does each module's Java loader actually extract/load?

Reads the string constants ending in .dll/.exe from ClientSideNativeLibraryLoader.java (decompiled tree, out of git)
and compares them with the files shipped under nativeLib/ and, for ffmpeg, with the import closure of ffmpeg-wrapper.dll.
Usage: loader_vs_shipped.py <organized-root>   -> TSV: module, file, shipped, in_loader_list, in_wrapper_import_closure
"""
import re
import sys
from pathlib import Path

import pelib


def loader_names(src):
    return set(re.findall(r'"([^"/\\]+\.(?:dll|exe))"', Path(src).read_text()))


def closure(libdir, start):
    seen, todo = set(), [start]
    while todo:
        n = todo.pop()
        if n.lower() in seen or not (libdir / n).exists():
            continue
        seen.add(n.lower())
        todo += list(pelib.PE((libdir / n).read_bytes()).imports())
    return seen


def main(org):
    org = Path(org)
    print("module\tfile\tshipped\tin_loader_list\tin_wrapper_import_closure")
    xp = org / "xprotect/resources/nativeLib"
    xl = loader_names(org / "xprotect/vineflower/com/tridium/xprotect/util/ClientSideNativeLibraryLoader.java")
    for f in sorted(p.name for p in xp.iterdir() if p.suffix.lower() in (".dll", ".exe")):
        print("xprotect\t%s\tyes\t%s\tn/a" % (f, "yes" if f in xl else "NO"))
    fd = org / "ffmpeg/resources/nativeLib/x86_64"
    fl = loader_names(org / "ffmpeg/vineflower/org/baja/ffmpeg/ClientSideNativeLibraryLoader.java")
    cl = closure(fd, "ffmpeg-wrapper.dll")
    for f in sorted(p.name for p in fd.iterdir()):
        print("ffmpeg\t%s\tyes\t%s\t%s" % (f, "yes" if f in fl else "NO", "yes" if f.lower() in cl else "no"))


if __name__ == "__main__":
    main(sys.argv[1])
