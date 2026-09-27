"""
Feasibility check — given a source `module-permissions.xml` plus a signing
certificate, simulate whether the module would deploy against the current
trust anchor, and if not, suggest the bypass path.

Command:
  feasibility-check --module-permissions <source.xml> --signing-cert <cert.pem>
    [--anchor-dir PATH] [--keytool PATH]

Stdlib only. Shells out to keytool for cert parsing (Windows-encoding safe).
"""

import os
import re
import subprocess
import xml.etree.ElementTree as ET

from module_nav_lib.permission_report import _META as GROUP_META
from module_nav_lib.trust_anchor import (
    _find_keytool, _normalize_dn, _parse_keytool_output, _resolve_anchor,
)


def _parse_source_permissions(path):
    """Parse a source `module-permissions.xml` → list of requested groups.

    Returns list of dicts: {type, group, purposeKey, params: [(name, value)]}.
    Raises on parse failure (caller prints).
    """
    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != "permissions":
        raise ValueError(
            "Expected <permissions> root, got <{}>".format(root.tag))
    reqs = []
    for jps in root.findall("niagara-permission-groups"):
        ptype = jps.get("type", "")
        for rp in jps.findall("req-permission"):
            name_el = rp.find("name")
            group = name_el.text.strip() if (name_el is not None and name_el.text) else ""
            purpose_el = rp.find("purposeKey")
            purpose = purpose_el.text.strip() if (purpose_el is not None and purpose_el.text) else ""
            params = []
            params_el = rp.find("parameters")
            if params_el is not None:
                for p in params_el.findall("parameter"):
                    params.append((p.get("name", ""), p.get("value", "")))
            reqs.append({
                "type": ptype,
                "group": group,
                "purposeKey": purpose,
                "params": params,
            })
    return reqs


def _run_keytool_file(keytool_path, cert_path, timeout=30):
    try:
        proc = subprocess.run(
            [keytool_path, "-printcert", "-file", cert_path],
            capture_output=True, timeout=timeout,
        )
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return -1, "", "keytool timed out"
    except (OSError, subprocess.SubprocessError) as e:
        return -1, "", str(e)


def _parse_single_cert(text):
    """Parse keytool -printcert -file output (single cert, no 'Signer #N:' split).

    Reuse the same field parsers from trust_anchor but without the signer split.
    """
    # Prepend a synthetic 'Signer #1:' so _parse_keytool_output works.
    synthetic = "Signer #1:\n\n" + text
    recs = _parse_keytool_output(synthetic)
    if not recs:
        return None
    return recs[0]


def cmd_feasibility_check(base_dir, module_permissions, signing_cert,
                          anchor_dir=None, keytool=None):
    _ = base_dir

    print("")
    print("=" * 72)
    print("  FEASIBILITY CHECK")
    print("=" * 72)
    print("  source perms:   {}".format(module_permissions))
    print("  signing cert:   {}".format(signing_cert))
    print("")

    if not os.path.isfile(module_permissions):
        print("  ERROR: module-permissions.xml not found.")
        print("")
        return
    if not os.path.isfile(signing_cert):
        print("  ERROR: signing cert not found.")
        print("")
        return

    # Parse source XML.
    try:
        reqs = _parse_source_permissions(module_permissions)
    except (ET.ParseError, ValueError) as e:
        print("  ERROR parsing module-permissions.xml: {}".format(e))
        print("")
        return

    print("  REQUESTED PERMISSION GROUPS ({}):".format(len(reqs)))
    if not reqs:
        print("    (none — empty declaration)")
    by_type = {}
    for r in reqs:
        by_type.setdefault(r["type"], []).append(r)
    for ptype, items in sorted(by_type.items()):
        print("    type={}".format(ptype))
        for r in items:
            sev, signed = GROUP_META.get(r["group"], ("?", False))
            print("      {:28s} [sev={}, signed={}]".format(
                r["group"][:28], sev, "yes" if signed else "no"))
            if r["purposeKey"]:
                print("        purpose: {}".format(r["purposeKey"]))
            for name, value in r["params"]:
                print("        {}={}".format(name, value))
    print("")

    # Which groups require signing?
    signed_groups = [
        r["group"] for r in reqs
        if GROUP_META.get(r["group"], ("", False))[1]
    ]
    if signed_groups:
        print("  SIGNED-REQUIRED groups requested: {}".format(
            ", ".join(sorted(set(signed_groups)))))
    else:
        print("  SIGNED-REQUIRED groups requested: (none)")
    print("")

    # Cert introspection via keytool.
    kt = _find_keytool(keytool)
    if not kt:
        print("  ERROR: keytool not found. Pass --keytool or ensure one is on PATH.")
        print("")
        return
    rc, out, err = _run_keytool_file(kt, signing_cert)
    if rc != 0:
        print("  ERROR: keytool failed (rc={}): {}".format(rc, err.strip()))
        print("")
        return

    cert = _parse_single_cert(out)
    if not cert:
        print("  ERROR: could not parse keytool output (dumping first lines):")
        print("    " + "\n    ".join(out.splitlines()[:8]))
        print("")
        return

    anchor, anchor_fp = _resolve_anchor(anchor_dir)
    anchor_subject = anchor.get("subjectDN", "")
    anchor_issuer = anchor.get("issuerDN", "")

    print("  SIGNING CERTIFICATE")
    print("    Owner:     {}".format(cert["owner"]))
    print("    Issuer:    {}".format(cert["issuer"]))
    print("    Valid:     {} -> {}".format(
        cert["valid_from"], cert["valid_until"]))
    print("    SHA256:    {}".format(cert["sha256"]))
    print("    KeyUsage:  {}".format(", ".join(cert["ku"]) or "(absent)"))
    print("    ExtKeyUsage: {}".format(", ".join(cert["eku"]) or "(absent)"))
    print("    BasicConstraints: {}".format(
        cert["basic_constraints"] or "(absent)"))
    print("")

    print("  TRUST ANCHOR (from {}):".format(
        anchor_fp or "(not found)"))
    print("    subjectDN: {}".format(anchor_subject or "(none)"))
    print("    issuerDN:  {}".format(anchor_issuer or "(none)"))
    print("")

    owner_n = _normalize_dn(cert["owner"])
    issuer_n = _normalize_dn(cert["issuer"])
    anchor_subj_n = _normalize_dn(anchor_subject)
    anchor_iss_n = _normalize_dn(anchor_issuer)

    is_self_signed = owner_n and owner_n == issuer_n
    dn_matches_anchor = anchor_subj_n and (
        owner_n == anchor_subj_n or issuer_n == anchor_subj_n)
    issuer_matches_anchor = anchor_iss_n and issuer_n == anchor_iss_n
    has_code_signing = "codesigning" in " ".join(cert["eku"]).lower().replace(" ", "")

    reasons_blocking = []
    if not dn_matches_anchor and not issuer_matches_anchor:
        reasons_blocking.append(
            "Cert does NOT chain to trust anchor (neither DN nor issuer match).")
    if is_self_signed and not dn_matches_anchor:
        reasons_blocking.append(
            "Cert is self-signed (Owner == Issuer).")
    if not has_code_signing:
        reasons_blocking.append(
            "Cert lacks ExtendedKeyUsage=codeSigning (OID 1.3.6.1.5.5.7.3.3).")
    bc = (cert.get("basic_constraints") or "").upper().replace(" ", "")
    if "CA:TRUE" in bc:
        reasons_blocking.append(
            "Cert has BasicConstraints CA=TRUE (expected leaf cert).")

    print("  VERDICT")
    if not reasons_blocking:
        print("    GO — cert is valid leaf signed by the trust anchor.")
        print("    Module would deploy via standard validateCertChain path.")
        print("")
        return

    print("    NO-GO — module would be rejected by cert chain validation.")
    print("    Blocking reasons:")
    for r in reasons_blocking:
        print("      - {}".format(r))
    print("")

    # Suggest bypass — cross-reference with bypass-status logic.
    from module_nav_lib.license_inspect import load_all_licenses
    licenses, _lic_dir, _src = load_all_licenses()
    dev_feature_active = False
    for lic in licenses or []:
        for feat in lic["features"]:
            if feat["name"] == "developer" and \
               feat["attrs"].get("skipModuleValidation", "").lower() == "true":
                dev_feature_active = True
                break
        if dev_feature_active:
            break

    print("  SUGGESTED BYPASS")
    print("    Bypass: niagara.classLoader.skipModuleValidation=true")
    if dev_feature_active:
        print("    License gate:  ACTIVE (feature 'developer' with "
              "skipModuleValidation=true present)")
        print("    Action needed: add the system property to etc/system.properties")
        print("    Confirm status: run 'bypass-status'")
    else:
        print("    License gate:  INACTIVE (feature 'developer' with "
              "skipModuleValidation=true absent)")
        print("    Bypass NOT available on this host — cert MUST chain to anchor, "
              "OR obtain a license with the developer feature.")
    print("")
