#!/usr/bin/env python3
"""B122 second instrument for the XProtectBridgeService.exe behaviour claims (no ilspycmd involved).

Reads the raw PE: #US user-string heap, MemberRef names, the embedded Win32 manifest and the IL bytes of
Program::GetTcpPort. Prints one `fact<TAB>result<TAB>detail` line per check; exit 1 if any check fails.
Usage: bridge_facts.py <XProtectBridgeService.exe>
"""
import re
import sys

import clrlib
import pelib

USER_STRINGS = ["XPBS_WEB_PORT", "XPBS_USE_TLS", "XPBS_AUTH_KEY", "SessionId", "http://tempuri.org/", "running: ",
                "APP_GUID:", "dynamic", "unauthorized user", "http://localhost:", "https://localhost:"]
MEMBERS = ["set_IncludeExceptionDetailInFaults", "set_HttpGetEnabled", "set_HttpsGetEnabled", "GetEnvironmentVariable",
           "ReadLine", "Loopback", "Login", "AddServer", "Initialize"]


def user_strings(c):
    off, size = c.streams["#US"]
    d, out, p = c.pe.d, [], off + 1
    while p < off + size:
        b = d[p]
        n, p = (b, p + 1) if b < 0x80 else (((b & 0x3F) << 8) | d[p + 1], p + 2)
        if n:
            out.append(d[p:p + n - 1].decode("utf-16le", "replace"))
        p += n
    return out


def manifest_level(raw):
    m = re.search(rb"<(?:\w+:)?assembly.*?</(?:\w+:)?assembly>", raw, re.S)
    if not m:
        return None
    xml = re.sub(rb"<!--.*?-->", b"", m.group(0), flags=re.S).decode("utf-8", "replace")
    return re.findall(r'requestedExecutionLevel\s+level="(\w+)"', xml)


def main(path):
    raw = open(path, "rb").read()
    c = clrlib.Clr(pelib.PE(raw))
    us = set(user_strings(c))
    mrefs = {c.heap_str(r[1]) for r in c.tab[10]}
    facts = [("user-string " + s, s in us) for s in USER_STRINGS] + [("memberref " + m, m in mrefs) for m in MEMBERS]
    facts.append(("default port 9117 (ldc.i4 0x239D in IL)", bytes.fromhex("209d230000") in raw))
    facts.append(("Win32 manifest level", manifest_level(raw) == ["requireAdministrator"]))
    facts.append(("MIPService operations", {"LoginBasic", "LoginWindows", "Logout", "GetCamerasUser", "GetCamerasSystem",
                                            "GetServers", "GetConfiguration", "SetupPollConfigServer", "PollConfigServer",
                                            "getPresets"} <= {c.heap_str(r[3]) for r in c.tab[6]}))
    bad = 0
    for name, ok in facts:
        bad += not ok
        print("%s\t%s" % ("PASS" if ok else "FAIL", name))
    print("manifest levels (comments stripped): %s" % manifest_level(raw), file=sys.stderr)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1])
