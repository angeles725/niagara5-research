# Block 50 — N4→N5 porting synthesis: what breaks, what to change, in what order

> **Scope**: Synthesizes the full N4→N5 porting-guide deliverable (`docs/n4-to-n5-porting-guide.md`) from
> the 27 prior blocks that cover module packaging/build toolchain (B1, B2, B7, B9), core API/behavioral
> delta (B5, B20, B22), the permission/security model (B8, B43, B47), three real build/PoC campaigns
> (B10, B16, B28, B39, B29), the migrator/station-migration path (B14, B17, B24, B26, B31), HA/niagaraSync
> (B37, and its concrete PoC-refactor sibling B45), the action-audit/write-Context chain (B41, B46, B49),
> and public/product evidence (B48). This
> block does not open any new primary source — every `[CERT]`-bearing fact it relies on was already sealed
> in its home block; this block's own contribution is the CROSS-BLOCK synthesis (ordering, prioritization,
> a single merged troubleshooting table, and a single merged migration runbook) that no individual source
> block attempted, plus explicit child gaps for every place that synthesis outran direct grounding. Does
> **not** re-derive, re-verify, or downgrade any source block's own findings — where two source blocks
> disagreed (e.g. [B24] §24.3's `encodeBog` characterization, corrected by [B47] §47.1), this block defers
> to the LATER, correcting block, per METHODOLOGY §14's cross-block-consistency convention.
>
> Subject version: **N5 5.0.0.28 (Beta)**, JRE 25.0.4.7, same install every source block below reads,
> compared against baseline **N4 4.14.0.162** (Honeywell OptimizerSupervisor OEM) and PANCCADIA's real
> **N4 4.15** station backup. No fresh artifact was opened this session — see Sources.
>
> Sources: full re-reads this session (not re-decompiled, not re-built) of `niagara5-block{1,2,3,5,7,8,9,
> 10,14,16,17,20,22,24,26,28,29,31,37,39,41,43,46,47,48,49}.md` in full, plus `RESEARCH-STATE.md` (gap
> backlog). **Amendment**: `niagara5-block45.md` (the ColdRoomPan HA-ready PoC, closing B37-G6) did not
> exist at this block's initial drafting time — the block list at that point genuinely jumped B44→B46 —
> and was written by a parallel session shortly after; per the orchestrator's explicit instruction this
> block and its companion guide were revised in place (METHODOLOGY §20 "revise in place, not by new
> block") to fold B45's findings into guide §2.10/§6 and this block's §50.2/§50.3/§50.4/§50.6, rather than
> leaving the original "no B45 yet" framing stale. Also read: `docs/decompiler-bakeoff.md` (checked, not
> load-bearing for this synthesis — it documents decompiler tool choice, not porting mechanics). METHODOLOGY
> `§3` (provenance markers), `§4` (block anatomy), `§11`
> (self-verification contract, incl. the synthesis-block "zero own `[CERT]`, `n/a` from `verify-block.sh`"
> signature), and `§20` (document-mode capture conventions) were read this session at
> `/home/cristian/investigacion/sdd-investigacion/research-sdd/METHODOLOGY.md` to confirm this block's own
> format compliance.
>
> Deliverable: `docs/n4-to-n5-porting-guide.md` (this block's companion artifact — the guide IS the
> synthesis; this block is its self-verify + connections + child-gap ledger, not a duplicate of its prose).
>
> Porting-synthesis layer. Connects every block listed above — see §50.3.
>
> **Type:** synthesis

---

## 50.1 — What this block is, and is not

This is a **synthesis block** per METHODOLOGY §4/§11: it draws `[INFER]` conclusions exclusively by
combining prior blocks' own `[CERT]`/`[CERT-hw]`/`[CERT-doc]` findings, not by opening a new primary
source. A `grep` for `[CERT]` in this file's own body (excluding this methodological note) will report
`n/a` — this is the EXPECTED signature for a correctly-written synthesis block (METHODOLOGY §11: "A
synthesis block that cites only prior `[Block N]` cross-references will report `n/a` ... this is the
EXPECTED signature of a correctly-written DESIGN block, not a defect"). Every factual claim in the
companion guide carries its own `[Bn §x.y]` citation inline; this block's self-verify table (§50.2) is
the reverse index — guide section → source block(s) — so a reviewer can audit completeness without
re-reading the guide's prose.

## 50.2 — Self-verify table: guide section → source block(s)

| Guide section | Claim synthesized | Source block(s) §section |
|---|---|---|
| §1 decision list — `niagara_config_home` redirect | jar task writes into whatever config_home resolves to; must be a local mirror | [B16 §16.3] |
| §1 decision list — any JDK 25 works | `n-java`'s `--module-path` never references the JRE dir | [B39 §39.2] |
| §1 decision list — no stub jars | real Maven artifacts, not stubs, is the supported fix | [B39 §39.3, §39.5] |
| §1 decision list — JUnit4 port needs a script | message-argument position differs per assertion type | [B29 §29.1–§29.2] |
| §1 decision list — niagaraTest cannot run here | Windows-only binary + license gate, both confirmed independently | [B16 §16.5.4][B29 §29.6][B17 §17.2] |
| §1 decision list — Context always required | 3,589 generated setters hard-code `null` | [B49 §49.1–§49.2] |
| §1 decision list — install before n5mig | `BModuleRemovalConverter` strips unresolved modules unconditionally | [B14 §14.5][B17 §17.5–§17.7] |
| §1 decision list — kitControl/tagdictionary/nrio need no converter | 315 real objects checked, zero removed slots | [B24 §24.6][B31 §31.7] |
| §2.1 build env / local mirror | same as decision-list row above | [B16 §16.3] |
| §2.1 bundled Gradle wrapper | `devkit.jar` ships a complete wrapper | [B9 §9.1] |
| §2.2 plugin id rename table | full 9-row rename table | [B2 §2.2][B10 BC-25] |
| §2.2 `moduleManifest{}` shape | extension simplified to `moduleName.set(...)` only | [B2 §2.4][B10 §10.3 step 9] |
| §2.2 drop parent `niagara-module.xml`, even multi-part | tested on ColdRoomPan (single) AND DashboardPan (was 3-part) | [B16 §16.4 CHK-7][B28 §28.3.5, closes B16-G2] |
| §2.3 `module-info.java` shape + `n-java` requirement | new file per module; `n-java` needed for `--module-path` | [B2 §2.7][B9 §9.4][B16 §16.2 step 3] |
| §2.4 `javax.baja.*`→`niagara.*` global rename, no shim | package-root census (zero `javax.baja` in 320 jars) + no compat class found | [B5 §5.1, §5.5][B14 §14.6][B9 §9.2] |
| §2.5 real signature-delta table | `javap`-diffed core types, N4 vs N5 | [B5 §5.3][B10 §10.4 BC-01/BC-04/BC-05/BC-06][B22 §22.2–§22.3] |
| §2.5 `Clock.schedule` guard unchanged; tick source changed | opcode-identical guard; `ticks()` now `System.nanoTime()` | [B20 §20.2] |
| §2.6 `jakarta.servlet` rename, zero call-site changes | confirmed by a real build + `javap` against live `WebOp`/`BWebServlet` | [B28 §28.5] |
| §2.7 multi-part merge steps | DashboardPan's real 3-part→1 merge, incl. the "-wb is often empty" finding | [B28 §28.3, §28.3.1–§28.3.6] |
| §2.8 `module-permissions.xml` deletable | zero live `<req-permission>` in any of our 3 modules | [B10 §10.11 CHK-8][B16 §16.4] |
| §2.8 4-of-8 Grant annotations usable by third parties | `isAnnotationPermitted` code trace | [B8 §8.1] |
| §2.8 file access confined to shared dirs; network audit-only | full advice-instrumentation trace | [B8 §8.8][B28 §28.1 correction] |
| §2.8 `module-include.xml` auto-regen, idempotent | `NiagaraTypeAnnotationProcessor`/`ModuleInclude` read in full | [B7 §7.2–§7.3][B10 CHK-9][B16 §16.4 CHK-9][B28 §28.3.6] |
| §2.9 Slotomatic unchanged, disconnected task | task-graph dry-run shows `slotomatic` absent; re-run is a no-op on unchanged source | [B7 §7.4][B9 §9.3][B16 §16.5.1] |
| §2.10 niagaraSync HA requirements + ColdRoomPan verdict | full protocol/validator trace + zero-hit grep on client worktree, PLUS a real refactor that builds/packages/passes 55/55 tests and a static validator-rule walk | [B37 §37.4, §37.6][B45 §45.2–§45.6] |
| §2.11 JavaFX/Batik compileOnly fix | root-caused via `javap` on the real module graph + validated on 2 toolchains | [B28 §28.4][B39 §39.1–§39.4] |
| §2.12 TestNG port recipe + gotchas | reorder table cross-checked against real `javac` compile, 51/51 pass + mutation-kill proof | [B16 §16.5.2–§16.5.3][B29 §29.1–§29.2, §29.7] |
| §2.13 Context-threading fix | applied to a real PoC, confirmed at the bytecode level | [B41 §41.4, §41.7][B46 §46.2–§46.4][B49 §49.3–§49.6] |
| §3 troubleshooting table (16 rows) | each row traced 1:1 to its own table row above / cited block | see table itself |
| §4 plain-TestNG fallback | 51/51 pass + mutation-kill (bite) proof | [B29 §29.7] |
| §5 JACE-9000-only / N4.15 LTS | Tridium FAQ PDF, quoted verbatim | [B48 §48.1–§48.2] |
| §5 step 1 — install-before-migrate + `moduleName=` trick | the ONE technique found; live-verified on 1 of 249 modules | [B14 §14.5, §14.10][B17 §17.4–§17.7] |
| §5 step 2 — license gate | 4 independent binaries (`n5mig`, `station`, `test`, and the `wb`/`-help` control) hit the identical exception | [B17 §17.2][B29 §29.6] |
| §5 step 4 — bog-protection passphrase / keyring force-clear | `BBogMigrator.migrateBog()` read line-by-line, cross-checked against PANCCADIA's real header | [B47 §47.1, §47.4–§47.5] |
| §5 step 6 — program-object signing | `BProgramConverter`'s cert-check + graceful-degrade path read in full | [B10 BC-29][B14 §14.8] |
| §5.1 96% clean / 8 removed-slot types / 1 live orphan | full 288-type slot diff against PANCCADIA's real 3,545-element bog | [B24 §24.6][B31 §31.4–§31.6] |
| §5.1 `BCapacity` storage-size hazard narrowed to zero PANCCADIA exposure | both editors' widget code traced; PANCCADIA's 23 real capacities counted | [B20 §20.5][B26 §26.5–§26.8] |
| §6 open risks (all 8 bullets) | each restates an OPEN child gap from its own source block, not a new claim | see bullet-level citations in the guide |

## 50.3 — Connections

- **[B1]** — module packaging/JPMS foundation (`schemaVersion="5"`, one JAR per module, `runtimeProfile`
  removal) underlies guide §2.2/§2.7's "drop the parent grouping file" and §2.5's `RuntimeProfile`-removal
  row.
- **[B2]** — the plugin-id rename table, `moduleManifest{}` shape, and the 9-item original kit-delta list
  this guide's §2.2/§2.3/§2.5 (Clock/servlet rows partially) and Appendix draw from directly.
- **[B3]** — background context only (boot/JRE/SecurityManager replacement); not directly cited in the
  guide because the PermissionManager mechanism itself is covered via [B8], its direct successor block.
- **[B5]** — the core API-delta census (§2.4/§2.5's entire signature-delta table) and the porting-cost
  baseline (18 files/133 import lines across our 3 modules) that first established the rename is
  "mechanically bounded but not zero-effort" — the framing this whole guide operationalizes.
- **[B7]** — the Slotomatic-vs-annotation-processor division of labor (§2.9's entire procedure, §2.8's
  auto-regeneration claim) — a "breakthrough" block this guide leans on directly, not merely cites.
- **[B8]** — the permission/annotation model (§2.8's Grant-annotation table, the file/network
  gated-vs-audited finding) — closes the open question of what a genuinely third-party module CAN request.
- **[B9]** — the first real build PoC (`n5Hello`) — the two "invisible to static inspection" discoveries
  (namespace rename, Slotomatic task-graph gap) this guide's §2.4/§2.9/troubleshooting table are built on,
  and the concrete `com.tridium.n-java` gotcha (§2.2, §3 row 2).
- **[B10]** — the official transition-guide read + the CHK-1..CHK-15 checklist this guide's entire §2
  procedure is a validated, build-confirmed superset of; every CHK item is referenced by number somewhere
  in §2/§5.1.
- **[B14]** — the `n5mig`/migrator SPI architecture (§5 steps 1/3/6, the `BModuleRemovalConverter`
  mechanism that makes step 1 mandatory, program-object signing enforcement).
- **[B16]** — the first REAL-module build PoC (ColdRoomPan-rt) — validates 8 of B10's 15 CHK items live,
  surfaces the `niagara_config_home` install-pollution hazard (§2.1, §3 row 3) and the Slotomatic
  no-op-on-rebuild finding (§2.9), and is the first block to reach `niagaraTest`'s real platform gate
  (§3 row 7).
- **[B17]** — the first real `n5mig` execution attempt against PANCCADIA — identifies the license gate
  (§5 step 2, §3 row 8) and the `moduleName=` compatibility mechanism (§5 step 1) that is this guide's
  single most load-bearing migration-runbook finding.
- **[B20]** — the control/alarm/history/schedule/kitControl behavioral delta — grounds §2.5's `Clock`
  guard-unchanged/tick-source-changed row and §5.1's `BCapacity` hazard statement (later narrowed by [B26]).
- **[B22]** — the driver-framework delta (`isUnoperational`→`isNonOperational`, `Log` removal,
  `BTuningPolicy` unchanged) — grounds two rows of §2.5's signature-delta table; **flagged as the one area
  of §2 never validated by an actual build**, since none of our 3 modules is a driver (see §50.4, B50-G1).
- **[B24]** — the full 58-type migrator catalog + the PANCCADIA cross-check — grounds §5.1's "96% clean"
  headline and the CORRECTION [B47] later applied to its `encodeBog` characterization (deferred to per
  §50 header).
- **[B26]** — the `BCapacity` re-investigation that NARROWS [B20]'s hazard framing to a specific,
  never-activated-under-N4 scenario with zero PANCCADIA exposure — this guide's §5.1 states the narrowed
  (correct) verdict, not [B20]'s original broader framing.
- **[B28]** — the second/third real-module build PoC (CompPan, DashboardPan) — validates the remaining 4
  DashboardPan-specific CHK items live, surfaces the `niagara.alarm`/JavaFX/Batik compile wall (§2.11),
  and the multi-part-merge steps (§2.7).
- **[B29]** — the JUnit4→TestNG port + niagaraTest/test.exe investigation — grounds §2.12's entire
  procedure, §4's fallback, and the license-gate corroboration in §5 step 2 (a 4th independent binary).
- **[B31]** — the full PANCCADIA slot-compatibility census — grounds §5.1's exact numbers (259/288 clean,
  8 removed-slot, 1 live orphan) and directly answers "will kitControl/tagdictionary/nrio need a
  converter" (no).
- **[B37]** — the niagaraSync deep-dive — grounds §2.10's entire HA-porting procedure (the marker
  interface, `BNiagaraSyncTicket`/`BNiagaraSyncTicks`, the validator's admission rules) and named the
  concrete, load-bearing child gap **B37-G6** (build a real HA refactor and prove it), which [B45] then
  closes with a working artifact.
- **[B45]** — the concrete HA-refactor PoC that **closes B37-G6**: ColdRoomPan-rt's 3 component classes,
  8 `Clock.Ticket` timers, and 9 plain interlock fields (plus one no-stock-precedent FIFO, encoded as a
  CSV `String` Property) migrated to the `niagaraSync` contract, built (`jar`+`moduleTestJar` both `BUILD
  SUCCESSFUL`), tested (55/55, 51 unchanged + 4 new with a mutation-kill proof), and walked statically
  against every `NiagaraSyncComponentSpaceValidator` admission rule (all pass). Grounds guide §2.10's
  concrete refactor pattern (steps 3–7) and the narrowed §6 open-risk statement (only the *live*
  two-station failover remains unverified — B45-G1, merging into B37-G1/B37-G3). Does not itself close
  B37-G1/B37-G3 (no live station was available); narrows them to a specific, already-buildable artifact
  rather than a hypothetical migration.
- **[B39]** — the JavaFX/Batik real-fix block — supersedes [B28]'s own stub-jar workaround; §2.11's
  recommended 6-line dependency block is [B39]'s finding, not [B28]'s.
- **[B41]** — the action-audit + web-auth-chain block — grounds §2.13's `Context`-recovery mechanism and
  the audit-gate statement (`context != null && context.getUser() != null`, unchanged from N4).
- **[B43]** — the data-at-rest cryptography map — grounds §3's KeyRing-alias-rename troubleshooting row
  and the `AEADBadTagException` failure-mode statement (later scoped by [B47] to "unreachable via n5mig
  specifically").
- **[B46]** — the Context-threading PoC applied to DashboardPan — grounds §2.13's "verified this fixes the
  write path" claim at the bytecode level.
- **[B47]** — the KeyRing-secrets-across-migration investigation — grounds §5 step 4 and the §3
  troubleshooting row on `migrate.breakKeyringEncoding`; ALSO the block whose correction of [B24] §24.3
  this synthesis defers to (§50 header).
- **[B48]** — the public-evidence block — grounds §5's JACE-9000-only/N4.15-LTS opening statement and the
  §6 open-risk about GA-vs-beta permissiveness.
- **[B49]** — the generated-setter/Context census — grounds §2.13's "3,589 generated setters, corpus-wide"
  headline number and the recommended-pattern ordering (prefer `@NiagaraRpc` > manual `niagara.context`
  recovery > generated setter for internal-only state).

## 50.4 — Child gaps (guide claims this synthesis could not fully ground)

> **Correction (added by [Block 106], §14 cross-block).** B50-G5's batik-awt-util fix is version-locked: only
> 1.18+ carries the `Automatic-Module-Name` that gx.jar requires; 1.14–1.17 fail with `module not found`. See
> [Block 106].

- **B50-G1** — **No driver-type module has ever been built against N5 end-to-end.** Guide §2 (the entire
  step-by-step procedure) was validated by three real build PoCs — ColdRoomPan-rt (control logic, [B16]),
  CompPan-rt (control logic, [B28]), DashboardPan-rt (control logic + servlet, [B28]) — none of which is a
  `BDeviceNetwork`/`BProxyExt`-based driver module. [B22]'s driver-framework findings (basicDriver
  deprecation-but-still-compiles, the `isUnoperational`→`isNonOperational` rename, `BTuningPolicy`
  byte-identical) are all STATIC (real-source-vs-real-source diff, no build attempted) — B22-G2 itself
  flags exactly this as `requires-execution`. If the `build-n4-module` kit is ever used to scaffold an N5
  driver module, the procedure in guide §2 should be treated as **unconfirmed** for that module shape
  until a real driver PoC build is attempted.
- **B50-G2** — **The guide's §2 procedure has not been exercised against a native/native-agg module** (the
  `com.tridium.native`/`native-agg`/`npsdk-native` plugin family, [B2 §2.1] lists these plugin ids but
  [B2]'s own scope explicitly excludes native module builds). None of our 3 modules use native code; if a
  future module needs a native-code build, the plugin-id rename table (guide §2.2) is `[CERT]`-grounded for
  the plugin IDs themselves but the *build procedure* around them is unvalidated.
- **B50-G3** — **The migration runbook's step 1 (install-before-migrate) has never been observed end-to-end
  on a completed `n5mig` run.** The `BModuleRemovalConverter` mechanism ([B14] §14.5) and the
  `moduleName=` compatibility trick ([B17] §17.5) are both real, `[CERT]`-level code-trace findings, but
  chained together into "this WILL make our modules survive migration" is a synthesis this block performs
  across two static-evidence blocks, never confirmed by watching a real migration complete (both [B14
  B14-G1] and [B17 B17-G1] are still open, blocked by the license gate documented in guide §5 step 2). The
  runbook's step 1 recommendation is sound engineering advice grounded in real decompiled control flow,
  but is formally still an `[INFER]` synthesis, not an observed outcome.
- **B50-G4** — **The `moduleName=` trick's durability under a REAL `n5mig` conversion of the module's own
  bog entries has not been tested.** [B17] §17.5 confirms the registry-resolution MECHANISM
  (`Sys.getRegistry().getModule("ColdRoomPan")` would resolve), but the actual `n5mig` run that would
  exercise `BTypeSpecConverter` against a `ColdRoomPan:*` typespec referencing this correctly-declared
  module was never performed (same license-gate blocker). Guide §5 step 1's confidence in this technique
  is therefore bounded by the same B50-G3 caveat.
- **B50-G5** — **Whether the 6-line JavaFX/Batik `compileOnly` fix (guide §2.11) is version-sensitive** was
  explicitly left open by its own source block: [B39 B39-G2] notes only `batik-awt-util:1.19` (the latest
  published version at the time) was validated; whether an older/pinned version matters (e.g. to match
  whatever Batik version a hypothetical JavaFX-bundled JDK distribution beyond Tridium's bare `jre/` might
  expect) is untested. The guide states the fix as unconditional; it should be read as "validated at
  `1.19`, not confirmed version-locked."
- **B50-G6** — **The guide's §2.13 Context-threading recommendation for `@NiagaraRpc` methods (item 1 of
  the "recommended pattern" list) cites the injection MECHANISM from the sibling N4 corpus ([B613] REMIT
  via [B49] §49.5), not a re-opened N5-side `NiagaraRpcServlet` dispatcher.** [B49 B49-G2] explicitly
  flags this as the reason its own `@NiagaraRpc`-audited classification carries `[INFER]` rather than
  `[CERT]`. The guide's ordering (prefer `@NiagaraRpc` first) is sound given the evidence available, but
  the injection code itself was never independently re-verified on the N5 side this corpus has decompiled.
- **B50-G7** — **The guide provides no procedure for a first-party module authored directly as N5-native
  (i.e. never having existed as an N4 module)** — every step in guide §2 is framed as a PORT (N4 source →
  N5), because that is the only scenario any source block tested. A greenfield N5 module would skip most
  of §2's rename/delta steps but this guide does not separately state a "build fresh" path; §2.1–§2.3 and
  §2.9/§2.11–§2.13 remain applicable, §2.4–§2.7 do not apply and this is not stated explicitly in the
  guide's prose (only implicit from context). Flagged for a future guide revision, not a corpus gap per se.

## 50.5 — Self-verification (METHODOLOGY §11)

**Marker tally.** This block makes zero `[CERT]`/`[CERT-hw]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` claims of
its own — every factual assertion is a `[Bn §x.y]` cross-reference to a claim already sealed in its home
block, which is the declared, expected shape of a `Type: synthesis` block (METHODOLOGY §11's own worked
example: "A synthesis block that cites only prior `[Block N]` cross-references will report `n/a`"). A
mechanical `grep -c '\[CERT'` against this file's body (excluding this paragraph's own discussion of the
convention) returns 0, as expected. `[INFER]` appears where this block draws a conclusion by COMBINING two
or more source blocks' own `[CERT]` facts (e.g. §50.4's B50-G3/B50-G4, chaining [B14]+[B17]) — every such
combination is named explicitly in §50.2/§50.4 rather than asserted as a bare claim.

**Citation resolution.** Every `[Bn §x.y]` citation in this block and in the companion guide resolves to a
real section header inside the correspondingly-numbered `niagara5-blockN.md` file in this same corpus —
confirmed by this session's own re-read of all 26 originally-assigned source blocks in full before
drafting, plus a full read of B45 at the amendment (see Sources) — 27 source blocks total. No citation in
either deliverable points to a block section that does not exist.

**Coverage check against the assigned source list.** Blocks read this session, per the task's explicit
list: 1, 2, 3, 5, 7, 8, 9, 10, 14, 16, 17, 20, 22, 24, 26, 28, 29, 31, 37, 39, 41, 43, 46, 47, 48, 49 — all
26 present and read in full. At initial drafting, block 45 did not exist in this corpus
(`RESEARCH-STATE.md`'s own block list jumped from B44 to B46, confirmed by directory listing, not
assumed), so the HA section was first written from the real B37 deep-dive alone. **Amendment**: once
`niagara5-block45.md` was written (the ColdRoomPan HA-ready PoC closing B37-G6), this block and its
companion guide were revised in place per the orchestrator's instruction — guide §2.10/§6, and this
block's §50.2/§50.3/§50.4/§50.6, now cite B45 directly; no other section changed. 27 source blocks are
cited in total after the amendment.

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block50.md`. The
companion guide exists at `/home/cristian/niagara5-research/docs/n4-to-n5-porting-guide.md`. Per this
task's scope, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated or hand-edited this
session — flagged for the next iteration/orchestrator, consistent with every source block's own disclosed
choice.

**MCP-doc snapshots.** N/A — no web/MCP citation in this block; [B48]'s own web citations are reused by
reference (§5, §6), not re-fetched.

## 50.6 — Child-gap ledger cross-reference (inherited, not new)

For completeness, every OPEN child gap from a source block that this guide's §6 "Known open risks"
restates is listed here by its original id, so a reviewer does not need to re-open each source block to
confirm none was silently dropped: B16-G1, B17-G1, B22-G2, B29-G2, B31-G4, B37-G1, B37-G3, B39-G4,
B41-G4, B46-G4, B48 §48.1/§48.6 (B48-G3), B49-G1, and (post-amendment) **B45-G1** (the live two-station
niagaraSync pair test — the same underlying need as B37-G1/B37-G3, narrowed by B45 to a specific,
already-buildable artifact rather than a hypothetical migration). **B37-G6** (build a real HA refactor
and prove it) is now CLOSED by B45 — it is intentionally absent from the open-risk list above; it is
named here only so a reviewer sees it was closed, not silently dropped. None of the still-open gaps are
re-opened or re-adjudicated by this block — they remain the responsibility of their originating
block/corpus backlog.
