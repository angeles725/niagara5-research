# Block 81 — Closing the security-residual cluster: `FilePermission`/`RuntimeExecPermission`/`NiagaraBasicPermission`'s grant-matching bodies, `securityBridge.jar`'s unmodularized readability edge (narrowing away from `-Xbootclasspath/a:`), LDAP Kerberos/GSSAPI support REMOVED (not relocated) in N5, and `BServerPort`'s opt-in, inbound-only nftables firewall

> Research closing four named child gaps left open across [Block 65]/[Block 38]/[Block 15], all part of the
> same security-residual cluster: **B65-G3** (read `FilePermission`/`RuntimeExecPermission`/
> `NiagaraBasicPermission`'s own `doIsGrantedTo(Module)` grant-matching bodies — [Block 65] §65.2 traced WHERE
> the call happens, not HOW the match is computed); **B65-G4** (empirically confirm, or find further static
> evidence for, [Block 3] §3.8's `[INFER]` claim that `securityBridge.jar` loads via `-Xbootclasspath/a:`);
> **B38-G3** (locate LDAP Kerberos/GSSAPI support — [Block 38] §38.9 found no such mechanism in
> `BAuthenticationMechanism`'s 4-entry enum and left open whether it lives in a separate config class); and
> **B15-G3** (determine whether N5 offers a network-egress control at a layer outside `NiagaraPermission` — an
> OS-level firewall integration, a platform "allowed hosts" config, or a `niagara.net`-module ACL — [Block 15]
> §15.6 scoped its own CONFIRMED verdict strictly to `com.tridium.nre.security.**` + `httpClient.jar`). All
> four are closed or substantively advanced this session by opening sources each parent block named but did
> not itself read.
>
> Does **not** cover: a live/dynamic confirmation that any of these code paths behaves as read here on a
> running N5 station (no runnable install this session — same blocker as [Block 41]'s **B41-G4**/[Block 54]'s
> **B54-G2**/[Block 61]'s **B61-G1**/[Block 65]'s **B65-G1**); the literal native JVM launch command-line for
> `station.exe`/`niagarad.exe` (§81.2 narrows **B65-G4**'s mechanism structurally but does not observe the
> actual `java`/launcher invocation — that remains the same native-launch-flag limitation class as **B65-G1**/
> **B65-G4**'s own scope note); `PermissionManager.initThirdPartyPermissions()`'s own annotation-scanning
> internals (already whole-file-read by [Block 65]'s header, re-cited not re-opened here); the `nft` binary's
> own ACL semantics or the Linux kernel netfilter subsystem itself (only Niagara's own Java-side command
> construction was read, not `nft`'s man page or kernel behavior); Windows' own native firewall (explicitly
> out of scope per `NullFirewallProcessor`'s own doc comment, read verbatim in §81.4 — not traced further);
> and `com.tridium.migrator.kerberos`'s own XML-diff/conversion correctness (only its `CONVERT_TYPES` set and
> `migrate()` body were read, enough to answer B38-G3, not a full migrator-module audit).
>
> Subject version: **N5 5.0.0.28 (Beta)**, the same install every predecessor block in this corpus reads
> (`etc/brand.properties:workbench.notice`, per [Block 65]'s subject-version convention, not re-verified this
> session). No fresh decompilation — every file cited was already present in `organized/` from prior corpus
> extractions ([Block 1]'s `nre.jar`/`niagarad.jar` extraction; [Block 25]/[Block 44]'s `bin/ext` extraction
> for the `_bin-ext/nre`, `_bin-ext/niagarad`, `_bin-ext/securityBridge` locations; the standalone `ldap`/
> `migrator` module extractions already in-corpus).
>
> Sources: `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/FilePermission.java` (whole
> 245-line file — `doIsGrantedTo`:70-106, `impliedBy`:195-208, `getPermissionsGrantedToAllModules`:210-236,
> `init`:134-154, `attemptExpansion`:238-244 — [Block 65]'s header explicitly scoped its own read of this file
> to "class header + field block only, `:1-60`"; this session reads the remaining 185 lines including the full
> method body); `organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/RuntimeExecPermission.java`
> (whole 132-line file, never opened by any prior block — `doIsGrantedTo`:34-53, `impliedBy`:85-105,
> `checkCommandPath`:70-83, `getRealCommandPath`:107-120, `getFullPath`:122-131);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/NiagaraBasicPermission.java` (whole
> 120-line file, never opened by any prior block — `doIsGrantedTo`:94-104, beyond the gap's named scope but
> opened for completeness since it was already in-corpus and unread);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/NiagaraPermission.java:24-26`
> (`getPermissions(Module,Class)` static wrapper, targeted read — confirms this delegates to
> `PermissionManager.getPermissions`, already whole-file-read by [Block 65]'s header); `organized/_bin-ext/nre/
> vineflower/com/tridium/nre/security/permissions/restricted/PermissionUtil.java` (whole 13-line file —
> `moduleDevPath` field, re-opened from [Block 65]'s citation for a different field than `isTrustedDomain`).
> `organized/_bin-ext/securityBridge/vineflower/module-info.java` (whole 3-line file, re-read from [Block 65]'s
> citation — `module niagara.securityBridge { exports com.tridium.securityBridge; }`);
> `organized/_bin-ext/nre/vineflower/module-info.java` (whole 75-line file, re-read from [Block 65]'s citation
> — searched for, and confirmed ABSENT, any `requires niagara.securityBridge` clause);
> `organized/_bin-ext/niagarad/vineflower/module-info.java` (whole file, same absence check);
> `organized/_bin-ext/securityBridge/recon.json` (whole file — `jar_path` field, confirms `securityBridge.jar`
> lives at the live install's `bin/ext/securityBridge/securityBridge.jar`, the standard `bin/ext` module
> location, not a distinguished path); `organized/_bin-ext/nre/vineflower/com/tridium/nre/bootstrap/
> Bootstrap.java:1-40,130-239` (re-read from [Block 65]'s narrower `:228-238` citation, extended to the full
> import list and the `JVM_BOOT_MODULE_LAYER.findModule(...)` sequence, `:145-227`);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/PermissionBridge.java` (whole
> 73-line file, re-read from [Block 65]'s citation — `import com.tridium.securityBridge.IPermissionBridge`
> line 3, a SECOND independent `niagara.nre`-internal import of a `securityBridge` class with no `requires`
> backing it); corpus-wide `grep -rn "requires.*securityBridge\|niagara\.securityBridge"` across all of
> `organized/` (single-hit search, reported verbatim in §81.2).
>
> `organized/ldap/vineflower/com/tridium/ldap/v3/BAuthenticationMechanism.java` (re-read from [Block 38]'s
> citation, whole file — the 4-entry enum, re-confirmed); `organized/ldap/vineflower/com/tridium/ldap/`
> directory listing (`find`, this session — confirms only 18 total `.java` files across `{v2,v3,dashboard,ui}`
> plus 6 top-level classes, zero Kerberos-named class anywhere under `organized/ldap/`);
> `organized/migrator/vineflower/com/tridium/migrator/kerberos/BKerberosMigrator.java` (whole 71-line file,
> never opened by any prior block in this corpus); `organized/migrator/vineflower/com/tridium/migrator/
> kerberos/BKeytabFileRemover.java` (whole 41-line file, never opened by any prior block);
> `organized/migrator/vineflower/module-info.java` (whole file — confirms `niagara.migrator` `requires
> niagara.ldap` and `exports com.tridium.migrator.kerberos`); corpus-wide
> `grep -rli "kerberos|gssapi|GSSAPIContext|SaslClient|Krb5"` across all `organized/**/*.java` (this session,
> reported verbatim in §81.3).
>
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/{FirewallProcessor,FirewallRule,InputRule,
> NullFirewallProcessor}.java` (all 4 whole files, none opened by any prior block — `com.tridium.nre.firewall`
> and `com.tridium.nre.firewall.nft` are both `exports`-listed in `niagara.nre`'s `module-info.java`, already
> cited above, but never previously opened); `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/
> NftablesFirewallProcessor.java` (whole 267-line file); `organized/baja/vineflower/niagara/firewall/
> BServerPort.java:1-11,195-363` (targeted read — `validateSet`/`isAlphanumeric`:206-231, `getRuleHint`:264-275,
> `updateFirewallRules`:277-321, `fw()`/`isUseFirewall()`/`FirewallHolder` static holder:333-362 — this class
> is the SAME `niagara.firewall.BServerPort` [Block 40]/[Block 61] already cited for the unrelated
> `ruleHintOverride`/`setRequiresValidation` validation-bypass question; this session opens the firewall-wiring
> body of the same class, not previously read by either block); `organized/baja/vineflower/com/tridium/
> firewall/ConcurrentFirewallProcessor.java:1-60` (targeted read — the decorator `BServerPort.fw()` actually
> holds when `niagara.firewall.enabled=false` or `frontend != nft`).
>
> Method: direct reading of pre-existing in-corpus Vineflower decompiles (nothing re-decompiled this session);
> two corpus-wide `grep -rn`/`grep -rli` runs to establish exhaustive negative-existence claims (the
> `securityBridge` requires-clause search and the Kerberos/GSSAPI class-name search), each reported verbatim,
> not sampled. Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) ·
> `[CERT-a]` secondary source · `[INFER]` deduction. `file:line` citations point into `organized/<module>/
> vineflower/...` inside **this** corpus (`/home/cristian/niagara5-research/`) — per METHODOLOGY §11's
> decompiled-tree rule, `verify-block.sh` classifies paths under `organized/` as IN-TARGET (this corpus's root
> IS `/home/cristian/niagara5-research/`, unlike a nested-corpus layout), so these are expected to resolve
> `ok`, not `extern` — see §81.5.
>
> Security-residual cluster: permission grant-matching (NRE core), module-loading mechanics (NRE
> bootstrap/JPMS), LDAP authentication (ldap module), and network-egress control (NRE firewall +
> `niagara.firewall.BServerPort`, baja). Connects [Block 65] (closes **B65-G3**; advances **B65-G4**),
> [Block 38] (closes **B38-G3**), [Block 15] (closes **B15-G3**), [Block 3] (§81.2 narrows/partially refutes
> §3.8's `-Xbootclasspath/a:` `[INFER]`), [Block 40]/[Block 61] (§81.4's `BServerPort`/`getRuleHint()` read is
> the first direct read of what `TunnelService.serverPort`'s `ruleHintOverride` literal is actually FOR — new
> corroborating detail, not a correction, for either block's own verdict).
>
> **Type:** `mixed` — §81.2 upgrades [Block 3] §3.8's `[INFER]`-level `-Xbootclasspath/a:` hypothesis by
> opening sources §3.8 never read (`securityBridge`'s own `module-info.java`, `niagara.nre`'s `module-info.java`,
> a corpus-wide requires-clause search) and narrows/partially refutes it — the `[INFER]`-across-a-prior-block
> correction trigger per METHODOLOGY §4/§11. §81.1, §81.3, and §81.4 are straightforward evidence-closures of
> their respective gaps, each opening a source its parent block explicitly named as unopened.

---

## 81.1 — B65-G3 CLOSED: `FilePermission`/`RuntimeExecPermission`/`NiagaraBasicPermission`'s `doIsGrantedTo(Module)` bodies — path-prefix/real-path matching against a per-module grant set, plus two undocumented blanket bypasses (a hardcoded "granted to all modules" file list, and a module-dev-path read exception) `[CERT]`

**`FilePermission.doIsGrantedTo(Module)` — gated, then matched, then bypassed.** The whole check is
short-circuited to a silent PASS unless `(Bootstrap.isStation() || Bootstrap.isTest()) &&
(!Bootstrap.isTest() || !PermissionManager.shouldRunTestsAsWorkbench())` — i.e., outside a running station or
a genuine (non-workbench-mode) test run, `doIsGrantedTo` returns without ever throwing
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/FilePermission.java:72`.
Inside that gate, it collects the module's own granted `FilePermission` set via
`NiagaraPermission.getPermissions(module, FilePermission.class)` — a thin static wrapper delegating to
`PermissionManager.getPermissions(module, cls)` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/
security/permissions/NiagaraPermission.java:24-26` (answering the exact "WHERE→HOW" gap [Block 65] §65.2
left open) — UNIONS it with a second, hardcoded set (`getPermissionsGrantedToAllModules()`, below), then
iterates: a requested permission is granted if some granted permission `impliedBy()`-matches it AND
`(grantedPermission.actions & this.actions) == this.actions` (the requested action bits must be a SUBSET of
the granted ones) `[CERT]` `FilePermission.java:70-106` (whole method).

`impliedBy(FilePermission grantedPermission)` (`FilePermission.java:195-208`, whole method) has three cases,
checked in order: (1) `grantedPermission.allFiles` (constructed from the literal path `"*"`) implies
EVERYTHING, unconditionally; (2) `grantedPermission.recursiveDirectory` (path ends in the OS separator + `-`,
e.g. `.../shared/-`) implies any path `this.path.startsWith(grantedPath)` — a real recursive-subtree match;
(3) otherwise, `grantedPermission.directory` (path ends in separator + `*`, a SINGLE-level directory grant)
implies an exact match on the path itself OR its immediate parent, and a non-directory grant implies only an
exact path match. Paths are resolved via `Path.of(...).toAbsolutePath()` at construction (`init()`,
`FilePermission.java:134-154`), cached in a static `ConcurrentHashMap<String,Path>` (`realPathCache`,
`:40,151`) — this is STRING-absolute-path comparison, not a symlink-resolved real-path comparison (contrast
`RuntimeExecPermission`, below, which DOES resolve symlinks via `toRealPath()`/`Files.isSameFile()`) — a
policy difference between the two permission classes worth naming: a `FilePermission` grant can be defeated
or over-matched by a symlink pointing outside the granted path, `RuntimeExecPermission` cannot `[CERT]` (both
method bodies read directly, this session).

**Two undocumented bypasses, both new findings not carried by any prior block.** (1)
`getPermissionsGrantedToAllModules()` (`FilePermission.java:210-236`, whole method) is a HARDCODED, lazily-
built `Set<FilePermission>` unioned into EVERY module's grant check regardless of that module's own
`@GrantFilePermission` annotations — 11 fixed entries: `${niagara.user.home}/shared/-` (all, recursive),
`.../logging/-` (all), the JVM temp dir (all), `.../modules/-` (read), `.../lexicon/-` (read), `.../etc/-`
(read), `.../jar-cache/-` (read), the bundled JRE's `bin/-` and `conf/-` (read), `bin/ext/-` (read), the JVM
`cacerts` file (read), and `${protected.station.home}/shared/-` (all, expanded) — plus a 12th,
test-only entry (`TEST_STATION_HOME`, read+write) added only `if (Bootstrap.isTest())` `[CERT]`
`FilePermission.java:210-236`. Every module, with zero explicit grant, can read the module/lexicon/etc/
jar-cache/JRE/cacerts trees and read+write its own shared/logging/temp directories. (2) A MODULE-DEV-PATH
read exception: if a permission would otherwise be DENIED, the throw is still suppressed when
`PermissionUtil.moduleDevPath != null && this.path.startsWith(PermissionUtil.moduleDevPath) &&
this.actions == 1` (`actions==1` is the `READ` bitmask alone, from `getMask()`, `FilePermission.java:169-193`)
`[CERT]` `FilePermission.java:93-104`; `PermissionUtil.moduleDevPath` is a public static `Path` field,
`null` by default, set (by code not read this session) presumably for a module-development workflow `[CERT]`
`organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/restricted/PermissionUtil.java:8`. Net:
when a dev-path is configured, READ access anywhere under it is granted to every module unconditionally,
independent of that module's own declared `FilePermission` grants.

**`RuntimeExecPermission.doIsGrantedTo(Module)` — narrower, no all-modules bypass, real-path matching
throughout.** No gating condition (unlike `FilePermission`, this check always runs) and no
`getPermissionsGrantedToAllModules()`-style hardcoded bypass set — only the module's own
`getPermissions(module, RuntimeExecPermission.class)` grants are consulted `[CERT]`
`organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/RuntimeExecPermission.java:34-53` (whole
method). It first resolves the REQUESTED command to an absolute, `PATH`-env-var-searched real path
(`checkCommandPath`→`getRealCommandPath`→`getFullPath`, `:70-131`, scanning `System.getenv("PATH")` split
entries for an executable file matching the bare command name) and throws immediately if that resolution
fails `[CERT]` `RuntimeExecPermission.java:70-83,107-131`. `impliedBy(RuntimeExecPermission grantedPermission)`
(`:85-105`, whole method) has the same three-case shape as `FilePermission` (`"*"` wildcard; trailing `-` for
a recursive directory prefix; trailing `*` for a single-level directory) but resolves BOTH sides via
`Path.toRealPath()`/`Files.isSameFile()` — symlink-resolved comparison throughout, not raw path-string
equality `[CERT]` `RuntimeExecPermission.java:85-105`. No dev-path or all-modules exception exists for this
class — every denial path in the method ends in a thrown `PermissionException` (`:52`), unconditionally.

**`NiagaraBasicPermission.doIsGrantedTo(Module)` — the simplest of the three, exact-name or wildcard only.**
No path semantics at all: a named capability string (`"KEY_MATERIAL"`, `"MANAGE_SECURITY_PROVIDERS"`,
`"SKIP_PASSWORD_STRENGTH_CHECK"`, etc. — 40 named constants read off the class's own `public static final`
field block, `NiagaraBasicPermission.java:8-87`) is granted only if the module's own granted set contains
EITHER the exact same name OR the literal wildcard string `"*"` `[CERT]` `organized/_bin-ext/nre/vineflower/
com/tridium/nre/security/permissions/NiagaraBasicPermission.java:94-104` (whole method) — no
`getPermissionsGrantedToAllModules()`-equivalent, no dev-path exception, no path/real-path resolution of any
kind. Opened beyond B65-G3's named scope (only `FilePermission`/`RuntimeExecPermission` were named) because
the file was already present in-corpus and unread; included here for completeness rather than left as a
residual gap.

**Net verdict, closing B65-G3.** All three `doIsGrantedTo` bodies are now read in full. The per-module
grant-matching algorithm [Block 65] §65.2 could only identify by WHERE it is called (`PermissionManager.
checkPermission`) is: path-prefix/real-path containment for the two filesystem-shaped permissions (differing
in symlink-resolution policy between the two), exact-name-or-wildcard for the capability-shaped one, ANDed
against an action-bitmask subset test for `FilePermission`, and layered under two undocumented bypass paths
(`FilePermission`'s hardcoded all-modules grant list and module-dev-path read exception) that neither
[Block 65] nor any prior block had surfaced.

## 81.2 — B65-G4 ADVANCED, not closed: `securityBridge.jar` is a REAL, standalone JPMS module at the ordinary `bin/ext/` location, imported directly by TWO classes inside `niagara.nre` with NO `requires niagara.securityBridge` anywhere in the corpus — structurally narrowing away from, not confirming, [Block 3] §3.8's `-Xbootclasspath/a:` hypothesis `[CERT]`+`[INFER]`

[Block 3] §3.8 named `securityBridge.jar`'s loading mechanism as `-Xbootclasspath/a:`-based, explicitly
flagged `[INFER]`; [Block 65] §65.5 reopened this as **B65-G4**, naming a live `jcmd`/launch-flag probe as the
closing method. No runnable station exists this session (same blocker named in this block's own header), so
this session instead re-examines the STATIC evidence already in-corpus and finds it points a different
direction than the original hypothesis.

**`securityBridge.jar` is packaged as an ordinary, standalone JPMS module at the standard `bin/ext/` location
— not a bootclasspath-only shim.** `recon.json`'s own extraction metadata records `jar_path: "/mnt/c/Program
Files/Niagara/5.0.0.28/bin/ext/securityBridge/securityBridge.jar"` `[CERT]`
`organized/_bin-ext/securityBridge/recon.json` — the identical `bin/ext/<module>/<module>.jar` layout
[Block 25]/[Block 44] established for `nre.jar` and `niagarad.jar`, not a distinguished or hidden path. The
jar ships a real `module-info.class`/`.java`: `module niagara.securityBridge { exports
com.tridium.securityBridge; }` `[CERT]` `organized/_bin-ext/securityBridge/vineflower/module-info.java`
(whole 3-line file) — a properly named, exported JPMS module, not a bare classpath jar with no module
descriptor at all (a `-Xbootclasspath/a:`-only jar would typically ship WITHOUT a meaningful module
descriptor, since bootclasspath-appended classes join the bootstrap classloader's UNNAMED module and a
`module-info.class` there is not used to mint a named module in `ModuleLayer.boot()` — `[INFER]`, general JPMS
behavior, not itself sourced from this corpus).

**Two independent classes inside `niagara.nre` import `securityBridge` classes directly, yet NEITHER
`niagara.nre`'s nor `niagara.niagarad`'s `module-info.java` declares `requires niagara.securityBridge` —
and no file anywhere in the corpus does.** `Bootstrap.java` (`package com.tridium.nre.bootstrap`, inside
`niagara.nre`) has `import com.tridium.securityBridge.SecurityBridge;` (`:18`) and writes
`SecurityBridge.permissionBridge = new PermissionBridge();` (`:233`, re-cited from [Block 65]'s citation)
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/bootstrap/Bootstrap.java:18,232-234`.
`PermissionBridge.java` (`package com.tridium.nre.security.permissions`, also inside `niagara.nre`)
independently has `import com.tridium.securityBridge.IPermissionBridge;` (`:3`) and `implements
IPermissionBridge` (`:15`) `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/
PermissionBridge.java:3,15`. A direct compile-time `import`+field-write / `import`+`implements` reference to
another module's exported type REQUIRES a `requires` (or `requires transitive`, inherited) edge under
ordinary JPMS strong encapsulation. `niagara.nre`'s own `module-info.java` (whole 75-line file, re-read this
session) lists 25 `requires`/`requires transitive`/`requires static` clauses and NONE names
`niagara.securityBridge` `[CERT]` `organized/_bin-ext/nre/vineflower/module-info.java:1-24` (full requires
block). `niagara.niagarad`'s `module-info.java` (`requires transitive niagara.nre` plus 16 others) likewise
names no `securityBridge` requires `[CERT]` `organized/_bin-ext/niagarad/vineflower/module-info.java:1-18`. A
corpus-wide `grep -rn "requires.*securityBridge\|niagara\.securityBridge"` across ALL of `organized/` returns
exactly ONE hit — `securityBridge`'s own `module niagara.securityBridge {` declaration line — zero `requires`
clauses anywhere `[CERT]` (verbatim grep, this session, single-hit, exhaustive not sampled).

**Reading this correctly.** This is a genuine JPMS anomaly this session did not expect going in: TWO
independent classes in `niagara.nre` compile-time-reference `securityBridge` types with no static
readability edge visible anywhere in the decompiled module graph. Three non-exclusive candidate mechanisms
would explain it, none confirmed this session (no launch-flag/live evidence, same limitation as
[Block 65]'s **B65-G1**): (1) a `--add-reads niagara.nre=niagara.securityBridge` (or `=ALL-UNNAMED`) flag
passed on the actual `java`/native-launcher command line — the standard JPMS-supported way to grant a
readability edge WITHOUT a static `requires` clause, and the only one of the three that would make a proper
named-module descriptor (which `securityBridge.jar` demonstrably has) meaningful; (2) a runtime
`Module.addReads()` call somewhere in the corpus not yet located (`Bootstrap.java` already calls
`Module.addExports`/`addOpens` on OTHER modules at `:164-224`, re-cited from [Block 65], establishing the
CAPABILITY exists in this codebase, though no `addReads` call naming `securityBridge` was found this
session); (3) `securityBridge.jar`'s classes are placed on a classpath (`-Xbootclasspath/a:` or plain `-cp`)
joining the UNNAMED module, which the classes' own compiled bytecode could then be read from by ANY named
module without a `requires` clause IF that named module was launched with `--add-reads <module>=ALL-UNNAMED`
— structurally the SAME missing-command-line-flag gap as (1), just naming which unnamed-module surface is
being read. **Reading (3) alone — [Block 3]'s original `-Xbootclasspath/a:` hypothesis, unqualified — is
WEAKENED by this session's findings**, because it does not by itself explain why `securityBridge.jar` bothers
shipping a real, named `module-info.java` at all: a classpath-only artifact gains nothing from a module
descriptor the JVM would not use to create a named module in that configuration `[INFER]`. **Net: B65-G4 is
ADVANCED, not closed** — the loading mechanism is narrowed from "bootclasspath shim, `[INFER]`" to "a
real named JPMS module at the ordinary `bin/ext/` location, reachable from `niagara.nre` via SOME
launch-time or runtime readability grant this session could not locate in static source, most plausibly an
`--add-reads`-class command-line flag rather than a pure `-Xbootclasspath/a:` classpath append" — refined as
**B81-G1**.

## 81.3 — B38-G3 CLOSED: N5's `ldap` module has NO Kerberos/GSSAPI bind mechanism anywhere — and the `migrator` module's own `BKerberosMigrator`/`BKeytabFileRemover` classes actively STRIP Kerberos LDAP config and keytab files during an upgrade to N5, evidence Kerberos/GSSAPI LDAP bind support was REMOVED, not relocated `[CERT]`+`[INFER]`

[Block 38] §38.9 read `BAuthenticationMechanism`'s 4-entry enum (`none`/`simple`/`cramMd5`/`digestMd5`,
`BAuthenticationMechanism.java:23-29`, re-confirmed this session at the same lines) and, noting
`niagara-research`'s N4 corpus (B30) found Kerberos support in its ~40-class LDAP `v3/` package, left open
whether N5's Kerberos support simply moved to a separate config class not read that session — **B38-G3**.

**No Kerberos/GSSAPI class exists anywhere under `organized/ldap/`.** A directory listing of the whole
`ldap` module (`organized/ldap/vineflower/com/tridium/ldap/`) shows exactly 6 top-level classes plus 3
subpackages (`v2/` — 1 class, `v3/` — 3 classes: `BAuthenticationMechanism`, `BLdapV3Config`,
`BindNameFormatter`, per [Block 38]'s own citation list — `dashboard/`, `ui/`) `[CERT]` `find` over
`organized/ldap/vineflower/com/tridium/ldap/`, this session. A corpus-wide case-insensitive
`grep -rli "kerberos|gssapi|GSSAPIContext|SaslClient|Krb5"` across every `.java` file in `organized/` (not
scoped to `ldap/`) returns exactly 8 hits, and NONE is inside the `ldap` module: `fox/session/Tuner.java`
(a Fox-protocol tuning parameter unrelated to auth), `docSource/backup/BBackupService.java`,
`saml/BAuthnContextClassRefType.java` + `saml/utils/SAMLConstants.java` (SAML's own, unrelated
`urn:...kerberos` `AuthnContextClassRef` constant — a SAML federation concept, not an LDAP bind mechanism),
`nss/dashboard/BSecurityPropertyDashboardItemProviderAgent.java`, and TWO hits under
`organized/migrator/vineflower/com/tridium/migrator/kerberos/` `[CERT]` (verbatim grep output, this session,
exhaustive not sampled).

**Those two migrator classes are the answer.** `BKerberosMigrator` (`package com.tridium.migrator.kerberos`,
whole 71-line file, never opened by any prior block) declares `CONVERT_TYPES = List.of("baja:User",
"ldap:KerberosAuthenticationScheme", "ldap:KerberosConfig", "ldap:KeytabFile")` `[CERT]`
`organized/migrator/vineflower/com/tridium/migrator/kerberos/BKerberosMigrator.java:24` — i.e. an OLDER
Niagara version (the migrator's own job is converting `.bog`/config XML from a PRIOR version into the
current one) had real `ldap:KerberosAuthenticationScheme`/`ldap:KerberosConfig`/`ldap:KeytabFile` types. Its
`convertXElem()` method, for the `"ldap:KerberosAuthenticationScheme"` case, does NOT convert the element —
it records the scheme's name, calls `this.cleanUpUsers()` (which walks previously-seen `baja:User` elements
and DELETES any user whose `authenticationSchemeName` matches a Kerberos scheme, logging
`"kerberos.userDelete"`), logs `"kerberos.propDelete"`, and returns `null` — `null` from `convertXElem` is
this migrator framework's own drop-the-element convention (the SAME method returns the element unchanged,
`return x;`, for every OTHER input) `[CERT]` `BKerberosMigrator.java:35-49` (whole method). Its sibling
`BKeytabFileRemover` (`package com.tridium.migrator.kerberos`, whole 41-line file, `extends
BFileMigrator`, `getMigrateDirs() = {"ldap"}`, `getMigrateTypes() = {"keytab"}`) has a `migrate()` body that
iterates the source station's keytab files and, for each, ONLY logs `"keytabFileRemover.noCopy"` — `return
Optional.empty()` — i.e. it explicitly does NOT copy keytab files forward to the migrated N5 station `[CERT]`
`organized/migrator/vineflower/com/tridium/migrator/kerberos/BKeytabFileRemover.java:23-40` (whole method).
`niagara.migrator`'s own `module-info.java` confirms `requires niagara.ldap` and `exports
com.tridium.migrator.kerberos` `[CERT]` `organized/migrator/vineflower/module-info.java:20,42`.

**Net reading.** A migrated-FROM Niagara version had a real `ldap:KerberosAuthenticationScheme`/
`ldap:KerberosConfig`/`ldap:KeytabFile` type set — consistent with [Block 38]'s own citation of
`niagara-research` B30's ~40-class N4 LDAP `v3/` package including Kerberos. N5's own `ldap` module
(re-confirmed this session, 18 total files across all subpackages) implements NONE of them, and the
migration path from a Kerberos-configured station does not merely drop the setting silently — it actively
DELETES the user accounts that depended on it and refuses to carry forward their keytab files, with
purpose-built logging keys (`"kerberos.propDelete"`, `"kerberos.userDelete"`,
`"keytabFileRemover.noCopy"`) that exist for no other reason `[CERT]` for all of the above; the conclusion
that Kerberos/GSSAPI LDAP bind support was DELIBERATELY REMOVED in N5 (not relocated to an unread class, the
possibility B38-G3 was framed around) is `[INFER]` — no design-rationale document or release note was read
this session, but a migrator module that actively strips a feature's config and denies its credential files
is far stronger evidence of removal than mere absence would be on its own. This closes **B38-G3**: the
"separate config class not read this session" possibility [Block 38] left open does not exist — GSSAPI/
Kerberos LDAP bind is corpus-absent, and the migrator module is corpus-present evidence of why.

## 81.4 — B15-G3 CLOSED: N5 DOES have an OS-level platform-firewall integration (Linux `nftables`, via `niagara.firewall.BServerPort`) — but it is opt-in (disabled by default), INBOUND-only (`INPUT_RULE`/accept, opening listening ports), and provides ZERO outbound/egress control, reinforcing rather than contradicting [Block 15]'s own audit-only verdict `[CERT]`

[Block 15] §15.6 delivered a CONFIRMED verdict — outbound network access is audit-only in N5, no
`NiagaraPermission` check gates it — but scoped its search to `com.tridium.nre.security.**` + `httpClient.jar`
and explicitly left open (**B15-G3**) whether a DIFFERENT layer entirely (OS firewall, platform allowed-hosts
config, a `niagara.net` ACL) exists outside that scope.

**A real, first-party platform-firewall subsystem exists: `com.tridium.nre.firewall`/`com.tridium.nre.
firewall.nft`, both `exports`-listed in `niagara.nre`'s own `module-info.java` (already cited in this block's
header) — never previously opened by any prior block.** `FirewallProcessor` (abstract, whole 66-line file) is
the pluggable-backend contract: `addRule`/`removeRule`/`getRulesList`/`validateRule`(abstract)/
`processRules`(abstract)/`processRule`(abstract) `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/
nre/firewall/FirewallProcessor.java`. `FirewallRule` (abstract, whole 50-line file) models a rule as
`{ruleType ∈ {REDIRECT_RULE, INPUT_RULE, NOOP_RULE}, publicServerPort, localServerPort, ipProtocol, adapter,
bindToLoopback}` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/FirewallRule.java`.
`NftablesFirewallProcessor` (whole 267-line file, the Linux backend) constructs and runs literal `nft`
command lines via `ProcessBuilder` under `SecurityUtil.doPrivileged(...)`
(`doExecuteFirewallAddRuleCommand`/`doFirewallCommand`, `:130-176`) — e.g.
`"<frontEndPath> add rule inet <table> <chain> [iif lo | iifname <adapter>] {tcp|udp|meta l4proto {tcp,udp}
th} dport <port> counter accept [comment \"<ruleHint>\"]"` (`processRule`, `:84-128`) — and its
`validateRule()` ONLY accepts `INPUT_RULE`; a `REDIRECT_RULE` is explicitly REJECTED with `"Rule type ...
cannot be processed by NftablesFirewallProcessor"` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/
nre/firewall/nft/NftablesFirewallProcessor.java:48-65`. Configuration is via 5 system properties:
`niagara.firewall.frontend`, `.frontend.path`, `.backend`, `.input.table` (default `"filter"`),
`.input.chain` (default `"input"`) `[CERT]` `NftablesFirewallProcessor.java:23-41`. `InputRule` (whole
78-line file) is the ONLY rule type actually EXERCISED by this backend; its constructor sets
`publicServerPort == localServerPort` (no port-translation) and carries a `ruleHint` used verbatim as the
`nft` rule's `comment` (validated by `isRuleHintValid()` to be alphanumeric + `.`/`$` only,
`NftablesFirewallProcessor.java:258-266`) `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/
firewall/InputRule.java`. `NullFirewallProcessor` (whole 41-line file) is the no-op fallback, and its own doc
comment states its purpose verbatim: `"A no-op firewall that is used on platforms that have their own managed
firewall. (Like Windows)"` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/
NullFirewallProcessor.java:1-7` — i.e. this subsystem is Linux-specific by design; Windows relies entirely on
the OS's own firewall, untraced by this corpus (out of scope, declared in this block's header).

**Wired in by `niagara.firewall.BServerPort` — the identical class [Block 40]/[Block 61] already cited for
the unrelated `ruleHintOverride`/`setRequiresValidation` question — opened here for its firewall-wiring body
for the first time.** A private static holder class picks the backend at class-init: `NftablesFirewallProcessor`
if AND ONLY IF `-Dniagara.firewall.enabled=true` AND `-Dniagara.firewall.frontend=nft`; a
`ConcurrentFirewallProcessor`-wrapped `NullFirewallProcessor` in EVERY other case, including both properties
UNSET (the default) `[CERT]` `organized/baja/vineflower/niagara/firewall/BServerPort.java:333-362` (whole
`FirewallHolder` static holder + `fw()`/`isUseFirewall()` accessors). `updateFirewallRules()`
(`:277-321`, whole method) additionally gates WHICH rule TYPE is constructed on that same
`niagara.firewall.enabled` flag: `isUseFirewall()==true` builds a real `InputRule`, `false` builds a `NoOpRule`
instead — so the system is doubly opt-in (both the property AND the per-port rule construction default to
inert) `[CERT]` `BServerPort.java:277-289`. `getRuleHint()` (`:264-275`) is the DEFAULT rule-comment source
this session had not previously traced: `getRuleHintOverride()` if non-empty, else `parent.getName() + "." +
this.getName()` — this is the exact auto-derivation [Block 40]/[Block 61]'s `BTunnelService.java:142` literal
`"TunnelService.serverPort"` OVERRIDES (a manually-set string matching what the default formula would ALSO
produce for a `serverPort` slot parented under a `TunnelService`, per those blocks' own citations) — new
corroborating detail on what that literal is FOR, not a correction to either block's own verdict `[CERT]`
`BServerPort.java:264-275`. `validateSet()`'s own `isAlphanumeric()` gate on `ruleHintOverride`
(`:206-231`, re-opened from [Block 40]/[Block 61]'s `setRequiresValidation` trace, permits letters+digits
ONLY) is STRICTER than `NftablesFirewallProcessor.isRuleHintValid()` (permits `.`/`$` too) — two independently
maintained validators for the same string, at two different layers of the same feature, a minor policy note
`[CERT]` cross-read this session.

**Net verdict, closing B15-G3.** N5 DOES have an OS-level network-control layer outside `NiagaraPermission`
— a real, pluggable, Linux-`nftables`-backed firewall subsystem, disabled by default and requiring TWO
explicit system properties to activate. But every rule type this backend actually implements
(`validateRule` rejects anything but `INPUT_RULE`) is an ACCEPT rule on the INBOUND `input` chain, for ports
Niagara's OWN `BServerPort`-backed services bind to listen on — this is dynamic INBOUND port-opening
(consistent with a service needing its listening port reachable through an otherwise-default-deny Linux
firewall), never an OUTBOUND/egress restriction. No `REDIRECT_RULE` implementation, no outbound-destination
ACL, and no evidence anywhere in `com.tridium.nre.firewall.*` of an egress-control code path. **This
REINFORCES, rather than contradicts, [Block 15] §15.6's audit-only verdict**: the one platform-firewall layer
this corpus's `nre` module ships governs a completely orthogonal direction of traffic (inbound service
exposure, not outbound module-initiated connections), so [Block 15]'s "no gate on outbound access" finding
stands even against this newly-opened subsystem. B15-G4 (the broader `niagara.security.dashboard` module
census) remains separately open and is NOT addressed by this session.

## 81.5 — Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block81.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block81.md
```

**[verbatim script output pasted below, exactly as run this session]**

```
== verify-block: niagara5-block81.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0  (adj 0)
   [CERT-live] 0
   [CERT] 68  (adj 61)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 0  (adj 0)
   [INFER] 9  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/61 = 0.10
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/bootstrap/Bootstrap.java:18,232-234
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/FirewallProcessor.java
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/FirewallRule.java
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/InputRule.java
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/NullFirewallProcessor.java:1-7
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java:23-41
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java:48-65
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/FilePermission.java:70-106
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/NiagaraBasicPermission.java:94-104
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/NiagaraPermission.java:24-26
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/PermissionBridge.java:3,15
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/restricted/PermissionUtil.java:8
   ok      organized/_bin-ext/niagarad/vineflower/module-info.java:1-18
   ok      organized/_bin-ext/nre/vineflower/module-info.java:1-24
   ok      organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/RuntimeExecPermission.java:34-53
   ok      organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/RuntimeExecPermission.java:70-131
   ok      organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/RuntimeExecPermission.java:85-105
   ok      organized/_bin-ext/securityBridge/vineflower/module-info.java
   ok      organized/baja/vineflower/niagara/firewall/BServerPort.java:206-231
   ok      organized/baja/vineflower/niagara/firewall/BServerPort.java:264-275
   ok      organized/baja/vineflower/niagara/firewall/BServerPort.java:277-289
   ok      organized/baja/vineflower/niagara/firewall/BServerPort.java:333-362
   ok      organized/migrator/vineflower/com/tridium/migrator/kerberos/BKerberosMigrator.java:24
   ok      organized/migrator/vineflower/com/tridium/migrator/kerberos/BKerberosMigrator.java:35-49
   ok      organized/migrator/vineflower/com/tridium/migrator/kerberos/BKeytabFileRemover.java:23-40
   ok      organized/migrator/vineflower/module-info.java:20,42
   resolved 25 of 25
== exit 0 ==
```

**Reading the resolution.** All 25 script-recognized `[CERT]` citations resolve `ok` — because this corpus's
root IS `/home/cristian/niagara5-research/` (a flat-layout corpus per METHODOLOGY §3b, not nested under a
`corpus/` subdirectory), `organized/...`-prefixed paths are IN-TARGET, not `extern` (contrast [Block 61]'s
self-verify, whose 8 `extern` items were BARE `file:line` short-forms without the `organized/...` prefix —
every load-bearing citation in THIS block uses the full path form throughout, avoiding that split
entirely). `resolved 25 of 25` is the complete set the script recognizes as `file:line`-shaped; several
additional `[CERT]` claims in the block (the `recon.json` field read, the two `find`/`grep` corpus-wide
searches, the `module niagara.securityBridge {...}` one-line declaration) are not `file:line`-shaped and
fall outside the script's citation list by design, addressed by inline token-verify below.

**Reading the raw vs. adjusted split.** `[CERT]` 68 raw / 61 adjusted — the 7-count difference is this
Self-verify section's own prose quoting marker names while describing the tally (a routine, expected
self-referential inflation, same effect [Block 61]'s self-verify section flagged for its own `[CERT-hw]`
count). `[INFER]` 9 raw / 6 adjusted, for the same reason (this section and §81.2's own discussion of what
`[INFER]` marks). Real evidence tally: **61 `[CERT]`** against **6 real `[INFER]`**, ratio ≈ 0.10 — well
below the ~0.5 exhaustion threshold, consistent with a session that closed 3 of 4 gaps outright by opening
sources each parent block had explicitly left unread, not one running low on investigable material. The 6
real `[INFER]`s are concentrated in §81.2 (candidate mechanisms (1)/(2)/(3) for `securityBridge`'s readability
edge, and the "weakened" reading of [Block 3]'s original hypothesis) and §81.3's single "deliberately removed,
not merely relocated" design-intent reading — both honestly bounded, neither load-bearing for the THREE gaps
this block closes outright (B65-G3, B38-G3, B15-G3), which rest entirely on `[CERT]` claims.

**Inline token-verify.** Every `file:line` citation above points at a file this session `Read` in full or via
a targeted range this session, cross-checked against the file's own printed line numbers (via the `Read`
tool's `cat -n`-style output) rather than hand-counted. Spot-check tokens independently confirmed present
this session (whitespace-normalized): `doIsGrantedTo`/`impliedBy`/`getPermissionsGrantedToAllModules`/
`moduleDevPath` (`FilePermission.java`); `doIsGrantedTo`/`impliedBy`/`checkCommandPath`/`toRealPath`
(`RuntimeExecPermission.java`); `doIsGrantedTo`/`"*".equals(grantedPermissionName)`
(`NiagaraBasicPermission.java`); `module niagara.securityBridge` (`securityBridge/module-info.java`) cross-
checked against a corpus-wide `grep -rn "requires.*securityBridge"` returning exactly that one line and no
`requires` clause anywhere else — a genuine, actively-executed absence check, not an unread assumption;
`import com.tridium.securityBridge.SecurityBridge`/`import com.tridium.securityBridge.IPermissionBridge`
(`Bootstrap.java`/`PermissionBridge.java`) confirmed present via direct `Read`, independently in two separate
files; `CONVERT_TYPES`/`"kerberos.userDelete"`/`"kerberos.propDelete"` (`BKerberosMigrator.java`),
`"keytabFileRemover.noCopy"` (`BKeytabFileRemover.java`) confirmed via direct `Read`; a corpus-wide
`grep -rli "kerberos|gssapi|..."` confirmed exactly 8 hits, 2 of them the migrator classes, ZERO under
`organized/ldap/` — the negative-existence claim's symmetric-opening obligation (METHODOLOGY §3) is satisfied
by having actually run this grep and read its full 8-line output, not merely asserted; `validateRule`/
`processRule`/`"comment \""` (`NftablesFirewallProcessor.java`), `FirewallHolder`/`useFirewall`/
`niagara.firewall.enabled`/`niagara.firewall.frontend` (`BServerPort.java`) confirmed via direct `Read`.
Token-verify: **≈24 distinct load-bearing tokens** confirmed present (or confirmed ABSENT, for the
`requires niagara.securityBridge` and Kerberos-in-`ldap` negative-existence claims, per METHODOLOGY §3's
symmetric-opening-obligation rule — both are ABOUT named artifacts/directories this session actually opened
and searched end-to-end, not merely not-found) in their cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block81.md`. Per the caller's
explicit instruction to touch no other file, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and
backlog re-classification are deliberately NOT performed this session — left to the orchestrator, matching
[Block 40]'s/[Block 61]'s own convention for the same instruction.

## 81.6 — Child gaps opened

- **B81-G1** (refines/narrows **B65-G4**) — Confirm the EXACT mechanism by which `niagara.nre` reads
  `niagara.securityBridge` with no `requires` clause anywhere in the corpus: capture the live JVM's actual
  launch command line (`jcmd <pid> VM.command_line` or `ManagementFactory.getRuntimeMXBean().
  getInputArguments()` on a running `station`/`niagarad` process) and check specifically for an
  `--add-reads niagara.nre=niagara.securityBridge` (or `=ALL-UNNAMED`) flag, OR grep the corpus for a runtime
  `Module.addReads(...)` call naming `securityBridge` not found this session (§81.2's three candidate
  mechanisms were not adjudicated between). Same live-station blocker as **B54-G1**/**B54-G2**/**B61-G1**/
  **B65-G1** — a sixth gap sharing that one blocker, all closeable together in a single live-station session.
- **B81-G2** — `PermissionUtil.moduleDevPath`'s OWN setter/configuration site was not located this session
  (only the field declaration, `PermissionUtil.java:8`, was read) — confirm what sets this path (a system
  property, a dev-mode CLI flag, a `nre.properties` entry) and whether it is reachable in a normal production
  station or only in an explicit module-development build/run configuration, to bound the blast radius of
  §81.1's module-dev-path read bypass.
- **B81-G3** — This session's `BServerPort`/`NftablesFirewallProcessor` read is entirely static; confirm
  live (same blocker class as above) that a Linux N5 install with `-Dniagara.firewall.enabled=true
  -Dniagara.firewall.frontend=nft` actually set produces working `nft` rules end-to-end, and separately
  confirm via a fresh install/packaging read whether these two system properties are ever set BY DEFAULT on
  a genuine Linux deployment (this session found only the Java-side default-OFF code path, not any
  platform-specific launch script or installer default that might override it).

## 81.x — Connections

- **[Block 65]** — closes **B65-G3** (§81.1: all three `doIsGrantedTo` bodies read whole); advances but does
  not close **B65-G4** (§81.2: narrows/partially refutes [Block 3]'s `-Xbootclasspath/a:` hypothesis with
  fresh structural evidence, opens **B81-G1** in its place).
- **[Block 3]** — §81.2's `securityBridge` module-descriptor + missing-requires-clause evidence WEAKENS,
  without fully refuting, §3.8's original `-Xbootclasspath/a:` `[INFER]` — a correction-class finding per
  this block's own `Type: mixed` declaration, not a full reversal (no live evidence adjudicates between the
  three candidate mechanisms named in §81.2).
- **[Block 38]** — closes **B38-G3** (§81.3): the "separate config class not read this session" possibility
  [Block 38] §38.9 left open is replaced with a corpus-wide negative-existence confirmation plus a positive,
  independently-motivated explanation (the `migrator` module's Kerberos-stripping classes) neither block had
  opened before.
- **[Block 15]** — closes **B15-G3** (§81.4) with a CONFIRMED-and-reinforcing verdict: a real OS-firewall
  layer exists, but it governs the opposite traffic direction (inbound) from the one [Block 15]'s own
  audit-only finding concerns (outbound), so the two verdicts corroborate rather than compete.
- **[Block 40]** / **[Block 61]** — §81.4's `BServerPort.getRuleHint()`/`updateFirewallRules()` read is the
  first direct trace of what `TunnelService.serverPort`'s `ruleHintOverride` literal (`BTunnelService.
  java:142`, already `[CERT]` per both blocks) is FOR at the firewall layer — new corroborating mechanism
  detail, not a correction to either block's own `setRequiresValidation`/type-hierarchy verdict.
