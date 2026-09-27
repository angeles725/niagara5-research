#!/usr/bin/env bash
# SessionStart hook — Research-SDD protocol for Niagara N5 (5.0.0.28 beta).
# Mirror of the niagara-research hook, parameterized for this target
# (niagara5-research). Registered in .claude/settings.json
# (matcher startup|resume|clear|compact).
#
# §479: also records the session-start git sha so retro-gate.sh can detect
# which research files changed during this session.
set -euo pipefail

# Read session_id from SessionStart hook JSON stdin (§479 session-sha recording)
_hook_stdin=$(cat)
_session_id=$(printf '%s' "$_hook_stdin" | jq -r '.session_id // empty' 2>/dev/null) || _session_id=""

# Record session-start git sha for retro-gate.sh (hooks live two levels below target)
# Write only when missing/empty so that compact/clear/resume (all trigger SessionStart
# with matcher "") cannot overwrite the sha recorded at the true session start.
# Installed copies must be re-initialized from this template to pick up this fix.
#
# Very long sessions / reused session ids (documented, not silently assumed — see rotation
# below and #984):
#   - A single session running longer than the 7-day rotation window must not have ITS OWN
#     state files deleted out from under it mid-session — that would silently flip retro-gate
#     into degraded mode. The rotation below excludes this session's own files by name.
#   - If a session id were ever reused across two genuinely different sessions (this hook has
#     no way to detect that — it cannot distinguish "resuming the same session" from "a new
#     session that happens to reuse an old id"), write-once semantics keep the FIRST sha
#     recorded under that id, which would then be stale for the second, unrelated session.
#     This is an accepted tradeoff: fixing it would require extra state (e.g. a session-start
#     timestamp or a monotonically-increasing counter) to tell "resume" apart from "reuse",
#     which is out of scope here. Not currently known to happen in practice.
_hook_target="$(cd "$(dirname "$0")/../.." && pwd)"
if [ -n "$_session_id" ]; then
  _rsdd_file="$_hook_target/.claude/.rsdd-session-${_session_id}"
  if [ ! -s "$_rsdd_file" ]; then
    _sha=$(git -C "$_hook_target" rev-parse HEAD 2>/dev/null) || _sha=""
    if [ -n "$_sha" ]; then
      mkdir -p "$_hook_target/.claude"
      printf '%s\n' "$_sha" > "$_rsdd_file"
    fi
  fi
  # Rotate stale session state files (older than 7 days) to prevent accumulation. Exclude THIS
  # session's own files by name: a session that has been running longer than 7 days must keep
  # its own session-start sha and block-once marker, or retro-gate.sh would silently fall back
  # to degraded (mtime) mode mid-session.
  # Residual (documented, not fixed): this by-name exclusion protects a session only from ITS
  # OWN rotation pass. A CONCURRENT session's rotation pass does not know this session's id and
  # can still delete this session's files once they age past the 7-day window.
  # $_session_id is embedded unescaped in the `find -name` exclusion patterns below — VALIDATE
  # it carries no glob metacharacter (`*`, `?`, `[`) first, rather than merely assuming it is a
  # UUID: an id shaped like that would widen or narrow the exclusion match, turning this into a
  # mis-scoped delete. Skip rotation loudly (never silently) when the id fails that check.
  case "$_session_id" in
    *[\*\?\[]*)
      printf 'hook-sessionstart: WARN: session_id contains a glob metacharacter — skipping rotation to avoid a mis-scoped delete: %s\n' "$_session_id" >&2
      ;;
    *)
      find "$_hook_target/.claude" -maxdepth 1 \
        \( -name '.rsdd-session-*' -o -name '.rsdd-retro-blocked-*' \) \
        ! -name ".rsdd-session-${_session_id}" ! -name ".rsdd-retro-blocked-${_session_id}" \
        -mtime +7 -delete 2>/dev/null || true
      ;;
  esac
  unset _rsdd_file _sha
fi
unset _hook_stdin _session_id _hook_target

# Probe for jq (§7 — could the instrument run at all?).
# Without jq the final JSON emission silently fails; emit a typed degraded line and a
# minimal valid hook JSON so the session is not broken.
if ! command -v jq >/dev/null 2>&1; then
  printf 'degraded: jq missing — install jq for full research-sdd context injection\n' >&2
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[degraded: jq missing — install jq for full research-sdd context]"}}'
  exit 0
fi

read -r -d '' CTX <<'EOF' || true
RESEARCH PROTOCOL — Niagara N5 5.0.0.28 beta (Research-SDD)

Every session in this project is READ-ONLY research of Niagara N5 5.0.0.28
(Java 25), with the N4↔N5 delta as an organizing axis. Before answering a
research question, work in this order:

1. FIRST search the project's own .md blocks (truth already distilled):
   - niagara5-block*.md
   - INDEX.md  (map + Pending/gaps section)
   - CATALOG.md
   - RESEARCH-STATE.md (open gaps, NEXT)
   Review them before opening any tool. Also see
   tools/hooks/n5-research-protocol.sh and tools/hooks/n5-tools.sh
   (loaded alongside this hook) for the full three-source protocol and the
   local tools card.

2. Toolbelt tools (Research-SDD) — pick the wrapper for the artifact type from
   $RESEARCH_SDD_KIT/toolbelt/tool-registry.md (profile-target.sh classifies
   binaries and suggests one). For this target's OWN tools (corpus-nav.py,
   n5-modules.py, n5-api-diff.py, ...) see tools/README.md.

3. PRIMARY SOURCES of Niagara N5 (real paths):
   - N5 modules (jars): /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules
   - N5 install: "/mnt/c/Program Files/Niagara/5.0.0.28"
     (bin, jre, defaults/*.bog, javadoc/niagaraJavadoc.jar, etc/m2)
   - N4 install (delta baseline): /mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules
   - N5 decompiled output (this repo, partial while work is in progress):
     <repo>/organized/<module>/{extracted,resources,<decompiler>,recon.json}
   - N4 sibling corpus (docSource originals, prior N4 research):
     /home/cristian/niagara-research

4. PROVENANCE AND CERTAINTY (mandatory markers on every claim):
   [CERT-hw] live system/device (highest) · [CERT-live] live remote service · [CERT] local primary ·
   [CERT-doc] official document (sources/) · [CERT-web] official web · [CERT-a] forum/secondary ·
   [INFER] deduction. No citation ⇒ [INFER] or omit.

5. EXTERNAL EVIDENCE: if you find a relevant datasheet/manual/forum/link, DOWNLOAD it with
   fetch-doc.sh (lands in sources/ + registered in SOURCES.md) and cite the local file.

ACTION AT START: review the project's .md blocks first, then choose the toolbelt
tool(s) yourself from the artifact type and say in one line which you chose.
Inside a /research-sdd loop, continue the loop; do not stop to ask.
EOF

jq -n --arg ctx "$CTX" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
