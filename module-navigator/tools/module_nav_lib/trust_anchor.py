"""
Trust anchor check for a signed JAR.

Shells out to `keytool -printcert -jarfile <jar>` (the JDK is expected to be
on PATH or resolvable from $NIAGARA_HOME/jre/bin). Parses the human-readable
output — stdlib alone cannot decode PKCS7/X.509 without adding a dep.

Compares the JAR's signer subjectDN against the trust anchor recorded in
`bin/policy/signing.properties`. Reports a simple GO / NO-GO verdict with
reasons based on:
  - DN match with anchor (exact or anchor-as-issuer)
  - BasicConstraints: CA=false expected (leaf cert)
  - ExtendedKeyUsages: codeSigning (OID 1.3.6.1.5.5.7.3.3) expected

Command:
  trust-anchor-check <jar-path> [--anchor-dir PATH] [--keytool PATH]
"""

import os
import re
import shutil
import subprocess
import zipfile

from module_nav_lib.license_inspect import resolve_niagara_home
from module_nav_lib.policy_inspect import _parse_signing_properties


def _find_keytool(explicit=None):
    if explicit and os.path.isfile(explicit) and os.access(explicit, os.X_OK):
        return explicit
    # Prefer a Unix keytool on PATH (avoids WSL Interop glue + encoding issues
    # when running a Windows keytool.exe under Linux).
    found = shutil.which("keytool")
    if found:
        return found
    home, _ = resolve_niagara_home()
    if home:
        for name in ("keytool", "keytool.exe"):
            cand = os.path.join(home, "jre", "bin", name)
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
    return None


def _jar_has_signer(jar_path):
    """Return list of signer file names in META-INF that look like signatures."""
    try:
        with zipfile.ZipFile(jar_path) as z:
            names = [n for n in z.namelist()
                     if n.startswith("META-INF/")
                     and n.rsplit(".", 1)[-1].upper() in (
                         "RSA", "DSA", "EC", "SF")]
        return names
    except (zipfile.BadZipFile, IOError, OSError) as e:
        return None


def _run_keytool(keytool_path, jar_path, timeout=30):
    try:
        proc = subprocess.run(
            [keytool_path, "-printcert", "-jarfile", jar_path],
            capture_output=True, timeout=timeout,
        )
        # Decode manually to tolerate non-utf-8 locales (Windows keytool.exe
        # under WSL may emit cp1252).
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return -1, "", "keytool timed out"
    except (OSError, subprocess.SubprocessError) as e:
        return -1, "", str(e)


# --- Parsers over keytool's human-readable output -----------------------

_OWNER_RE = re.compile(r"^Owner:\s*(.+?)\s*$", re.MULTILINE)
_ISSUER_RE = re.compile(r"^Issuer:\s*(.+?)\s*$", re.MULTILINE)
_VALID_RE = re.compile(
    r"^Valid from:\s*(.+?)\s+until:\s*(.+?)\s*$", re.MULTILINE)
_SERIAL_RE = re.compile(r"^Serial number:\s*(.+?)\s*$", re.MULTILINE)
_SHA256_RE = re.compile(r"^\s*SHA256:\s*([0-9A-Fa-f:]+)\s*$", re.MULTILINE)
_SIGALG_RE = re.compile(r"^Signature algorithm name:\s*(.+?)\s*$", re.MULTILINE)

# ExtendedKeyUsages block — capture bracket body. keytool prints the label
# on the line immediately after the ObjectId line (no intervening line).
_EKU_BLOCK_RE = re.compile(
    r"ObjectId:\s*2\.5\.29\.37[^\n]*\s+ExtendedKeyUsages\s*\[([^\]]+)\]",
    re.DOTALL)
_KU_BLOCK_RE = re.compile(
    r"ObjectId:\s*2\.5\.29\.15[^\n]*\s+KeyUsage\s*\[([^\]]+)\]",
    re.DOTALL)
_BC_BLOCK_RE = re.compile(
    r"ObjectId:\s*2\.5\.29\.19[^\n]*\s+BasicConstraints:?\[([^\]]+)\]",
    re.DOTALL)


def _parse_keytool_output(text):
    """Split per-signer blocks and extract fields.

    keytool -printcert -jarfile prints 'Signer #1:', 'Signer #2:', etc.
    Returns a list of dicts, one per signer.
    """
    # Split on 'Signer #N:' boundaries, keeping the separator.
    parts = re.split(r"\nSigner #\d+:\s*\n", "\n" + text)
    # parts[0] is anything before first signer (usually empty); real bodies from [1:]
    signers = []
    for body in parts[1:]:
        if not body.strip():
            continue
        rec = {"raw": body}
        m = _OWNER_RE.search(body)
        rec["owner"] = m.group(1) if m else ""
        m = _ISSUER_RE.search(body)
        rec["issuer"] = m.group(1) if m else ""
        m = _VALID_RE.search(body)
        if m:
            rec["valid_from"] = m.group(1)
            rec["valid_until"] = m.group(2)
        else:
            rec["valid_from"] = rec["valid_until"] = ""
        m = _SERIAL_RE.search(body)
        rec["serial"] = m.group(1) if m else ""
        m = _SHA256_RE.search(body)
        rec["sha256"] = m.group(1) if m else ""
        m = _SIGALG_RE.search(body)
        rec["sig_alg"] = m.group(1) if m else ""

        m = _EKU_BLOCK_RE.search(body)
        eku_items = []
        if m:
            eku_items = [s.strip() for s in m.group(1).splitlines() if s.strip()]
        rec["eku"] = eku_items

        m = _KU_BLOCK_RE.search(body)
        ku_items = []
        if m:
            ku_items = [s.strip() for s in m.group(1).splitlines() if s.strip()]
        rec["ku"] = ku_items

        m = _BC_BLOCK_RE.search(body)
        if m:
            rec["basic_constraints"] = m.group(1).strip()
        else:
            rec["basic_constraints"] = ""

        signers.append(rec)
    return signers


def _normalize_dn(dn):
    """Loose DN compare — strip whitespace, uppercase keys."""
    if not dn:
        return ""
    parts = [p.strip() for p in re.split(r",(?![^=]*=[^,]*$)", dn) if p.strip()]
    norm = []
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            norm.append("{}={}".format(k.strip().upper(), v.strip()))
        else:
            norm.append(p.upper())
    return ", ".join(norm)


def _resolve_anchor(anchor_dir=None):
    if anchor_dir and os.path.isdir(anchor_dir):
        signing_fp = os.path.join(anchor_dir, "signing.properties")
        if os.path.isfile(signing_fp):
            return _parse_signing_properties(signing_fp) or {}, signing_fp
    home, _ = resolve_niagara_home()
    if home:
        signing_fp = os.path.join(home, "bin", "policy", "signing.properties")
        if os.path.isfile(signing_fp):
            return _parse_signing_properties(signing_fp) or {}, signing_fp
    return {}, None


def cmd_trust_anchor_check(base_dir, jar_path, anchor_dir=None, keytool=None):
    _ = base_dir
    print("")
    print("=" * 72)
    print("  TRUST ANCHOR CHECK")
    print("=" * 72)
    print("  JAR:  {}".format(jar_path))

    if not os.path.isfile(jar_path):
        print("")
        print("  ERROR: file not found.")
        print("")
        return

    signer_files = _jar_has_signer(jar_path)
    if signer_files is None:
        print("")
        print("  ERROR: not a valid zip/jar (or read failure).")
        print("")
        return

    if not signer_files:
        print("  SIGNED?  no (no META-INF/*.RSA|DSA|EC found)")
        print("  VERDICT: NO-GO (unsigned)")
        print("")
        return

    print("  SIGNED?  yes ({})".format(", ".join(signer_files)))

    kt = _find_keytool(keytool)
    if not kt:
        print("")
        print("  ERROR: keytool not found on PATH and not in $NIAGARA_HOME/jre/bin.")
        print("  Pass --keytool /path/to/keytool to override.")
        print("")
        return

    print("  keytool: {}".format(kt))
    rc, out, err = _run_keytool(kt, jar_path)
    if rc != 0:
        print("")
        print("  ERROR: keytool failed (rc={}): {}".format(rc, err.strip()))
        print("")
        return

    signers = _parse_keytool_output(out)
    if not signers:
        print("")
        print("  ERROR: could not parse keytool output — dumping raw:")
        print(out[:500])
        print("")
        return

    anchor, anchor_fp = _resolve_anchor(anchor_dir)
    anchor_subject = anchor.get("subjectDN", "")
    anchor_issuer = anchor.get("issuerDN", "")

    print("")
    print("  TRUST ANCHOR (from signing.properties)")
    print("    file:        {}".format(anchor_fp or "(not found)"))
    print("    subjectDN:   {}".format(anchor_subject or "(none)"))
    print("    issuerDN:    {}".format(anchor_issuer or "(none)"))
    print("")

    go_overall = True
    for i, s in enumerate(signers, 1):
        print("  SIGNER #{}".format(i))
        print("    Owner (subjectDN):  {}".format(s["owner"]))
        print("    Issuer:             {}".format(s["issuer"]))
        print("    Serial:             {}".format(s["serial"]))
        print("    Valid:              {} -> {}".format(
            s["valid_from"], s["valid_until"]))
        print("    SigAlgorithm:       {}".format(s["sig_alg"]))
        print("    SHA256:             {}".format(s["sha256"]))
        print("    BasicConstraints:   {}".format(s["basic_constraints"] or "(absent)"))
        print("    KeyUsage:           {}".format(", ".join(s["ku"]) or "(absent)"))
        print("    ExtendedKeyUsage:   {}".format(", ".join(s["eku"]) or "(absent)"))

        reasons = []
        # DN match — anchor_subject vs signer owner OR signer issuer
        signer_owner_n = _normalize_dn(s["owner"])
        signer_issuer_n = _normalize_dn(s["issuer"])
        anchor_subj_n = _normalize_dn(anchor_subject)
        anchor_iss_n = _normalize_dn(anchor_issuer)

        if anchor_subj_n and signer_owner_n == anchor_subj_n:
            dn_verdict = "MATCH (signer == anchor subjectDN)"
        elif anchor_subj_n and signer_issuer_n == anchor_subj_n:
            dn_verdict = "MATCH (anchor subjectDN == signer issuer — anchor issued this leaf)"
        elif anchor_iss_n and signer_issuer_n == anchor_iss_n:
            dn_verdict = "MATCH-ISSUER (shared issuer with anchor)"
        else:
            dn_verdict = "MISMATCH (signer not chained to anchor)"
            reasons.append("DN does not match trust anchor")
            go_overall = False

        print("    DN check:           {}".format(dn_verdict))

        # BasicConstraints — expect CA=false (leaf)
        bc = s["basic_constraints"].upper()
        if "CA:TRUE" in bc.replace(" ", ""):
            reasons.append("BasicConstraints CA=TRUE (expected leaf cert with CA=false)")
            go_overall = False

        # ExtendedKeyUsage — expect codeSigning
        eku_str = " ".join(s["eku"]).lower()
        if "codesigning" not in eku_str.replace(" ", ""):
            reasons.append("ExtendedKeyUsage missing codeSigning (OID 1.3.6.1.5.5.7.3.3)")
            go_overall = False

        # Self-signed detection — separate informational flag.
        if signer_owner_n and signer_owner_n == signer_issuer_n:
            reasons.append("Self-signed (Owner == Issuer) — not chained to any CA")
            go_overall = False

        if reasons:
            print("    Issues:")
            for r in reasons:
                print("      - {}".format(r))
        else:
            print("    Issues:             (none)")
        print("")

    verdict = "GO" if go_overall else "NO-GO"
    print("  VERDICT: {}".format(verdict))
    print("")
