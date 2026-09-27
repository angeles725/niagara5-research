"""
Bypass status — reports whether two documented, license-gated bypasses are
currently active on this install:

  1. classloader skipModuleValidation
     - system prop: niagara.classLoader.skipModuleValidation=true
     - license gate: feature "developer" with skipModuleValidation="true"
     Both must be present for the bypass to take effect.

  2. security manager disable
     - system prop: niagara.security.manager.disable=true
     - license gate: feature "smDeveloperMode" present

Evidence pointers (from decompiled baja / httpClient-rt in session
niagara-research 2026-04-20):
  com.tridium.sys.module.ModuleClassLoader    — lines 88-96, 543-569

Command:
  bypass-status [--dir NIAGARA_HOME]
"""

import os

from module_nav_lib.license_inspect import (
    load_all_licenses, resolve_niagara_home,
)


# Key = bypass id; value = config describing the checks.
BYPASSES = [
    {
        "id": "skipModuleValidation",
        "label": "Skip Module Validation (classloader cert chain bypass)",
        "prop": "niagara.classLoader.skipModuleValidation",
        "expected": "true",
        "feature": "developer",
        "feature_attr": "skipModuleValidation",
        "feature_attr_expected": "true",
        "activation_hint": (
            "add 'niagara.classLoader.skipModuleValidation=true' to "
            "etc/system.properties"),
    },
    {
        "id": "smDisable",
        "label": "Security Manager disable (JSM off)",
        "prop": "niagara.security.manager.disable",
        "expected": "true",
        "feature": "smDeveloperMode",
        "feature_attr": None,
        "feature_attr_expected": None,
        "activation_hint": (
            "add 'niagara.security.manager.disable=true' to "
            "etc/system.properties"),
    },
]


def _load_properties(path):
    """Tiny Java .properties reader — ignores comments/blank, no continuations."""
    if not os.path.isfile(path):
        return None
    props = {}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\r\n")
                if not line or line.lstrip().startswith("#"):
                    continue
                if line.lstrip().startswith("!"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
    except (IOError, OSError):
        return None
    return props


def _check_prop(prop_name, expected, prop_files):
    """Look up prop in each file; return (any_set_value_or_None, per_file_results)."""
    per_file = []
    effective_value = None
    for fp, props in prop_files:
        if props is None:
            per_file.append((fp, "(file missing)"))
            continue
        v = props.get(prop_name)
        if v is None:
            per_file.append((fp, "NOT SET"))
        else:
            per_file.append((fp, v))
            # Later files in the list win (etc overrides defaults).
            effective_value = v
    active = (effective_value is not None and
              effective_value.strip().lower() == expected.strip().lower())
    return active, effective_value, per_file


def _check_feature(licenses, feat_name, attr_name, attr_expected):
    """Scan all licenses; return list of (vendor, license_file, attrs_if_match)."""
    hits = []
    for lic in licenses or []:
        for f in lic["features"]:
            if f["name"] != feat_name:
                continue
            if attr_name is None:
                hits.append((lic["vendor"], lic["file"], f["attrs"]))
            else:
                v = f["attrs"].get(attr_name)
                if v is not None and v.strip().lower() == attr_expected.strip().lower():
                    hits.append((lic["vendor"], lic["file"], f["attrs"]))
    return hits


def cmd_bypass_status(base_dir, niagara_dir=None):
    _ = base_dir
    home = niagara_dir
    if not home or not os.path.isdir(home):
        home, _src = resolve_niagara_home(niagara_dir)
    if not home:
        print("")
        print("  ERROR: could not locate Niagara home.")
        print("  Pass --dir /path/to/niagara-install or set $NIAGARA_HOME.")
        print("")
        return

    etc_fp = os.path.join(home, "etc", "system.properties")
    defaults_fp = os.path.join(home, "defaults", "system.properties")
    # Order matters: defaults first, etc second (etc overrides).
    prop_files = [
        (defaults_fp, _load_properties(defaults_fp)),
        (etc_fp, _load_properties(etc_fp)),
    ]

    licenses, lic_dir, lic_src = load_all_licenses()

    print("")
    print("=" * 72)
    print("  BYPASS STATUS")
    print("=" * 72)
    print("  Niagara home:  {}".format(home))
    print("  Licenses:      {} ({} file(s))".format(
        lic_dir or "(not found)", len(licenses or [])))
    print("")

    for bp in BYPASSES:
        print("  === {} ===".format(bp["label"]))
        prop_active, effective, per_file = _check_prop(
            bp["prop"], bp["expected"], prop_files)

        print("    Condition 1 — system property")
        print("      key:       {}".format(bp["prop"]))
        print("      expected:  = {}".format(bp["expected"]))
        for fp, val in per_file:
            print("      {:42s} {}".format(fp + ":", val))
        print("      status:    {}".format("ACTIVE" if prop_active else "INACTIVE"))

        print("    Condition 2 — license feature")
        if bp["feature_attr"]:
            print("      feature:   '{}' with {}='{}'".format(
                bp["feature"], bp["feature_attr"], bp["feature_attr_expected"]))
        else:
            print("      feature:   '{}' present".format(bp["feature"]))

        hits = _check_feature(
            licenses, bp["feature"], bp["feature_attr"],
            bp["feature_attr_expected"])
        if not hits:
            print("      match:     NOT PRESENT in any license")
            feat_active = False
        else:
            feat_active = True
            for vendor, fname, attrs in hits:
                attr_parts = " ".join(
                    "{}={}".format(k, v) for k, v in sorted(attrs.items()))
                print("      match:     [{}] {} ({})".format(
                    vendor, fname, attr_parts or "(no attrs)"))
        print("      status:    {}".format(
            "ACTIVE" if feat_active else "INACTIVE"))

        combined = prop_active and feat_active
        print("    Combined:  {}".format(
            "BYPASS EFFECTIVE" if combined else
            "LICENSE-GATED bypass AVAILABLE (add system prop)"
            if feat_active else
            "DISABLED (license feature missing — cannot activate)"))
        if not prop_active and feat_active:
            print("    To activate: {}".format(bp["activation_hint"]))
        print("")
