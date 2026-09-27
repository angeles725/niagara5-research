# ODD feature — n5-research-bootstrap

- **Objective:** stand up `niagara5-research`, the Niagara N5 (5.0.0.28 beta, Java 25) sibling of
  `niagara-research` (N4, Java 8): corpus scaffold, decompiled module tree (`organized/`, gitignored),
  N5-adapted tooling + hooks, and a frontier research campaign.
- **Problem / why:** all current corpus + tooling targets N4. N5 changes packaging (one jar per module,
  no -rt/-ux/-wb split), bytecode (major 69) and ships `docSource.jar` originals; Java 25 bytecode
  should decompile better than N4's Java 8 + ZKM output.
- **Scope (authorized by the user 2026-09-27):** ODD + RDD (granted) + commit + push + PR + issues +
  merge; frontier heavy automatic chain; self-answer open questions with recommendations.
- **Constraints:** the N5 install is READ-ONLY; decompiled/proprietary material never enters git;
  repo is PRIVATE; artifacts in English.
- **TDD:** Strict TDD mode enabled (session config). Runner: plain bash smoke tests under
  `tools/tests/` (+ python unittest for Python tools). Tools get a RED smoke test first.
- **Delivery strategy:** ask-on-risk → self-answered `feature-branch-chain` (user pre-authorized merge).

## Tasks

| ID | Task | Route (trigger evidence) | Status | Evidence |
|---|---|---|---|---|
| T1 | Scaffold repo (research-sdd-init, flat, prefix niagara5), .gitignore, ODD doc | inline (mechanical) | done | init OK 2026-09-27 |
| T2 | Decompiler bake-off on Java 25 classes + `tools/n5-decompile.sh` + full run over 247 jars | delegated (writer, 2+ files) | in progress | — |
| T3 | Map N4 tools/hooks → N5 adaptation plan | delegated (mapper, 4+ files) | done | mapper report 2026-09-27: 12 navigator builders keyed on hardcoded organized path in build_module_inventory.py:216; station-modules.py N4-only; niagara-help rebuild = extract docDeveloper/docSource/javadoc |
| T4 | Port/adapt tools (in progress: writer)  for N5 (corpus-nav, gen-catalog, check-coverage, module-find, bog-nav, navigator/help rebuild, N4↔N5 diff) | delegated writer | pending | — |
| T5 | N5 SessionStart protocol + tools-card hooks, settings wiring | inline/delegated | pending | — |
| T6 | Register target in kit TARGETS.md (kit PR) + private GitHub remote | inline | done | kit PR #1170 merged (issue #1171); repo angeles725/niagara5-research PRIVATE |
| T7 | Seed frontier backlog + run block loop | delegated per block | in progress | 16 gaps seeded; B1 (G1), B2 (G6), B3 (G7) delegated |
| T8 | Retro (§18) + session close | inline | pending | — |
