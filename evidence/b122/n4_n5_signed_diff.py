#!/usr/bin/env python3
"""B122: are the 14 .NET files of N4-4.15.3.28 (xprotect-wb.jar) and N5 (xprotect.jar) the same code, differing only by signature?

Compares the PE Authenticode hash (SHA-256 over the image excluding the checksum field, the certificate-table
entry and the certificate blob) of each file. Equal image hash + different whole-file sha256 = re-signed only.
Usage: n4_n5_signed_diff.py <n4 nativeLib dir> <n5 nativeLib dir>
"""
import hashlib
import sys
from pathlib import Path

import pelib


def main(a, b):
    print("file\twhole_file_equal\timage_hash_equal\tn4_size\tn5_size")
    for f in sorted(Path(b).iterdir()):
        if f.suffix.lower() not in (".dll", ".exe") or not (Path(a) / f.name).exists():
            continue
        x, y = (Path(a) / f.name).read_bytes(), f.read_bytes()
        hx, hy = pelib.PE(x).authenticode_hash(), pelib.PE(y).authenticode_hash()
        print("%s\t%s\t%s\t%d\t%d" % (f.name, hashlib.sha256(x).digest() == hashlib.sha256(y).digest(), hx == hy, len(x), len(y)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
