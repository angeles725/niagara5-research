#!/usr/bin/env python3
"""B122 step 3c: import closure, signing and third-party-codec markers for the FFmpeg DLLs.

Instrument A: pelib import directory. Instrument B: `objdump -p` "DLL Name:" lines (must agree).
Also reports Authenticode presence and grep-style markers of external codec libraries (GPL/nonfree suspects).
Usage: dll_deps.py <nativeLib-dir>
"""
import re
import subprocess
import sys
from pathlib import Path

import pelib
from clr_dump import signer

EXTERNAL = [b"libx264", b"x264 ", b"libx265", b"libfdk", b"fdk-aac", b"openh264", b"libvpx", b"libmp3lame",
            b"libopus", b"libvorbis", b"libtheora", b"libxvid", b"libaom", b"nonfree", b"--enable-gpl",
            b"--enable-version3", b"--enable-nonfree"]


def main(d):
    print("dll\timports_agree\tnon_system_imports\tsystem_imports\tauthenticode_digest\tauthenticode_leaf\texternal_markers")
    for f in sorted(Path(d).glob("*.dll")):
        data = f.read_bytes()
        pe = pelib.PE(data)
        a = sorted(pe.imports())
        od = subprocess.run(["objdump", "-p", str(f)], capture_output=True, text=True).stdout
        b = sorted(set(re.findall(r"DLL Name: (\S+)", od)))
        sysdlls = [x for x in a if re.match(r"(?i)(api-ms-|kernel32|user32|advapi32|ole32|oleaut32|shell32|ws2_32|bcrypt|crypt32|"
                                            r"secur32|ncrypt|mfplat|mf|mfreadwrite|mfuuid|strmiids|vcruntime|msvcp|"
                                            r"gdi32|winmm|d3d|dxgi|dxva|ntdll|shlwapi|rpcrt4|mfcore|evr|quartz|avrt|"
                                            r"wmcodecdspuuid|imm32|version|setupapi|comdlg32|propsys|userenv|iphlpapi)", x)]
        non = [x for x in a if x not in sysdlls]
        ext = [m.decode() for m in EXTERNAL if m in data]
        print("\t".join([f.name, str([x.lower() for x in a] == [x.lower() for x in b]), ",".join(non),
                         str(len(sysdlls)), *signer(pe), ",".join(ext) or "-"]))


if __name__ == "__main__":
    main(sys.argv[1])
