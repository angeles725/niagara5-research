#!/usr/bin/env python3
"""B122 audit helper: which PE files inside jars (nested jars followed) export JNI entry points (`Java_*`)?

Tests [Block 117] §117.3 "ffmpeg-wrapper.dll ... the only JNI library shipped inside a jar".
Scans the 247 config-home module jars and every jar under the install's bin/ (bin/ext, nested).
Output TSV: container!member, sha256, exports, java_exports (name starts with Java_, ?Java_ or the x86 stdcall form _Java_).
"""
import glob
import hashlib
import io
import sys
import zipfile

import pelib

ROOTS = ["/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar",
         "/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/**/*.jar", "/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/*.jar"]


def walk(zf, container, depth=0):
    for zi in zf.infolist():
        if zi.is_dir():
            continue
        data = zf.read(zi)
        name = container + "!" + zi.filename
        if data[:2] == b"MZ":
            try:
                ex = [n for n, _, _ in pelib.PE(data).exports()]
            except Exception:
                continue
            java = [n for n in ex if n.startswith(("Java_", "?Java_", "_Java_"))]
            print("%s\t%s\t%d\t%d" % (name, hashlib.sha256(data).hexdigest(), len(ex), len(java)))
        elif zi.filename.endswith((".jar", ".zip")) and depth < 3:
            try:
                walk(zipfile.ZipFile(io.BytesIO(data)), name, depth + 1)
            except zipfile.BadZipFile:
                pass


def main():
    print("member\tsha256\texports\tjava_exports")
    seen = set()
    for pat in ROOTS:
        for j in sorted(glob.glob(pat, recursive=True)):
            if j not in seen:
                seen.add(j)
                walk(zipfile.ZipFile(j), j.split("/5.0.0.28/")[1])


if __name__ == "__main__":
    main()
