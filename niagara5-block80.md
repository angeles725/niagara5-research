# Block 80 — Corpus-wide census of the two Java-21 `SequencedCollection` adoption forms, the JMX/MXBean surface, and the state of the N4-4.15 slot-diff prerequisite

> Research closing/narrowing three census-shaped child gaps left open by earlier blocks, plus recording the
> availability state of a fourth's prerequisite. Covers: **B25-G2** (corpus-wide `SequencedCollection`
> census — [Block 25] and [Block 70] only measured 4 of ~246 decompiled modules); **B70-G1** (the ambiguous
> `getFirst`/`getLast`/`addFirst`/`addLast` call sites — are they the *new* `SequencedCollection` default
> methods on `List`, or the *old* `Deque`/`LinkedList` API?); **B33-G1** (JMX/`javax.management` usage across
> the remaining modules beyond [Block 33]'s permission-gating scope). Does **not** cover: a full per-call-site
> receiver-type classification of all 110 `getFirst`/`getLast` files (sampled, not exhaustively typed — see
> child gap); a decompile-and-diff of the 5 N4-4.15 types for **B31-G1** (the 4.15 install is present on this
> host but no decompiled tree exists for it — recorded as a blocked prerequisite, not closed).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (246 module `vineflower/` trees + `bajaui/fallback/` CFR trees where Vineflower timed out, per [Block 30]'s
> decompiler bake-off; 18,022 `.java` files total). Census method: `find organized -name '*.java' -exec grep`
> over the whole tree (a shell-glob `grep -r organized/*/vineflower` silently under-matched and was discarded
> in favour of `find -exec`). The N4 baseline referenced for deltas is the 4.14 corpus at
> `/home/cristian/niagara-research/organized` (OptimizerSupervisor-N4.14.0.162).

## 80.1 — B25-G2 CLOSED: explicit `java.util.SequencedCollection`/`SequencedMap` *types* appear in exactly ONE N5 subsystem — the `bajaui` NSS2 stylesheet engine — and nowhere else in 18,022 decompiled files `[CERT]`

A corpus-wide census for the literal type names `SequencedCollection`, `SequencedSet`, and `SequencedMap`
(the three interfaces added by JEP 431 in Java 21) returns hits in exactly **7 files, all inside the
`bajaui` module's NSS ("Niagara Style Sheet") theming subsystem** `[CERT]`
(`find organized -name '*.java' -exec grep -l 'Sequenced' {} +`, this session — 6 distinct source files
plus the `docSource` copy of `BStyleDeclarations.java`). `SequencedSet` has **zero** references anywhere
`[CERT]`. The two used types resolve to genuine `java.util.*` imports, not same-named Niagara classes:

- `niagara.ui.style.BStyleDeclarations` declares `private final SequencedMap<String, StyleDeclaration> map;`
  (`organized/bajaui/fallback/niagara/ui/style/BStyleDeclarations.java:24` `import java.util.SequencedMap;`,
  `:40` the field) and its no-arg constructor backs it with a `LinkedHashMap` (`:49`) — i.e. the codebase
  uses `SequencedMap` as the *interface type* for an insertion-ordered map whose runtime class is
  `LinkedHashMap` (which retroactively implements `SequencedMap` under Java 21) `[CERT]`.
- The NSS2 selector engine exposes `SequencedCollection<IStylable>` as the **return type of a public SPI
  method** on every combinator: `ICombinator.getTraversableStylables(...)`
  (`organized/bajaui/fallback/com/tridium/ui/theme/custom/nss/combinator/ICombinator.java:15`) and its four
  implementations `DirectChildCombinator`/`DescendentCombinator`/`SelfCombinator` (`:21`/`:35`/`:20`), all
  consumed at `NSS2.java:93` `SequencedCollection<IStylable> nextStylables = combinator.getTraversableStylables(...)`
  `[CERT]`. This is a CSS-combinator selector-traversal model (`>` direct-child, descendant, self) — a
  genuinely new N5 theming engine, and the one place the Tridium code chose the new interface *type* as an
  API contract rather than a concrete class `[CERT]`.

These 7 files are in `bajaui/fallback/` — the **CFR-decompiled** tree, because Vineflower timed out on
`bajaui` ([Block 30] §decompiler-bake-off). The finding stands regardless of decompiler: the `import`
statements and generic type parameters are structural, not a decompiler artefact `[CERT]`. **B25-G2 verdict:
explicit new-collection-interface *types* are a single-subsystem phenomenon (bajaui NSS2), not a
corpus-wide idiom** — closing [Block 25] §25.2's and [Block 70] §70.5's "only 4 jars measured" scope.

## 80.2 — B70-G1 ADVANCED: the `SequencedCollection` *default methods* (`getFirst`/`getLast` on `List`) ARE adopted in `baja` core — a second, wider adoption form the type-name census in §80.1 cannot see `[CERT]`+`[INFER]`

> **Correction (added by [Block 90], §14 cross-block).** The `EngineManager.peakScanStats`/`peakInterscanStats`
> sites left `[INFER]` below are definitively the OLD `Deque` API: both fields are declared
> `LinkedList<EngineManager.EngineStats>` (`EngineManager.java:58-59`). Full 211-site classification
> (91 new / 61 old / 59 homonym) in [Block 90] §90.1.

Separately from the *type* references, `getFirst()`/`getLast()`/`addFirst()`/`addLast()`/`removeFirst()`/
`removeLast()` — the six methods JEP 431 added as **default methods on `List`/`Deque`/`SequencedCollection`** —
appear in **110 files** across the corpus (`find ... -exec grep -lE '\.(getFirst|getLast|addFirst|addLast|removeFirst|removeLast)\('`,
excluding the `fallback/` duplicate tree) `[CERT]`. The receiver's static type decides whether a given call
is *new* (Java-21 `List.getFirst()`, previously written `get(0)`/`get(size()-1)`) or *old*
(`Deque`/`LinkedList`, where these methods predate Java 21). A sample read of the `baja` hits shows **both
forms coexist**, and several are unambiguously the NEW form on a `List`-typed receiver `[CERT]`:

- `com/tridium/sys/module/ModuleSetClassLoader.java:542,564` — `(X509Certificate) certificates.getFirst()`
  where `certificates` is a `List<? extends Certificate>` from a cert path → **new** `List.getFirst()` `[CERT]`.
- `com/tridium/sys/module/NModuleModuleFinderFactory.java:651,657` —
  `codeSigner.getSignerCertPath().getCertificates().getFirst()...getPublicKey()` and the matching `.getLast()`
  → **new** form, in the module code-signing path (the same TPK/leaf-key path [Block 77] §77.4 read for B53-G5)
  `[CERT]`.
- `niagara/tag/Tags.java:44` `values.getFirst()` and `niagara/timezone/DstRule.java:138`
  `javaRules.getTransitionRules().getFirst()` — both on `List`-returning expressions → **new** form `[CERT]`.
- `com/tridium/sys/engine/EngineManager.java:168,176,203,211,429,432` — `peakScanStats.getFirst()`/
  `.getLast()` on the engine's peak-scan-stats collection; receiver type not confirmed in this sample, so
  new-vs-old is **[INFER]** pending the field declaration read `[INFER]`.

**B70-G1 verdict: partial.** The corpus uses the new `SequencedCollection` default methods on `List`
receivers in `baja` core (signing, tags, timezone) — a real, if light, Java-21 modernization that the
type-name census in §80.1 structurally cannot detect (a `List.getFirst()` call carries no `Sequenced*`
token). A full new-vs-old classification of all 110 files requires reading each receiver's declared type and
is left as child gap **B80-G1**. This refines [Block 25] §25's "45 records / 33 pattern-switches / 0 virtual
threads" modernization profile: add "≥6 confirmed `List.getFirst`/`getLast` new-API call sites in baja,
adoption otherwise sparse."

## 80.3 — B33-G1 CLOSED: N5's JMX surface is read-only MXBean *introspection* in 7 modules plus exactly ONE MBean *registration* (Jetty's) — no Tridium module exposes its own MBeans `[CERT]`

`java.lang.management.ManagementFactory` is referenced in **7 modules** — `systemMonitor` (3 files),
`workbench` (2), `platform` (2), `baja` (2), `_bin-ext/nre` (2), `_bin-ext/niagarad` (2), `jetty` (1)
`[CERT]` (`find ... -exec grep -l 'ManagementFactory'`, `fallback/` excluded). Every use is **read-only
platform-MXBean introspection**, not MBean publication `[CERT]`:

- `ManagementFactory.getMemoryPoolMXBeans` (6×), `getThreadMXBean` (4×), `getClassLoadingMXBean` (4×),
  `getPlatformMXBean` (3×), `getRuntimeMXBean` (2×) — e.g.
  `systemMonitor/.../BLoadedClassesMonitor.java:60` (`getClassLoadingMXBean`),
  `BCodeCacheMemoryMonitor.java:67` / `BMetaSpaceMemoryMonitor.java:67` (`getMemoryPoolMXBeans`) `[CERT]`.
- **`registerMBean` has zero occurrences corpus-wide** `[CERT]`. The single `MBeanServer` reference is
  `jetty/.../BJettyWebServer.java:562` `new MBeanContainer(ManagementFactory.getPlatformMBeanServer())` —
  Jetty's own standard JMX integration, which registers **Jetty's** connector/thread-pool MBeans, not any
  Niagara component `[CERT]`.
- The lone `javax.management` string in the corpus is a **logger-name literal** in
  `_bin-ext/niagarad/.../NiagaraDaemonLogSettings.java:37` (a list of `java.util.logging` package names to
  configure), not a JMX API use `[CERT]`. The 80 `ObjectName` hits are a **false positive**: zero
  `import javax.management.ObjectName` statements exist — they are a same-named Niagara-internal class `[CERT]`.

**B33-G1 verdict:** N5's JMX footprint is diagnostic-only (memory/thread/class-loading MXBean reads,
concentrated in `systemMonitor`) plus Jetty's self-registration; no first-party Niagara type is published to
JMX, consistent with [Block 33]'s finding that the `MBEAN`-class permission gate has little first-party
surface to guard. What the `MBeanContainer` exposes and whether the platform server is remotely reachable is
child gap **B80-G2**.

## 80.4 — B31-G1 prerequisite recorded, NOT closed: an N4-4.15 install exists on this host but no decompiled tree does, so the 5-type slot diff cannot be run this session `[CERT]`

[Block 31] §31 left the 4.14→4.15 slot diff for 5 types open because the N4 sibling corpus at
`/home/cristian/niagara-research/organized` is decompiled from **4.14** (`OptimizerSupervisor-N4.14.0.162`)
`[CERT]`. This session confirms an N4-**4.15** installation is physically present —
`/mnt/c/ProgramData/Niagara4.15` and `/mnt/c/Users/equipo/Niagara4.15` `[CERT]` (`find /mnt/c -maxdepth 3
-iname '*4.15*'`) — but there is **no decompiled `organized/`-style tree for it**, and decompiling the 5
target modules' jars is a separate bounded effort out of this census block's scope. **B31-G1 stays open,
re-tagged as investigable-with-prerequisite** (the jars are reachable; only the decompile step is missing) —
child gap **B80-G3** names the exact deliverable (javap/decompile the 5 types from the 4.15 jars and diff
against the 4.14 corpus).

## 80.x — Connections

- Extends [Block 25] (Java-feature adoption census) and [Block 70] (which measured only control/alarm/
  kitControl/schedule): §80.1/§80.2 give the whole-corpus picture [Block 70] §70.5 explicitly deferred.
- §80.2's code-signing `getFirst`/`getLast` sites are in the same `NModuleModuleFinderFactory` cert path
  [Block 77] §77.4 read for the TPK/Honeywell-leaf-key identity (B53-G5).
- §80.3 refines [Block 33]'s JMX permission-gating discussion with the concrete usage census.
- §80.4 is the unblocking note for [Block 31]'s deferred 4.15 diff.

## 80.x — Child gaps opened

- **B80-G1** — Full new-vs-old classification of all 110 `getFirst`/`getLast`/`addFirst`/`addLast` call
  sites by declared receiver type (`List`/`SequencedCollection` = new; `Deque`/`LinkedList` = old).
- **B80-G2** — What Jetty's `MBeanContainer` publishes on N5 and whether the platform MBean server is
  remotely reachable / authenticated.
- **B80-G3** — Decompile the 5 B31 target types from the on-host N4-4.15 jars and diff their slots against
  the 4.14 corpus (the prerequisite for B31-G1).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `SequencedCollection`/`SequencedSet`/`SequencedMap` types appear only in bajaui NSS (7 files) | [CERT] | `find ... -exec grep -l 'Sequenced'` → 7 files, all `bajaui`; `SequencedSet` 0 hits |
| 2 | `BStyleDeclarations` uses `SequencedMap` as field type over a `LinkedHashMap` | [CERT] | `BStyleDeclarations.java:24,40,49` |
| 3 | `ICombinator` SPI returns `SequencedCollection<IStylable>`, consumed at `NSS2.java:93` | [CERT] | `ICombinator.java:15`, `NSS2.java:93` |
| 4 | `getFirst`/`getLast`/… appear in 110 files corpus-wide | [CERT] | `find ... -exec grep -lE` count |
| 5 | ≥4 confirmed new-form `List.getFirst()`/`getLast()` sites in baja (signing, tags, timezone) | [CERT] | `ModuleSetClassLoader.java:542,564`; `NModuleModuleFinderFactory.java:651,657`; `Tags.java:44`; `DstRule.java:138` |
| 6 | EngineManager `peakScanStats.getFirst/getLast` new-vs-old not confirmed | [INFER] | `EngineManager.java:168,176,203,211,429,432` (receiver type unread) |
| 7 | `ManagementFactory` used in 7 modules, MXBean introspection only | [CERT] | `find ... -exec grep -l 'ManagementFactory'` module tally; `ManagementFactory.get*` breakdown |
| 8 | `registerMBean` zero occurrences; only `MBeanServer` use is jetty's `MBeanContainer` | [CERT] | `registerMBean` 0 hits; `BJettyWebServer.java:562` |
| 9 | 80 `ObjectName` hits are a false positive (0 `javax.management.ObjectName` imports) | [CERT] | `import javax.management.ObjectName` → 0 |
| 10 | An N4-4.15 install exists on-host but has no decompiled tree | [CERT] | `find /mnt/c -maxdepth 3 -iname '*4.15*'`; N4 corpus is 4.14 |

Tally: 9 [CERT], 1 [INFER] (ratio 0.10). Load-bearing tokens confirmed present this session via direct
`grep`/`find` output (not recalled): `SequencedMap`/`SequencedCollection` imports + declarations in the named
bajaui files; `registerMBean` zero-hit; `ManagementFactory.getMemoryPoolMXBeans`/`getThreadMXBean` counts;
`BJettyWebServer.java:562` `MBeanContainer`; the `/mnt/c/...Niagara4.15` paths. Negative-existence claims
(`SequencedSet` = 0, `registerMBean` = 0, `javax.management.ObjectName` import = 0) each rest on a
whole-corpus `find -exec grep` that ran to completion, per METHODOLOGY §3's symmetric-opening rule.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block80.md`. This block was
authored directly by the orchestrator (Opus) because the wave-8 delegated writer for this cluster was
terminated by a weekly rate-limit before writing; census commands were run in-session. Per the wave
convention, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration is performed by the integrator step.
