# Block 15 — N5 outbound network access from third-party modules: gated or audit-only?

> Research closing gap **B8-G4**: does N5 actually check any `NiagaraPermission` before a module opens an
> outbound network connection, or is [Block 8]'s finding (`NetworkConnectionAdvice` audits only, zero
> `checkPermission` call sites) the whole story once the HIGHER layers (Niagara's own HTTP client APIs,
> JPMS, official docs) are checked too? Scope: re-derives [Block 8] §8.5/§8.8's `NetworkConnectionAdvice`
> finding independently this session; extends it to `httpClient.jar` (Niagara's public third-party-facing
> HTTP client module, both its OkHttp and Jetty/`HttpURLConnection` transports) and to `nre.jar`'s own
> internal cloud/subscription HTTP transports (Jetty client, OkHttp); checks JPMS's actual gating semantics;
> checks the official shipped developer docs for a network-permission section; compares against N4.14's real,
> enforced, parameterized `NETWORK_COMMUNICATION` permission group (REMITTANCE `niagara-research`). Does
> **not** cover: a live `[CERT-hw]` reproduction on a running N5 station (named child gap below — this
> report is entirely static/code-level per the caller's read-only scope); the internals of `okhttp-jvm.jar`
> / `jetty-client.jar` / `jetty.jar` themselves (only NIAGARA'S OWN usage of them was checked, not whether
> those third-party libraries carry an independent gate of their own); the broader
> `niagara.security.dashboard` module (only `httpClient.jar`'s dashboard AGENT into it was opened).
>
> Subject version: **N5 5.0.0.28 (Beta)** — same install as [Block 8]/[Block 3], same JRE 25.0.4.7
> (`etc/brand.properties:workbench.notice` Beta marker, per [Block 3]).
>
> Sources (all local, read-only, opened fresh this session):
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` — `com.tridium.nre.security.advice.*`
>   (`SecurityAgent`, `NetworkConnectionAdvice`), `com.tridium.nre.security.permissions.PermissionBridge`,
>   `com.tridium.nre.cloud.transport.NiagaraCloudHttpTransport`, `com.tridium.nre.subscription.HttpConnectionlessTransport`.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/httpClient.jar` — the full module (172
>   classes + `module-info.class`): `com.tridium.httpClient.**` (driver/servlet/transport layer),
>   `niagara.httpClient.**` (public third-party-facing API: `HttpClientBuilder`, `IHttpClient`),
>   `com.tridium.httpClient.util.sec.BHttpClientSecurityDashboardAgent`.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` —
>   `doc/security/niagaraPermissions.html`, `doc/security/requestingPermissions.html`,
>   `doc/security/security.html` (official shipped developer docs, read via Python `zipfile` +
>   HTML-tag-stripped text extraction, keyword-scanned this session).
> - REMITTANCE baseline: `niagara-research/niagara-mental-model.md:80` (["B1-3"], N4's `NiagaraSocketPermission`
>   custom-class model), `niagara-research/niagara-mental-model-bloque18.md` §18.4.2/§18.4.4 (N4's
>   `NETWORK_COMMUNICATION` group → build-time expansion to concrete `NiagaraSocketPermission`/`URLPermission`
>   Java `Permission` objects), `niagara-research/niagara-mental-model-bloque994.md` §994.5 (N4 LOW-mode
>   grant table), `niagara-research/niagara-mental-model-bloque112.md` (N4 `NetworkCommunicationPermissionGroup`
>   RiskLevel + Security Dashboard surfacing) — all fetched via `python3 corpus-nav.py find/show` this session.
> - [Block 8] (`niagara5-block8.md` §8.1, §8.5, §8.7, §8.8) — the parent finding this block re-derives and
>   extends (B8-G4).
>
> Method: `unzip` extraction of `nre.jar` (full jar, 126+ classes under `com/tridium/nre/**`) and
> `httpClient.jar` (full jar, 172 classes), decompiled with **Vineflower 1.12.0**
> (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar`) on
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java` (OpenJDK 26.0.2.1) into
> `/tmp/claude-1000/n5b15/decompiled/` (`nre.jar`, full-jar batch decompile) and
> `/tmp/claude-1000/n5b15/decompiled-httpclient/` (`httpClient.jar`, targeted + `module-info.java`) —
> both ephemeral scratch, not part of the corpus, re-derivable from the jars cited. A raw `grep -rla`
> (binary-safe `-a`) sweep across every extracted `.class` file's constant pool located candidate classes
> BEFORE decompiling any of them (`HttpClient`, `URLConnection`, `openConnection`, `InetAddress`,
> `checkPermission`, `NiagaraPermission`, `PermissionManager`, `SecurityManager` — each run against both
> jars' full extracted trees, zero-hit and non-zero-hit results both recorded verbatim in §15.2/§15.3). A
> Python `zipfile`+`re` keyword scan (`network`, `socket`, `http`, `outbound`, `connect`) HTML-stripped and
> counted every occurrence in the 3 `docDeveloper.jar` security pages. Markers: `[CERT]` local primary
> (jar/class file opened this session) · `[CERT-doc]` official shipped doc (`docDeveloper.jar`, opened this
> session) · `[INFER]` deduction. Every `[CERT]`/`[CERT-doc]` below was read/grepped this session; none is
> carried from memory — including the `SecurityAgent.java`/`NetworkConnectionAdvice.java`/`PermissionBridge.java`
> citations that overlap [Block 8]'s own findings (re-derived independently per the caller's instruction, not
> copied from the B8 text).
>
> Security/runtime layer. Direct child of [Block 8] §8.5/§8.8 (closes gap **B8-G4**). Cross-corpus:
> `niagara-research/niagara-mental-model.md`, `-bloque18.md`, `-bloque994.md`, `-bloque112.md`.
>
> **Type:** mixed — §15.1-§15.4 are fresh-decompiled evidence against N5 5.0.0.28; §15.5 draws `[INFER]`
> comparisons against PRIOR `niagara-research` corpus blocks (N4 baseline), which is the MIXED trigger per
> METHODOLOGY §11.

---

## 15.1 — Re-derivation of B8 §8.5/§8.8: zero `checkPermission` in `NetworkConnectionAdvice`, confirmed independently this session `[CERT]`

A **full, fresh read** of `SecurityAgent.java` (190 lines, `SecurityAgent.java:12-161`, this session's own
decompile — not the B8 decompile) confirms the **complete** instrumentation target list is unchanged from
[Block 8] §8.5: the agent installs exactly 5 ByteBuddy passes, and the ONLY network-related JDK entry points
instrumented anywhere in the file are `java.nio.channels.SocketChannel.open` (`:17-21`, exit advice
`NetworkConnectionAdvice.ForSocketChannel`), `java.net.Socket.connect` (`:26-32`, exit advice
`NetworkConnectionAdvice.ForSocket`), and `java.net.DatagramSocket.connect`/`.send` (`:33-38`, exit advice
`NetworkConnectionAdvice.ForDatagramSocket`). No `java.net.http.HttpClient`, `java.net.URL`,
`java.net.URLConnection`, or `java.net.InetAddress` method is matched anywhere in the 190-line `premain`
body — confirmed by reading every one of the 5 `.type(...)` blocks, not sampling.

A **full, fresh read** of `NetworkConnectionAdvice.java` (65 lines, this session's own decompile) confirms
all 3 advice classes (`ForDatagramSocket:16-27`, `ForSocket:30-43`, `ForSocketChannel:45-63`) follow the
identical shape: guard on `SecurityBridge.isInitialized()`, extract the remote `InetAddress`, skip loopback,
and call **only** `SecurityBridge.permissionBridge.auditNetworkConnection(String, String)`
(`:23`/`:38`/`:56`). **Zero** `checkPermission` call sites exist in this file — a full-file read, not a grep
miss. `PermissionBridge.java` (`PermissionBridge.java:39-46`, this session's own decompile) confirms
`auditNetworkConnection` is a 1-line delegate to
`SecurityUtil.getSecurityAuditor().audit(new SecurityAuditEvent("Network connection", ...))` — an AUDIT LOG
write, structurally identical to (and reusing) the same `SecurityAuditEvent` machinery `checkPermission`
denials use (§8.5's audit path), but never itself calling `permission.isGrantedTo(...)` or
`PermissionManager.checkPermission(...)`. Contrast: `PermissionBridge.checkPermission`
(`PermissionBridge.java:18-25`) — the method the FILE/PROCESS-EXEC advice classes call — is a real gate
(1-line delegate to `SecurityUtil.checkPermission`, can throw `PermissionException`); no advice class in
`NetworkConnectionAdvice.java` calls this method or any equivalent.

One new detail beyond B8: `PermissionBridge.isCoreConnectionModule` (`PermissionBridge.java:62-71`) — the
predicate used to pick which stack frame to NAME in the audit event — treats `"okhttp3"` as a filtered
"core" module name alongside `niagara.nre`/`niagara.net`/`niagara.baja`/`java.*`/`javax.*`/`jdk.*`/
`org.bouncycastle.*`. This is a direct code confirmation that N5's own internal machinery routes through the
`okhttp3` JPMS module by design (§15.2 traces where), and that the audit-attribution logic is aware of it
specifically enough to skip past it when naming "the module that really opened this connection".

## 15.2 — Higher layers checked: Niagara's own HTTP client stacks call no permission check either `[CERT]`

**Method note**: a binary-safe `grep -rla` sweep (`grep -rla "<token>" --include="*.class" .`) across the
FULL extracted `nre.jar` tree found zero hits for `HttpClient`/`URLConnection`/`openConnection`/`InetAddress`
on a first pass using `grep -rl` (no `-a`) — a false negative from grep's binary-file heuristic, caught by a
sanity re-check (`SocketChannel`, a string known-present in `NetworkConnectionAdvice.class`, also returned
zero without `-a`). Re-run with `-a` explicitly found real hits (below) — recorded here per METHODOLOGY §11's
whitespace/normalization re-check discipline, extended to the binary-grep case.

**Niagara's own internal HTTP transports (`nre.jar`) call no permission check.**
`com.tridium.nre.cloud.transport.NiagaraCloudHttpTransport` (full 70-line file, this session's decompile) —
Niagara Cloud's own outbound transport — builds and uses an `org.eclipse.jetty.client.HttpClient`
(`NiagaraCloudHttpTransport.java:37,57-69`, imports `org.eclipse.jetty.client.HttpClient` at `:17`) with a
custom TLS `SslContextFactory`/`TridiumHostnameVerifier`, and its `send()` method (`:36-55`) calls
`client.newRequest(uri).method(...).send()` directly — **no `checkPermission`, no `NiagaraPermission`
import, no `PermissionManager` reference anywhere in the file.** `com.tridium.nre.subscription.HttpConnectionlessTransport`
(full 242-line file, this session's decompile) — the entitlement/subscription-license HTTP transport — builds
and uses an `okhttp3.OkHttpClient` (imports at `:24-31`, built in `makeClient()` at `:52-87`) and its `send()`
method (`:89-161`) calls `this.client.newCall(request).execute()` directly — again **zero** `checkPermission`/
`NiagaraPermission`/`PermissionManager` references in the entire 242-line file (confirmed by both a full read
and a `grep -a` sweep of the source). Both classes are core `niagara.nre`-module code — i.e. even Niagara's
OWN first-party outbound HTTP calls run with no permission gate at this layer; the mechanism simply does not
exist for either core or third-party code at the transport level.

**Niagara's public third-party-facing HTTP client API (`httpClient.jar`) calls no permission check
either.** `httpClient.jar`'s `module-info.java` (this session's decompile, `module-info.java:1-59`) declares
`exports niagara.httpClient` and `exports niagara.httpClient.datatypes` — the intended PUBLIC entry point for
a third-party module wanting to make HTTP calls, via `niagara.httpClient.HttpClientBuilder`/`IHttpClient`.
A `grep -rla` sweep across the FULL 172-class extracted `httpClient.jar` tree for `checkPermission`,
`NiagaraPermission`, `PermissionManager`, and `SecurityManager` returned **zero hits in every single class**,
including: `niagara.httpClient.HttpClientBuilder` (192-line file, this session's decompile — the fluent
builder a third-party module calls: `withAddress`/`withHttpsAddress`/`build()`, `HttpClientBuilder.java:34-191`
— no permission call anywhere in the class); the two concrete transports
`com.tridium.httpClient.comm.transport.httpUrlConnection.BUrlConnectionHttpTransport` (wraps
`java.net.HttpURLConnection`) and `com.tridium.httpClient.comm.transport.okHttp.BOkHttpTransport` (wraps
`okhttp3.OkHttpClient`) — both decompiled this session, neither imports any `com.tridium.nre.security.**` or
`niagara.nre.security.**` type. `httpClient.jar`'s `module-info.class` itself carries **zero** `Grant*Permission`
annotations (`javap -verbose module-info.class`, this session — matches [Block 8] §8.1's closed 7-annotation
list; there being no NETWORK-shaped grant annotation to carry is consistent with §15.4's doc-silence finding).
Notably, `module-info.java` requires `okhttp3`, `org.eclipse.jetty.client`, `org.eclipse.jetty.io`,
`org.eclipse.jetty.util`, `org.eclipse.jetty.websocket.*` (`:2-29`) but **never `java.net.http`** — Niagara's
own client framework does not use the JDK's built-in `java.net.http.HttpClient` at all, exclusively Jetty's
client and OkHttp (both instrumented indirectly only insofar as they themselves eventually call
`SocketChannel.open`/`Socket.connect`, §15.1).

**The one dashboard surface found is a TLS/auth-posture checklist, not a network-destination gate.**
`com.tridium.httpClient.util.sec.BHttpClientSecurityDashboardAgent` (268-line file, this session's decompile)
implements `BISecurityDashboardProviderAgent` and DOES feed the live Security Dashboard — but its
`getSecurityDashboardItems` (`:91-135`) checks only 5 things: insecure (non-TLS) client mode (`:93-100`),
HTTP Basic auth usage (`:101-107`), TLS-compatibility-mode usage (`:108-114`), non-driver-framework client
usage (`:115-122`), and servlets accepting insecure requests (`:123-129`), plus SMA license expiry
(`:130-132,215-252`). **None of these checks inspects the DESTINATION host/port a client connects to** — it
is a security-HYGIENE checklist over clients that already went through the `httpClient` driver framework, not
a network-access allowlist/audit view; and it covers only modules that use the `httpClient` driver framework
in the first place (a module calling raw `java.net.http.HttpClient`/`Socket` directly is invisible to it).
This is a materially different feature from N4's PolicySpy hosts/ports display (§15.5) — it answers "is this
registered HTTP client's transport secure", not "what can this module reach".

## 15.3 — JPMS does not gate outbound network access `[INFER]`

The Java Platform Module System (in force here — N5 runs fully modularized, per [Block 3]/[Block 8]'s
`module-info`-based architecture) restricts **readability**: a module must `requires` another named module to
compile/link against its exported types, and the JVM enforces STRONG ENCAPSULATION only for packages that
module does NOT `exports` (an `IllegalAccessError`/`NoSuchMethodError`-shaped failure at reflection/link
time). `java.net`, `java.nio.channels`, and `java.net.http` are all exported by `java.base`, which every
module reads implicitly (`requires java.base` is automatic) — meaning ANY module, including a genuinely
third-party one with no special `requires` line, can call `new Socket(...)`, `SocketChannel.open()`, or
(if it separately `requires java.net.http`) `HttpClient.newHttpClient()` with no JPMS-level readability
barrier at all. JPMS's module graph is a COMPILE/LINK-time readability boundary, not a runtime
capability/authorization system — this is a documented structural property of the module system itself, not
a Niagara-specific finding, so it is marked `[INFER]` (general JDK-spec deduction) rather than `[CERT]`: no
JPMS enforcement code was decompiled this session to refute it, and none of the 172+126 classes read in
§15.1/§15.2 showed a module-readability check standing in for a permission check. Practically: JPMS is not a
candidate "higher/different layer" that could be quietly gating what §15.1/§15.2 found ungated — it operates
on a completely orthogonal axis (which TYPES a module may reference, not which network ADDRESSES it may
reach).

## 15.4 — Doc silence: the official permission docs never mention network/socket access at all `[CERT-doc]`

A keyword scan (`network`, `socket`, `http`, `outbound`, `connect` — case-insensitive, full HTML-tag-stripped
text) of `doc/security/niagaraPermissions.html` (8086 chars, the ENTIRE page, this session) returned **zero**
matches for all 5 keywords. This is the same page [Block 8] §8.1/§8.6 cites for the "third-party modules
cannot create custom permissions" and "disabling permission checks" claims — it enumerates the permission
model in full, and never once mentions network access as something the model covers.
`doc/security/requestingPermissions.html` (this session, same method) DOES mention `socket`/`connect`, but
only in the context of `MANAGE_SERVER_TRUST_ANCHORS` ("Allows a module to add trusted certificates to the fox
and web server sockets") and `RDB_CONNECTION` ("obtain a JDBC Connection... to interact directly with a
remote database") — i.e. INBOUND server-socket trust configuration and a JDBC-specific permission, not a
general outbound-connection gate. `doc/security/security.html` (this session, same method) mentions
`network`/`http`/`connect` only for Fox/HTTP AUTHENTICATION (workbench↔station, station↔station credentials)
— access control for WHO can connect INTO Niagara, not what a loaded module may reach OUT to. Across all 3
official developer security pages read this session, **no page documents any permission, group, or gate
governing a module's own outbound socket/HTTP connections** — the doc is silent on this exact question in the
same corpus where it is explicit about file access, keystores, backups, RDB, and code signing. Per the
code/doc convergence rule (METHODOLOGY §3: code wins for behaviour, doc for intent) — here code and doc
**agree**: neither documents nor implements an outbound-network gate. This is the doc-side confirmation of
§15.1/§15.2's code-side finding, not an independent discovery.

## 15.5 — N4.14 baseline: `NETWORK_COMMUNICATION` was a real, parameterized, enforced permission — the contrast is a genuine downgrade `[INFER]` (cross-corpus synthesis)

REMITTANCE `niagara-research/niagara-mental-model-bloque18.md` §18.4.2 (`:310-317`) documents the N4.14
build-time transformation of a declared `NETWORK_COMMUNICATION` permission group (e.g.
`hosts=*, ports=80,443`) into CONCRETE `java.security.Permission` objects embedded in the signed module's
`module.xml`: `<java-permission class="com.tridium.nre.security.NiagaraSocketPermission" name="*:80,443"
action="connect,resolve"/>` plus a `java.net.URLPermission` — both real `Permission` subclasses the N4
`SecurityManager` evaluates via `implies()` AT THE ACTUAL SOCKET-CONNECT CALL SITE, per
`niagara-research/niagara-mental-model.md:80` ("Niagara usa su propio `NiagaraSocketPermission`... El
SecurityManager intercepta en la capa FOX con la clase custom. Los módulos FOX requieren
`NETWORK_COMMUNICATION` permission group igual que cualquier otro" — no bypass, real enforcement). §18.4.4's
permission-group table lists `NETWORK_COMMUNICATION`'s parameters as `hosts, ports, type, proxySelector,
SSLSockets` (`niagara-mental-model-bloque18.md:322`) — a module author must DECLARE which hosts/ports it
intends to reach, and a connection attempt outside that declaration fails.
`niagara-research/niagara-mental-model-bloque994.md` §994.5 (`:173,181`) shows `NETWORK_COMMUNICATION` does
NOT require code-signing to be granted in N4.14's default LOW mode — but it is still a REAL, DECLARED,
PARAMETERIZED permission that must be requested and IS evaluated by the SecurityManager; LOW mode only skips
the SIGNATURE check, not the permission check itself. `niagara-research/niagara-mental-model-bloque112.md`
(`:45,47`) independently confirms the group is live and VISIBLE: `NetworkCommunicationPermissionGroup` carries
`RiskLevel.MODERATE`, and a module declaring it is surfaced on N4's live Security Dashboard/PolicySpy with its
`hosts=*, ports=443` parameters readable in the UI — a defender can literally see which hosts/ports an
installed module is entitled to reach.

**The comparison, stated plainly**: N4.14 required a module to (a) DECLARE its intended hosts/ports in a
`NETWORK_COMMUNICATION` permission request, (b) have that declaration compiled into a real, checked
`NiagaraSocketPermission`/`URLPermission` pair enforced at connect time by the SecurityManager, and
(c) be VISIBLE to an operator via PolicySpy/Security Dashboard with those exact parameters. N5 5.0.0.28 has
**none of the three**: no declaration mechanism exists (§15.1's 8-class taxonomy has no network-destination
permission — re-confirmed, not just cited, this session by the zero-hit sweeps of §15.2), no enforcement
happens at connect time (§15.1's advice classes audit only), and the one dashboard surface found (§15.2's
`BHttpClientSecurityDashboardAgent`) does not show destination hosts/ports at all. This is `[INFER]` because
it is a synthesis drawn across 4 PRIOR `niagara-research` blocks compared against this session's own `[CERT]`
findings — the individual halves (N4 side, N5 side) are each independently sourced, but the "this is a
downgrade" characterization is the researcher's own comparison, not a literal statement in any single source.

## 15.6 — Verdict: **CONFIRMED** — outbound network access is audit-only in N5 5.0.0.28, for every module, not just third-party

**CONFIRMED**, with this exact scope: in N5 5.0.0.28, no `NiagaraPermission` gates a module's own outbound
`Socket`/`DatagramSocket`/`SocketChannel` connection (and therefore no gate exists for anything built on top
of those primitives — `java.net.http.HttpClient`, `java.net.HttpURLConnection`, OkHttp, or Jetty's HTTP
client — since all of them bottom out at the JDK network primitives `SecurityAgent` instruments, or at
primitives it does NOT instrument at all in the `HttpClient`/`URLConnection` case per §15.1). This was
independently re-derived this session (not merely cited from [Block 8]) at 4 levels: the agent's own
instrumentation table (§15.1), Niagara's own core AND public-facing HTTP client code (§15.2, both `nre.jar`'s
internal transports and the whole `httpClient.jar` module — 0/172+2 classes call any permission-check API),
JPMS's structural inability to substitute for such a gate (§15.3), and the official developer docs' own
silence on the topic across all 3 relevant pages (§15.4). The finding is **NOT scoped to third-party modules
specifically** — it is a gap in the mechanism itself, and Niagara's OWN first-party cloud/subscription
transports (§15.2) run through the identical ungated path.

**What remains `[INFER]`, per the static-defect/runtime-exploitability split (METHODOLOGY §3):** that this
constitutes a REAL exploitable weakness in practice, rather than an intentional design choice (e.g. network
egress is assumed to be controlled at the OS/firewall/network layer instead, which this corpus has not
checked). The GATE CONDITION (METHODOLOGY §3) for turning this into a live concern is simply: any loaded
module, signed or not, third-party or core, calling any JDK/Jetty/OkHttp network API — there is no flag,
license feature, or configuration that currently closes this gap; §8.6's `niagara.permissions.disable`
developer-mode toggle is irrelevant here since checks are not merely suppressed but were never coded for this
surface in the first place.

**Practical impact for DashboardPan/ColdRoomPan-style modules (outbound HTTPS to Supabase/cloud, extending
[Block 8] §8.8):** an outbound HTTPS call from a third-party DashboardPan-style module — whether it uses
Niagara's OWN recommended `niagara.httpClient.HttpClientBuilder` API or raw `java.net.http.HttpClient`
directly — will succeed with **no `PermissionException` at any layer checked this session**, regardless of
destination host or port, and regardless of whether the module declares any grant annotation at all (there is
none to declare, §8.1/§15.2). The only trace left is a `SecurityAuditEvent("Network connection", <module>,
"<type> connected to: <address>")` audit-log entry (§15.1) — informative for FORENSICS after the fact, but
not preventive, and not surfaced on the live Security Dashboard the way N4's PolicySpy surfaced
`NETWORK_COMMUNICATION` grants with their host/port parameters (§15.5). For DashboardPan specifically, this
means the module's cloud-sync destination is unconstrained by the permission system — file I/O is confined to
the shared-directory allowlist by construction ([Block 8] §8.8), but outbound network reach is not confined
at all.

## Self-verify

`toolbelt/verify-block.sh niagara5-block15.md` (this session, verbatim, run from
`/home/cristian/niagara5-research`):
```
== verify-block: niagara5-block15.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 3  (adj 2)
   [CERT-live] 1
   [CERT] 9  (adj 7)
   [CERT-doc] 5  (adj 3)
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 11  (adj 9)
-- ratio -- [INFER]/[CERT*] = 9/15 = 0.60
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  HttpClientBuilder.java:34-191
   extern  PermissionBridge.java:18-25
   extern  PermissionBridge.java:39-46
   extern  PermissionBridge.java:62-71
   extern  SecurityAgent.java:12-161
   extern  module-info.java:1-59
   extern  niagara-mental-model-bloque18.md:322
   extern  niagara-mental-model.md:80
   extern  niagara-research/niagara-mental-model.md:80
   resolved 0 of 9
   WARN    resolved 0 of 9 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```
**Declared per METHODOLOGY §11's decompiled-tree rule**: `verify-block: 0 resolved (all extern — 6 point into
decompiled trees under /tmp/claude-1000/n5b15/{decompiled,decompiled-httpclient}/, ephemeral scratch,
re-derivable from the jars cited in the header; 3 point into the sibling `niagara-research` corpus, outside
this target's resolution root — the last 2 rows are the SAME citation matched twice by the script's regex,
once with and once without the `niagara-research/` path prefix); citation gate = inline token-verify`. The
script's regex matched only 9 of the many `file:line`-style tokens in the body — most in-body citations use
the shorter `ClassName:line` bare form (e.g. `ForDatagramSocket:16-27`) inside a parenthetical alongside a
fuller anchor elsewhere, per §11's "bare `:line` body + full `filename:line` self-verify anchor" convention;
the rows above are what the script's regex can see, not the full citation count.

**Ratio note (block declared `Type: mixed`) and a documented self-referential inflation.** The raw ratio
climbed from an earlier 0.50 to 0.60 across this section's own edit passes — expected and named in
METHODOLOGY §11: this Self-verify section itself QUOTES marker tokens (to report them), and the script counts
those quoted tokens as fresh claims, inflating both `[CERT]` and `[INFER]` on every re-run that adds more
self-referential quoting. The number reported above is the FINAL run's literal output, taken as-is rather
than chased to a fixed point. Read per-section, not by the blended raw ratio: §15.1/§15.2/§15.4 are
effectively `[CERT]`-only fresh evidence (every advice class, every `httpClient.jar` class, all 3 relevant
doc pages read in full, not sampled — genuinely near-exhausted for the exact question asked); §15.3 and
§15.5 are the declared `[INFER]` synthesis/deduction sections the MIXED type names (§15.5 draws `[INFER]`
across 4 prior `niagara-research` blocks, the exact MIXED trigger per METHODOLOGY §11).

**Inline token-verify**: every `file:line` citation into `SecurityAgent.java`, `NetworkConnectionAdvice.java`,
`PermissionBridge.java`, `NiagaraCloudHttpTransport.java`, `HttpConnectionlessTransport.java`,
`HttpClientBuilder.java`, `module-info.java` (httpClient), and `BHttpClientSecurityDashboardAgent.java` above
points at a class this session itself extracted+decompiled (§15.0 header Method) and then directly `Read`
with line numbers before citing it. Spot-check tokens independently re-`grep -a`-confirmed against the
extracted `.class` trees this session (whitespace-normalized): `auditNetworkConnection` (present in both
`PermissionBridge.class` and all 3 `NetworkConnectionAdvice$For*.class`), `checkPermission` (present in
`PermissionBridge.class`, ABSENT from all 3 `NetworkConnectionAdvice$For*.class` and from every one of the
172 `httpClient.jar` classes — the central negative finding of §15.1/§15.2), `okhttp3`
(`PermissionBridge.class`'s `isCoreConnectionModule` string literal, §15.1). Every REMITTANCE citation into
`niagara-research`'s 4 cited blocks was fetched via `corpus-nav.py find/show` this session and cross-checked
against a direct `sed -n`/`grep -n` read of the cited files' exact line ranges (not corpus-nav's summary text
alone) — confirmed present at `niagara-mental-model.md:80`, `niagara-mental-model-bloque18.md:322` (and
§18.4.2/§18.4.4 context), `niagara-mental-model-bloque994.md:173,181`,
`niagara-mental-model-bloque112.md:45,47`. Token-verify: every decompiled-tree and remittance citation used
in §15.1-§15.5 was opened and read (not inferred from a name) this session; the 8 the script mechanically
matched are listed above, the remainder were manually spot-checked as just described.

**MCP-doc snapshots**: N/A — the 3 `[CERT-doc]` sources are LOCAL files already shipped inside
`docDeveloper.jar` (opened via `zipfile`, not fetched from the web this session) — no snapshot-registration
step applies; cited by their exact in-jar path.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block15.md`. Per the caller's
explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration
and backlog re-classification are deliberately NOT performed this session — left to the orchestrator.

## 15.x — Child gaps opened

- **B15-G1** — `[CERT-hw]` live reproduction: deploy a minimal unsigned/unprivileged third-party N5 test
  module on a running 5.0.0.28 station that opens an outbound HTTPS `Socket`/`SocketChannel` connection to an
  arbitrary external host, confirm live that no `PermissionException` is thrown, and confirm the exact
  `SecurityAuditEvent("Network connection", ...)` entry appears in the audit trail with the module correctly
  attributed by `PermissionBridge.getFirstRelevantModuleInStack` (§15.1).
- **B15-G2** — Check whether `okhttp-jvm.jar`/`jetty-client.jar`/`jetty.jar` carry an INDEPENDENT
  interceptor/gate of their own (host allowlist, proxy-forced routing, etc.) that Niagara's usage does not
  add but the underlying library might apply regardless — only NIAGARA'S OWN classes referencing these
  libraries were opened this session, never the libraries' own bytecode.
- **B15-G3** — Determine whether N5 offers a network-egress control at a DIFFERENT layer entirely outside the
  `NiagaraPermission` mechanism — e.g. an OS-level firewall integration, a platform "allowed hosts" config, or
  a `niagara.net`-module-level ACL — not searched this session (scope was strictly
  `com.tridium.nre.security.**` + `httpClient.jar` + the 3 doc pages).
- **B15-G4** — Open the broader `niagara.security.dashboard` module itself (only `httpClient.jar`'s
  `BHttpClientSecurityDashboardAgent` AGENT into it was read this session) to confirm no OTHER dashboard
  provider anywhere in the 247-module census surfaces a live "which modules have opened outbound network
  connections" view — i.e. rule out that the missing PolicySpy-equivalent (§15.5) exists under an unrelated
  module name not yet identified.

## 15.x — Connections

- **[Block 8] §8.5/§8.8** — direct parent; this block closes gap **B8-G4** with a CONFIRMED verdict (scoped
  as above), re-deriving §8.5's `NetworkConnectionAdvice` table independently rather than citing it, and
  extending §8.8's third-party-module impact analysis with the higher-layer (`httpClient.jar`), JPMS, and
  doc-silence checks B8-G4 explicitly asked for.
- **[Block 3] §3.8** — grandparent; the SecurityAgent/PermissionManager discovery this whole chain traces
  back to.
- **REMITTANCE → `niagara-research/niagara-mental-model.md:80`, `-bloque18.md` §18.4.2/§18.4.4,
  `-bloque994.md` §994.5, `-bloque112.md`** — the N4.14 baseline §15.5 contrasts against: a real, declared,
  parameterized, SecurityManager-enforced, dashboard-visible `NETWORK_COMMUNICATION` permission group with no
  N5 structural analogue.
