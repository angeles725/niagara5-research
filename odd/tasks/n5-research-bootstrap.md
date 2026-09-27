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
| T2 | Decompiler bake-off on Java 25 classes + `tools/n5-decompile.sh` + full run over 247 jars | delegated (writer, 2+ files) | done | Vineflower primary / CFR fallback (switch-pattern recompile 5/5 vs 0/5); 246 modules, 20,723 classes + 6 bin/ext jars; bats 12/12; commits d39eb4a c4ed726 7c9a162; RDD approved |
| T3 | Map N4 tools/hooks → N5 adaptation plan | delegated (mapper, 4+ files) | done | mapper report 2026-09-27: 12 navigator builders keyed on hardcoded organized path in build_module_inventory.py:216; station-modules.py N4-only; niagara-help rebuild = extract docDeveloper/docSource/javadoc |
| T4 | Port/adapt tools for N5 | delegated writer | done (module-navigator + niagara-help N5 in progress) | 9 chained commits + SEC-11 fix (15929cf); 70+ unittest; RDD 8/9 approved + fix approved |
| T5 | N5 SessionStart protocol + tools-card hooks, settings wiring | delegated | done | commit 7a4fc5a; shellcheck clean |
| T6 | Register target in kit TARGETS.md (kit PR) + private GitHub remote | inline | done | kit PR #1170 merged (issue #1171); repo angeles725/niagara5-research PRIVATE |
| T7 | Seed frontier backlog + run block loop | delegated per block | in progress | 28+ blocks, 38/152 gaps closed, child gaps promoted (heavy mode) |
| T8 | Retro (§18) + session close | inline/delegated | in progress | retros 1 and 2 committed; kit issues #1173-#1181 + 7 more |


## Delivery

- Strategy: feature-branch slices merged to main after per-commit RDD review (user pre-authorized merge).
- Slice 1: feat/n5-bootstrap-tooling up to 0679d7a — all code commits RDD-approved; docs passive.
- Incident: PoC builds installed 2 jars into the N5 install (quarantined, not deleted; builds redirected to a local config-home mirror).

- Slice 2 (feat/n5-wave3): blocks 30-50, module-navigator N5 port, niagara-help (own repo angeles725/niagara5-help), porting guide, 3 more retros. RDD: 5f3aa8c, 8d709b6, fe1c291 approved; 30de796 skipped (vendored N4 baseline); d0b5d4f (.gitignore 1 line) under_budget; docs passive.
