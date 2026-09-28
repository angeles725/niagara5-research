# Block 112 — `BFoxHistorySpace`'s `getPermissions(null)` nav gate is CORRECTED, not confirmed: the class is a client-side fox proxy whose `BRootHistoryFolder.getPermissions()` override ignores `cx` entirely and instead round-trips the real session's permissions, and the server-side leaf-record path independently re-gates on `getSessionContext()`; the caller/callee-split null-Context census stays non-mechanical; N4-4.15.3.28's real SAML SP call chain is now traced end-to-end and accepts SHA-1 for an even more solidly-evidenced reason than [Block 98] found; `WebProperty`'s frozen-slot flag is found once more, on an unrelated first-party mechanism

> Research closing/narrowing four assigned child gaps from two prior blocks. **B107-G1** ([Block 107]
> §107.3/§107.x — does `BFoxHistorySpace`'s `getPermissions(null)` nav-visibility gate reach actual
> history CONTENT exposure, or is it discovery-only?); **B107-G2** ([Block 107] §107.x / [Block 99]
> §99.2 / [Block 91] §91.x's own **B91-G1** — the caller/callee-split and non-standard-wrapper-name
> null-Context census); **B109-G1** ([Block 109] §109.x, opened by its own correction to [Block 98]
> §98.1 — re-run [Block 98]'s SHA-1/XML-DSig secureValidation reachability analysis against N4-4.15.3.28's
> REAL, currently-shipped `com.onelogin.saml2.util.Util`/`com.tridium.saml.rp.Response` call chain);
> **B109-G2** ([Block 109] §109.1 — `WebProperty`'s frozen-slot metadata-sync path across third-party
> module SPI surfaces not yet checked). Does **not** cover: a live two-party fox session capture proving
> `BHistoryChannel.getSessionContext()` actually reflects a non-admin user's real permissions end-to-end
> (this session's proof is a full, in-context decompiled-source trace of the real dispatch code, not a
> live packet capture); a byte-level disassembly of N5's newer `xmlsec-4.0.4.jar` to confirm it shares
> N4's `xmlsec-3.0.4`'s MD5-only `secureValidation` scope (opened below as **B112-G3**, a genuinely new,
> narrow residual this session's own N4/N5 version-diff finding surfaced); an exhaustive semantic
> call-graph trace resolving B107-G2/B91-G1's own caller/callee-split shape (explicitly re-confirmed
> non-mechanical by this session too, for the fourth time across [Block 91]/[Block 99]/[Block 107]/this
> block); a search of any module OUTSIDE this corpus's 247 N5-bundled jars for a third-party `USER_DEFINED_3`
> declaration (structurally out of reach of a static corpus read, not merely undone — see §112.4).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> N4 baseline for **B109-G1**: PowerB N4-4.15.3.28 OEM package, read-only at `/mnt/c/PowerB/PowerB-4.15.3.28`
> (the same install [Block 98]/[Block 109] used), plus the pre-existing `/home/cristian/niagara-research/
> organized/saml/saml-rt/maven-sources/` tree (version-matched Maven-Central source jars for
> `com.onelogin:java-saml-core:2.9.0` and `org.apache.santuario:xmlsec:3.0.4`, confirmed this session
> against the REAL bundled jar's own `pom.properties`, not merely assumed). Method: full-context decompiled
> source reads (`BFoxHistorySpace.java`, `BRootHistoryFolder.java`, `BHistoryFolder.java`,
> `BHistorySpace.java`, `BHistoryDatabase.java`, `BHistoryChannel.java`, `BFoxChannel.java`) tracing the
> ACTUAL client-vs-server role and real call chain behind §107.3's three cited call sites, for B107-G1; two
> fresh corpus-wide mechanical greps (wrapper-method-name family, no-arg `getPermissions()`/`canRead()`/
> `canWrite()`/`canInvoke()` overload family) for B107-G2; extraction of the REAL `com/tridium/saml/rp/
> Response.class`+`AuthnRequest.class` from the actual PowerB `saml-rt.jar` (not previously opened by
> [Block 98]/[Block 109]) plus `javap -p -c` disassembly of both, cross-checked against a fresh disassembly
> of the already-extracted, sha256-reconfirmed `n4-Util.class`, plus a version-matched Maven-source read of
> `SignatureAlgorithm.java`/`Reference.java`/`Manifest.java`/`XMLSignature.java` from the real bundled
> `xmlsec-3.0.4` dependency, for B109-G1; a fresh, UN-filtered (docSource included) corpus-wide
> `USER_DEFINED_3` grep for B109-G2. All commands run this session, 2026-09-27. Scratch (never committed):
> `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b112/`
> (`extracted/` — `Response.class`/`AuthnRequest.class`/`IdPResponse.class`/`SAMLIdPAuthnRequestServlet.class`
> pulled fresh from the real `saml-rt.jar`; `response_javap.txt`/`authnrequest_javap.txt` — their `javap`
> disassembly; `utilclass/` — the [Block 109]-extracted `n4-Util.class` re-disassembled, `n4_util_javap.txt`;
> `allsaml/` — all 4 N4 SAML jars' `.class` files extracted for the Apache Santuario bundling census;
> `n5-saml-core.jar` — N5's nested `LIB-INF/java-saml-core-2.9.0.jar`, extracted for the xmlsec-version
> comparison). Markers (canonical list, METHODOLOGY §3): `[CERT]` local primary source (`file:line`) ·
> `[CERT-hw]` a live disassembly/extraction this session against a real installed jar (sha256-anchored) ·
> `[CERT-a]` a version-matched external source (Maven Central) confirmed against the real bundled
> `pom.properties`, not independently byte-diffed against the compiled `.class` · `[INFER]` deduction.

---

## 112.0 — ALREADY-COVERED check (all four gaps)

`rg -il` over `niagara5-block*.md` with at least two distinct terms per gap, run before investigating each:
`BFoxHistorySpace` → hits only [Block 107] (the gap's own origin, not a later closure); `caller.callee`/
`caller/callee` → hits [Block 91]/[Block 99]/[Block 107] (the gap's own lineage); `secureValidation` → hits
[Block 62]/[Block 98]/[Block 109] (the gap's own N4/N5 lineage, not a later re-run); `WebProperty` → hits
only [Block 109] (the gap's own origin). **No block postdating [Block 91]/[Block 99]/[Block 107]/[Block 109]
already closes any of these four gaps — none reported ALREADY-COVERED; all four investigated fresh.** `[CERT]`
(`rg -il` output, this session).

## 112.1 — B107-G1 CLOSED, WITH A CORRECTION TO [Block 107] §107.3: `BFoxHistorySpace` is a CLIENT-side fox proxy space, not a server-side gate — its cited `getPermissions(null)` calls all land on `BRootHistoryFolder`'s own override, which IGNORES the `null` argument entirely and instead round-trips the REAL session's server-computed permissions over the fox channel; the actual record-content-serving path independently re-checks the same real session context a second time `[CERT]`

**Gap text (verbatim, from [Block 107] §107.x):** *"Trace whether `BFoxHistorySpace`'s `getPermissions(null)`-
gated nav-folder-visibility check ... has any real consequence beyond folder-EXISTENCE/nav-tree visibility
over the fox protocol — specifically, whether the actual per-history READ ... is independently re-checked
with a real, non-null Context at the point of serving history data ... `investigable` — needs tracing
`BFoxHistorySpace`'s history-data-serving path ... and/or the `BHistoryFolder`/`BHistoryMirror` classes' own
read-time permission enforcement."*

**Step 1 — `BFoxHistorySpace` is confirmed CLIENT-side, not server-side.** [Block 107] §107.3 characterized
the class as "a fox-protocol history-space nav-listing handler" gating what "gets ... nav-advertised over
fox" as if this were the SERVER deciding what to expose to a remote requester. A full re-read shows the
opposite: `BFoxHistorySpace implements BIFoxProxySpace` `[CERT]` (`organized/history/vineflower/com/tridium/
history/fox/BFoxHistorySpace.java:58`), and `BIFoxProxySpace` is a bare marker interface (`init(BFoxSession)`/
`cleanup(BFoxSession)`, no server-role method) `[CERT]` (`organized/fox/vineflower/com/tridium/fox/sys/
BIFoxProxySpace.java`, whole 13-line file). `BFoxSession extends BFoxProxySession` `[CERT]`
(`organized/fox/vineflower/com/tridium/fox/sys/BFoxSession.java:79`) — the "Proxy"/"IFoxProxySpace" naming is
this corpus's own convention for the LOCAL representation of a REMOTE station's object, held by the
connecting side. This class runs in the requester's own JVM (Workbench, or another station acting as a fox
client), populating ITS OWN local nav-tree cache from what the remote server reports — it does not run on
the station being queried.

**Step 2 — the three cited `getPermissions(null)` call sites all construct a `BRootHistoryFolder` with
`space = this` (the `BFoxHistorySpace` instance itself).** All three (`:177,228,248`, re-read in full) follow
the identical shape: `BRootHistoryFolder rootFolder = new BRootHistoryFolder(this, ..., this); if
(rootFolder.getPermissions(null).hasOperatorRead()) { ... }` `[CERT]`
(`organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java:177-181,225-231,245-251`).
`BHistoryFolder`'s constructor stores this first argument verbatim as `this.space` `[CERT]`
(`organized/history/vineflower/com/tridium/history/BHistoryFolder.java:78-79`, `this.space = space;`) — so
for every one of these three call sites, `this.space instanceof BFoxHistorySpace` is unconditionally true.

**Step 3 — `BRootHistoryFolder.getPermissions(Context cx)` has a branch for exactly this case, and it
IGNORES the `cx` parameter entirely (whether null or not):**

```java
public BPermissions getPermissions(Context cx) {
   if (this.permissions != null) { return this.permissions; }
   if (this.space instanceof BFoxHistorySpace) {
      try {
         this.permissions = ((BFoxHistorySpace)this.space).channel().getPermissionsByOrd(this.getOrdInSession());
      } catch (Exception e) { e.printStackTrace(); return BPermissions.none; }
      return this.permissions;
   } else {
      return cx != null && cx.getUser() != null ? cx.getUser().getPermissionsFor(this) : BPermissions.all;
   }
}
```
`[CERT]` (`organized/history/vineflower/com/tridium/history/BRootHistoryFolder.java:42-58`, whole method).
The `cx != null ? ... : BPermissions.all` fail-open shape [Block 99] §99.2/[Block 107] §107.3 both correctly
identified for the GENERIC `BComponent`/base-class case is real — but it is the `else` branch, reached only
when `space` is NOT a `BFoxHistorySpace`. For the fox-proxy case (the ONLY case these three call sites ever
hit), the method instead makes a REAL remote round-trip: `channel().getPermissionsByOrd(ord)`.

**Step 4 — `channel().getPermissionsByOrd(BOrd)` is a real fox request, and its SERVER-side handler computes
the answer from the actual authenticated session, never from `null`.** `BFoxHistorySpace.channel()` returns
the `BHistoryChannel` bound to `this.getFoxSession().getConnection()` `[CERT]`
(`organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java:527-528`). `BHistoryChannel`
implements BOTH the client-send and server-dispatch halves of the same fox command in one class (a
corpus-wide convention already established for other channels) `[CERT]`
(`organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:169-233` dispatches `process
(FoxRequest)` by command string to per-command handler methods). The client-side overload sends a
`"getPermissionsByOrd"` request and decodes the integer mask from the reply; the SERVER-side handler is:

```java
public FoxResponse getPermissionsByOrd(FoxRequest req) throws Exception {
   String ordString = req.getString("ord");
   BOrd ord = BOrd.make("local:|" + ordString);
   BObject target = ord.resolve().get();
   if (!(target instanceof BIProtected)) throw new BajaRuntimeException("Not protected: " + ordString);
   BPermissions p = ((BIProtected)target).getPermissions(this.getSessionContext());
   ...
}
```
`[CERT]` (`organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:1945-1965`, whole
method). `BFoxChannel.getSessionContext()` — the base class both `BHistoryChannel` overloads inherit —
delegates to `this.getServerConnection().getSessionContext()`: the REAL, currently-authenticated fox
session's own Context, not a synthetic or null one `[CERT]` (`organized/fox/vineflower/com/tridium/fox/sys/
BFoxChannel.java:325-337`, `getSessionContext()`/`getPermissionsFor(Object, boolean)` — the latter also used
by every other server-side handler below). **The `null` literal at `BFoxHistorySpace.java:177,228,248` never
reaches a server-side security decision at all** — it is consumed only by `BRootHistoryFolder`'s own
override, which discards it in favor of asking the actual station what the actual logged-in user's actual
permissions are.

**Step 5 — the leaf record-content-serving path (the gap's own named residual) independently re-checks the
same real session context a SECOND time, via a completely separate code path.** `BHistoryChannel.timeQuery
(FoxCircuit circuit)` — the server-side handler for the client's `timeQuery` circuit, which streams the
actual `BHistoryRecord` time-series data — re-resolves the history and re-checks permissions from scratch:

```java
try (HistoryDatabaseConnection conn = db.getDbConnection(this.excludeArchiveData(query), this.getSessionContext())) {
   BIHistory h = conn.getHistory(id);
   BPermissions p = this.getPermissionsFor(h);
   if (!p.hasOperatorRead()) { h = null; }
   ...
   if (h == null) { resp.add("success", false); resp.add("error", "History not found: " + id); circuit.writeMessage(resp); return; }
   ... // only reached when h != null: RecordOutput streams the actual record data
}
```
`[CERT]` (`organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:978-1064`, whole
method) — again via `this.getPermissionsFor(h)` → `((BIProtected)h).getPermissions(this.getSessionContext())`,
the same real-session mechanism. The metadata-listing handlers a client would call before this (`listDevices`,
`listHistories`, `getHistory`) gate identically, each filtering its response list with the same
`getPermissionsFor(...).hasOperatorRead()` check before including an entry `[CERT]`
(`organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:279-296,347-372,510-537`).

**Verdict: B107-G1 CLOSED, with a correction to [Block 107] §107.3.** The nav-folder-visibility gate is
**not** a no-op and **not** merely discovery-only-with-a-downstream-re-check — it was never actually
fail-open to begin with, because the specific `getPermissions(null)` call sites §107.3 flagged all resolve
through an override that ignores the `null` and substitutes a real, server-verified, per-session permission
check. The leaf content-serving path (`timeQuery`/`getHistory`) enforces the identical real check
independently, a second time, via `BFoxChannel.getSessionContext()`. §107.3's own characterization —
"EVERY history root-folder/device-folder gets added to the folder cache and nav-advertised over fox,
irrespective of whether the connecting user has any real operator-read grant" — is **incorrect** for these
three call sites specifically (it remains an accurate description of the GENERIC `cx==null → BPermissions.all`
shape [Block 99] §99.2 documented for other, non-fox-proxy contexts, which this session did not re-examine).
**No fix is needed**: this is a correctly-designed indirection (delegate to the remote session's own
answer), not a defect — the `null` argument is inert by construction, not a security gap.

## 112.2 — B107-G2 ADVANCED, not closed: two further mechanical shapes (non-standard wrapper-method-name family; no-arg `getPermissions()`/`canRead()`/`canWrite()`/`canInvoke()` overload family) both come back negative — zero additional fail-open sites found — but the genuine caller/callee-split shape remains non-mechanical, confirmed for a fourth time `[CERT]`

**Gap text (verbatim, [Block 107] §107.x, itself reusing [Block 91] §91.x's **B91-G1**):** *"A semantic
caller/callee-split trace (a `Context` resolved or obtained in one method, then passed ... into a DIFFERENT
method's permission check) and a non-standard-wrapper-method-name census, neither of which ... mechanical
literal-argument grep could reach."*

**Wrapper-method-name census.** A corpus-wide grep for method declarations named after common
permission-check-wrapper idioms (`checkPermission`/`checkRead`/`checkWrite`/`checkAccess`/`hasAccess`/
`hasPermission`/`hasReadAccess`/`hasWriteAccess`/`verifyPermission`/`isAuthorized`/`canAccess`, returning
`boolean` or `BPermissions`) finds exactly **3 hits**, all read in full `[CERT]` (`grep -rnE` over
`organized --include=*.java`, this session): `NeqlUtil.hasPermission(Entity, Context)` and
`BFormat.hasPermission(BComplex, Slot, Context)` both take a real `Context` parameter and propagate it
directly into `((BIProtected)x).getPermissions(context)` — no drop, no null substitution `[CERT]`
(`organized/neql/vineflower/com/tridium/neql/NeqlUtil.java:289-290`; `organized/baja/vineflower/niagara/
util/BFormat.java:360-364`). `NiagaraPermissionOrientHook.hasPermission(ODocument, BPermissions)` takes NO
`Context` at all — but derives its answer from `this.user` (an instance field of the already-connected
database-hook object, set at connection time), with an explicit `this.user != null && this.user != INDEX_USER`
guard, falling to `true` ONLY for the special system `INDEX_USER` case — a deliberate internal-system-user
bypass, not a null-Context fail-open `[CERT]` (`organized/orientSystemDb/vineflower/com/tridium/systemDb/
orient/NiagaraPermissionOrientHook.java:155-166`). **Zero of the 3 reproduce the fail-open shape.**

**No-arg `getPermissions()`/`canRead()`/`canWrite()`/`canInvoke()` overload census.** A corpus-wide grep for
zero-argument overloads of these four names — a shape where a caller could invoke a permission check
WITHOUT any `null` literal visible at its own call site, because a DIFFERENT method supplies the default —
finds **5 hits**, all read `[CERT]`: `FoxDbSpec.getPermissions()`/`BNiagaraDiscoveredFileInfo.getPermissions()`
are plain stored-field getters (data-holder classes), not permission-computation wrappers — not the shape
`[CERT]` (`organized/orion/vineflower/com/tridium/orion/priv/fox/FoxDbSpec.java:36-37`;
`organized/niagaraDriver/vineflower/com/tridium/nd/file/BNiagaraDiscoveredFileInfo.java:104-106`).
`OrdTarget.canRead()`/`canWrite()`/`canInvoke()` (no-arg) each delegate to `st.canRead(this)`/etc., passing
the OrdTarget itself (which already carries a real, previously-resolved permissions-for-target value, not a
null Context) `[CERT]` (`organized/baja/vineflower/niagara/naming/OrdTarget.java:283-295`). **Zero of the 5
reproduce the fail-open shape either.**

**Verdict: B107-G2 ADVANCED, not closed.** This session's two additional mechanical censuses are exhaustive
for their own narrow shapes and both come back clean (no new fail-open instances), which is itself useful
negative evidence — but neither shape IS the caller/callee-split [Block 91]'s own **B91-G1** text names (a
`Context` resolved in method A, silently dropped when method A calls a DIFFERENT method B that performs the
actual check). That shape requires genuine cross-method/cross-class call-graph tracing or a semantic
definition of "acts as a permission-check wrapper" — exactly the framing [Block 91]/[Block 99]/[Block 107]
already gave it, independently reconfirmed by this session's own two negative mechanical attempts. Left
exactly as open as [Block 107] left it.

## 112.3 — B109-G1 CLOSED, with a refinement beyond both [Block 98] and [Block 61]: N4-4.15.3.28's REAL `com.tridium.saml.rp.Response` (extracted fresh from the actual `saml-rt.jar`, never before opened) calls the identical 4-arg `Util.validateSignNode` wrapper N5 uses, with no `secureValidation`/`SecurityManager` enablement anywhere in either class — but the SAML SP's actual XML-DSig engine is Apache Santuario's OWN standalone library (bundled inside the jar), not the JDK's `javax.xml.crypto.dsig` [Block 98] examined, and Santuario's OWN `secureValidation` mode (confirmed enabled) still does not restrict SHA-1 `[CERT]` + `[CERT-a]` + `[CERT-hw]`

**Gap text (verbatim, [Block 109] §109.x):** *"Re-run [Block 98] §98.1's own SHA-1/`jdk.xml.dsig.
secureValidationPolicy` gate analysis against N4-4.15.3.28's ACTUAL, currently-shipped SAML SP class,
`com.onelogin.saml2.util.Util` inside `saml-rt.jar` ... instead of the old `com.onelogin.saml.Utils` [Block
98] §98.1 actually read — does N4-4.15.3.28's real SAML consumer enable `setProperty("org.jcp.xml.dsig.
secureValidation", TRUE)` (or run under an active `SecurityManager`) anywhere in its own call chain?"*

**Step 1 — the real N4 caller class, never previously opened, is extracted fresh from the actual PowerB
jar and confirms the identical call shape N5 uses.** `unzip -p .../saml-rt.jar com/tridium/saml/rp/
Response.class` (sha256 `b02af88b119f2dcaca1c6087a1f44bd719ee2eb08514b6f5a63a23064e691525`) — this is
DIFFERENT from (and newer than) the OLD `com.onelogin.saml.Utils`-importing `Response.java` already
decompiled in the sibling `niagara-research` N4 corpus (which imports `com.onelogin.saml.Utils`, confirmed
by a fresh `grep -n import` this session — that decompiled copy is [Block 62]'s own older baseline, not
this OEM package's actual shipped class) `[CERT-hw]`. `javap -p -c` on the freshly-extracted real
`Response.class`'s `validateSignatures()` method shows the exact same call shape [Block 61] §61.3 disassembled
for N5:

```
invokestatic Method com/onelogin/saml2/util/Util.validateSignNode:
    (Lorg/w3c/dom/Node;Ljava/security/cert/X509Certificate;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Boolean;
```
called twice (response signature, assertion signature), each preceded by `aconst_null; aconst_null` for the
last two `String` arguments — the identical 4-arg-with-two-nulls overload N5's `Response.java:274,278`
calls `[CERT-hw]` (`/tmp/.../scratchpad/b112/response_javap.txt`, this session, method body at bytecode
offsets 238-325). A full `grep`-equivalent scan of this disassembly for `setProperty`/`SecurityManager`/
`secureValidation`/`jcp.xml` returns **zero hits** in `Response.class` itself `[CERT-hw]`. A companion class
in the same jar, `AuthnRequest.class`, DOES call `System.getSecurityManager()`/`SecurityManager.
checkPermission()` — but only to guard a Tridium-authored `SAMLPermission("createAuthnRequest")` check that
is a no-op when no `SecurityManager` is installed (`ifnull`-skips the check) `[CERT-hw]`
(`/tmp/.../scratchpad/b112/authnrequest_javap.txt:118-131`) — unrelated to XML-DSig secure-validation mode,
and does not establish that a `SecurityManager` IS installed (whether N4 stations run under one by default
remains [Block 98]'s own named, out-of-scope **B98-G1**, not re-examined here).

**Step 2 — a fresh disassembly of the already-extracted, sha256-reconfirmed `n4-Util.class` finds zero
`setProperty` calls for `secureValidation` either**, and independently reproduces every shape [Block 61]
§61.3 found for N5's byte-identical copy: the 4-arg `validateSignNode` overload hardcodes `Boolean.FALSE`
for the "reject deprecated" parameter (`iconst_0` at its very first bytecode); `isAlgorithmWhitelisted`
builds the identical 5-URI hardcoded `HashSet` (`dsa-sha1`, `rsa-sha1`, `rsa-sha256`, `rsa-sha384`,
`rsa-sha512`); the class's `static {}` initializer populates the identical 2-member `DEPRECATED_ALGOS` set
(`rsa-sha1`, `dsa-sha1`) `[CERT-hw]` (`/tmp/.../scratchpad/b112/n4_util_javap.txt:1505-1520,1635-1677,
2847-2878`, this session's own fresh `javap -p -c` run against sha256 `54f43814cd66b48fc9a407b8931d9f18
290993822bb924edb8a440ce168f0374`, matching [Block 109] §109.4's own citation for the same file). The
class's own `setProperty` calls are unrelated (`SAXParser.setProperty`/`Validator.setProperty` for XML
parsing hardening; `System.setProperty("org.apache.xml.security.ignoreLineBreaks", "true")` in the static
initializer) `[CERT-hw]`.

**Step 3 — a genuinely new refinement beyond both [Block 98] and [Block 61]: the static initializer's very
next call is `org.apache.xml.security.Init.init()`, and the low-level signature object [Block 61] §61.3
already disassembled (`new XMLSignature(element, "", true)`) is Apache Santuario's OWN standalone
`org.apache.xml.security.signature.XMLSignature` — a completely separate implementation from the JDK's
built-in `javax.xml.crypto.dsig` (JSR-105) API [Block 98] §98.1 examined `jre/lib/security/java.security`'s
`jdk.xml.dsig.secureValidationPolicy` default for.** These are different Java packages with independent
static state and independent config sources: `com.sun.org.apache.xml.internal.security.*` (JDK-internal,
governed by `jdk.xml.dsig.secureValidationPolicy`/`org.jcp.xml.dsig.secureValidation`) vs. `org.apache.xml.
security.*` (real, standalone Apache Santuario, bundled directly inside `saml-rt.jar` as 759 of its own
`.class` files — confirmed by extracting and listing the jar's full contents this session, plus a `pom.
properties` read: `groupId=org.apache.santuario, artifactId=xmlsec, version=3.0.4`) `[CERT-hw]`
(`/tmp/.../scratchpad/b112/allsaml/saml-rt/`, `unzip -p .../saml-rt.jar META-INF/maven/org.apache.santuario/
xmlsec/pom.properties`, this session). **The `jdk.xml.dsig.secureValidationPolicy` mechanism [Block 98]
§98.1 examined is not even in this call path at all** — the literal `true` third argument at `new
XMLSignature(element, "", true)` is Apache Santuario's OWN `secureValidation` constructor parameter, and it
IS explicitly enabled (hardcoded by OneLogin's own library code, not JDK/`SecurityManager`-gated at all).

**Step 4 — decisive check: does Apache Santuario 3.0.4's OWN `secureValidation` mode reject SHA-1?** A
version-matched Maven-Central source read (`org.apache.santuario:xmlsec:3.0.4`, confirmed this session
against the real bundled jar's own `pom.properties` — same version, not independently byte-diffed against
the compiled `.class`, marked `[CERT-a]`) of `SignatureAlgorithm.java`/`Reference.java`/`Manifest.java`/
`XMLSignature.java` shows secureValidation mode's algorithm restriction is **MD5-only, identical in scope to
the JDK's own default list [Block 98] §98.1 quoted**:

```java
// SignatureAlgorithm.java:157
if (secureValidation && (XMLSignature.ALGO_ID_MAC_HMAC_NOT_RECOMMENDED_MD5.equals(algorithmURI) ...
// Reference.java:294
if (secureValidation && MessageDigestAlgorithm.ALGO_ID_DIGEST_NOT_RECOMMENDED_MD5.equals(uri)) ...
```
`[CERT-a]` (`org.apache.santuario_xmlsec-3.0.4/org/apache/xml/security/algorithms/SignatureAlgorithm.java:157`;
`.../signature/Reference.java:294`, this session). `ALGO_ID_SIGNATURE_RSA_SHA1`/`ALGO_ID_SIGNATURE_ECDSA_SHA1`/
`ALGO_ID_MAC_HMAC_SHA1` remain fully-registered, unconditionally-supported algorithm constants throughout
`XMLSignature.java`/`SignatureAlgorithm.java` — secureValidation mode never references any of them as a
disallow condition anywhere in these 4 files `[CERT-a]` (full-file `grep -n "sha1\|SHA1"` on all 4, this
session, no `secureValidation &&` guard co-occurring with any SHA-1 constant).

**Verdict: B109-G1 CLOSED — SHA-1 is accepted, and now for a more solidly-evidenced reason than either
[Block 98] or [Block 61] individually established.** N4-4.15.3.28's real, currently-shipped SAML SP
(`com.tridium.saml.rp.Response` → `com.onelogin.saml2.util.Util`, both freshly extracted from the actual
package this session) never enables the JDK's `javax.xml.crypto.dsig` secure-validation gate [Block 98]
§98.1 examined — but that gate was never the relevant one to begin with, because this call chain uses
Apache Santuario's own standalone engine instead. That engine's OWN `secureValidation` flag IS explicitly
turned on (unconditionally, by OneLogin's library code, not gated behind a `SecurityManager` or any N4/N5
configuration choice) — and even fully enabled, it restricts only MD5-family algorithms, never SHA-1/DSA-
SHA1. The ultimate acceptance of a SHA-1-signed assertion therefore rests entirely on OneLogin's own explicit
`isAlgorithmWhitelisted` 5-URI allowlist ([Block 61] §61.3's own finding, now independently re-confirmed
against the REAL N4 caller, not merely inferred from a byte-identical `Util.class`) — which DOES include
`rsa-sha1`/`dsa-sha1` — not on any secureValidation/SecurityManager gate being off. **This does not change
[Block 61]'s bottom-line severity assessment; it removes an entire alternative hypothesis (that some
un-configured JDK/Santuario secure-validation toggle might independently block SHA-1 if only it were turned
on) — it would not, even if enabled.** **Defensive framing only, per this task's discipline**: no exploit
steps; this is a code-review finding about which of two independent, differently-scoped signature-validation
subsystems the SAML SP actually uses, and confirms neither one's "secure mode" toggle addresses the
SHA-1-acceptance gap [Block 61] §61.3 already recommended fixing at OneLogin's own `isAlgorithmWhitelisted`/
`mustRejectDeprecatedSignatureAlgo` layer — no new recommendation beyond reiterating that fix is the correct
layer (a JDK- or Santuario-level secureValidation toggle would not help even if flipped).

**A genuinely new, orthogonal observation surfaced in the process, not previously flagged anywhere in this
corpus**: N4-4.15.3.28's `saml-rt.jar` bundles `xmlsec-3.0.4`, while N5's `saml.jar` bundles a DIFFERENT,
newer `LIB-INF/xmlsec-4.0.4.jar` `[CERT-hw]` (`unzip -l` on both real jars, this session — N4:
`META-INF/maven/org.apache.santuario/xmlsec/pom.properties` → `version=3.0.4`; N5: `LIB-INF/
xmlsec-4.0.4.jar` present alongside `LIB-INF/java-saml-core-2.9.0.jar`). [Block 109] §109.4's
byte-identical-`Util.class` finding is correct and unaffected (that class doesn't embed Santuario, it only
calls its public API) — but the two platforms do NOT share the identical XML-DSig ENGINE version despite
sharing the identical OneLogin wrapper. Opened below as **B112-G3** (low priority — has N5's newer
`xmlsec-4.0.4` preserved the same MD5-only `secureValidation` scope, or has a newer Santuario release added
a SHA-1 disallow entry that N5 might benefit from but N4 cannot?).

## 112.4 — B109-G2 ADVANCED, not closed: one further first-party `USER_DEFINED_3` usage found corpus-wide (`BRdbms`'s `userName`/`password` display-name-migration marker) — a real static/frozen `@NiagaraProperty` slot carrying the flag, but on a non-`BWidget` class for an unrelated purpose, so it still cannot reach `WebProperty`'s browser-facet-editing path; the true third-party-module-SPI question remains structurally unanswerable from this corpus by construction `[CERT]`

**Gap text (verbatim, [Block 109] §109.x):** *"`WebProperty`'s 'web property' mechanism (`Flags.
USER_DEFINED_3`) is architecturally CAPABLE of exposing a frozen slot's facets to browser-side editing if
any `BWidget` subclass ever statically declares a property with that flag; this session found zero such
declarations in the current 247-module corpus, but did not exhaustively check every third-party module SPI
surface ... `investigable`, low priority — a targeted `grep` for `USER_DEFINED_3` alongside
`@NiagaraProperty` in any module not yet opened would close it outright."*

**A fresh, UN-filtered `grep -rln "USER_DEFINED_3" organized --include="*.java"`** (this session, no
`docSource`-exclusion filter, unlike [Block 109] §109.1's own "3 non-doc hits" framing) returns **6 files**,
one MORE than [Block 109] tallied: `ComponentWriter.java`, `Flags.java` (×2, `docSource`+`vineflower` mirror
of the same constant declaration), `Fw.java` — all 4 already read by [Block 109] — **plus
`organized/docSource/rdb/niagara/rdb/BRdbms.java`**, a genuinely new hit `[CERT]` (grep output, this
session). Confirmed NOT a mirror-duplicate artifact: the sibling `organized/rdb/vineflower/niagara/rdb/
BRdbms.java` (the Vineflower-decompiled copy of the identical class) does **not** contain this text at all
— the decompiler evidently dropped or restructured this specific code path, and only the `docSource` copy
(Tridium's own shipped, non-decompiled source snippet, per [Block 109] §109.2's own `docSource.jar`
discussion) preserves it `[CERT]` (`grep -n USER_DEFINED_3 organized/rdb/vineflower/niagara/rdb/BRdbms.java`
→ no match, this session).

**The new hit IS a real static/frozen `@NiagaraProperty` slot carrying the flag, but for an unrelated
purpose, on a non-widget class:**

```java
@NiagaraProperty(name = "userName", type = "String", defaultValue = "")   // line 92-95
@NiagaraProperty(name = "password", ...)                                  // line 102-...
public abstract class BRdbms extends BDevice implements BILicensed { ...
  private void checkSlotDisplayNames() {
    // Since bajaScript can't detect the override of the getDisplayName() method below, the
    // following startup code will check ... so that bajaScript can pick it up, but only do this
    // once (use the USER_DEFINED_3 flag to indicate that).
    if (!Flags.isUserDefined3(this, userName)) {
      ...
      setFlags(userName, getFlags(userName) | Flags.USER_DEFINED_3);
    }
    if (!Flags.isUserDefined3(this, password)) { ...; setFlags(password, ... | Flags.USER_DEFINED_3); }
  }
```
`[CERT]` (`organized/docSource/rdb/niagara/rdb/BRdbms.java:92-105,624-656`, whole `checkSlotDisplayNames()`
method plus the two cited `@NiagaraProperty` declarations). `userName`/`password` ARE genuine static,
class-level `@NiagaraProperty` slots (used across `rdb.jar`/`rdbHsqlDb.jar`/`rdbMySQL.jar`/
`rdbSqlServer.jar`'s shared RDBMS-connection base class) — but the flag here is an idempotency marker
("have I already pushed an updated display-name into the `BNameMap` for bajaScript's benefit"), unrelated to
`WebProperty.isWebProperty()`'s "is this a web property eligible for browser-metadata-sync" semantics. Two
structural reasons this can never reach `WebProperty`'s exposure path regardless: (1) `BRdbms extends
BDevice`, not `BWidget` — `WebWidgetInterop.browserCalledMetadataChanged()` (the actual browser-to-host
metadata-sync trigger [Block 109] §109.1 traced) only fires against a `BWidget` instance; (2) even if it
did, the flag's PRESENCE alone is all `isWebProperty()` checks per [Block 109]'s own citation — but the
semantic misuse here (an idempotency bit, not an actual "let the browser edit this facet" declaration)
would only matter if some code path actually attempted browser-side facet editing against a `BRdbms`
instance, which none does.

**Verdict: B109-G2 ADVANCED, not closed — for a reason inherent to the question, not merely unfinished
work.** This session's corpus-wide, `docSource`-inclusive sweep is now genuinely exhaustive for the
first-party, 247-N5-module universe (6 of 6 hits read, zero are `BWidget` subclasses, zero exhibit
`WebProperty`'s actual browser-facet-editing semantics) — strengthening [Block 109]'s own negative finding
from "3 hits, all innocuous" to "6 hits (docSource included), all innocuous, one genuinely novel and worth
recording as a documented non-security reuse of the same flag bit." But the gap's own remaining ask — "every
third-party module SPI surface," e.g. a customer/OEM-authored driver never bundled with N5 at all — is
**structurally outside what any grep over `organized/` (a decompile of N5's OWN 247 shipped modules) could
ever answer**, by construction: a third-party module not present in this corpus cannot be found by
searching this corpus, no matter how exhaustively. This is not a "didn't get to it yet" residual but a
permanently open, inherently-unbounded question — left exactly as open as [Block 109] framed it, with the
first-party half now fully closed out.

## 112.x — Corrections to earlier blocks

- **[Block 107] §107.3** — its characterization of `BFoxHistorySpace.java:177,228,248`'s `getPermissions
  (null)` calls as "always evaluates `hasOperatorRead()==true` regardless of the actual remote fox
  requester's real permissions" / "this visibility gate is a no-op" is **corrected by §112.1**: all three
  call sites resolve through `BRootHistoryFolder`'s `space instanceof BFoxHistorySpace` override, which
  ignores the `null` argument and substitutes a real, server-computed, per-session permission check via
  `BHistoryChannel.getPermissionsByOrd`/`getSessionContext()`. §107.3's own generic citation of [Block 99]
  §99.2's `cx==null → BPermissions.all` fail-open shape remains correct as a description of the OTHER
  (non-fox-proxy) branch of the same method — the correction is scoped to these three specific call sites,
  not to [Block 99] §99.2's own finding.

## 112.x — Connections

- **[Block 107]/[Block 99]/[Block 91]** — §112.1 closes **B107-G1** with a correction to §107.3;
  §112.2 advances **B107-G2**, the fourth session across four blocks to independently reconfirm the
  caller/callee-split shape as non-mechanical.
- **[Block 98]/[Block 61]/[Block 109]** — §112.3 closes **B109-G1**, extending [Block 61] §61.3's N5-side
  `isAlgorithmWhitelisted`/`DEPRECATED_ALGOS` finding onto the REAL N4 caller (not merely the byte-identical
  `Util.class` [Block 109] §109.4 already established), and identifies that [Block 98] §98.1's own
  `jdk.xml.dsig.secureValidationPolicy` analysis examines a mechanism this call chain never uses at all —
  Apache Santuario's OWN, separately-versioned, standalone engine is the real one, confirmed still MD5-only
  in its `secureValidation` scope.
- **[Block 109]** — §112.4 advances **B109-G2**, finding one additional first-party `USER_DEFINED_3` site
  (`BRdbms`) beyond [Block 109] §109.1's own 3-hit "non-doc" tally, and sharpens the gap's own remaining
  half into an explicitly out-of-corpus-reach question rather than an unfinished grep.

## 112.x — Child gaps opened

- **B112-G1** (low priority, cosmetic residual of **B107-G1**) — a live two-fox-session capture (a real
  low-privilege user connecting to a real N5/N4 station over fox and requesting a history nav listing)
  confirming `BHistoryChannel.getSessionContext()` genuinely reflects that low-privilege user's OWN
  permissions end-to-end, rather than some ambient/admin context — this session's proof is a full,
  in-context source trace showing the MECHANISM is real, not a live end-to-end packet-level confirmation.
  `requires-execution` (a live two-station or Workbench-to-station fox session with a non-admin test user).
- **B112-G2** (low priority, refines the still-open half of **B91-G1**/**B107-G2**) — the genuine
  caller/callee-split null-Context shape (a `Context` resolved in one method, silently dropped when that
  method calls a DIFFERENT method that performs the actual permission check) remains untraced after FOUR
  independent sessions' worth of mechanical attempts ([Block 91]/[Block 99]/[Block 107]/this block).
  `investigable`, low priority, explicitly non-mechanical per all four blocks' own framing — would need
  either full call-graph tooling or a narrower, precisely-defined semantic pattern to grep for.
- **B112-G3** (low priority, new — surfaced by §112.3's own version-diff finding) — N4-4.15.3.28 bundles
  Apache Santuario `xmlsec-3.0.4`; N5 5.0.0.28 bundles a newer, DIFFERENT `xmlsec-4.0.4` inside `saml.jar`'s
  own `LIB-INF/`. Whether N5's newer engine preserves the same MD5-only `secureValidation` algorithm-
  restriction scope (§112.3's Step 4 finding, confirmed only for 3.0.4), or whether a newer Santuario
  release has added a SHA-1 disallow entry N5 could benefit from (but N4 structurally cannot, being pinned
  to the older 3.0.4), was not checked this session. `investigable` — a fresh Maven-Central version-matched
  source read (or direct decompile) of `LIB-INF/xmlsec-4.0.4.jar`'s own `SignatureAlgorithm.java`/
  `Reference.java`, no live station needed.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `BFoxHistorySpace implements BIFoxProxySpace`, a client-side marker interface with no server-role method | [CERT] | `organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java:58`; `organized/fox/vineflower/com/tridium/fox/sys/BIFoxProxySpace.java` (whole file) |
| 2 | All 3 cited `getPermissions(null)` call sites construct `new BRootHistoryFolder(this, ..., this)`, i.e. `space=this` | [CERT] | `organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java:177-181,225-231,245-251` |
| 3 | `BHistoryFolder`'s constructor stores its first arg verbatim as `this.space` | [CERT] | `organized/history/vineflower/com/tridium/history/BHistoryFolder.java:78-79` |
| 4 | `BRootHistoryFolder.getPermissions(cx)`'s `space instanceof BFoxHistorySpace` branch ignores `cx` and calls `channel().getPermissionsByOrd(...)` instead | [CERT] | `organized/history/vineflower/com/tridium/history/BRootHistoryFolder.java:42-58` |
| 5 | The server-side `getPermissionsByOrd(FoxRequest)` handler resolves the target and calls `getPermissions(this.getSessionContext())`, a real per-session Context | [CERT] | `organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:1945-1965` |
| 6 | `BFoxChannel.getSessionContext()` delegates to `getServerConnection().getSessionContext()`; `getPermissionsFor()` uses the same | [CERT] | `organized/fox/vineflower/com/tridium/fox/sys/BFoxChannel.java:325-337` |
| 7 | The leaf record-content path `BHistoryChannel.timeQuery(FoxCircuit)` independently re-checks `getPermissionsFor(h).hasOperatorRead()` before streaming any record data | [CERT] | `organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:978-1064` |
| 8 | Wrapper-method-name census: 3 hits, all propagate a real Context/user, zero fail-open | [CERT] | `organized/neql/vineflower/com/tridium/neql/NeqlUtil.java:289-290`; `organized/baja/vineflower/niagara/util/BFormat.java:360-364`; `organized/orientSystemDb/vineflower/com/tridium/systemDb/orient/NiagaraPermissionOrientHook.java:155-166` |
| 9 | No-arg `getPermissions()`/`canRead()`/`canWrite()`/`canInvoke()` overload census: 5 hits, zero fail-open | [CERT] | `organized/orion/vineflower/com/tridium/orion/priv/fox/FoxDbSpec.java:36-37`; `organized/niagaraDriver/vineflower/com/tridium/nd/file/BNiagaraDiscoveredFileInfo.java:104-106`; `organized/baja/vineflower/niagara/naming/OrdTarget.java:283-295` |
| 10 | The REAL PowerB `saml-rt.jar`'s `com/tridium/saml/rp/Response.class` (freshly extracted, sha256 `b02af88b...`) calls `Util.validateSignNode` with 2 trailing `aconst_null` args, identical to N5's shape | [CERT-hw] | `/tmp/.../scratchpad/b112/response_javap.txt` (offsets 238-325), this session |
| 11 | `n4-Util.class` (sha256 `54f43814...`, matching [Block 109] §109.4) disassembles to the identical `isAlgorithmWhitelisted`/`DEPRECATED_ALGOS`/hardcoded-`Boolean.FALSE` shape [Block 61] §61.3 found for N5 | [CERT-hw] | `/tmp/.../scratchpad/b112/n4_util_javap.txt:1505-1520,1635-1677,2847-2878` |
| 12 | `saml-rt.jar` bundles Apache Santuario `xmlsec` version 3.0.4 as 759 of its own `.class` files (`org/apache/xml/security/**`, `org/apache/jcp/xml/dsig/internal/dom/**`) | [CERT-hw] | `unzip -p .../saml-rt.jar META-INF/maven/org.apache.santuario/xmlsec/pom.properties`, this session; file count via `unzip -l` |
| 13 | Apache Santuario 3.0.4's `secureValidation` mode restricts only MD5-family algorithms; SHA-1/DSA-SHA1 constants are never guarded by a `secureValidation &&` check in `SignatureAlgorithm.java`/`Reference.java`/`Manifest.java`/`XMLSignature.java` | [CERT-a] | `org.apache.santuario_xmlsec-3.0.4/org/apache/xml/security/algorithms/SignatureAlgorithm.java:157`; `.../signature/Reference.java:294`; version-matched against the real jar's own `pom.properties` (claim 12) |
| 14 | N5's `saml.jar` bundles a DIFFERENT, newer `LIB-INF/xmlsec-4.0.4.jar`, not the N4-side 3.0.4 | [CERT-hw] | `unzip -l /mnt/c/ProgramData/Niagara/.../saml.jar`, this session |
| 15 | A fresh corpus-wide `USER_DEFINED_3` grep (docSource included) finds 6 files, one new beyond [Block 109]'s 3-hit tally: `organized/docSource/rdb/niagara/rdb/BRdbms.java` | [CERT] | `grep -rln "USER_DEFINED_3" organized --include="*.java"`, this session |
| 16 | The `vineflower`-decompiled sibling `BRdbms.java` does NOT contain the same text — the `docSource` copy is not a mirror duplicate here | [CERT] | `organized/rdb/vineflower/niagara/rdb/BRdbms.java` (grep returns no match), this session |
| 17 | `BRdbms`'s `userName`/`password` are genuine static `@NiagaraProperty`-declared slots; `checkSlotDisplayNames()` sets `USER_DEFINED_3` on them as a one-time display-name-migration idempotency marker, unrelated to `WebProperty` semantics; `BRdbms extends BDevice`, not `BWidget` | [CERT] | `organized/docSource/rdb/niagara/rdb/BRdbms.java:92-105,164-166,624-656` |

**Tally**: 12 `[CERT]` + 4 `[CERT-hw]` + 1 `[CERT-a]` = 17 `[CERT]`-family claims · 0 `[INFER]` used as a
load-bearing claim marker (the "structurally out-of-reach" framing in §112.4 and the non-mechanical
reconfirmation in §112.2 are hedged prose built directly on the `[CERT]` claims above them, not
independently marker-tagged deductions). [INFER]/[CERT*] ratio: 0.

**Artifacts**: `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/
scratchpad/b112/` — `extracted/` (`Response.class` sha256 `b02af88b119f2dcaca1c6087a1f44bd719ee2eb08514b6f
5a63a23064e691525`, `AuthnRequest.class` sha256 `de618f2c191b36d4ca989d290e4a8600ab8f96265a428c7d27af45852
c294259`, `IdPResponse.class`, `SAMLIdPAuthnRequestServlet.class`, all freshly pulled from the real
`saml-rt.jar` this session) + `response_javap.txt`/`authnrequest_javap.txt` (their disassembly);
`utilclass/com/onelogin/saml2/util/Util.class` (re-copy of [Block 109]'s own `n4-Util.class`, sha256
`54f43814cd66b48fc9a407b8931d9f18290993822bb924edb8a440ce168f0374`, reconfirmed) + `n4_util_javap.txt`;
`allsaml/{saml-rt,saml-wb,saml-ux,samlEncryption-rt}/` (all 4 real N4 SAML jars' `.class` files, extracted
for the Santuario-bundling census); `n5-saml-core.jar` (N5's own nested `LIB-INF/java-saml-core-2.9.0.jar`,
extracted for the xmlsec-version comparison, claim 14).
