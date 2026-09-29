#!/usr/bin/env python3
"""B122 step 3b: FFmpeg version / build-configuration / license strings of the 7 shipped FFmpeg DLLs.

Instrument A: byte regex over the raw PE (pelib gives file offset + VA).
Instrument B: `r2 -n -c "psz @ VA"` reads the string back at that VA (independent loader + string reader).
Instrument C: GNU `strings -a -t x` file offsets must contain the same offsets.
Also compares the ident numbers to the version headers of the source tarball Tridium ships (--src DIR).
Usage: ff_idents.py <nativeLib-dir> [--src <extracted-ffmpeg-src-root>]
"""
import hashlib
import re
import struct
import subprocess
import sys
from pathlib import Path

import pelib

PAT = re.compile(rb"(FFmpeg version n[^\0]+|--prefix=[^\0]+|lib[a-z]+ license: [^\0]+|L(?:av[cfudf]|sw[a-z]+)\d+\.\d+\.\d+)\0")
LIBS = {"avcodec": "AVCODEC", "avformat": "AVFORMAT", "avutil": "AVUTIL", "avdevice": "AVDEVICE",
        "avfilter": "AVFILTER", "swscale": "SWSCALE", "swresample": "SWRESAMPLE"}


def imagebase(pe):
    return struct.unpack_from("<Q" if pe.is64 else "<I", pe.d, pe.opt + (24 if pe.is64 else 28))[0]


def va_of(pe, off):
    for _, va, vs, ro, rs in pe.sections:
        if ro <= off < ro + rs:
            return off - ro + va + imagebase(pe)
    return None


def r2_string(path, va):
    p = subprocess.run(["r2", "-q", "-c", "psz @ 0x%x" % va, str(path)], capture_output=True, text=True)
    return p.stdout.strip()


def src_versions(src):
    out = {}
    for lib, up in LIBS.items():
        vals = {}
        for h in (Path(src).glob("*/lib%s/version*.h" % lib)):
            for k in ("MAJOR", "MINOR", "MICRO"):
                m = re.search(r"define LIB%s_VERSION_%s\s+(\d+)" % (up, k), h.read_text())
                if m:
                    vals[k] = m.group(1)
        out[lib] = ".".join(vals.get(k, "?") for k in ("MAJOR", "MINOR", "MICRO"))
    return out


def main(libdir, src=None):
    sv = src_versions(src) if src else {}
    print("dll\tsha256\tsize\toffset\tva\tstring\tr2_agrees\tstrings_agrees\tsrc_version")
    for dll in sorted(Path(libdir).glob("*.dll")):
        data = dll.read_bytes()
        pe = pelib.PE(data)
        sha = hashlib.sha256(data).hexdigest()
        sout = subprocess.run(["strings", "-a", "-t", "x", str(dll)], capture_output=True, text=True).stdout
        soffs = {int(m.group(1), 16) for m in re.finditer(r"^\s*([0-9a-f]+) ", sout, re.M)}
        for m in PAT.finditer(data):
            s = m.group(1).decode()
            va = va_of(pe, m.start(1))
            r2ok = va is not None and r2_string(dll, va) == s
            print("\t".join([dll.name, sha, str(len(data)), hex(m.start(1)), hex(va) if va else "", s, str(r2ok),
                             str(m.start(1) in soffs), sv.get(dll.name.split("-")[0].replace("lib", ""), "")]))


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[args.index("--src") + 1] if "--src" in args else None)
