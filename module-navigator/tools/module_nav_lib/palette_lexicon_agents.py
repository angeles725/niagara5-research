"""
Palette / Lexicon / Agent census for Module Navigator.

Commands:
  palette-lexicon-agents <module>
    [--json]             # structured JSON output

For every artifact (sub-directory) of the given module under organized/,
reports three categories:

1. Palette census — <p> entries from module.palette (XML):
     n= (name), t= (type), m= (module-alias)

2. Lexicon keys + duplicate-bare-key report — from <artifact>.lexicon
   (Java .properties format).  A duplicate bare key is a key (everything
   before the first '=') that appears more than once in the same file;
   later lines silently override earlier ones (B759 hazard).

3. Agent registrations — <agent> elements inside <type> elements of
   extracted/META-INF/module.xml.

Reads from extracted/ on disk when present; falls back to the JAR via
zipfile for module.palette.
"""

import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile


# ---------------------------------------------------------------------------
# Pure parse helpers (callable directly from tests)
# ---------------------------------------------------------------------------

def parse_palette(text):
    """Parse module.palette XML and return a list of palette entry dicts.

    Each dict has keys: n (name), t (type), m (module alias or None).
    Only direct children of the document root are returned (the root <p>
    element itself is the container, its children are the actual entries).
    For nested BOG trees this is intentionally shallow — callers who want
    all entries recursively can walk the XML themselves; the census only
    counts top-level and second-level entries to avoid double-counting.

    We collect ALL <p> elements in the whole document to count the total.
    """
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    entries = []
    for elem in root.iter("p"):
        entry = {}
        if "n" in elem.attrib:
            entry["n"] = elem.attrib["n"]
        if "t" in elem.attrib:
            entry["t"] = elem.attrib["t"]
        if "m" in elem.attrib:
            entry["m"] = elem.attrib["m"]
        if entry:
            entries.append(entry)
    return entries


def find_duplicate_keys(lexicon_text):
    """Return a dict mapping each DUPLICATE bare key to its occurrence count.

    A lexicon file is Java .properties format: key=value, # comments,
    blank lines.  The "bare key" is everything before the first '=' on
    a non-comment, non-blank line.

    A key is a duplicate when it appears more than once in the file (the
    later occurrence silently overrides the earlier one — B759 hazard).
    Only entries with count > 1 are returned.
    """
    counts = {}
    for line in lexicon_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1

    return {k: v for k, v in counts.items() if v > 1}


def parse_agents(module_xml_text):
    """Parse agents from module.xml text.

    Returns a list of dicts with keys:
      type_name  — the name= attribute of the enclosing <type>
      type_class — the class= attribute of the enclosing <type>
      on_types   — list of type= values from <on> children of <agent>
    """
    if not module_xml_text:
        return []
    try:
        root = ET.fromstring(module_xml_text)
    except ET.ParseError:
        return []

    agents = []
    for type_elem in root.iter("type"):
        for agent_elem in type_elem.findall("agent"):
            on_types = [
                on.attrib.get("type", "")
                for on in agent_elem.findall("on")
            ]
            agents.append({
                "type_name": type_elem.attrib.get("name", ""),
                "type_class": type_elem.attrib.get("class", ""),
                "on_types": on_types,
            })
    return agents


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_extracted_file(extracted_dir, filename):
    """Read a file from the extracted/ directory; return text or None."""
    path = os.path.join(extracted_dir, filename)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except IOError:
            return None
    return None


def _read_from_jar(jar_path, member_name):
    """Read a named member from a JAR (ZIP); return text or None."""
    if not os.path.isfile(jar_path):
        return None
    try:
        with zipfile.ZipFile(jar_path, "r") as zf:
            if member_name in zf.namelist():
                return zf.read(member_name).decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, IOError, KeyError):
        pass
    return None


def _collect_artifact_data(artifact_dir, artifact_name):
    """Collect palette + lexicon + agents for one artifact directory.

    Returns a dict:
      {
        artifact:         str,
        palette_entries:  list[dict],
        lexicon_keys:     int,
        duplicate_keys:   dict[str, int],    # only those with count > 1
        agents:           list[dict],
        errors:           list[str],
      }
    """
    result = {
        "artifact": artifact_name,
        "palette_entries": [],
        "lexicon_keys": 0,
        "duplicate_keys": {},
        "agents": [],
        "errors": [],
    }

    extracted_dir = os.path.join(artifact_dir, "extracted")
    jar_path = os.path.join(artifact_dir, artifact_name + ".jar")

    # --- Palette ---
    palette_text = _read_extracted_file(extracted_dir, "module.palette")
    if palette_text is None:
        palette_text = _read_from_jar(jar_path, "module.palette")
    if palette_text is not None:
        result["palette_entries"] = parse_palette(palette_text)
    else:
        # No palette is normal (e.g. wb-only or se artifacts)
        pass

    # --- Lexicon ---
    lexicon_filename = artifact_name + ".lexicon"
    lexicon_text = _read_extracted_file(extracted_dir, lexicon_filename)
    if lexicon_text is None:
        lexicon_text = _read_from_jar(jar_path, lexicon_filename)
    if lexicon_text is not None:
        all_keys = []
        for line in lexicon_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key:
                    all_keys.append(key)
        result["lexicon_keys"] = len(all_keys)
        result["duplicate_keys"] = find_duplicate_keys(lexicon_text)
    else:
        # No lexicon is normal for some artifact types
        pass

    # --- Agents ---
    module_xml_text = _read_extracted_file(
        os.path.join(extracted_dir, "META-INF"), "module.xml"
    )
    if module_xml_text is not None:
        result["agents"] = parse_agents(module_xml_text)

    return result


def _find_artifacts(module_dir, module_name):
    """Return list of (artifact_name, artifact_path) for a module directory.

    Artifacts are subdirectories starting with <module_name>- that contain
    a .jar file or an extracted/ subdirectory.
    """
    artifacts = []
    if not os.path.isdir(module_dir):
        return artifacts
    for entry in sorted(os.listdir(module_dir)):
        artifact_dir = os.path.join(module_dir, entry)
        if not os.path.isdir(artifact_dir):
            continue
        # Must start with the module name or match directly
        has_jar = os.path.isfile(os.path.join(artifact_dir, entry + ".jar"))
        has_extracted = os.path.isdir(os.path.join(artifact_dir, "extracted"))
        if has_jar or has_extracted:
            artifacts.append((entry, artifact_dir))
    return artifacts


# ---------------------------------------------------------------------------
# Main command entry point
# ---------------------------------------------------------------------------

def cmd_palette_lexicon_agents(base_dir, module_name, as_json=False):
    """Extract and report palette, lexicon, and agent data for a module.

    base_dir — the organized/ root (e.g. /home/cristian/niagara-research/organized).
    module_name — module directory name (e.g. 'alarm').
    """
    module_dir = os.path.join(base_dir, module_name)
    if not os.path.isdir(module_dir):
        msg = "Module directory not found: {}".format(module_dir)
        if as_json:
            print(json.dumps({"error": msg}, indent=2))
        else:
            print("  ERROR: " + msg)
        return

    artifacts = _find_artifacts(module_dir, module_name)
    if not artifacts:
        msg = "No artifacts found in: {}".format(module_dir)
        if as_json:
            print(json.dumps({"module": module_name, "error": msg}, indent=2))
        else:
            print("  WARNING: " + msg)
        return

    all_data = []
    for artifact_name, artifact_dir in artifacts:
        data = _collect_artifact_data(artifact_dir, artifact_name)
        all_data.append(data)

    if as_json:
        output = {
            "module": module_name,
            "artifacts": [
                {
                    "artifact": d["artifact"],
                    "palette_count": len(d["palette_entries"]),
                    "palette_entries": d["palette_entries"],
                    "lexicon_keys": d["lexicon_keys"],
                    "duplicate_bare_keys": d["duplicate_keys"],
                    "agents": d["agents"],
                    "errors": d["errors"],
                }
                for d in all_data
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        _print_report(module_name, all_data)


def _print_report(module_name, all_data):
    SEP = "=" * 65
    print("")
    print("  " + SEP)
    print("  PALETTE / LEXICON / AGENTS: {}".format(module_name))
    print("  " + SEP)

    total_palette = sum(len(d["palette_entries"]) for d in all_data)
    total_lexicon = sum(d["lexicon_keys"] for d in all_data)
    total_agents = sum(len(d["agents"]) for d in all_data)
    total_dups = sum(len(d["duplicate_keys"]) for d in all_data)

    print("")
    print("  Artifacts scanned:  {}".format(len(all_data)))
    print("  Palette entries:    {}".format(total_palette))
    print("  Lexicon keys:       {}".format(total_lexicon))
    print("  Duplicate bare keys:{}".format(total_dups))
    print("  Agent registrations:{}".format(total_agents))
    print("")

    for d in all_data:
        artifact = d["artifact"]
        print("  " + "-" * 60)
        print("  Artifact: {}".format(artifact))
        print("")

        # Palette
        entries = d["palette_entries"]
        print("  [PALETTE]  {} entries".format(len(entries)))
        for e in entries[:50]:
            parts = []
            if "n" in e:
                parts.append("n={}".format(e["n"]))
            if "t" in e:
                parts.append("t={}".format(e["t"]))
            if "m" in e:
                parts.append("m={}".format(e["m"]))
            print("    <p {}>".format("  ".join(parts)))
        if len(entries) > 50:
            print("    ... and {} more".format(len(entries) - 50))
        print("")

        # Lexicon
        dups = d["duplicate_keys"]
        print("  [LEXICON]  {} keys total".format(d["lexicon_keys"]))
        if dups:
            print("  *** DUPLICATE BARE KEYS DETECTED (B759 hazard) ***")
            for key, count in sorted(dups.items()):
                print("    DUP key={!r}  occurrences={}".format(key, count))
        else:
            print("    No duplicate bare keys.")
        print("")

        # Agents
        agents = d["agents"]
        print("  [AGENTS]   {} registration(s)".format(len(agents)))
        for ag in agents:
            print("    type_name={!r}  class={!r}  on={}".format(
                ag["type_name"], ag["type_class"], ag["on_types"]
            ))
        if not agents:
            print("    (none)")
        print("")

        if d["errors"]:
            print("  [ERRORS]")
            for err in d["errors"]:
                print("    " + err)
            print("")
