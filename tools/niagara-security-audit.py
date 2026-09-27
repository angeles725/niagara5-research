#!/usr/bin/env python3
"""
niagara-security-audit.py — station/platform security-posture auditor for Niagara N4/N5.

Ported from niagara-research (N4 kit tool) for the niagara5-research corpus. Adaptation:
  - Labeled N4/N5: the checks (moduleVerificationMode, truststore defaults, signing,
    plaintext ports, ...) are platform-general, not N4-only.
  - Honest 'not-found' reporting: the N4 original silently OMITTED a row (no SEC-02,
    SEC-06, SEC-15 entry at all) when its target path did not exist, and SEC-11 went
    further — an absent truststore made `sizes` empty, `weak` empty, and the check
    reported a false PASS ("all keys >= 2048") for zero keys actually inspected. On a
    fresh N5 install there is no security/ directory yet (no station has been created),
    so this path is the common case here, not an edge case: every check whose target is
    missing now emits an explicit NOTFOUND row instead of a silent gap or a misleading
    PASS.

Consolidates the dispersed hardening findings of the niagara-research corpus (B75, B112,
B113, B114, B160, B316/B317, B379/B384, B392-B397) into one READ-ONLY checker. Inspects a
niagara_home on disk (+ optional live ports) and reports, per check, the observed value vs
the secure baseline, with severity and source block.

READ-ONLY. Never writes to or restarts the target. Reports secret STRUCTURE, never values
(SECRETS DISCIPLINE): "truststore opens with default password", not the key material.

Usage:
  niagara-security-audit.py <niagara_home> [--station <config.bog>] [--host 127.0.0.1] [--json]

  <niagara_home>  install dir: bin/ + defaults/system.properties + security/
  --station       path to a station config.bog (for BProgramService / BSyslogService checks)
  --host          probe live TLS/plaintext ports on this host
  --json          machine-readable output

Check IDs (SEC-01..SEC-18) follow the corpus consolidation in B398.
"""
import argparse, json, os, re, subprocess, socket, sys

SEV = {"crit": 3, "high": 2, "med": 1, "info": 0}
C = {"crit": "\033[91m", "high": "\033[93m", "med": "\033[96m", "info": "\033[90m",
     "ok": "\033[92m", "off": "\033[0m"}


class Report:
    def __init__(self): self.rows = []
    def add(self, cid, sev, title, observed, secure, verdict, block, note=""):
        self.rows.append(dict(id=cid, sev=sev, title=title, observed=observed,
                              secure=secure, verdict=verdict, block=block, note=note))
    def dump(self, as_json):
        if as_json:
            print(json.dumps(self.rows, indent=2)); return
        self.rows.sort(key=lambda r: (-SEV[r["sev"]], r["id"]))
        fails = [r for r in self.rows if r["verdict"] == "FAIL"]
        notfound = [r for r in self.rows if r["verdict"] == "NOTFOUND"]
        print(f"\n  Niagara N4/N5 security posture — {len(fails)} finding(s), "
              f"{len(notfound)} not-found / {len(self.rows)} checks\n")
        for r in self.rows:
            mark = {"FAIL": "FAIL", "PASS": "PASS", "NOTFOUND": "N/FND"}.get(r["verdict"], "MANUAL")
            col = C[r["sev"]] if r["verdict"] == "FAIL" else (C["ok"] if r["verdict"] == "PASS" else C["info"])
            print(f"  {col}[{mark:6}]{C['off']} {r['id']} ({r['sev']}) {r['title']}  [{r['block']}]")
            if r["verdict"] in ("FAIL", "MANUAL", "NOTFOUND"):
                print(f"           observed: {r['observed']}")
                if r["verdict"] == "FAIL":
                    print(f"           secure  : {r['secure']}")
                if r["note"]:
                    print(f"           note    : {r['note']}")
        crit = sum(1 for r in fails if r["sev"] == "crit")
        high = sum(1 for r in fails if r["sev"] == "high")
        med = sum(1 for r in fails if r["sev"] == "med")
        print(f"\n  summary: {crit} critical · {high} high · {med} med · {len(fails)} findings\n")


def read_props(home):
    props = {}
    for rel in ("defaults/system.properties", "system.properties"):
        p = os.path.join(home, rel)
        if os.path.isfile(p):
            for line in open(p, encoding="utf-8", errors="replace"):
                m = re.match(r"\s*(#?)\s*(niagara\.[\w.]+|program\.[\w.]+)\s*=\s*(.*)", line)
                if m:
                    props[m.group(2)] = (m.group(3).strip(), m.group(1) == "#")
    return props


def keytool_default(path, pw="changeit"):
    if not os.path.isfile(path): return None
    r = subprocess.run(["keytool", "-list", "-keystore", path, "-storepass", pw],
                       capture_output=True, text=True)
    return not any(x in r.stderr.lower() for x in ("tampered", "incorrect", "invalid keystore"))


def keytool_keysizes(path, pw="changeit"):
    """Return key sizes from a keystore, or None if it could not be inspected
    (missing file, or keytool failed — e.g. a non-default storepass). Callers
    must not treat None as "zero keys, all fine" (that produced a false PASS
    when the store had a custom password: keytool fails silently, stdout has
    no 'N-bit' tokens, and an empty sizes list looked identical to a clean
    scan)."""
    if not os.path.isfile(path): return None
    r = subprocess.run(["keytool", "-list", "-v", "-keystore", path, "-storepass", pw],
                       capture_output=True, text=True)
    if r.returncode != 0 or any(x in r.stderr.lower() for x in ("tampered", "incorrect", "invalid keystore")):
        return None
    return [int(x) for x in re.findall(r"(\d+)-bit", r.stdout)]


def tls_subject(host, port):
    try:
        r = subprocess.run(["openssl", "s_client", "-connect", f"{host}:{port}"],
                           input="", capture_output=True, text=True, timeout=15)
        c = subprocess.run(["openssl", "x509", "-noout", "-subject"],
                           input=r.stdout, capture_output=True, text=True)
        return c.stdout.strip() or None
    except Exception:
        return None


def port_open(host, port):
    try:
        with socket.create_connection((host, port), 3):
            return True
    except Exception:
        return False


def bog_ascii(path):
    """Best-effort ASCII slurp of a .bog (it embeds XML-ish tokens)."""
    try:
        d = open(path, "rb").read()
        return b" ".join(re.findall(rb"[ -~]{4,}", d)).decode("ascii", "replace")
    except Exception:
        return ""


def audit(home, station_bog, host, rep):
    props = read_props(home)

    # SEC-01 crit — moduleVerificationMode
    v, com = props.get("niagara.moduleVerificationMode", (None, True))
    bad = v is None or com or v.lower() == "low"
    rep.add("SEC-01", "crit", "moduleVerificationMode", f"{v or '(unset)'}{' [commented]' if com else ''}",
            "high", "FAIL" if bad else "PASS", "B75/B397",
            "low lets an UNSIGNED module requesting NETWORK_COMMUNICATION load (the 443 incident)")

    # SEC-02 crit — truststore default password
    ts = os.path.join(home, "security", "truststore.jks")
    if not os.path.isfile(ts):
        rep.add("SEC-02", "crit", "truststore.jks default password",
                "not-found (no security/truststore.jks — no station created yet)",
                "non-default store password", "NOTFOUND", "B392/B397",
                "cannot check without a provisioned station; not a PASS")
    else:
        d = keytool_default(ts)
        if d is not None:
            rep.add("SEC-02", "crit", "truststore.jks default password",
                    "opens with 'changeit'" if d else "custom password", "non-default store password",
                    "FAIL" if d else "PASS", "B392/B397", "FS/daemon access -> trust-anchor injection")
        else:
            rep.add("SEC-02", "crit", "truststore.jks default password",
                    "present but unreadable (need keytool)", "non-default store password",
                    "MANUAL", "B392/B397", "run: keytool -list -keystore <ts> -storepass changeit")

    # SEC-03 crit — security/ filesystem ACLs (Windows icacls; note on Linux)
    secdir = os.path.join(home, "security")
    if os.path.isdir(secdir):
        winpath = to_winpath(secdir)
        if winpath and shutil_which("icacls.exe") or (winpath and os.path.exists("/mnt/c")):
            r = subprocess.run(["icacls.exe", winpath], capture_output=True, text=True)
            loose = bool(re.search(r"(Authenticated Users|Users|Everyone)[^\n]*\((M|F|W)", r.stdout))
            rep.add("SEC-03", "crit", "security/ filesystem ACLs",
                    "Modify/Write for Authenticated Users/Everyone" if loose else "restricted",
                    "Admin/SYSTEM only", "FAIL" if loose else "PASS", "B316/B113",
                    "any authenticated user can plant a trust anchor / license")
        else:
            rep.add("SEC-03", "crit", "security/ filesystem ACLs", "not checked (need icacls)",
                    "Admin/SYSTEM only", "MANUAL", "B316/B113", "run: icacls <home>\\security")

    # SEC-04 crit — default TLS cert (live)
    if host:
        for port, name in ((443, "station HTTPS"), (5011, "platform TLS")):
            s = tls_subject(host, port)
            if s:
                default = "ForRecoveryPurposes" in s
                rep.add(f"SEC-04:{port}", "crit", f"{name} certificate",
                        "default self-signed (ForRecoveryPurposes)" if default else s,
                        "CA-issued cert, replaced", "FAIL" if default else "PASS", "B397/B156",
                        "default cert = no real TLS trust, MITM-able on mgmt LAN")

    # SEC-05 high — commandLinePropertyBlacklist covers skip levers
    v, com = props.get("niagara.commandLinePropertyBlacklist", (None, True))
    covered = v and not com and "skipModuleValidation" in v and "ignoreVerificationMode" in v
    rep.add("SEC-05", "high", "commandLinePropertyBlacklist covers skip levers",
            "disabled/absent" if not v or com else ("partial" if not covered else "full"),
            "includes skipModuleValidation + commissioning.ignoreVerificationMode",
            "FAIL" if not covered else "PASS", "B113",
            "-Dniagara.classLoader.skipModuleValidation can disable chain validation at launch")

    # SEC-06 high — license attributes that relax signing
    lic_hits = []
    licdir = os.path.join(home, "security", "licenses")
    if os.path.isdir(licdir):
        for f in os.listdir(licdir):
            if f.endswith(".license"):
                t = open(os.path.join(licdir, f), encoding="utf-8", errors="replace").read()
                for attr in ("skipModuleValidation", "smDeveloperMode", "unreleasedSoftware"):
                    if re.search(attr + r'\s*=\s*"?true', t) or (attr in t and 'developer' in t):
                        lic_hits.append(f"{f}:{attr}")
        rep.add("SEC-06", "high", "license attributes relaxing signature",
                ", ".join(sorted(set(lic_hits))) or "none", "no developer/unreleased/smDeveloper flags",
                "FAIL" if lic_hits else "PASS", "B75/B113",
                "developer{skipModuleValidation}/unreleasedSoftware accept self-signed / disable validation")
    else:
        rep.add("SEC-06", "high", "license attributes relaxing signature",
                "not-found (no security/licenses/ — no station created yet)",
                "no developer/unreleased/smDeveloper flags", "NOTFOUND", "B75/B113",
                "cannot check without a provisioned station; not a PASS")

    # SEC-07 high — program.requireSigning
    v, com = props.get("program.requireSigning", (None, True))
    bad = v is None or com or v.lower() == "false"
    rep.add("SEC-07", "high", "program.requireSigning (BProgram bytecode)",
            "false/default" if bad else v, "true", "FAIL" if bad else "PASS", "B75",
            "superuser BProgram runs arbitrary bytecode unsigned")

    # SEC-08 high — allowProgramRuntimeExec (station config)
    # SEC-10 high — syslog offload enabled (station config)
    if station_bog and os.path.isfile(station_bog):
        txt = bog_ascii(station_bog)
        exec_on = re.search(r"allowProgramRuntimeExec[^>]*true", txt) is not None
        rep.add("SEC-08", "high", "allowProgramRuntimeExec", "true" if exec_on else "false/default",
                "false", "FAIL" if exec_on else "PASS", "B75", "Runtime.exec() from programs")
        sys_on = ("SyslogService" in txt or "BSyslogSettings" in txt) and re.search(r"enabled[^>]*true", txt)
        rep.add("SEC-10", "high", "syslog offload to external SIEM",
                "enabled" if sys_on else "disabled/absent", "enabled + serverHost + TLS transport",
                "FAIL" if not sys_on else "PASS", "B75/B393/B396",
                "the ONLY tamper-resistance for the (unsigned) local audit/history record")
    else:
        for cid, title in (("SEC-08", "allowProgramRuntimeExec"), ("SEC-10", "syslog offload to SIEM")):
            rep.add(cid, "high", title, "not checked (no --station config.bog)", "-", "MANUAL",
                    "B75/B396", "pass --station <config.bog>")

    # SEC-09 high — platform plaintext 3011 (live)
    if host and port_open(host, 3011):
        loopback = host in ("127.0.0.1", "localhost", "::1")
        rep.add("SEC-09", "high" if not loopback else "med", "platform daemon plaintext port 3011",
                f"3011 open{' (loopback only, mitigated)' if loopback else ' on reachable iface'}",
                "sslOnly=true (5011 only)", "FAIL", "B75/B397", "platform creds in cleartext if used")

    # SEC-11 med — weak keys / FIPS
    fips = os.path.isfile(os.path.join(home, "jre", "lib", "security", "cacerts.bcfks"))
    if not os.path.isfile(ts):
        rep.add("SEC-11", "med", "weak signing keys / FIPS",
                f"not-found (no security/truststore.jks); FIPS keystore {'present' if fips else 'absent'}",
                "all keys >= 2048; FIPS suppresses RSA-1024 option",
                "NOTFOUND", "B113/B392",
                "no station provisioned yet — cannot inspect key sizes; not a PASS")
    else:
        sizes = keytool_keysizes(ts)
        if not sizes:
            # None = keytool could not read the store; [] = it read nothing
            # that looks like a key. Neither proves "all keys >= 2048".
            why = "unreadable with default storepass (need keytool)" if sizes is None else "no key sizes reported by keytool"
            rep.add("SEC-11", "med", "weak signing keys / FIPS",
                    f"{why}; FIPS keystore {'present' if fips else 'absent'}",
                    "all keys >= 2048; FIPS suppresses RSA-1024 option",
                    "MANUAL", "B113/B392",
                    "run: keytool -list -v -keystore <ts> -storepass <real password>")
        else:
            weak = [s for s in sizes if s < 2048]
            rep.add("SEC-11", "med", "weak signing keys / FIPS",
                    f"key sizes {sorted(set(sizes)) or 'n/a'}; FIPS keystore {'present' if fips else 'absent'}",
                    "all keys >= 2048; FIPS suppresses RSA-1024 option",
                    "FAIL" if weak else "PASS", "B113/B392", "RSA-1024 allowed with click-through warning")

    # SEC-12 med — .bog at-rest encryption (spot-check station config header)
    if station_bog and os.path.isfile(station_bog):
        head = open(station_bog, "rb").read(4096)
        keyring = b"keyring" in head or b"EncryptionKeySource" in head
        rep.add("SEC-12", "med", "config.bog at-rest encryption",
                "keyring/external" if keyring else "none (plaintext)", "keyring",
                "FAIL" if not keyring else "PASS", "B114",
                "EncryptionKeySource=none leaves reversible passwords in the clear")

    # SEC-14 med — Fox/HTTP plaintext ports (live)
    if host:
        for port, name, blk in ((1911, "Fox plaintext", "B397/B134"), (80, "HTTP plaintext", "B397")):
            if port_open(host, port):
                rep.add(f"SEC-14:{port}", "med", f"{name} port {port}", f"{port} open",
                        "TLS-only (4911/443)", "FAIL", blk, "station comms/UI in cleartext")

    # SEC-15 med — KeyRingPermission wildcard in an UNSIGNED module (secret-store read)
    moddir = os.path.join(home, "modules")
    if os.path.isdir(moddir):
        total, wild, wild_unsigned = scan_keyring_perms(moddir)
        risk = len(wild_unsigned) > 0
        rep.add("SEC-15", "med", "KeyRingPermission wildcard in unsigned module",
                f"{len(total)} modules declare it, {len(wild)} wildcard(name=*), "
                f"{len(wild_unsigned)} of those UNSIGNED",
                "no wildcard KeyRingPermission in an unsigned/attacker module",
                "FAIL" if risk else "PASS", "B114",
                ("unsigned wildcard holders: " + ", ".join(wild_unsigned)) if risk else
                "all wildcard holders are signed; risk only if an UNSIGNED module (SEC-01/06) declares name=*")
    else:
        # On N5, modules do not live under niagara_home/modules (unlike N4) —
        # they ship at .../tridium/config/<ver>/modules. Report honestly
        # rather than silently omitting the row; the caller can point a
        # module scan at the real N5 module dir separately.
        rep.add("SEC-15", "med", "KeyRingPermission wildcard in unsigned module",
                f"not-found ({moddir} does not exist)",
                "no wildcard KeyRingPermission in an unsigned/attacker module",
                "NOTFOUND", "B114",
                "N5 modules ship outside niagara_home (tridium/config/<ver>/modules) — "
                "not checked here; not a PASS")

    # SEC-16 (informational) — data record is unsigned by design
    rep.add("SEC-16", "med", "local data record integrity (audit/history/backup/.bog)",
            "unsigned by design (architectural)", "syslog offload (SEC-10) = resistance, not evidence",
            "FAIL", "B393/B396", "Niagara signs code, not data; no toggle fixes this - audit via SEC-10")


# Forensic IOC set (B112 / B75) — signature-bypass & unsigned-load evidence that persists
# in logs even after Sys.setAuditor(null) erases the in-station audit.
LOG_IOCS = [
    ("crit", "module-validation-disabled banner", re.compile(r"Module validation has been DISABLED", re.I)),
    ("crit", "module validation is disabled", re.compile(r"module validation is disabled", re.I)),
    ("high", "unsigned module loaded (No code signers)", re.compile(r"No code signers for entry", re.I)),
    ("high", "unsigned BProgram executed", re.compile(r"program\.notSigned|is not signed", re.I)),
    ("med", "signature validation failure", re.compile(r"failed signature validation|Invalid signature", re.I)),
    ("med", "self-signed cert not permitted", re.compile(r"Self signed signing certificate not permitted", re.I)),
    ("med", "cert path validation failure", re.compile(r"CERT_PATH_VALIDATION_FAILURE|Error validating cert path", re.I)),
]


def scan_logs(logroot):
    """Harvest signature/verification IOCs from Niagara console/station logs (B112).
    Returns list of (severity, ioc_label, file, lineno, line)."""
    hits = []
    for dirp, _, files in os.walk(logroot):
        for fn in files:
            if not re.search(r"(console|station|nre|daemon).*\.(log|txt)$|\.log(\.\d+)?$", fn, re.I):
                continue
            p = os.path.join(dirp, fn)
            try:
                for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                    for sev, label, rx in LOG_IOCS:
                        if rx.search(line):
                            hits.append((sev, label, p, i, line.strip()[:160]))
            except Exception:
                continue
    return hits


def scan_keyring_perms(moddir):
    """Scan modules/*.jar META-INF/module.xml for KeyRingPermission. Returns
    (all_holders, wildcard_holders, wildcard_AND_unsigned)."""
    import zipfile
    all_h, wild, wild_uns = [], [], []
    for f in sorted(os.listdir(moddir)):
        if not f.endswith(".jar"):
            continue
        try:
            z = zipfile.ZipFile(os.path.join(moddir, f))
            names = z.namelist()
            if "META-INF/module.xml" not in names:
                continue
            xml = z.read("META-INF/module.xml").decode("utf-8", "replace")
        except Exception:
            continue
        if "KeyRingPermission" not in xml:
            continue
        all_h.append(f)
        vals = re.findall(r'KeyRingPermission"[^>]*?(?:name|target)="([^"]*)"', xml)
        if "*" in vals:
            wild.append(f)
            signed = any(n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC"))
                         for n in names)
            if not signed:
                wild_uns.append(f)
    return all_h, wild, wild_uns


def to_winpath(p):
    m = re.match(r"/mnt/([a-z])/(.*)", p)
    return f"{m.group(1).upper()}:\\" + m.group(2).replace("/", "\\") if m else None


def shutil_which(name):
    import shutil
    return shutil.which(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("niagara_home")
    ap.add_argument("--station", default=None)
    ap.add_argument("--host", default=None)
    ap.add_argument("--scan-logs", default=None, metavar="DIR",
                    help="forensic mode: harvest signature/verification IOCs from a log tree (B112)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.scan_logs:
        hits = scan_logs(a.scan_logs)
        if a.json:
            print(json.dumps([dict(sev=s, ioc=l, file=f, line=n, text=t) for s, l, f, n, t in hits], indent=2))
        else:
            print(f"\n  Log-IOC harvest — {len(hits)} indicator(s) in {a.scan_logs}\n")
            for s, l, f, n, t in sorted(hits, key=lambda x: -SEV[x[0]]):
                print(f"  {C[s]}[{s}]{C['off']} {l}  {f}:{n}\n         {t}")
            if not hits:
                print("  no signature-bypass / unsigned-load IOCs found (clean).")
            print()
        return
    if not os.path.isdir(a.niagara_home):
        sys.exit(f"ERROR: not a directory: {a.niagara_home}")
    rep = Report()
    audit(a.niagara_home, a.station, a.host, rep)
    rep.dump(a.json)


if __name__ == "__main__":
    main()
