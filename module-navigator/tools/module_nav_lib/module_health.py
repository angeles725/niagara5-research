"""
Module Health Scorecard for Module Navigator (Batch 5, Gap #21).

Aggregates all validation gap commands into a single A/B/C/D/F scorecard
showing how well-built a module is.

Commands:
  module-health <module> [--json]

Scoring categories:
  SLOT HYGIENE      - slot collisions, intra-module duplicates, lexicon coverage
  ORD SAFETY        - dangling ORDs, unsafe .resolve(), external service in SS
  SERIALIZATION     - missing UIDs, serial conflicts
  ARCHITECTURE      - circular deps, god classes, layer violations
  SECURITY          - hardcoded credentials, insecure patterns, permission gaps
  DEPENDENCIES      - third-party, honeywell add-ons, platform deps

Reuses: slot_collision, ord_validate, resolve_audit, service_order,
        driver_cleanup, serialization, analysis (security-audit),
        architecture (cycles, god-classes, layer-check), dependency_audit
"""

import io
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Grade thresholds
# ---------------------------------------------------------------------------

_GRADE_THRESHOLDS = [
    (90, 'A', 'excellent — production ready'),
    (75, 'B', 'good — minor issues'),
    (60, 'C', 'fair — review recommended'),
    (40, 'D', 'poor — significant issues'),
    (0,  'F', 'critical — do not deploy'),
]


def _grade(score):
    """Return (grade, description) for a score 0-100."""
    for threshold, grade, desc in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade, desc
    return 'F', 'critical — do not deploy'


def _clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Sub-command runners (call functions directly for data, no subprocess)
# ---------------------------------------------------------------------------

def _run_slot_collision(base_dir, module_name):
    """Run slot-collision for a specific module, return parsed data.

    Returns dict with keys: total_collisions, intra_module_dups, lexicon_coverage_pct
    """
    from module_nav_lib.slot_collision import (
        _load_annotations, _load_class_index, _build_slot_index, _find_collisions
    )

    ann = _load_annotations(base_dir)
    ci = _load_class_index(base_dir)
    if not ann:
        return None

    niagara_types = ann.get("niagara_types", {})
    total_slots = sum(len(e.get("properties", [])) for e in niagara_types.values())

    # Build slot index
    slot_index = _build_slot_index(niagara_types)

    # Find all collisions (no filter yet — we'll filter per-slot)
    all_collisions = _find_collisions(slot_index, module_filter=None)

    # Now filter: only collisions involving the target module
    # Each collision: list of {class, module, type}
    collisions_involving_module = []
    for c in all_collisions:
        refs = c["refs"]
        modules_in_collision = set(r["module"] for r in refs)
        if module_name in modules_in_collision:
            collisions_involving_module.append(c)

    # Intra-module duplicates: same slot name used multiple times within the same module
    # (a slot defined on two different classes in the same module)
    intra_module_dups = 0
    for c in all_collisions:
        refs = c["refs"]
        # Group refs by module
        module_refs = {}
        for r in refs:
            m = r["module"]
            if m not in module_refs:
                module_refs[m] = []
            module_refs[m].append(r)

        # If any module has 2+ refs for this slot, that's an intra-module dup
        for m, m_refs in module_refs.items():
            if len(m_refs) > 1:
                intra_module_dups += 1
                break  # count each collision once even if multiple dups within

    # Lexicon coverage: what % of module's classes have annotations
    # For this module, count annotated classes vs total classes
    module_classes = set()
    total_classes = 0
    annotated_in_module = 0
    for class_name, entry in niagara_types.items():
        if entry.get("module") == module_name:
            annotated_in_module += 1
        total_classes += 1  # rough estimate

    # Better approach: count module's annotated classes vs all its classes
    ci_data = ci
    if ci_data:
        module_class_names = set()
        annotated_in_mod = set()
        classes_data = ci_data.get("classes", {})
        for cn, entries in classes_data.items():
            for e in entries:
                if e.get("module") == module_name and e.get("outer_class") is None:
                    module_class_names.add(cn)
        for cn in niagara_types:
            entry = niagara_types.get(cn, {})
            if entry.get("module") == module_name:
                annotated_in_mod.add(cn)

        total_module_classes = len(module_class_names)
        annotated_module_classes = len(annotated_in_mod)
        if total_module_classes > 0:
            lexicon_coverage = int(100.0 * annotated_module_classes / total_module_classes)
        else:
            lexicon_coverage = 100  # no classes found, assume OK
    else:
        lexicon_coverage = 100

    return {
        "slot_collisions": len(collisions_involving_module),
        "intra_module_dups": intra_module_dups,
        "lexicon_coverage_pct": lexicon_coverage,
        "total_slots": total_slots,
    }


def _run_ord_validate(base_dir, module_name):
    """Run ord-validate for a module, return dangling ORD count."""
    from module_nav_lib.ord_validate import (
        _load_annotations, _load_class_index,
        _build_known_slots, _build_known_components, _build_class_for_slot,
        _query_module_ords, _validate_ord,
    )

    known_slots = _build_known_slots(base_dir)
    known_components = _build_known_components(base_dir)
    slot_to_classes = _build_class_for_slot(base_dir)

    ords = _query_module_ords(base_dir, module_name)
    if not ords:
        return {"dangling_ords": 0, "total_ords": 0}

    dangling = 0
    for o in ords:
        v = _validate_ord(o, known_slots, known_components, slot_to_classes)
        if v["status"] == "DANGLING":
            dangling += 1

    return {
        "dangling_ords": dangling,
        "total_ords": len(ords),
    }


def _run_resolve_audit(base_dir, module_name):
    """Run resolve-audit for a module, return unsafe resolve count."""
    from module_nav_lib.resolve_audit import (
        _load_class_index, _load_module_inv, _get_source_root,
        _read_source, _RE_UNSAFE, _RE_RESOLVE,
    )

    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return None

    inv_data = _load_module_inv(base_dir)
    source_root = _get_source_root(ci_data)
    if not source_root:
        return None

    classes = ci_data.get("classes", {})

    unsafe_count = 0
    safe_count = 0
    files_scanned = 0

    for class_name, entries in classes.items():
        for entry in entries:
            if entry.get("outer_class") is not None:
                continue
            if entry["module"] != module_name:
                continue

            filepath = os.path.join(source_root, entry["path"])
            if not os.path.isfile(filepath):
                continue

            lines = _read_source(filepath)
            files_scanned += 1

            for i, line in enumerate(lines, 1):
                if not _RE_RESOLVE.search(line):
                    continue
                if _RE_UNSAFE.search(line):
                    unsafe_count += 1
                else:
                    safe_count += 1

    return {
        "unsafe_resolves": unsafe_count,
        "safe_resolves": safe_count,
    }


def _run_service_order(base_dir, module_name):
    """Run service-order analysis, return external service count."""
    from module_nav_lib.service_order import (
        _load_method_index, _load_class_index,
        _get_source_root,
        _find_method_body, _extract_ords_from_method_body,
        _extract_service_name_from_ord, _extract_service_class_from_source,
        _classify_service_resolution,
    )

    mi = _load_method_index(base_dir)
    if not mi:
        return {"external_service_count": 0}

    ci = _load_class_index(base_dir)
    if not ci:
        return {"external_service_count": 0}

    classes = ci.get("classes", {})
    source_root = _get_source_root(ci)
    if not source_root:
        return {"external_service_count": 0}

    methods_idx = mi.get("methods", {})
    service_started_entries = methods_idx.get("serviceStarted", [])

    external_count = 0
    for entry in service_started_entries:
        if entry.get("module") != module_name:
            continue
        cname = entry.get("class", "")
        if not cname:
            continue

        class_entries = classes.get(cname, [])
        if not class_entries:
            continue
        ce = class_entries[0]
        if ce.get("outer_class") is not None:
            continue

        filepath = os.path.join(source_root, ce["path"])
        if not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except (IOError, OSError):
            continue

        body_start, body_end = _find_method_body(lines, "serviceStarted", entry.get("line", 0))
        if body_start >= body_end:
            body_end = body_start

        ords = _extract_ords_from_method_body(lines, body_start, body_end)

        for ord_val in ords:
            slot_name, canonical_class = _extract_service_name_from_ord(ord_val)
            inferred_class = _extract_service_class_from_source(
                lines[body_start - 1:body_end], ord_val)
            service_class = inferred_class or canonical_class
            if not service_class:
                continue
            classification, svc_module = _classify_service_resolution(
                ord_val, service_class, ci, module_name)
            if classification == "EXTERNAL":
                external_count += 1

    return {
        "external_service_count": external_count,
    }


def _run_serial_audit(base_dir, module_name):
    """Run serial-audit for a module, return missing UID and conflict counts."""
    # Capture stdout to parse text output
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        # Import and call the function — it prints to stdout
        from module_nav_lib.serialization import cmd_serial_audit
        cmd_serial_audit(base_dir, module_filter=module_name, limit=5000)
    except Exception as e:
        sys.stdout = old_stdout
        return {"missing_uids": 0, "serial_conflicts": 0, "error": str(e)}
    finally:
        output = captured.getvalue()
        sys.stdout = old_stdout

    # Parse the output
    missing_uids = 0
    serial_conflicts = 0

    # Pattern: "  Missing serialVersionUID: 47"
    m_uid = re.search(r'Missing serialVersionUID:\s*(\d+)', output)
    if m_uid:
        missing_uids = int(m_uid.group(1))

    # Pattern: "  CONFLICTS (same UID): 0"
    m_conf = re.search(r'CONFLICTS.*?:\s*(\d+)', output)
    if m_conf:
        serial_conflicts = int(m_conf.group(1))

    return {
        "missing_uids": missing_uids,
        "serial_conflicts": serial_conflicts,
    }


def _run_security_audit(base_dir, module_name):
    """Run security-audit for a module, return finding counts by category."""
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        from module_nav_lib.analysis import cmd_security_audit
        cmd_security_audit(base_dir, module_filter=module_name, limit=5000)
    except Exception as e:
        sys.stdout = old_stdout
        return {"hardcoded_credentials": 0, "insecure_patterns": 0, "permission_gaps": 0, "error": str(e)}
    finally:
        output = captured.getvalue()
        sys.stdout = old_stdout

    # Parse category counts from text output
    # Pattern: "  [Hardcoded Credentials] (3 findings)"
    hardcoded_creds = 0
    insecure_patterns = 0
    permission_gaps = 0

    # Map category names from analysis.py to our buckets
    # analysis.py uses: Hardcoded Credentials, SQL Injection, Path Traversal,
    #   Weak Crypto, Hardcoded IP, Insecure Cookie, etc.
    category_map = {
        "Hardcoded Credentials": "hardcoded_credentials",
        "Hardcoded Password": "hardcoded_credentials",
        "Hardcoded API Key": "hardcoded_credentials",
        "Hardcoded Secret": "hardcoded_credentials",
        "SQL Injection": "insecure_patterns",
        "Path Traversal": "insecure_patterns",
        "Command Injection": "insecure_patterns",
        "XSS": "insecure_patterns",
        "Insecure Cookie": "insecure_patterns",
        "Insecure Deserialization": "insecure_patterns",
        "XML External Entity": "insecure_patterns",
        "LDAP Injection": "insecure_patterns",
        "Template Injection": "insecure_patterns",
        "Weak Crypto": "insecure_patterns",
        "Hardcoded IP": "insecure_patterns",
        "Missing Permission Check": "permission_gaps",
        "Permission Gap": "permission_gaps",
    }

    category_counts = {}
    for line in output.split('\n'):
        m = re.match(r'\s*\[([^\]]+)\]\s*\((\d+)\s*findings?\)', line)
        if m:
            cat_name = m.group(1)
            count = int(m.group(2))
            bucket = category_map.get(cat_name, "insecure_patterns")
            category_counts[bucket] = category_counts.get(bucket, 0) + count

    return {
        "hardcoded_credentials": category_counts.get("hardcoded_credentials", 0),
        "insecure_patterns": category_counts.get("insecure_patterns", 0),
        "permission_gaps": category_counts.get("permission_gaps", 0),
    }


def _run_cycles(base_dir, module_name):
    """Run cycles analysis, return count of cycles involving the module."""
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        from module_nav_lib.architecture import cmd_cycles
        cmd_cycles(base_dir, max_depth=6, limit=5000)
    except Exception as e:
        sys.stdout = old_stdout
        return {"module_cycles": 0, "error": str(e)}
    finally:
        output = captured.getvalue()
        sys.stdout = old_stdout

    # Parse: count cycles that involve the target module
    # Pattern: cycle lines look like "  Cycle: moduleA -> moduleB -> moduleC"
    # Or from the architecture.py cycles output format
    cycle_count = 0
    in_cycle_block = False
    for line in output.split('\n'):
        if re.search(r'Cycle|Cyclic|SCC|cycle found', line, re.IGNORECASE):
            if module_name in line:
                in_cycle_block = True
                cycle_count += 1
        elif in_cycle_block:
            if line.strip().startswith('  ') and module_name in line:
                cycle_count += 1
            elif not line.strip() or line.strip().startswith('---'):
                in_cycle_block = False

    # Try parsing summary line: "Cycles found: 3"
    m_summary = re.search(r'[Cc]ycles?\s+found:\s*(\d+)', output)
    if m_summary:
        cycle_count = int(m_summary.group(1))

    return {
        "module_cycles": cycle_count,
    }


def _run_god_classes(base_dir, module_name):
    """Run god-classes analysis, return count in the module."""
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        from module_nav_lib.architecture import cmd_god_classes
        cmd_god_classes(base_dir, threshold=100, limit=5000)
    except Exception as e:
        sys.stdout = old_stdout
        return {"god_classes": 0, "error": str(e)}
    finally:
        output = captured.getvalue()
        sys.stdout = old_stdout

    # Count god classes belonging to this module
    god_count = 0
    for line in output.split('\n'):
        if module_name in line and ('god' in line.lower() or
                                   re.search(r'Score:\s*\d+', line)):
            god_count += 1

    # Try parsing: "God classes found: N" or "Total: N"
    m_god = re.search(r'god\s+classes?\s+(?:found|total)[:\s]+(\d+)', output, re.IGNORECASE)
    if m_god:
        god_count = int(m_god.group(1))

    # Try parsing per-line counts
    m_total = re.search(r'TOTAL.*?[:\s](\d+)', output, re.IGNORECASE)
    if m_total:
        god_count = int(m_total.group(1))

    return {
        "god_classes": god_count,
    }


def _run_layer_check(base_dir, module_name):
    """Run layer-check for a module, return violation count."""
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        from module_nav_lib.architecture import cmd_layer_check
        cmd_layer_check(base_dir, module_filter=module_name)
    except Exception as e:
        sys.stdout = old_stdout
        return {"layer_violations": 0, "error": str(e)}
    finally:
        output = captured.getvalue()
        sys.stdout = old_stdout

    # Parse violation count
    # Pattern: "Layer violations found: 8" or "Violations: 8"
    violations = 0
    m_viol = re.search(r'violations?\s+(?:found|total)[:\s]+(\d+)', output, re.IGNORECASE)
    if m_viol:
        violations = int(m_viol.group(1))
    else:
        # Count violation lines (typically "  VIOLATION: classA (rt) imports classB (wb)")
        for line in output.split('\n'):
            if re.search(r'VIOLATION|LAYER\s+VIOLATION', line, re.IGNORECASE):
                violations += 1

    return {
        "layer_violations": violations,
    }


def _run_dependency_audit(base_dir, module_name):
    """Run dependency-audit for a module, return counts by category."""
    # This module supports --json, so we can use the function directly
    # and capture its JSON output
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        from module_nav_lib.dependency_audit import cmd_dependency_audit
        cmd_dependency_audit(base_dir, module_name, as_json=True)
    except Exception as e:
        sys.stdout = old_stdout
        return {"third_party": 0, "honeywell": 0, "platform": 0, "error": str(e)}
    finally:
        json_output = captured.getvalue()
        sys.stdout = old_stdout

    try:
        data = json.loads(json_output)
        summary = data.get("summary", {})
        return {
            "third_party": summary.get("third_party", 0),
            "honeywell": summary.get("honeywell", 0),
            "platform": summary.get("platform", 0),
        }
    except (json.JSONDecodeError, TypeError):
        # Fallback: parse text
        return {"third_party": 0, "honeywell": 0, "platform": 0}


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def _score_slots(data):
    """Score SLOT HYGIENE category: 0-100.
    
    Uses sqrt-normalized penalties so large numbers don't instantly zero-out
    the score. A module with 500 intra-module dups shouldn't score 0.
    """
    if data is None:
        return 50  # unknown → middle score
    collisions = data.get("slot_collisions", 0)
    intra_dups = data.get("intra_module_dups", 0)
    lexicon_missing = max(0, 100 - data.get("lexicon_coverage_pct", 100))

    score = 100.0
    # Sqrt-normalized: a module with 500 dups still gets some credit
    score -= min(collisions * 1.0, 50.0)         # -1 per collision, cap at 50
    score -= min(intra_dups * 0.5, 30.0)         # -0.5 per dup, cap at 30
    score -= min(lexicon_missing * 1.0, 20.0)    # -1 per % missing, cap at 20

    return _clamp(round(score))


def _score_ords(data, resolve_data, service_data):
    """Score ORD SAFETY category: 0-100."""
    dangling = data.get("dangling_ords", 0) if data else 0
    unsafe_resolves = resolve_data.get("unsafe_resolves", 0) if resolve_data else 0
    external_svcs = service_data.get("external_service_count", 0) if service_data else 0

    score = 100.0
    score -= min(dangling * 5.0, 30.0)         # -5 per dangling ORD, cap at 30
    score -= min(unsafe_resolves * 3.0, 20.0)  # -3 per unsafe resolve, cap at 20
    score -= min(external_svcs * 5.0, 20.0)    # -5 per external service, cap at 20

    return _clamp(round(score))


def _score_serialization(data):
    """Score SERIALIZATION category: 0-100."""
    if data is None:
        return 50
    missing_uids = data.get("missing_uids", 0)
    conflicts = data.get("serial_conflicts", 0)

    score = 100.0
    score -= min(missing_uids * 1.0, 50.0)  # -1 per missing UID, cap at 50
    score -= min(conflicts * 20.0, 50.0)    # -20 per conflict, cap at 50

    return _clamp(round(score))


def _score_architecture(cycles_data, god_data, layer_data):
    """Score ARCHITECTURE category: 0-100.
    
    Uses sqrt-normalized penalties for god classes (large counts are common
    in big modules and shouldn't instantly zero the score).
    """
    cycles = cycles_data.get("module_cycles", 0) if cycles_data else 0
    god = god_data.get("god_classes", 0) if god_data else 0
    violations = layer_data.get("layer_violations", 0) if layer_data else 0

    score = 100.0
    score -= min(cycles * 10.0, 30.0)       # -10 per cycle, cap at 30
    score -= min(god * 1.0, 40.0)            # -1 per god class, cap at 40
    score -= min(violations * 2.0, 30.0)     # -2 per violation, cap at 30

    return _clamp(round(score))


def _score_security(data):
    """Score SECURITY category: 0-100."""
    if data is None:
        return 50
    hardcoded = data.get("hardcoded_credentials", 0)
    insecure = data.get("insecure_patterns", 0)
    perm_gaps = data.get("permission_gaps", 0)

    score = 100.0
    score -= min(hardcoded * 20.0, 50.0)    # -20 per hardcoded credential, cap at 50
    score -= min(insecure * 5.0, 30.0)      # -5 per insecure pattern, cap at 30
    score -= min(perm_gaps * 10.0, 20.0)    # -10 per permission gap, cap at 20

    return _clamp(round(score))


def _score_dependencies(data):
    """Score DEPENDENCIES category: 0-100."""
    if data is None:
        return 50
    third_party = data.get("third_party", 0)
    honeywell = data.get("honeywell", 0)

    score = 100.0
    score -= min(third_party * 5.0, 40.0)   # -5 per third-party dep group, cap at 40
    score -= min(honeywell * 2.0, 20.0)     # -2 per honeywell add-on, cap at 20

    return _clamp(round(score))


def _score_overall(scores):
    """Compute overall score as average of all categories."""
    cats = [
        scores.get("slots", 0),
        scores.get("ords", 0),
        scores.get("serialization", 0),
        scores.get("architecture", 0),
        scores.get("security", 0),
        scores.get("dependencies", 0),
    ]
    valid = [s for s in cats if s > 0]
    if not valid:
        return 50
    return round(sum(valid) / len(valid))


# ---------------------------------------------------------------------------
# Text output formatters
# ---------------------------------------------------------------------------

def _icon(issue_count, threshold_red=1, threshold_warn=1):
    """Return appropriate icon based on count (for issue counts: higher = worse)."""
    if issue_count >= threshold_red:
        return "X"   # bad
    elif issue_count >= threshold_warn:
        return "!"   # warning
    else:
        return "V"   # checkmark (OK)


def _icon_for_pct(pct):
    """Return appropriate icon for a percentage value (higher = better)."""
    if pct >= 80:
        return "V"   # green checkmark (OK)
    elif pct >= 50:
        return "!"   # warning
    else:
        return "X"   # red (bad)


def _format_check_line(label, count, should_be_zero=True, warn_threshold=1):
    """Format a single check line."""
    if should_be_zero:
        if count == 0:
            icon = "[OK]"
            status = "OK"
        elif count >= 3:
            icon = "[BAD]"
            status = "BAD"
        else:
            icon = "[WARN]"
            status = "WARN"
        return "  +- {}: {:>4}    {}  (should be 0)".format(label, count, icon)
    else:
        pct = count
        icon = _icon_for_pct(pct)
        return "  +- {}: {:>3}%   {} (should be >80%)".format(label, pct, icon)


def _emit_text_output(module_name, all_data, scores, overall):
    """Print the human-readable scorecard."""
    grade, desc = _grade(overall)

    sep = "=" * 70
    print("")
    print("MODULE HEALTH: {}".format(module_name))
    print(sep)
    print("")

    # ── SLOT HYGIENE ──
    slots_data = all_data.get("slots", {})
    print("  SLOT HYGIENE")
    print(_format_check_line(
        "Slot collisions", slots_data.get("slot_collisions", 0)))
    print(_format_check_line(
        "Intra-module dup slots", slots_data.get("intra_module_dups", 0)))
    print("  L- Lexicon coverage: {:>3}%   {}".format(
        slots_data.get("lexicon_coverage_pct", 0),
        _icon_for_pct(slots_data.get("lexicon_coverage_pct", 0))))
    print("")

    # ── ORD SAFETY ──
    ord_data = all_data.get("ords", {})
    resolve_data = all_data.get("resolve", {})
    service_data = all_data.get("service_order", {})
    print("  ORD SAFETY")
    print(_format_check_line(
        "Dangling ORDs", ord_data.get("dangling_ords", 0)))
    print(_format_check_line(
        "Unsafe .resolve()", resolve_data.get("unsafe_resolves", 0)))
    print(_format_check_line(
        "External service in SS", service_data.get("external_service_count", 0)))
    print("")

    # ── SERIALIZATION ──
    serial_data = all_data.get("serialization", {})
    print("  SERIALIZATION")
    print(_format_check_line(
        "Missing UIDs", serial_data.get("missing_uids", 0)))
    print(_format_check_line(
        "Serial conflicts", serial_data.get("serial_conflicts", 0)))
    print("")

    # ── ARCHITECTURE ──
    cycles_data = all_data.get("cycles", {})
    god_data = all_data.get("god_classes", {})
    layer_data = all_data.get("layer_check", {})
    print("  ARCHITECTURE")
    print(_format_check_line(
        "Circular deps", cycles_data.get("module_cycles", 0)))
    print(_format_check_line(
        "God classes", god_data.get("god_classes", 0)))
    print(_format_check_line(
        "Layer violations", layer_data.get("layer_violations", 0)))
    print("")

    # ── SECURITY ──
    sec_data = all_data.get("security", {})
    print("  SECURITY")
    print(_format_check_line(
        "Hardcoded credentials", sec_data.get("hardcoded_credentials", 0)))
    print(_format_check_line(
        "Insecure patterns", sec_data.get("insecure_patterns", 0)))
    print(_format_check_line(
        "Permission gaps", sec_data.get("permission_gaps", 0)))
    print("")

    # ── DEPENDENCIES ──
    dep_data = all_data.get("dependencies", {})
    print("  DEPENDENCIES")
    print(_format_check_line(
        "Third-party", dep_data.get("third_party", 0)))
    print(_format_check_line(
        "Honeywell add-ons", dep_data.get("honeywell", 0)))
    print("  \\- Platform: {:>4}    {}".format(
        dep_data.get("platform", 0), _icon_for_pct(dep_data.get("platform", 0))))
    print("")

    # -- DIVIDER --
    print("  " + "-" * 64)
    print("")
    print("  OVERALL SCORE:  {}  ({}/100)".format(grade, overall))
    print("  -> {}".format(desc))
    print("")
    print("  Grade thresholds:")
    print("    A: 90-100  (excellent -- production ready)")
    print("    B: 75-89   (good -- minor issues)")
    print("    C: 60-74   (fair -- review recommended)")
    print("    D: 40-59   (poor -- significant issues)")
    print("    F: 0-39    (critical \u2014 do not deploy)")
    print("")


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def cmd_module_health(base_dir, module_name, as_json=False):
    """Compute and display the module health scorecard.

    Args:
        base_dir: module-navigator root directory
        module_name: module to score (e.g. 'alarm-rt')
        as_json: if True, emit JSON instead of human-readable output
    """
    # Progress messages go to stderr so JSON output (on stdout) stays clean
    progress_out = sys.stderr
    progress_out.write("  Analyzing module '{}'...\n".format(module_name))
    progress_out.flush()

    # Run all sub-checks
    results = {}

    progress_out.write("    running slot-collision...")
    progress_out.flush()
    try:
        results["slots"] = _run_slot_collision(base_dir, module_name)
    except Exception as e:
        results["slots"] = {"slot_collisions": 0, "intra_module_dups": 0,
                            "lexicon_coverage_pct": 100, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running ord-validate...")
    progress_out.flush()
    try:
        results["ords"] = _run_ord_validate(base_dir, module_name)
    except Exception as e:
        results["ords"] = {"dangling_ords": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running resolve-audit...")
    progress_out.flush()
    try:
        results["resolve"] = _run_resolve_audit(base_dir, module_name)
    except Exception as e:
        results["resolve"] = {"unsafe_resolves": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running service-order...")
    progress_out.flush()
    try:
        results["service_order"] = _run_service_order(base_dir, module_name)
    except Exception as e:
        results["service_order"] = {"external_service_count": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running serial-audit...")
    progress_out.flush()
    try:
        results["serialization"] = _run_serial_audit(base_dir, module_name)
    except Exception as e:
        results["serialization"] = {"missing_uids": 0, "serial_conflicts": 0,
                                    "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running security-audit...")
    progress_out.flush()
    try:
        results["security"] = _run_security_audit(base_dir, module_name)
    except Exception as e:
        results["security"] = {"hardcoded_credentials": 0, "insecure_patterns": 0,
                               "permission_gaps": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running cycles...")
    progress_out.flush()
    try:
        results["cycles"] = _run_cycles(base_dir, module_name)
    except Exception as e:
        results["cycles"] = {"module_cycles": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running god-classes...")
    progress_out.flush()
    try:
        results["god_classes"] = _run_god_classes(base_dir, module_name)
    except Exception as e:
        results["god_classes"] = {"god_classes": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running layer-check...")
    progress_out.flush()
    try:
        results["layer_check"] = _run_layer_check(base_dir, module_name)
    except Exception as e:
        results["layer_check"] = {"layer_violations": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    progress_out.write("    running dependency-audit...")
    progress_out.flush()
    try:
        results["dependencies"] = _run_dependency_audit(base_dir, module_name)
    except Exception as e:
        results["dependencies"] = {"third_party": 0, "honeywell": 0,
                                    "platform": 0, "error": str(e)}
    progress_out.write(" done\n")
    progress_out.flush()

    # Compute scores
    scores = {
        "slots": _score_slots(results.get("slots")),
        "ords": _score_ords(
            results.get("ords"),
            results.get("resolve"),
            results.get("service_order"),
        ),
        "serialization": _score_serialization(results.get("serialization")),
        "architecture": _score_architecture(
            results.get("cycles"),
            results.get("god_classes"),
            results.get("layer_check"),
        ),
        "security": _score_security(results.get("security")),
        "dependencies": _score_dependencies(results.get("dependencies")),
    }

    overall = _score_overall(scores)
    grade, desc = _grade(overall)

    if as_json:
        output = {
            "command": "module-health",
            "module": module_name,
            "checks": results,
            "scores": scores,
            "overall": {
                "score": overall,
                "grade": grade,
                "description": desc,
            },
            "grade_thresholds": [
                {"min": 90, "max": 100, "grade": "A", "description": "excellent — production ready"},
                {"min": 75, "max": 89, "grade": "B", "description": "good — minor issues"},
                {"min": 60, "max": 74, "grade": "C", "description": "fair — review recommended"},
                {"min": 40, "max": 59, "grade": "D", "description": "poor — significant issues"},
                {"min": 0, "max": 39, "grade": "F", "description": "critical — do not deploy"},
            ],
        }
        print("")
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        _emit_text_output(module_name, results, scores, overall)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) < 2:
        print("Usage: python module_health.py <module> [--json]")
        sys.exit(1)
    module = sys.argv[1]
    as_json = "--json" in sys.argv
    cmd_module_health(base, module, as_json=as_json)
