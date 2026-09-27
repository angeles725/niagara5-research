"""
Policy inspection — `bin/policy/` triad (signing.properties, java.policy,
java.security).

Commands:
  policy-inspect [--dir PATH] [--verify-signatures]

Output:
  - Trust anchor cert metadata from signing.properties
  - java.policy grant blocks (codeBase + permission count each)
  - Detection of the NIAGARA SIGNATURE trailer block in java.policy
  - java.security: active crypto providers + jdk.{tls,certpath,jar}.disabledAlgorithms

`--verify-signatures` is a stub — we report detected signature blocks but do
NOT attempt PKCS7 verification (stdlib can't do it cleanly). A future version
may shell out to openssl if available.

Stdlib only.
"""

import os
import re
import sys
from datetime import datetime, timezone

from module_nav_lib.license_inspect import resolve_niagara_home


def _resolve_policy_dir(explicit=None):
    if explicit and os.path.isdir(explicit):
        return explicit, "explicit"
    home, src = resolve_niagara_home()
    if not home:
        return None, src
    cand = os.path.join(home, "bin", "policy")
    if os.path.isdir(cand):
        return cand, "derived from {}".format(src)
    return None, [("derived", cand)]


def _parse_signing_properties(path):
    """Parse simple key=value file, decode Java-style backslash escapes."""
    out = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if not line or line.startswith("#") or line.startswith("!"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                # Java .properties escape: "\=" -> "=", "\:" -> ":"
                v = v.replace("\\=", "=").replace("\\:", ":").replace("\\,", ",")
                out[k.strip()] = v.strip()
    except (IOError, OSError):
        return None
    return out


def _format_millis(ms_str):
    """Convert a millis-since-epoch string to ISO date, tolerant of junk."""
    try:
        ms = int(ms_str)
    except (TypeError, ValueError):
        return ms_str
    try:
        dt = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OverflowError, OSError, ValueError):
        return "(out-of-range: {})".format(ms_str)


# Match `grant codeBase "file:..." {` with optional signedBy.
_GRANT_RE = re.compile(
    r'grant\s+(?:signedBy\s+"([^"]+)"\s*,\s*)?codeBase\s+"([^"]+)"\s*\{',
    re.MULTILINE,
)


def _parse_java_policy(path):
    """Extract grant blocks and count permissions in each.

    Returns (grants, has_signature_block). grants is a list of dicts with
    codeBase, signedBy, permission_count.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except (IOError, OSError):
        return [], False

    has_sig = "-----BEGIN NIAGARA SIGNATURE-----" in text

    grants = []
    # Iterate matches; for each, scan forward to the matching '};' and count
    # the number of "permission " tokens inside the block.
    for m in _GRANT_RE.finditer(text):
        signed_by = m.group(1) or ""
        code_base = m.group(2)
        start = m.end()
        # Find the closing '};' naive but sufficient — grants don't nest.
        close = text.find("};", start)
        if close == -1:
            continue
        body = text[start:close]
        perm_count = body.count("permission ")
        grants.append({
            "codeBase": code_base,
            "signedBy": signed_by,
            "permission_count": perm_count,
        })
    return grants, has_sig


def _parse_java_security(path):
    """Extract crypto providers and disabled algorithms."""
    providers = []
    disabled = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except (IOError, OSError):
        return [], {}

    # Providers: security.provider.N=CLASS
    prov_re = re.compile(r"^security\.provider\.(\d+)\s*=\s*(.+?)\s*$",
                         re.MULTILINE)
    for m in prov_re.finditer(text):
        providers.append((int(m.group(1)), m.group(2).strip()))
    providers.sort(key=lambda x: x[0])

    # Disabled algorithm lists may span multiple lines with continuation `\`.
    # We only care about the three known keys; handle them one-by-one with
    # a small parser that joins continuation lines.
    for key in ("jdk.certpath.disabledAlgorithms",
                "jdk.jar.disabledAlgorithms",
                "jdk.tls.disabledAlgorithms"):
        pat = re.compile(
            r"^" + re.escape(key) + r"\s*=\s*((?:.*\\\n)*.*)$",
            re.MULTILINE)
        m = pat.search(text)
        if m:
            val = m.group(1).replace("\\\n", " ").strip()
            disabled[key] = val

    return providers, disabled


def cmd_policy_inspect(base_dir, policy_dir=None, verify_signatures=False):
    _ = base_dir
    path, src = _resolve_policy_dir(policy_dir)
    if not path:
        print("")
        print("  ERROR: could not locate bin/policy directory.")
        if isinstance(src, list):
            for label, p in src:
                print("    {:20s} {}".format(label, p))
        print("")
        return

    signing_fp = os.path.join(path, "signing.properties")
    policy_fp = os.path.join(path, "java.policy")
    security_fp = os.path.join(path, "java.security")

    print("")
    print("=" * 72)
    print("  POLICY INSPECTION")
    print("=" * 72)
    print("  Directory:  {}".format(path))
    print("  Source:     {}".format(src))
    print("")

    # Signing trust anchor
    print("  SIGNING TRUST ANCHOR (signing.properties)")
    print("  " + "-" * 68)
    if not os.path.isfile(signing_fp):
        print("    MISSING: {}".format(signing_fp))
    else:
        props = _parse_signing_properties(signing_fp) or {}
        fields = [
            ("subjectDN", props.get("subjectDN", "")),
            ("issuerDN", props.get("issuerDN", "")),
            ("serialNumber", props.get("serialNumber", "")),
            ("notBefore", _format_millis(props.get("notBefore", ""))),
            ("notAfter", _format_millis(props.get("notAfter", ""))),
        ]
        for k, v in fields:
            print("    {:14s} {}".format(k + ":", v))
    print("")

    # java.policy grants
    print("  JAVA.POLICY GRANTS")
    print("  " + "-" * 68)
    if not os.path.isfile(policy_fp):
        print("    MISSING: {}".format(policy_fp))
    else:
        grants, has_sig = _parse_java_policy(policy_fp)
        print("    Total grant blocks: {}".format(len(grants)))
        print("")
        print("    {:60s} {}".format("codeBase", "permissions"))
        for g in grants[:25]:
            cb = g["codeBase"]
            if len(cb) > 60:
                cb = "..." + cb[-57:]
            print("    {:60s} {:>5d}".format(cb, g["permission_count"]))
        if len(grants) > 25:
            print("    ... {} more grants".format(len(grants) - 25))
        print("")
        sig_label = "DETECTED" if has_sig else "NOT FOUND"
        print("    SIGNATURE BLOCK (-----BEGIN NIAGARA SIGNATURE-----): {}".format(
            sig_label))
        if verify_signatures:
            print("    [--verify-signatures] stdlib PKCS7 verification not "
                  "implemented — block presence only.")
    print("")

    # java.security
    print("  JAVA.SECURITY")
    print("  " + "-" * 68)
    if not os.path.isfile(security_fp):
        print("    MISSING: {}".format(security_fp))
    else:
        providers, disabled = _parse_java_security(security_fp)
        print("    Crypto providers ({}):".format(len(providers)))
        for idx, cls in providers:
            print("      {:>2d}. {}".format(idx, cls))
        print("")
        if disabled:
            print("    Disabled algorithms:")
            for key in sorted(disabled):
                val = disabled[key]
                if len(val) > 100:
                    val = val[:97] + "..."
                print("      {}".format(key))
                print("        {}".format(val))
    print("")
