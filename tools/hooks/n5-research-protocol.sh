#!/usr/bin/env bash
# SessionStart hook — Niagara N5 research protocol for this project.
# Emits additionalContext that Claude reads at the start of every session.
# Modeled on niagara-research/tools/hooks/niagara-research-protocol.sh (the
# N4 corpus's equivalent hook), rewritten for N5's paths and single-jar
# module layout (no -rt/-ux/-wb split).
#
# LOCATION: lives here (tools/hooks/), not under .claude/, because .claude/
# is gitignored in this repo and a NEW file placed only there would never be
# versioned. .claude/settings.json references this file by
# $CLAUDE_PROJECT_DIR/tools/hooks/n5-research-protocol.sh so both pieces
# travel with the repo.

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  printf 'degraded: jq missing — install jq for full research protocol context\n' >&2
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[degraded: jq missing — install jq for full research protocol context]"}}'
  exit 0
fi

read -r -d '' CTX <<'EOF' || true
NIAGARA N5 RESEARCH PROTOCOL (project: niagara5-research)

────────────────────────────────────────────────────────────────────────
STEP 0 — Orient BEFORE investigating
────────────────────────────────────────────────────────────────────────
  1. INDEX.md: layer summary, full block map, pending gap backlog.
  2. RESEARCH-STATE.md: open gaps, the NEXT one, and the <!-- research-state.v1 -->
     envelope counters.
  3. Next block number = highest niagara5-block<N>.md on disk + 1 (numbering is
     global; do not fill historical gaps if any appear later).
  4. Run `python3 tools/check-coverage.py <realModuleOrPackageName>...` on the
     target's REAL module/package names before opening a new focus or seeding
     a gap — NOT on the abstract topic, and never trusting blocks recalled
     from a parent terminal. It scans niagara5-block*.md AND RESEARCH-STATE*.md.
  5. mem_context + mem_search on the topic before touching files.

  Tell the user in one line: current gap NEXT · next block number.

  This does not apply as a hard gate for meta-work (auditing tooling, a retro,
  or a simple question about an existing block) — say so and continue.

────────────────────────────────────────────────────────────────────────
THE THREE SOURCES — cumulative, not alternative
────────────────────────────────────────────────────────────────────────
  Each gives something different; none replaces another. Consult all three
  before: closing a gap · claiming something does NOT exist or is undocumented
  · contradicting a previous block.

  ── SOURCE 1: this project's own blocks ──
    rg -i '<term>' CATALOG.md
    rg -il '<term>' niagara5-block*.md
    mem_search '<term>'
    python3 tools/corpus-nav.py find '<term>'   /  by-marker INFER|CERT...
    SUFFICIENCY: at least TWO distinct terms — the Niagara name and the
    domain/protocol name. If a hit looks close, OPEN the block and read the
    section, don't infer from the title alone.
    If a block already answers it: do NOT re-derive it. Cite it and move on.

  ── SOURCE 2: shipped N5 docs (official, not decompiled) ──
    - Javadoc (compiled API reference):
        "/mnt/c/Program Files/Niagara/5.0.0.28/javadoc/niagaraJavadoc.jar"
      (a jar of HTML — extract or serve, do not decompile: this IS the doc.)
    - docDeveloper.jar / docDeveloperAnalytics.jar (developer guides):
        /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper*.jar
    ✔ GIVES: intended API contracts, migration guidance, official terminology.
    ✘ Does NOT give: internal wiring, actual runtime behavior, undocumented
      defaults — that is what SOURCE 3 (code) is for.

  ── SOURCE 3: code — organized/, with docSource ORIGINALS first ──
    Root: <repo>/organized/<module>/   (populated incrementally by
    tools/n5-decompile.sh; may be PARTIAL while work is in progress)
    FIDELITY PRIORITY (highest to lowest), mirrors N4 METHODOLOGY §6:
     a) ORIGINAL TRIDIUM SOURCE (not decompiled) — N5's docSource.jar ships
        real .java for many packages, package-renamed from N4's javax.baja.*
        to niagara.* (see niagara5-block3.md B3-G2). Read directly from the
        jar:
          python3 -c "import zipfile; z=zipfile.ZipFile('/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docSource.jar'); print(z.read('<module>/<pkg-path>/<Class>.java').decode())"
        VERIFY HERE FIRST when available for the class in question.
     b) Decompiled (organized/<module>/<decompiler>/...) — check
        docs/decompiler-bakeoff.md for which decompiler is preferred per this
        corpus's own bake-off; fall back to another decompiler only if the
        preferred one is unreadable for that class.
     c) Bytecode structure only (module-info.class, class file layout) via
        tools/lib/moduleinfo.py or `javap -p` — when you need JPMS
        requires/exports, not method bodies.
    N4<->N5 delta is a first-class axis: use tools/n5-modules.py (module set,
    dependencies, JPMS surface) and tools/n5-api-diff.py (source- and
    binary-level API diff, package-rename aware) rather than re-deriving deltas
    by hand.

  Tie-break when two sources disagree: SOURCE 3 (code) wins for "what actually
  happens at runtime"; SOURCE 2 (shipped docs) wins for "what the vendor
  intends/contracts"; SOURCE 1 (this project's own blocks) is a MIRROR of a
  prior pass through 2+3 — if it disagrees with a fresh read of 2 or 3, the
  block is probably stale; note it as a correction, don't silently override it.

────────────────────────────────────────────────────────────────────────
PROVENANCE AND CERTAINTY — mandatory marker on every claim
────────────────────────────────────────────────────────────────────────
  [CERT-hw] live device/hardware you physically hold (highest) ·
  [CERT-live] live remote service you do not own ·
  [CERT] local primary (javadoc/docDeveloper/docSource original, or decompiled
    code you actually read) · [CERT-doc] official document under sources/ ·
  [CERT-web] official web page · [CERT-a] forum/secondary · [INFER] deduction.
  No citation => [INFER], or omit the claim.

────────────────────────────────────────────────────────────────────────
CLOSING A SESSION / A GAP
────────────────────────────────────────────────────────────────────────
  - Update RESEARCH-STATE.md and INDEX.md's Pending section for anything
    closed or newly opened.
  - Run `python3 tools/gen-catalog.py` after adding/renaming a block — it is
    AUTOGENERATED, never hand-edit CATALOG.md.
  - Record any new/adapted/downloaded tool in tools/README.md the moment it
    is acquired (METHODOLOGY §10) — not reconstructed later at retro time.

ACTION AT START: read INDEX.md + RESEARCH-STATE.md first, then pick the
toolbelt tool(s) yourself from the artifact type and say in one line which
you chose. Inside a /research-sdd loop, continue the loop; do not stop to ask.
EOF

jq -n --arg ctx "$CTX" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
