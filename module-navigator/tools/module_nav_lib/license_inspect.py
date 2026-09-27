"""
License inspection — parse installed `.license` XML files and aggregate.

Reads:
  <license vendor="X" expiration="YYYY-MM-DD" hostId="..." version="..." ...>
    <feature name="developer" moduleDev="true" skipModuleValidation="true"/>
    ...
  </license>

Commands wired:
  license-inspect [--dir PATH] [--critical-features]
    Full report: license headers + features per vendor + shared + SMA-exempt
    + critical (bypass-enabling) features.
    --critical-features limits output to the critical-features table.

Default directory: $NIAGARA_HOME/security/licenses, fallback to the project's
known install ($NIAGARA_INSTALL env var or hard-coded path resolved once).

Stdlib only. No deps.
"""

import glob
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict


# License feature names that gate privileged bypasses or developer modes.
# These attribute names are the ones whose presence with value="true" unlocks
# the bypass; feature merely existing is not enough.
CRITICAL_FEATURES = {
    "developer": ["moduleDev", "skipModuleValidation"],
    "smDeveloperMode": [],
    "skipModuleValidation": [],
    "moduleDev": [],
    "bulkCertSigner": [],
    "certSigningService": [],
}


def resolve_niagara_home(explicit=None):
    """Find the Niagara install root.

    Priority:
      1. explicit argument (--dir parent)
      2. $NIAGARA_HOME env var
      3. hard-coded fallback for this workstation
    Returns (path, source_label) or (None, tried_list).
    """
    tried = []
    if explicit:
        tried.append(("explicit", explicit))
        if os.path.isdir(explicit):
            return explicit, "explicit"

    env = os.environ.get("NIAGARA_HOME")
    if env:
        tried.append(("env NIAGARA_HOME", env))
        if os.path.isdir(env):
            return env, "env NIAGARA_HOME"

    fallback = "/home/cristian/Honeywell/OptimizerSupervisor-N4.14.0.162"
    tried.append(("fallback", fallback))
    if os.path.isdir(fallback):
        return fallback, "fallback"

    return None, tried


def resolve_license_dir(explicit=None):
    """Resolve the directory containing .license files.

    If explicit is an absolute dir, use it. Otherwise derive from Niagara home.
    """
    if explicit and os.path.isdir(explicit):
        return explicit, "explicit"
    home, src = resolve_niagara_home()
    if not home:
        return None, src
    cand = os.path.join(home, "security", "licenses")
    if os.path.isdir(cand):
        return cand, "derived from {}".format(src)
    return None, [("derived", cand)]


def _parse_license_file(path):
    """Parse a single .license file into a dict or None on failure."""
    try:
        tree = ET.parse(path)
    except (ET.ParseError, IOError, OSError):
        return None
    root = tree.getroot()
    if root.tag != "license":
        return None
    features = []
    for feat in root.findall("feature"):
        name = feat.get("name", "")
        attrs = {k: v for k, v in feat.attrib.items() if k != "name"}
        features.append({"name": name, "attrs": attrs})
    return {
        "file": os.path.basename(path),
        "path": path,
        "vendor": root.get("vendor", ""),
        "expiration": root.get("expiration", ""),
        "hostId": root.get("hostId", ""),
        "version": root.get("version", ""),
        "generated": root.get("generated", ""),
        "features": features,
    }


def _format_critical_attrs(feat, critical_keys):
    """Return a short string showing which critical attrs are set to true."""
    if not critical_keys:
        return "(present)"
    parts = []
    for k in critical_keys:
        v = feat["attrs"].get(k)
        if v is not None:
            parts.append("{}={}".format(k, v))
    return " ".join(parts) if parts else "(present, no critical attrs)"


def cmd_license_inspect(base_dir, license_dir=None, critical_only=False,
                        md_output=False):
    """Entry point for `license-inspect`."""
    _ = base_dir
    path, src = resolve_license_dir(license_dir)
    if not path:
        print("")
        print("  ERROR: could not locate license directory.")
        if isinstance(src, list):
            print("  Tried:")
            for label, p in src:
                print("    {:20s} {}".format(label, p))
        print("")
        print("  Pass --dir /path/to/licenses OR set $NIAGARA_HOME.")
        print("")
        return

    files = sorted(glob.glob(os.path.join(path, "*.license")))
    if not files:
        print("")
        print("  No .license files found in {}".format(path))
        print("")
        return

    licenses = []
    failures = []
    for f in files:
        parsed = _parse_license_file(f)
        if parsed is None:
            failures.append(os.path.basename(f))
        else:
            licenses.append(parsed)

    if md_output:
        _print_md(licenses, path, src, failures, critical_only)
        return

    if critical_only:
        _print_critical(licenses, path)
        return

    _print_header(licenses, path, src, failures)
    _print_feature_summary(licenses)
    _print_critical(licenses, path)


def _print_md(licenses, path, src, failures, critical_only):
    from collections import defaultdict
    from datetime import datetime

    print("---")
    print("title: License inspection")
    print("generated: {}".format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    print("source: tools/module_nav.py license-inspect")
    print("directory: {}".format(path))
    print("resolution: {}".format(src))
    print("licenses: {}".format(len(licenses)))
    if failures:
        print("parse_failures: [{}]".format(", ".join(failures)))
    print("---")
    print("")
    print("# License inspection")
    print("")
    print("## Installed licenses")
    print("")
    print("| Vendor | File | Expiration | HostId | Version |")
    print("|--------|------|------------|--------|---------|")
    for lic in licenses:
        print("| {} | `{}` | {} | `{}` | {} |".format(
            lic["vendor"], lic["file"], lic["expiration"],
            lic["hostId"], lic["version"]))
    print("")

    if not critical_only:
        by_vendor = defaultdict(set)
        feature_owners = defaultdict(set)
        sma_exempt = []
        for lic in licenses:
            for f in lic["features"]:
                by_vendor[lic["vendor"]].add(f["name"])
                feature_owners[f["name"]].add(lic["vendor"])
                if f["attrs"].get("sma.exempt") == "true":
                    sma_exempt.append((lic["vendor"], f["name"]))

        print("## Feature summary")
        print("")
        print("| Metric | Value |")
        print("|--------|------:|")
        print("| Unique feature names | {} |".format(len(feature_owners)))
        print("| Shared across 2+ vendors | {} |".format(
            len([1 for vs in feature_owners.values() if len(vs) > 1])))
        print("| SMA-exempt entries | {} |".format(len(sma_exempt)))
        print("")
        print("### Features per vendor")
        print("")
        print("| Vendor | Features |")
        print("|--------|---------:|")
        for v in sorted(by_vendor):
            print("| {} | {} |".format(v, len(by_vendor[v])))
        print("")
        if sma_exempt:
            print("### SMA-exempt")
            print("")
            print("| Vendor | Feature |")
            print("|--------|---------|")
            for v, fn in sma_exempt:
                print("| {} | `{}` |".format(v, fn))
            print("")

    print("## Critical (bypass-enabling) features")
    print("")
    print("| Feature | Status | Vendor | License | Critical attrs |")
    print("|---------|--------|--------|---------|----------------|")
    for crit_name, crit_attrs in sorted(CRITICAL_FEATURES.items()):
        rows = []
        for lic in licenses:
            for f in lic["features"]:
                if f["name"] == crit_name:
                    rows.append((lic["vendor"], lic["file"], f))
        if not rows:
            print("| `{}` | NOT PRESENT | — | — | — |".format(crit_name))
            continue
        for vendor, fname, feat in rows:
            details = _format_critical_attrs(feat, crit_attrs)
            print("| `{}` | PRESENT | {} | `{}` | {} |".format(
                crit_name, vendor, fname, details))
    print("")


def _print_header(licenses, path, src, failures):
    print("")
    print("=" * 72)
    print("  LICENSE INSPECTION")
    print("=" * 72)
    print("  Directory:  {}".format(path))
    print("  Source:     {}".format(src))
    print("  Files:      {}   parsed: {}   failed: {}".format(
        len(licenses) + len(failures), len(licenses), len(failures)))
    if failures:
        print("  Skipped:    {}".format(", ".join(failures)))
    print("")
    print("  {:18s} {:28s} {:12s} {:24s}".format(
        "VENDOR", "FILE", "EXPIRATION", "HOST_ID"))
    print("  " + "-" * 84)
    for lic in licenses:
        print("  {:18s} {:28s} {:12s} {:24s}".format(
            lic["vendor"][:18],
            lic["file"][:28],
            lic["expiration"][:12],
            lic["hostId"][:24]))
    print("")


def _print_feature_summary(licenses):
    # Features per vendor (dedup by feature name within a vendor).
    by_vendor = defaultdict(set)
    feature_owners = defaultdict(set)  # feature_name -> set(vendor)
    sma_exempt = []
    total_feat_entries = 0

    for lic in licenses:
        v = lic["vendor"]
        for f in lic["features"]:
            total_feat_entries += 1
            by_vendor[v].add(f["name"])
            feature_owners[f["name"]].add(v)
            if f["attrs"].get("sma.exempt") == "true":
                sma_exempt.append((v, f["name"]))

    shared = sorted(
        [fn for fn, vs in feature_owners.items() if len(vs) > 1])

    print("  FEATURE SUMMARY")
    print("  Total feature entries:       {}".format(total_feat_entries))
    print("  Unique feature names:        {}".format(len(feature_owners)))
    print("  Shared across 2+ vendors:    {}".format(len(shared)))
    print("  SMA-exempt entries:          {}".format(len(sma_exempt)))
    print("")
    print("  Features per vendor:")
    for v in sorted(by_vendor):
        print("    {:18s} {} features".format(v[:18], len(by_vendor[v])))
    print("")

    if sma_exempt:
        print("  SMA-EXEMPT features (sma.exempt=\"true\"):")
        for v, fn in sma_exempt:
            print("    {:18s} {}".format(v[:18], fn))
        print("")


def _print_critical(licenses, _path):
    print("  CRITICAL FEATURES (bypass-enabling)")
    print("  " + "-" * 68)
    for crit_name, crit_attrs in sorted(CRITICAL_FEATURES.items()):
        hits = []
        for lic in licenses:
            for f in lic["features"]:
                if f["name"] == crit_name:
                    hits.append((lic["vendor"], lic["file"], f))
        if not hits:
            print("  {:22s} NOT PRESENT".format(crit_name))
            continue
        first = True
        for vendor, fname, feat in hits:
            tag = crit_name if first else ""
            first = False
            details = _format_critical_attrs(feat, crit_attrs)
            print("  {:22s} [{:18s}] {} ({})".format(
                tag, vendor[:18], details, fname))
    print("")


def load_all_licenses(license_dir=None):
    """Helper for other commands (e.g. bypass-status) to reuse parsing.

    Returns (licenses, dir_path, src) where licenses is a list of dicts or
    None on failure.
    """
    path, src = resolve_license_dir(license_dir)
    if not path:
        return None, None, src
    licenses = []
    for f in sorted(glob.glob(os.path.join(path, "*.license"))):
        parsed = _parse_license_file(f)
        if parsed:
            licenses.append(parsed)
    return licenses, path, src
