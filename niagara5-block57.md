# Block 57 — The command-line denylist's own override path, and N4 parity for data-at-rest defaults

> Research closing three named child gaps: **B53-G3** (whether the self-referential bypass [Block 53] §53.2
> flagged in `niagara.commandLinePropertyDenyList`'s own read is reachable in practice — i.e. can a
> command-line `-D` override of that key itself neuter Gate A before Gate A ever runs), **B43-G2** (narrows
> **B19-G1**: does N4.14 already default `BOrientSystemDb.databaseEncryption` to `encrypted`, or is that
> N5-new), and **B43-G3** (sharpens **B19-G2**: does N4.14's own `EncryptionKeySource` enum already carry
> the same 5 members N5's does). Covers: the exact boot-time call order in `Nre.boot(BootEnv)` between
> `verifySystemProperties()` and `loadSystemProperties()`/`addToSystemProperties()`; a fresh, unguarded read
> of `addToSystemProperties`'s denylist-derivation branch showing it has no membership check and no
> `cmdline::`-shadow check of its own key; a second, file-based JVM-argument-injection surface
> (`nre.properties`'s `station.java.options=`/`wb.java.options=` keys) not previously logged in this corpus;
> a fresh `strings` corroboration of `nre.dll`'s `-Dcmdline::` tagging; and a direct N4.14.0.162-vs-N5
> byte-level comparison of both `BOrientSystemDb.databaseEncryption`'s default and `EncryptionKeySource`'s
> enum body. Does **not** cover: live `[CERT-hw]` reproduction of the `-D` override on a running install
> (no execution performed — see child gap below); disassembly of `nre.dll`'s `nre.properties`-file-reading
> code path (only its raw-argv path has `strings` corroboration from [Block 53] and this session); tracing
> how `platDaemon` actually spawns the `station.exe`/service process (searched, not found in this corpus —
> see child gap).
>
> Subject version: **dual subject, both re-confirmed this session**. (1) Local N5 install **5.0.0.28
> (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install [Block 40]/[Block 43]/[Block 53]
> read; decompiled sources at `/home/cristian/niagara5-research/organized/{baja,_bin-ext/nre}/vineflower/`.
> (2) Local N4 install **4.14.0.162 (OEM Honeywell "Optimizer Supervisor")** at
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162` — the `niagara-research` corpus's own subject;
> decompiled sources at `/home/cristian/niagara-research/{sources/decompiled/nre-ext,
> organized/orientSystemDb/orientSystemDb-se}/vineflower/`. Both `BOrientSystemDb`'s and `EncryptionKeySource`'s
> N4-side host jars (`orientSystemDb-se.jar`, `bin/ext/nre.jar`) carry the identical `vendorVersion="4.14.0.162"`
> and near-identical `buildMillis` (`1718363816953` / `1718362543724` — same release build, minutes apart),
> confirmed by re-reading both `module.xml` files this session — an apples-to-apples single-install
> comparison, not a cross-version guess.
>
> Sources: `organized/baja/vineflower/com/tridium/sys/Nre.java` (re-read `:178-267` `main()` head, `:608-689`
> `boot(BootEnv)` in full, `:785-853` `loadSystemProperties`/`addToSystemProperties`/
> `hasWritePermissionsToSystemPropertiesFile` whole-method, `:875-881` `verifySystemProperties()` whole-method
> — all fresh reads this session, not re-cited from [Block 40]/[Block 53]);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/util/SystemPropertiesUtil.java` (whole file, re-read,
> confirms `CMDLINE_PROP="cmdline::"` constant not previously cited in this corpus);
> `/mnt/c/Program Files/Niagara/5.0.0.28/defaults/nre.properties` and
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/etc/nre.properties` (live install file reads, this
> session); `strings` output over `/mnt/c/Program Files/Niagara/5.0.0.28/bin/nre.dll` (fresh independent run,
> this session, not reused from [Block 53]); `organized/platDaemon/vineflower/com/tridium/platDaemon/command/
> BStartStationCommand.java` (grepped, not whole-file-read — see §57.1's precondition discussion);
> N4-side: `niagara-research/sources/decompiled/nre-ext/com/tridium/nre/security/EncryptionKeySource.java`
> (whole file, 7 lines) + its `META-INF/module.xml`; `niagara-research/organized/orientSystemDb/
> orientSystemDb-se/vineflower/com/tridium/systemDb/orient/BOrientSystemDb.java` (targeted reads: `:100-190`
> property declaration block, `:925-948` `KeyRingAttributeHolder.getPasswordFromKeyRing`) + its
> `META-INF/module.xml`; N5-side comparison file
> `organized/_bin-ext/nre/vineflower/niagara/nre/security/EncryptionKeySource.java` (whole file, 10 lines,
> re-read this session for a literal side-by-side, not merely re-cited from [Block 43]).
>
> Method: targeted + whole-method reading of already-decompiled Vineflower sources (no fresh decompilation
> this session — every file read was already present in `organized/`/`sources/decompiled/` from prior
> sessions) + 2 live install-file reads (`nre.properties` ×2) + 1 fresh `strings` pass on `nre.dll` for
> independent corroboration + `grep`-driven negative-existence re-checks. Markers: `[CERT-hw]` verified
> empirically against the live system/device — highest · `[CERT]` local primary source (`file:line`) ·
> `[CERT-web]` official web · `[CERT-a]` secondary source/forum · `[INFER]` deduction. For MINIFIED/OBFUSCATED
> sources: n/a this block (all reads are Vineflower-decompiled, non-minified source already in the two
> corpora, not fresh scratch-temp decompilation).
>
> Security/licensing + data-at-rest-cryptography layers. Connects [Block 40] (§40.1's `Nre.loadSystemProperties`/
> `addToSystemProperties` boot loader), [Block 43] (§43.5's `BOrientSystemDb` default, §43.3's
> `EncryptionKeySource` enum), [Block 53] (§53.2's Gate A self-referential bypass, first flagged as `[INFER]`-
> exploitability).
>
> **Type:** `mixed` — §57.1 closes a prior block's evidence gap with fresh `file:line`/`strings` reading and
> draws a bounded severity conclusion across [Block 40]/[Block 53]'s own prior findings (synthesis half);
> §57.2/§57.3 are straight comparative `[CERT]` evidence blocks (byte-level N4-vs-N5 reads), per METHODOLOGY
> §11's MIXED trigger.

---

## 57.1 — B53-G3 CLOSED: the self-override is CONFIRMED reachable at the code level, but it requires a precondition already equivalent to host-admin access; a second, file-based injection surface (`nre.properties`) was also found `[CERT]`

[Block 53] §53.2 found that `niagara.commandLinePropertyDenyList` is read via a plain
`System.getProperty(key, default)` call and is absent from both of N5's "dangerous sysprop" gates, then
flagged as `[INFER]` (named **B53-G3**) whether this is exploitable — i.e. whether anything upstream of
`Nre.main` stops an unprivileged actor from supplying an arbitrary `-D` flag in the first place. This
session traces the exact boot-time order, re-reads the vulnerable method fresh, and finds a second injection
surface not previously logged.

**Exact boot order, re-traced from `Nre.boot(BootEnv)` this session:**

```
608  public static synchronized boolean boot(BootEnv bootEnv) {
 ...
646  verifyPolicyFiles();
647  verifySystemProperties();      // Gate B's FATAL check — 27-entry native list ONLY
 ...
680  loadSystemProperties();        // → addToSystemProperties() — Gate A lives HERE
681  overrideSecurityProperties();
```
`[CERT]` `Nre.java:608-689` (whole method, re-read this session). `verifySystemProperties()` runs **33 lines
before** `loadSystemProperties()`, and its own body (`:875-881`, re-read whole this session) iterates
`SystemPropertiesUtil.PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` exclusively:

```
875  private static void verifySystemProperties() {
876     for (String protectedNativeProperty : SystemPropertiesUtil.PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST) {
877        if (System.getProperty(protectedNativeProperty) != null && System.getProperty("cmdline::" + protectedNativeProperty) != null) {
878           fatal(...);
```
`[CERT]` `Nre.java:875-881`. A fresh re-check of `SystemPropertiesUtil.java` this session (whole file,
`grep -n "commandLinePropertyDenyList\|skipModuleValidation"` → **zero hits**) re-confirms [Block 53]'s
negative-existence claim independently: `niagara.commandLinePropertyDenyList` is not a member of this
27-entry list, so `verifySystemProperties()` — the ONLY unconditional, fatal, pre-file-load gate in the boot
sequence — never examines it, by construction. `[CERT]` (fresh grep, this session, not inherited from
[Block 53]/[Block 40]'s prior counts).

**`addToSystemProperties`'s denylist read, re-read whole this session — no membership check, no
`cmdline::`-shadow check of its OWN key, unlike every sibling check in the same method:**

```
801  private static void addToSystemProperties(File systemPropertiesFile, Properties props) {
802     boolean hasSystemPropsWriteAccess = hasWritePermissionsToSystemPropertiesFile(systemPropertiesFile);
803     if (!hasSystemPropsWriteAccess) {
804        String denylistProperty = System.getProperty(
805           "niagara.commandLinePropertyDenyList",
806           "niagara.export.preventCSVInjection,niagara.webbrowser.disable,niagara.webbrowser.urlAllowList,
                niagara.baja.formatDenyList,niagara.baja.formatDenyListExclusions,jdk.tls.rejectClientInitiatedRenegotiation"
807        );
808        System.setProperty("niagara.commandLinePropertyDenyList", denylistProperty);
809        String[] denylistedProps = denylistProperty.split(",");
810        for (String denylistedProp : denylistedProps) {
811           String trimmedDenylistedProp = denylistedProp.trim();
812           if (!trimmedDenylistedProp.isEmpty()
813              && (System.getProperty(trimmedDenylistedProp) != null || System.getProperty("cmdline::" + trimmedDenylistedProp) != null)) {
814              System.clearProperty(trimmedDenylistedProp);
815              System.clearProperty("cmdline::" + trimmedDenylistedProp);
816              LOGGER.warning(...);
817           }
818        }
819     }
822     for (String key : props.stringPropertyNames()) {         // file-content keys only, from HERE down
823        if (SystemPropertiesUtil.PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST.contains(key)) { ... }
825        else {
826           if (System.getProperty(key) != null && System.getProperty("cmdline::" + key) != null) { ... }
834           System.setProperty(key, props.getProperty(key).trim());
835        }
836     }
837  }
```
`[CERT]` `Nre.java:801-837` (whole method, re-read this session — line numbers verbatim from source, not
reflowed except the multi-line string literal at `:806`, reflowed for width as in [Block 53]). **The line
804-806 read is a bare two-argument `System.getProperty(key, default)` call — no membership check against
any list, and critically no check of `System.getProperty("cmdline::niagara.commandLinePropertyDenyList")`
at all**, in direct contrast to (a) the file-content loop three lines below it (`:826`, which DOES check the
`cmdline::`-shadow for every key it processes) and (b) `verifySystemProperties()`'s identical shadow-check
pattern for the 27-entry native list (`:877`). This asymmetry is the exact mechanism [Block 53] §53.2 named:
**re-confirmed by full-method re-read, not merely re-cited, this session.**

**Two independent findings sharpen the bound beyond what [Block 53] established:**

1. **The whole denylist-derivation block is gated behind `!hasSystemPropsWriteAccess` (`:803`)** — an OS-level
   `FileLock` probe on `system.properties` itself (`hasWritePermissionsToSystemPropertiesFile`, `:839-853`,
   re-read whole this session). This means Gate A is **already a no-op, with or without any override**,
   whenever the OS user launching the process already has write access to its own `system.properties` file —
   the ordinary single-user/admin-owned Windows or Linux install case. The self-referential override
   (`-Dniagara.commandLinePropertyDenyList=`) only matters for the NARROWER case where the launching user
   lacks that write access but CAN still supply arbitrary `-D` flags to the launcher — itself an unusual
   split of privilege (bounded further below).
2. **A second, file-based JVM-argument-injection surface exists, not previously logged in this corpus.**
   `nre.properties` — read live from both the shipped dist-default template and this host's config-home
   copy this session — declares:
   ```
   station.java.options=
   wb.java.options=
   test.java.options=
   nre.java.options=
   ```
   `[CERT]` `/mnt/c/Program Files/Niagara/5.0.0.28/defaults/nre.properties` and
   `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/etc/nre.properties` (both read this session, both
   currently EMPTY on this install — a negative/default-state finding, not a live override). Per the file's
   own header comment, these keys are "used by the NRE launch executable to initialize the containing JRE" —
   i.e. `nre.dll`'s launcher stub reads this file and folds its value into the JVM's own launch argv,
   **entirely independent of the OS-level argv the `.exe` itself was invoked with**. This means "supplying a
   command-line `-D` flag" is not limited to literally typing it at a shell prompt: an actor with write
   access to `<config-home>/etc/nre.properties` (the SAME directory holding `system.properties`, `.km`, and
   every other host-security config file) could populate `station.java.options=-Dniagara.commandLinePropertyDenyList=`
   to the same effect. **Whether `nre.dll` ALSO stamps a `cmdline::`-prefixed shadow for options sourced from
   this FILE (vs. only for options typed on the actual OS argv) was not determined this session** — the
   `strings` evidence below corroborates only the raw-argv path, not `nre.properties`-file parsing, which
   would require disassembly — named child gap **B57-G1**.

**Fresh `strings` corroboration of the native `-Dcmdline::` tagging, run independently this session (not
reused from [Block 53]):**
```
952 nre>   modulePath               = %s
953 nre>   applicationType          = %d
954 nre>   argv[%d] = "%s"
955 -Dcmdline::
956 --add-opens=java.base/java.net=niagara.nre
...
960 -javaagent:%s\bin\ext\nre.jar
```
`[CERT-hw]` `strings "/mnt/c/Program Files/Niagara/5.0.0.28/bin/nre.dll"`, this session. The `-Dcmdline::`
literal sits immediately after `nre>   argv[%d] = "%s"` (the debug-trace format string `nre.dll`'s own
`buildArgs()`-equivalent routine uses while echoing each constructed JVM argument) and immediately before a
run of FIXED, non-property `--add-opens=...`/`-javaagent:...` literals — consistent with [Block 53]'s own
reading: `-Dcmdline::` is a generic prefix concatenated with whichever key/value the native code is currently
processing, not a name-specific filter. No `niagara.commandLinePropertyDenyList`-specific string, and no
`skipModuleValidation`-specific string, appears anywhere in this dump (re-confirmed, zero hits both terms,
this session) — the native binary still does not special-case any property NAME, matching [Block 53] §53.2's
conclusion.

**Precondition / severity bound — who can reach this at all.** Two access paths were found this session,
both requiring host-local privilege already comparable to what an attacker would need to cause equal or
greater damage by simpler means:
- **Raw OS argv**: whoever can execute `station.exe`/`n5mig.exe`/`wb.exe` WITH custom arguments already has
  local execute access to the install's `bin/` directory — the same position from which `system.properties`,
  `nre.properties`, or `.km`/KeyRing files could often be read or replaced directly, subject to OS file
  permissions.
- **`nre.properties` edit**: requires filesystem WRITE access to `<config-home>/etc/`, the identical
  directory holding `system.properties` (Gate B's own protected file) and the platform's security config —
  an actor with THAT access could, more directly, simply add `niagara.commandLinePropertyDenyList=` as a
  plain KEY in `system.properties` itself for the SAME effect (Gate B's file-content loop, `:822-836`, only
  refuses keys on the 27-entry NATIVE list, never `niagara.commandLinePropertyDenyList`) — no `-D`/`cmdline::`
  mechanism is even required from this position.
- **No remotely-reachable path was found.** `BStartStationCommand.java` (the `platDaemon` command class that
  would plausibly handle a remote-triggered station start/restart) was grepped this session for
  `ProcessBuilder`/argument-list construction and returned **zero hits** — a negative finding, but a narrow
  one: no Java source anywhere in this N5 corpus contains `ProcessBuilder` outside API documentation pages
  (`docDeveloper`'s `RuntimeExecPermission` docs) `[CERT]` (fresh `grep -rl "ProcessBuilder"` across
  `organized/`, this session). Actual station-process spawning (Windows Service Control Manager start, or an
  equivalent native daemon call) is therefore NOT visible at the source level in this corpus — it is either
  native-code-mediated or outside the decompiled tree entirely. This is a genuine gap, not a clean negative
  — named **B57-G2**.

**Net verdict, closing B53-G3: CONFIRMED, not merely `[INFER]`, at the static-code level — `Nre.java:804-806`
reads `niagara.commandLinePropertyDenyList` with no membership check and no self-referential shadow check, so
a command-line-or-`nre.properties`-supplied override of that exact key IS honored verbatim and DOES neuter
Gate A's 6 named protections.** Exploitability is **BOUNDED**, not open: every access path found this session
already requires local host-admin-equivalent privilege (process-launch argument control, or write access to
`<config-home>/etc/`) — a position from which Gate B's OWN, narrower file-content denylist (the 27-entry
native list) could also be trivially sidestepped by editing `system.properties` directly for keys NOT on that
list, `niagara.commandLinePropertyDenyList` among them. No privilege-escalation or remote-trigger path was
found; this is a confirmed design gap in a defense-in-depth layer, not a standalone vulnerability with its
own reachable precondition below "already has host config-write or process-launch-argument access."

## 57.2 — B43-G2 CLOSED (and B19-G1 fully settled): N4.14.0.162's `BOrientSystemDb.databaseEncryption` is ALREADY `encrypted` by default — byte-identical default to N5, not new `[CERT]`

[Block 43] §43.5 found N5 5.0.0.28's `systemDb` is encrypted-at-rest by default, but had only opened the N5
module, leaving N4 parity as `[INFER]` (**B43-G2**, narrowing [Block 19]'s **B19-G1**). This session opens
the N4.14.0.162 `orientSystemDb-se` module (the exact vendor build already present in `niagara-research`'s
corpus, confirmed same-release via `module.xml`) directly.

```
104  @NiagaraProperty(
105     name = "databaseEncryption",
106     type = "BDatabaseEncryptionState",
107     defaultValue = "BDatabaseEncryptionState.encrypted",
...
141  public static final Property databaseEncryption = newProperty(5, BDatabaseEncryptionState.encrypted, null);
```
`[CERT]` `niagara-research/organized/orientSystemDb/orientSystemDb-se/vineflower/com/tridium/systemDb/orient/
BOrientSystemDb.java:104-141` (property declaration + static `Property` init, read fresh this session). This
is a **verbatim match** to N5's own citation ([Block 43] §43.5: `BOrientSystemDb.java:109`, same
`defaultValue = "BDatabaseEncryptionState.encrypted"`, same `flags = 5`) — the property name, type, default
value string, and flags integer are identical between the two versions.

The three dedicated KeyRing aliases [Block 43] §43.5 found EXPORTABLE in N5 are also byte-identical in N4:

```
166  private static final String KEY_RING_ROOT_ALIAS = "orientSystemDb.root";
167  private static final String KEY_RING_ADMIN_ALIAS = "orientSystemDb.admin";
168  private static final String KEY_RING_DB_ALIAS = "orientSystemDb.database";
...
941                  k = keyRing.createKey(keyAlias, true);   // isExportable=true, same literal as N5:939
```
`[CERT]` `BOrientSystemDb.java:166-168,925-943` (`KeyRingAttributeHolder.getPasswordFromKeyRing`, read fresh
this session). Alias strings, the `createKey(keyAlias, true)` exportable-by-construction call, and the
lazy-auto-create-on-first-use pattern (`getKey(alias)` → `null` → `createKey`) all match [Block 43] §43.5's
N5 citations line-for-line in structure (different line numbers, identical code shape).

**Net finding, closing B43-G2 and fully settling B19-G1: `databaseEncryption`'s `encrypted`-by-default
polarity is NOT new in N5 — it was already the N4.14.0.162 default**, confirmed by direct decompile of the
exact vendor build already present in this session's two-corpus setup, not inferred from OrientDB's own
upstream defaults as [Block 43] §43.5 had to fall back to. The mechanism, the three alias names, and the
exportability flag are all unchanged across the N4→N5 boundary for this artefact.

## 57.3 — B43-G3 CLOSED (and B19-G2 fully settled): N4.14.0.162's `EncryptionKeySource` enum is the SAME 5 members as N5 — only the package name changed `[CERT]`

[Block 19] §19.7 quoted N5's 5-member `EncryptionKeySource` enum (`none, keyring, external, shared,
undefined`) and left open whether N4 4.14 already had the same 5 (**B19-G2**); [Block 43] §43.3 sharpened
this as **B43-G3**, noting every OTHER structural constant in the surrounding `com.tridium.nre.security.*`
package was found byte-identical between versions, raising the prior that this enum would be too — but did
not open the N4 file. This session finds it already present, undecompiled-this-session but already in the
`niagara-research` corpus from an earlier (2026-06-29/2026-08-24) `nre.jar` decompile pass, and reads it
fresh:

```
package com.tridium.nre.security;

public enum EncryptionKeySource {
   none,
   keyring,
   external,
   shared,
   undefined;
}
```
`[CERT]` `niagara-research/sources/decompiled/nre-ext/com/tridium/nre/security/EncryptionKeySource.java`
(whole file, 7 lines, re-read this session). Side-by-side against N5's own file, also re-read whole this
session:

```
package niagara.nre.security;

public enum EncryptionKeySource {
   none,
   keyring,
   external,
   shared,
   undefined;
}
```
`[CERT]` `niagara5-research/organized/_bin-ext/nre/vineflower/niagara/nre/security/EncryptionKeySource.java`
(whole file, 10 lines, re-read this session).

| | N4.14.0.162 | N5 5.0.0.28 |
|---|---|---|
| Package | `com.tridium.nre.security` | `niagara.nre.security` |
| Enum body | `none, keyring, external, shared, undefined` | `none, keyring, external, shared, undefined` |
| Member count | **5** | **5** |
| Member names/order | identical | identical |

`[CERT]` table built from the two whole-file reads above. **The ONLY difference between the two files is the
package declaration** — `com.tridium.*` → `niagara.*` — the exact same rename pattern [Block 5] already
established for the broader `javax.baja.*`→`niagara.*` move and [Block 43] §43.4 already found for the
`BAes256PasswordEncoder.key` KeyRing alias STRING (a related but separate rename, `javax.baja.security.
BAes256PasswordEncoder.key` → `niagara.security.BAes256PasswordEncoder.key`). The enum's own five member
NAMES are untouched by the package move.

Both host jars are the SAME release build (`module.xml` cross-check, this session):
`orientSystemDb-se.jar` → `vendorVersion="4.14.0.162" buildMillis="1718363816953"`; `bin/ext/nre.jar` →
`vendorVersion="4.14.0.162" buildMillis="1718362543724"` — 1.27 seconds apart in epoch-millis terms is wrong
to read literally (these are two DIFFERENT modules' own build timestamps, not a single build event) but both
carry the identical `buildHost="ee033fd13409"` and `releaseDate="2024-05-28"` `[CERT]`, confirming both files
came from the SAME Honeywell 4.14.0.162 release artifact set, not two different N4 point releases mixed
together.

**Net finding, closing B43-G3 and fully settling B19-G2: `shared` and `undefined` are NOT N5-new members —
all 5 `EncryptionKeySource` values already existed, unchanged, in N4.14.0.162.** [Block 43] §43.3's own
BEHAVIORAL resolution of what `shared`/`undefined` DO (backup/restore in-memory re-wrapping; a header-parse
sentinel, respectively) therefore also transfers to N4 as the likely N4 semantics, though that specific
BEHAVIORAL claim (as opposed to the enum body's existence) was not independently re-verified against N4's own
`BogPasswordObjectEncoder` this session — a narrower residual question than B43-G3 itself, named below.

## 57.4 — Connections

- **[Block 40]** — §57.1 re-reads and re-confirms §40.1's own boot-order tracing (`verifySystemProperties()`
  before `loadSystemProperties()`, the 27-entry `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` correction to 27
  from [Block 33]'s original 24), extending it with the `nre.properties`-file injection surface §40.1 did not
  examine.
- **[Block 43]** — §57.2 closes **B43-G2** (narrowing [Block 19]'s **B19-G1**): §43.5's N5-only
  `databaseEncryption` default finding now has its N4 twin, byte-identical. §57.3 closes **B43-G3**
  (sharpening [Block 19]'s **B19-G2**): §43.3's 5-member enum reading now has its N4 twin, byte-identical
  bar the package rename. Both confirm §43.1's own thesis (the three-layer secrets chain, and now these two
  further artefacts, survive N4→N5 essentially unchanged) more strongly than §43's own hedged framing.
- **[Block 53]** — §57.1 closes **B53-G3**: the self-referential Gate A bypass §53.2 first surfaced as a
  static `[CERT]` fact with `[INFER]` exploitability is now CONFIRMED reachable in code, and BOUNDED to an
  already-privileged precondition — upgrading, not merely re-stating, §53.2's split.
- **[Block 19]** — both **B19-G1** and **B19-G2**, the block's two oldest still-open child gaps on this
  topic (predating even [Block 43]'s partial narrowing), are now fully settled by §57.2/§57.3.

## 57.5 — Child gaps

- **B57-G1** — Determine whether `nre.dll`'s `nre.properties`-file-reading code path (parsing
  `station.java.options=`/`wb.java.options=`/etc.) ALSO stamps a `cmdline::`-prefixed shadow property for
  each option it injects, the same way the raw-OS-argv path does (per [Block 53]'s and this session's
  `strings` evidence). If it does NOT, an `nre.properties`-supplied `-D` flag would be indistinguishable from
  a `system.properties`-file-supplied one to `verifySystemProperties()`/`addToSystemProperties()`'s
  `cmdline::`-shadow checks — a DIFFERENT bypass shape than the one this block traced. Requires disassembly
  (Ghidra) of `nre.dll`'s option-file parser, not `strings`-level corroboration.
- **B57-G2** — Trace how `platDaemon`/niagarad actually spawns the `station.exe` OS process (Windows Service
  Control Manager start, systemd/native daemon call, or something else) — not visible at the Java source
  level in this corpus (`grep -rl "ProcessBuilder"` returned zero non-doc hits, this session). Needed to
  fully close whether ANY remote/daemon-mediated path could inject `-D` flags into a station launch, vs. only
  the local-argv and `nre.properties`-write paths this session confirmed.
- **B57-G3** — Live `[CERT-hw]` reproduction: actually launch `station.exe`/`n5mig.exe` with
  `-Dniagara.commandLinePropertyDenyList=` on a test install lacking `system.properties` write access, and
  confirm the 6 named protections (CSV-injection prevention, browser URL allowlist, TLS-renegotiation
  rejection) are observably disabled — this session's finding is a static code-read, not a live
  reproduction.
- **B57-G4** — Independently re-verify N4.14.0.162's own `BogPasswordObjectEncoder.java` (not opened this
  session) to confirm `shared`/`undefined`'s BEHAVIORAL semantics ([Block 43] §43.3's reading, transferred
  here only by enum-body identity, not independently re-derived from N4's own encoder class).

## Self-verification

**Token check:** every `file:line` citation in §57.1-§57.3 was `grep -n`-confirmed present at or adjacent to
the stated line this session, immediately before drafting each section. `Nre.java` citations (`:608`, `:647`,
`:680`, `:801`, `:804-806`, `:822`, `:826`, `:834`, `:839`, `:875-878`) — all present, re-read as whole method
bodies, not single-line greps. `SystemPropertiesUtil.java` — whole file re-read, `CMDLINE_PROP` constant at
line 18 confirmed present (not previously cited in this corpus). N4-side `EncryptionKeySource.java` (7 lines)
and `BOrientSystemDb.java:104-141,166-168,925-943` — whole-file / targeted re-reads, all present. N5-side
`EncryptionKeySource.java` (10 lines) — whole file re-read for the side-by-side table.

**Marker tally (manual count — no `toolbelt/verify-block.sh` invocation available in this session's toolset;
same disclosed absence as [Block 53]/[Block 17]/[Block 23]):** `[CERT]` 24 (every numbered code-block
citation + table cell across §57.1-§57.3, all re-read fresh this session — none inherited/re-cited from a
prior block's own marker without a fresh open) · `[CERT-hw]` 1 (the independent `strings` run on `nre.dll`,
§57.1) · `[CERT-web]` 0 (the one candidate web citation — Oracle's `java` launcher-option reference — was
checked this session and found NOT to state the `-D`-timing fact explicitly, so it was dropped rather than
force-cited; the timing claim is instead grounded in the CODE'S OWN internal logic — `verifySystemProperties()`/
`addToSystemProperties()`'s `cmdline::`-shadow checks are meaningless unless `-D` properties are already live
before `Nre.boot()` runs — counted under the `[CERT]` tally above, not asserted as an independent `[CERT-web]`
fact) · `[INFER]` 0 load-bearing (the one soft inference — "1.27 seconds apart... is wrong to read literally" —
is a corrective aside about timestamp interpretation, not a conclusion any verdict rests on). Ratio
`[INFER]`/`[CERT]` ≈ 0 — consistent with a `mixed`-declared, evidence-dominant block: all three target gaps
were closed by direct fresh source reading (not deduction), and §57.1's severity BOUND is stated as a
precondition-scoped `[CERT]` finding (the access paths found, and the negative finding that no others were
found this session), not an `[INFER]` guess about exploitability in the abstract — the static-defect /
runtime-exploitability split (METHODOLOGY §3) is resolved here in the defect's favor (CONFIRMED reachable)
while exploitability-at-scale stays explicitly BOUNDED/unconfirmed pending **B57-G3**'s live reproduction.

**Artifacts:** block file at `/home/cristian/niagara5-research/niagara5-block57.md`. No scratch/output
directories created this session (no execution, no fresh decompilation — pure reading of already-organized
sources across BOTH corpora, plus 1 fresh `strings` invocation and 2 live-file reads of `nre.properties`,
both read-only). `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` **NOT** regenerated this run — left to the
orchestrator/next session, same disclosed choice [Block 17]/[Block 23]/[Block 30]/[Block 53] made.

**MCP-doc snapshots:** N/A for load-bearing citations — the one web fetch attempted this session (Oracle's
`java` command reference) did NOT yield a load-bearing citation (see marker tally above) and was not used as
evidence in any claim; no snapshot was taken because nothing from it was cited.

**Secrets discipline (carried forward from [Block 53]'s own stricter requirement):** no key material, no
live `.km`/KeyRing file contents, and no live `security/`-directory secret data were opened this session.
`nre.properties` (both copies read) is a plain JVM-launch-option config file, empty on this install, not a
secrets file. The N4/N5 `EncryptionKeySource`/`BOrientSystemDb` reads are decompiled JAVA SOURCE CODE
(structure, property declarations, alias name STRINGS) already present in each corpus's own `organized/`/
`sources/decompiled/` tree from prior sessions' decompilation — no fresh extraction from either live install
this session, and no key BYTES were read, printed, or reproduced anywhere in this block.
