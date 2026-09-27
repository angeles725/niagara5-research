#!/usr/bin/env python
"""
Shared corpus (organized/) directory + layout resolution for the N5
module-navigator builders (build_module_inventory.py, build_class_index.py,
build_swing_index.py).

N5 port note: the N4 tool hardcoded an absolute, machine-specific corpus path
inside three builder scripts. This module centralizes resolution so nothing
under tools/ contains an absolute, machine-specific, or N4-specific path
literal.

Resolution order (first hit wins):
  1. explicit `cli_value` (e.g. --organized CLI flag)
  2. NAV_ORGANIZED_DIR environment variable
  3. sibling `organized/` directory of module-navigator/ (i.e.
     <parent-of-module-navigator>/organized) -- this is where the N5
     decompiled corpus lives for this copy of the tool
  4. `_meta.source` recorded in an existing indexes/module-inventory.json
     (lets downstream builders re-derive the same corpus root the inventory
     was built from, without re-specifying it)

Requires: Python 3.x (stdlib only)
"""

import json
import os

DEFAULT_LAYOUT = "flat"
VALID_LAYOUTS = ("flat", "n4")

# Directory names at the top of organized/ that are never modules, even
# though they sit alongside module directories.
NON_MODULE_TOP_DIRS = {"docSource", "_logs", "_recon"}

# Directory that holds bin/ext-style modules one level deeper, each named
# `_bin-ext/<jar>` in the inventory.
BIN_EXT_DIR = "_bin-ext"


def default_organized_dir(base_dir):
    """Sibling `organized/` directory of module-navigator (base_dir)."""
    return os.path.join(os.path.dirname(os.path.abspath(base_dir)), "organized")


def default_organized_dir_from_lib_file(lib_file):
    """Convenience for module_nav_lib/*.py callers: pass their own
    `__file__` and get the same sibling organized/ default, without each
    lib module re-deriving base_dir from its own nesting depth
    (module_nav_lib/<file>.py -> tools/ -> module-navigator/)."""
    lib_dir = os.path.dirname(os.path.abspath(lib_file))
    tools_dir = os.path.dirname(lib_dir)
    base_dir = os.path.dirname(tools_dir)
    return default_organized_dir(base_dir)


def resolve_organized_dir(base_dir, cli_value=None):
    """Resolve the organized/ corpus directory for this tool copy.

    Returns an absolute path. Does not require the path to exist -- callers
    are responsible for validating it (so error messages can be specific).
    """
    if cli_value:
        return os.path.abspath(cli_value)

    env_value = os.environ.get("NAV_ORGANIZED_DIR")
    if env_value:
        return os.path.abspath(env_value)

    sibling = default_organized_dir(base_dir)
    if os.path.isdir(sibling):
        return sibling

    inv_path = os.path.join(base_dir, "indexes", "module-inventory.json")
    if os.path.isfile(inv_path):
        try:
            with open(inv_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            src = data.get("_meta", {}).get("source", "")
            if src:
                return src
        except (OSError, ValueError):
            pass

    return sibling


def resolve_layout(cli_value=None):
    """Resolve the corpus layout: 'flat' (N5, default) or 'n4' (legacy)."""
    if cli_value:
        if cli_value not in VALID_LAYOUTS:
            raise ValueError(
                "Invalid --layout '{}': must be one of {}".format(
                    cli_value, VALID_LAYOUTS
                )
            )
        return cli_value
    env_value = os.environ.get("NAV_LAYOUT")
    if env_value and env_value in VALID_LAYOUTS:
        return env_value
    return DEFAULT_LAYOUT


def is_module_dir(name):
    """True if a top-level organized/ entry name could be a real module
    directory (not a housekeeping dir like docSource/_logs/_recon)."""
    return name not in NON_MODULE_TOP_DIRS and name != BIN_EXT_DIR


def iter_flat_module_dirs(organized_dir):
    """Yield (module_key, module_path) pairs for the flat N5 layout.

    - Regular modules: organized/<name>/ with a recon.json directly inside.
    - Bin-ext modules: organized/_bin-ext/<jar>/ with a recon.json directly
      inside, yielded as module_key "_bin-ext/<jar>".

    Directories without a recon.json (docSource, _logs, _recon, or anything
    unexpected) are skipped.
    """
    if not os.path.isdir(organized_dir):
        return

    for name in sorted(os.listdir(organized_dir)):
        path = os.path.join(organized_dir, name)
        if not os.path.isdir(path):
            continue

        if name == BIN_EXT_DIR:
            for child in sorted(os.listdir(path)):
                child_path = os.path.join(path, child)
                if not os.path.isdir(child_path):
                    continue
                if os.path.isfile(os.path.join(child_path, "recon.json")):
                    yield "{}/{}".format(BIN_EXT_DIR, child), child_path
            continue

        if not is_module_dir(name):
            continue

        if os.path.isfile(os.path.join(path, "recon.json")):
            yield name, path
