#!/usr/bin/env bash
# hook-stop-retro-gate.sh — installable Stop-hook wrapper for §18 retro enforcement.
#
# Install: copy to /home/cristian/niagara5-research/.claude/hooks/retro-gate-stop.sh (research-sdd-init.sh does this).
# The init script replaces /home/cristian/investigacion/sdd-investigacion/research-sdd and /home/cristian/niagara5-research with absolute paths at install time.
# Register in /home/cristian/niagara5-research/.claude/settings.json under hooks.Stop (see init output for snippet).
#
# Behaviour: pipes stdin (Stop-hook JSON) to retro-gate.sh /home/cristian/niagara5-research.
# Always exits 0 (hook contract). BLOCK = stdout {"decision":"block","reason":"..."}.
#
# §8 propose-never-apply: the script itself is installed by the operator; never auto-edited.

KIT="/home/cristian/investigacion/sdd-investigacion/research-sdd"       # replaced by research-sdd-init.sh: absolute path to the kit root
TARGET="/home/cristian/niagara5-research" # replaced by research-sdd-init.sh: absolute path to this research target

exec "$KIT/toolbelt/retro-gate.sh" "$TARGET"
