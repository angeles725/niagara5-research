# Block 83 — Closing box's WebSocket filter ordering and wire-format opcodes, Jetty's MBeanContainer diagnostic scope, and the servlet Context-threading census tail

> Research closing/narrowing four census- and trace-shaped child gaps, plus a blocked note on a fifth.
> Covers: **B78-G1** (box's `jetty-web.xml` contextPath contents + WebSocket-upgrade-filter vs. auth-filter
> ordering); **B78-G4** (box's binary wire-format message opcodes / frame body layout); **B80-G2** (what
> Jetty's `MBeanContainer` publishes on N5 and whether the platform MBean server is remotely reachable);
> **B68-G1** (the 14 previously-uncensused first-party servlets from [Block 68]'s §68.1 census, checked for
> the same dropped-`Context` write pattern). Does **not** cover: a live JMX enumeration against a running,
> `diagnosticsEnabled=true` station (§83.3's scope is source-only); the JSON (non-fragment) box frame's own
> internal message-type structure beyond the `p`/`v`/`id` envelope fields already read (child gap); a second
> re-verification of `BNaServlet`'s alarm-attribution pattern against the primary `alarm` module's own UI ack
> path (child gap).
>
> **Gap-ID drift note (mandatory per assignment instructions):** the task's fifth gap was stated as
> "B82-G4 — `BJettyQoSFilterMigrator` runtime effect on N5 jetty config". The actual `niagara5-block82.md`
> text for **B82-G4** is different: *"§82.3.1's `SLOTS_TO_REMOVE` map-key-scoping finding … was checked
> against [Block 31] §31.1's PUBLISHED PANCCADIA census tables, not against a fresh re-open of `config.bog`'s
> real `file.xml` bytes this session — a direct `grep` for `uxMediaPrefersBrowserPreviewMode`/
> `rememberUserIdCookie` cross-contamination in PANCCADIA's actual `web:WebService`/`workbench:WebBrowserOptions`
> instances would make the 'no observed practical effect' claim `[CERT]` instead of `[INFER]`"* (`niagara5-block82.md:527-532`).
> This block uses the ACTUAL text per the assignment's own drift-check instruction. §83.4 records why even
> the actual gap could not be closed this session.
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (246 module `vineflower/` trees). Method: targeted whole-file/whole-method reads of the specific classes
> named by each parent gap, plus `find organized -name '*.java' -exec grep` for the two corpus-wide negative
> checks in §83.3 and §83.5 (not partial-glob searches, per METHODOLOGY's `find -exec` over shell-glob rule).

## 83.1 — B78-G1 CLOSED: box's `jetty-web.xml` sets contextPath to `/wsbox`; the WebSocket upgrade runs strictly AFTER the same four-filter chain every WAR module gets, never bypassing it `[CERT]`+`[INFER]`

**contextPath.** Box's `WEB-INF/jetty-web.xml` is a 6-line file with exactly ONE directive `[CERT]`:

```xml
<Configure id="webApp" class="org.eclipse.jetty.ee11.webapp.WebAppContext">
  <Set name="contextPath">/wsbox</Set>
</Configure>
```

`organized/box/extracted/WEB-INF/jetty-web.xml:3-5`, whole file read. Box's own `web.xml` declares
**zero `<filter>` elements** — only the `ws` servlet (`com.tridium.box.BoxWebSocketServlet`, mapped `/*`) and
a session listener `[CERT]` `organized/box/extracted/WEB-INF/web.xml:6-17`, whole file read.

**Where the auth filters actually come from.** `BJettyWebServer.addModuleWebAppHandlers()` builds one
`WebAppContext` per module for which `NModuleInfo.isWar()` is true (`Arrays.stream(...).filter(NModuleInfo::isWar)`,
`organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:1232-1233`) — box qualifies, since its jar
carries `WEB-INF/web.xml` (the [Block 68] B27-G4 rule). For every such context it sets a default
`contextPath` of `"/" + moduleName` (`:1245`, i.e. `/box` for box, later overridden by `jetty-web.xml`'s own
`<Set>` when Jetty's standard `WebAppContext` startup parses that descriptor from the module jar — a Jetty
framework behaviour, not decompiled in this corpus, `[INFER]`), then calls
`this.configureNiagaraWebApp(context)` **unconditionally**, for every WAR module context alike (`:1248`).
`configureNiagaraWebApp` is where the auth filter chain is actually wired, in this fixed program order
`[CERT]` `organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:1287-1290`:

```java
context.addFilter(AddSubjectFilter.class, "/*", null);
context.addFilter(TridiumSecurityFilter.class, "/*", null);
context.addFilter(LocaleFilter.class, "/*", null);
context.addFilter(ContextFilter.class, "/*", null);
```

— optionally followed by `DoSFilter` if `getDenialOfServiceSettings().getEnabled()` (`:1291-1306`). None of
this lives in box's own `web.xml`; it is injected identically into EVERY WAR module's `WebAppContext` by the
shared Jetty server bootstrap, which is exactly why box's `web.xml` has no `<filter>` block of its own.

**Ordering vs. the WebSocket upgrade.** `BoxWebSocketServlet extends JettyWebSocketServlet`
(`organized/box/vineflower/com/tridium/box/BoxWebSocketServlet.java:15`) `[CERT]` — Jetty's own public
WebSocket-servlet base class (not decompiled in this corpus; per Jetty's documented `jetty-ee11-websocket-jetty-server`
API contract it is an ordinary `HttpServlet` subclass reached through the same `<servlet-mapping>`/filter-chain
machinery as any other servlet, `[INFER]`, not source-verified here). Because it is mapped through the
standard Jakarta Servlet dispatch, the four filters above run on every request BEFORE `BoxWebSocketServlet`'s
own `service()`/upgrade handling ever executes — the WebSocket-specific gate inside
`BoxWebSocketCreator.createWebSocket()` (`BBoxService.isOperational()` + `getWebSocketAcceptor().isOperational()`
+ HTTPS-policy check, `organized/box/vineflower/com/tridium/box/BoxWebSocketServlet.java:38-46`, already
`[CERT]`'d by [Block 78] §78.2) is a SECOND, additional check performed INSIDE the already-filtered request,
not a substitute for the filter chain and not a bypass of it. **B78-G1 verdict: CLOSED** — contextPath is
`/wsbox` `[CERT]`; the WebSocket upgrade is ordered strictly after `AddSubjectFilter → TridiumSecurityFilter →
LocaleFilter → ContextFilter` `[CERT]`, with the one open link (that `JettyWebSocketServlet` really is a
plain filter-subject `HttpServlet`) resting on Jetty's own well-documented framework contract rather than
decompiled bytecode in this corpus `[INFER]`.

## 83.2 — B78-G4 CLOSED: box's fragmented wire format is a single opcode byte `'F'` (70) followed by 6 `';'`-delimited header fields and a raw payload tail; the plain JSON frame path carries no opcode byte at all `[CERT]`

`BBoxService.handleRequest(InputStream, Writer, BoxOp)` decides which of the two wire encodings it is reading
by peeking exactly one byte `[CERT]` `organized/box/vineflower/com/tridium/box/BBoxService.java:317-325`:

```java
public void handleRequest(InputStream in, Writer writer, BoxOp op) throws Exception {
   in = toMarkableInputStream(in);
   if (peekFirst(in) == 70) {
      this.handleBoxFragment(in, writer, op);
   } else {
      JSONObject obj = new JSONObject(new JSONTokener(new InputStreamReader(in)));
      this.handleBoxFrame(obj, writer, op);
   }
}
```

`70` is `'F'` in ASCII — the **only** transport-level opcode byte in the box protocol; every other frame is
parsed as plain JSON with no leading marker at all. The decode side confirms the exact field layout
`[CERT]` `organized/box/vineflower/com/tridium/box/BBoxService.java:327-346`:

```java
Scanner s = new Scanner(in);
s.useDelimiter(";");
String fragmentMarker = s.next();      // "F"
String boxVersion = s.next();          // e.g. "2.4"
String sessionId = s.next();
long envelopeId = s.nextLong();
int fragmentCount = s.nextInt();
int fragmentIndex = s.nextInt();
boolean unsolicited = "u".equals(s.next());
s.skip(";");
s.useDelimiter("\\A");
byte[] payload = s.next().getBytes(StandardCharsets.UTF_8);   // raw bytes, run to end of stream
```

and the encode side (`BoxEnvelope.toBoxFragmentBytes`) writes the identical field order byte-for-byte
`[CERT]` `organized/box/vineflower/com/tridium/box/mux/BoxEnvelope.java:241-259`:

```java
private byte[] toBoxFragmentBytes(int fragmentCount, int fragmentIndex, byte[] payload) {
   return writeBytes(out -> {
      out.write(70);                                                     // 'F'
      out.write(59);                                                     // ';'
      out.write("2.4".getBytes(StandardCharsets.UTF_8)); out.write(59);  // boxVersion
      out.write(this.serverSessionId.getBytes(StandardCharsets.UTF_8)); out.write(59);
      out.write(String.valueOf(this.envelopeId).getBytes(StandardCharsets.UTF_8)); out.write(59);
      out.write(String.valueOf(fragmentCount).getBytes(StandardCharsets.UTF_8)); out.write(59);
      out.write(String.valueOf(fragmentIndex).getBytes(StandardCharsets.UTF_8)); out.write(59);
      out.write(this.unsolicited ? 117 : 114);                           // 'u' unsolicited / 'r' response
      out.write(59);
      out.write(payload);
   });
}
```

**Full frame body layout, one message = one opcode byte + 6 semicolon-terminated ASCII fields + raw payload
tail:**

| Field | Encoding | Value / meaning |
|---|---|---|
| opcode | 1 byte | `70` = `'F'` — the ONLY box-protocol opcode; anything else means "next byte begins a JSON document" |
| `boxVersion` | ASCII, `;`-terminated | protocol version string, e.g. `"2.4"` |
| `sessionId` | ASCII, `;`-terminated | the box `BServerSession` id |
| `envelopeId` | ASCII decimal, `;`-terminated, parsed as `long` | multi-fragment envelope correlation id |
| `fragmentCount` | ASCII decimal, `;`-terminated, parsed as `int` | total fragments in this envelope |
| `fragmentIndex` | ASCII decimal, `;`-terminated, parsed as `int` | this fragment's 0-based position |
| solicited flag | 1 byte, `;`-terminated | `117`=`'u'` unsolicited (server-pushed), `114`=`'r'` response (solicited) |
| payload | raw bytes to end-of-stream | the actual JSON-array chunk being fragmented |

The plain-JSON path (`handleBoxFrame`) has no wrapper opcode of its own; instead each JSON object in the
request array is stamped with protocol metadata fields **inside** the JSON, confirmed by the response builder
`[CERT]` `organized/box/vineflower/com/tridium/box/mux/BoxEnvelope.java:191-204`: `frame.put("p", "box");
frame.put("v", "2.4"); frame.put("id", serverSessionId);` before `service.handleBoxFrame(frame, writer, this.op)`
is called per array element. **B78-G4 verdict: CLOSED** — there is exactly one transport-level binary opcode
(`'F'`/70, fragment framing), the full 6-field header layout is now named field-by-field with matching
encode/decode citations, and the alternative (non-fragmented) path is confirmed opcode-less at the byte
level, using in-band JSON keys (`p`/`v`/`id`) instead. What remains unexamined is the JSON path's own
message-type/method-dispatch structure beyond these three envelope keys — child gap **B83-G3**.

## 83.3 — B80-G2 CLOSED: Jetty's `MBeanContainer` publication is opt-in (`diagnosticsEnabled=false` by default) onto the JVM's shared platform MBean server; no first-party JMX-remote connector exists anywhere in the corpus, so remote reachability is not a source-confirmable capability `[CERT]`+`[INFER]`

**Wiring.** `BJettyWebServer`'s `MBeanContainer` is created and attached to the Jetty `Server` object ONLY
when diagnostics are on `[CERT]` `organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:561-565`:

```java
if (this.getDiagnosticsEnabled()) {
   MBeanContainer mBeanContainer = new MBeanContainer(ManagementFactory.getPlatformMBeanServer());
   this.jetty.addEventListener(mBeanContainer);
   this.jetty.addBean(mBeanContainer);
}
```

`getDiagnosticsEnabled()` reads the `diagnosticsEnabled` boolean property on `jetty:JettyWebServer`, whose
declared default is **`false`** `[CERT]` `organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:235`
(`@NiagaraProperty(name = "diagnosticsEnabled", type = "boolean", defaultValue = "false")`), getter at `:498-499`.
The SAME flag also gates `initializeJettyStatistics()` (`:761-763`) and the `DiagnosticBenchmarkFilter`
(`:1272-1274`) — diagnostics is a single opt-in switch for a whole cluster of instrumentation, JMX included,
not a JMX-specific setting.

**Target server.** The constructor argument is `ManagementFactory.getPlatformMBeanServer()` — the JVM's own
single shared platform MBean server, the same one any other in-process JMX client (including a future
`-Dcom.sun.management.jmxremote` launch flag) would see `[CERT]` (same citation as above). `MBeanContainer`
is registered BOTH as a `Container`-event listener AND as a managed bean on the Jetty `Server` itself
(`addEventListener` + `addBean`, both `:563-564`) — per Jetty's own documented `MBeanContainer` contract
(class not decompiled in this corpus — Jetty is a third-party dependency, `[INFER]`), attaching it as an
event listener means it auto-publishes an MBean for every Jetty-managed component subsequently added to that
`Server`'s bean graph (connectors, thread pool, session-id manager, and each per-module `WebAppContext`
created later by `addModuleWebAppHandlers()`, box's `/wsbox` context included) — not merely a static
self-registration of the `Server` object alone.

**Remote reachability — corpus-wide negative check.** A search for any first-party JMX-remote exposure
mechanism across the full 246-module tree returns **zero hits** `[CERT]`
(`find organized -name '*.java' -exec grep -l 'JMXConnectorServer\|RMIConnectorServer\|jmxremote\|JMXServiceURL' {} +`,
this session, completed run over the whole corpus). No module constructs an `RMIConnectorServer`/
`JMXConnectorServer`, publishes a `JMXServiceURL`, or references `com.sun.management.jmxremote` system
properties anywhere in Niagara's own Java source. **B80-G2 verdict: CLOSED.** What `MBeanContainer` publishes
is: nothing by default (opt-in, `diagnosticsEnabled=false`), and when enabled, an MBean per Jetty-managed
component (connectors, thread pool, per-module `WebAppContext`s) registered into the JVM's own shared
platform MBean server — the same server every other in-process introspection in [Block 33]'s census already
reads from. Whether that platform server is *remotely* reachable is NOT something this Java-source corpus can
answer either way: it depends entirely on external JVM launch flags (`-Dcom.sun.management.jmxremote.*`),
which live outside any decompiled `.java` file and are therefore out of this corpus's evidentiary reach
`[INFER]` — this is a scope boundary, not an open question the corpus could still resolve.

## 83.4 — B82-G4 (actual text) BLOCKED this session: the PANCCADIA `config.bog` re-read was denied by the sandbox's client-data-handling policy `[CERT]`

Per the header's gap-ID drift note, the real **B82-G4** asks for a fresh `grep` of PANCCADIA's actual
`config.bog` bytes for `uxMediaPrefersBrowserPreviewMode` cross-contamination under `web:WebService` and
`rememberUserIdCookie`/`AppletModuleCachingType`/`WebStartConfig`/`JnlpDownloadPolicy` cross-contamination
under `workbench:WebBrowserOptions`, to upgrade [Block 82] §82.3.1's `[INFER]` "no observed practical effect"
claim to `[CERT]`. The target file was located on this host
(`/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA/config.bog`, confirmed to exist and
to be a standard zip archive by `file(1)`) `[CERT]`, but the attempt to extract and grep it this session was
**denied by the Claude Code sandbox's own PII-data-handling classifier** before any byte of the file was
read `[CERT]` (this session's own tool-denial event, reproducible: the action itself, not its content, was
refused). Per the denial's own instructions this was not retried through another tool, encoding, or route.
**B82-G4 verdict: BLOCKED, not investigable in this sandbox/session** — the check remains exactly as
[Block 82] left it (`[INFER]`, structural finding only); it needs either an explicit, differently-scoped
authorization for this specific client production file, or to be re-run from a session/environment where
that policy does not apply. Recorded as child gap **B83-G4** rather than silently dropped.

## 83.5 — B68-G1 CLOSED: of the 14 previously-uncensused first-party servlets, exactly ONE is a third fully-`Context`-threaded write path (`BObixServer`'s oBIX PUT/POST) and ONE threads `Context` into a manual, non-`ComponentSlotMap` alarm-attribution mechanism (`BNaServlet`'s `UpdateAlarms`); the remaining 12 show zero write signal under the identical §68.4 grep standard `[CERT]`

[Block 68] §68.1's census left 14 files individually unopened: 6 plain-`HttpServlet` files (`QueryServlet`,
`SecurityDashboardServlet`, `WbWebWidgetServlet`, `AnalyticsChartFileServlet`, `AnalyticQueryServlet`,
`SeriesTransformWebChartQueryServlet`) and 8 `BWebServlet` subclasses (`BVelocityServlet`, `BNaServlet`,
`BBoxServlet`, `BSnmpMibServer`, `BObixServer`, `BStationOutputServlet`, `BSoapServlet`, `BClientEnvServlet`).
Every file was grepped this session for the SAME write-signal regex §68.4 used
(`\.set(\|\.invoke(\|\.submit(\|\.add(`) `[CERT]`.

**10 files show zero hits** `[CERT]` (grep run this session against each): `SecurityDashboardServlet.java`,
`AnalyticsChartFileServlet.java`, `AnalyticQueryServlet.java`, `SeriesTransformWebChartQueryServlet.java`,
`BVelocityServlet.java`, `BBoxServlet.java`, `BSnmpMibServer.java`, `BStationOutputServlet.java`,
`BSoapServlet.java`, `BClientEnvServlet.java` — read-only/export endpoints, not audit-relevant, per the same
exclusion rule §68.4 applied to `HierarchyServlet`.

**2 files show hits that resolve to local, non-station collections** — not real write signal, once opened
`[CERT]`: in `organized/history/vineflower/com/tridium/history/servlets/QueryServlet.java:213`, `set.add(...)`
is a local `TreeSet<BComplex>` sort buffer (declared `organized/history/vineflower/com/tridium/history/servlets/QueryServlet.java:195`),
and `organized/history/vineflower/com/tridium/history/servlets/QueryServlet.java:370-383`'s `component.add(...)`
builds a transient, never-mounted `BComponent` purely to shape a JSON query response; in
`organized/bajaux/vineflower/com/tridium/ux/WbWebWidgetServlet.java:381`, `resources.add(build)` is a local
`ArrayList` used to resolve JS build dependencies (whole method
`organized/bajaux/vineflower/com/tridium/ux/WbWebWidgetServlet.java:378-386`). Neither reaches
`BComplex.set`/`BComponent.invoke` on a real station object.

**`BObixServer` — a THIRD confirmed "Yes" case, extending §68.4's table.** `BObixServer.service(WebOp op)`
dispatches HTTP `PUT`/`POST` to `ObixUtils.serviceWrite`/`serviceInvoke`, both called with
`OrdTarget tgt = this.resolve(uri, op)` (`op` is the real authenticated `WebOp` `Context`, per §68.2)
`[CERT]` `organized/obixDriver/vineflower/niagara/obix/driver/BObixServer.java:293,311-320`. Both write
paths thread that resolved identity all the way to the audited call `[CERT]`
`organized/obixDriver/vineflower/com/tridium/obix/util/ObixUtils.java:521-555,483-519`:

- `serviceWrite` (PUT): `parent.set(pary[idx], val, ot.getUser())` (`:547`) — the 3-arg
  `BComplex.set(Property, BValue, Context)` overload (`organized/baja/vineflower/niagara/sys/BComplex.java:400`),
  and `ot.getUser()` type-checks because `BUser implements Context`
  (`organized/baja/vineflower/niagara/user/BUser.java:169`).
- `serviceInvoke` (POST): `ot.getComponent().invoke(a, val, ot)` (`:503`) — the 3-arg
  `BComponent.invoke(Action, BValue, Context)` overload (`organized/baja/vineflower/niagara/sys/BComponent.java:571`),
  and `OrdTarget` itself qualifies as the `Context` argument because `OrdTarget implements Context`
  (`organized/baja/vineflower/niagara/naming/OrdTarget.java:18`), with `ot.getUser()` (`:124`) returning the
  same real user resolved from `op` through the `BasicContext` chain §68.6 already traced.

This is a genuine, fully-threaded audited write — the third such case after [Block 68]'s `NiagaraRpcServlet`
and `BacnetAwsServlet`.

**`BNaServlet`/`UpdateAlarms` — a NEW, third pattern: manual attribution outside `ComponentSlotMap` entirely.**
`BNaServlet`'s alarm-update API method (`case "UpdateAlarms": apiMethod = new UpdateAlarms(map, op);`,
`organized/analytics/vineflower/com/tridiumx/analytics/ws/BNaServlet.java:184-185`) performs a LIVE
permission check using the real context (`BUser user = this.cx.getUser(); user.checkWrite(svc, prop);`,
`organized/analytics/vineflower/com/tridiumx/analytics/ws/UpdateAlarms.java:50-57`) and threads `this.cx`
into `Alarms.ackAlarm(rec, this.cx)` (`:92`), which manually writes the resolved username onto the alarm
record (`rec.setUser(u.getUsername())`, `organized/analytics/vineflower/com/tridiumx/analytics/util/Alarms.java:28-42`)
and persists it via `AlarmDbConnection.update(rec)` / `BAlarmService.ackAlarm(rec)`/`routeAlarm(rec)`
(`organized/analytics/vineflower/com/tridiumx/analytics/util/Alarms.java:122-136`) — none of which is a
`BComplex.set()`/`BComponent.invoke()` call on a `ComponentSlotMap` slot at all (`BAlarmRecord` is a
serializable alarm-database record, not a mounted `BComponent`). This is `Context`-threaded and genuinely
attributed (unlike `UxBuilderServlet`/`BStringServlet`'s silent drops), but through a domain-specific,
hand-rolled mechanism structurally outside [Block 41]'s `AuditEvent`/`@AuditableSpace` machinery — the same
kind of scope boundary §68.5 already found for `FileServlet.doPut`, but here paired with genuine (if
non-standard) attribution rather than none. `[CERT]` all cited lines read this session.

**B68-G1 verdict: CLOSED.** Of the 14 previously-uncensused files: 12 are confirmed read-only/non-audit-relevant
under the identical §68.4 write-signal standard, `BObixServer` is a third fully-audited (`ComponentSlotMap`-level)
write path, and `BNaServlet`/`UpdateAlarms` is a genuinely-attributed write that bypasses `ComponentSlotMap`
via its own alarm-database mechanism. The full §68.1 census (33 files: 23 `HttpServlet` + 10 `BWebServlet`)
is now completely classified between [Block 68] and this block. Whether the SAME manual alarm-attribution
pattern generalizes to the primary `alarm` module's own (non-`analytics`) acknowledgement UI/servlet path is
child gap **B83-G2**.

## 83.x — Connections

- **[Block 78]** — closes **B78-G1** (§83.1) and **B78-G4** (§83.2), both left open by §78.2/§78.1's own
  transport-envelope-only read. No correction to [Block 78]'s own claims, only depth added.
- **[Block 80]** — closes **B80-G2** (§83.3), extending §80.3's JMX-introspection census (which already
  established the `MBeanContainer` citation this block reads in full) with the publish-scope and
  remote-reachability half [Block 80] deferred.
- **[Block 82]** — §83.4 records why the ACTUAL B82-G4 (not the task-supplied, drifted text) stays open;
  [Block 82] §82.3.1's `[INFER]` verdict is unchanged, not upgraded.
- **[Block 68]** — closes **B68-G1** (§83.5), completing the full 33-file first-party servlet census split
  across [Block 68] and this block. §83.5's `BObixServer` finding directly extends §68.4's table with a third
  "Yes" row using the exact same `OrdTarget`/`WebOp`-as-`Context` mechanism §68.2/§68.6 already established.
  §83.5's `BNaServlet` finding is a genuinely new pattern (attributed-but-outside-`ComponentSlotMap`),
  distinct from both §68.4's "audited" and "unaudited by omission" categories, and from §68.5's
  `FileServlet` scope-boundary case (which has no attribution at all).
- **[Block 72]**/**[Block 27]** — §83.1's filter-chain read corroborates, without correcting, [Block 72]'s
  "box is one of three jetty-web.xml-bearing modules" finding and [Block 27]'s `isWar()` census this block's
  `addModuleWebAppHandlers()` citation directly consumes.

## 83.x — Child gaps opened

- **B83-G1** — Whether `MBeanContainer`'s `Container.Listener` registration on the top-level Jetty `Server`
  (§83.3) actually propagates into MBean publication for each per-module `WebAppContext` created LATER by
  `addModuleWebAppHandlers()` (box's `/wsbox` included), or only for beans added directly to `Server` itself
  — needs either Jetty's own (non-decompiled) `MBeanContainer` source or a live JMX enumeration against a
  `diagnosticsEnabled=true` test station; not resolvable from this corpus alone. `investigable-with-live-station`.
- **B83-G2** — Whether the manual, non-`ComponentSlotMap` alarm-attribution pattern found in `analytics`'s
  `BNaServlet`/`UpdateAlarms` (§83.5) is the GENERAL mechanism for all N5 alarm acknowledgement, or specific
  to the `analytics` websocket API — the primary `alarm` module's own UI/servlet-driven ack path was not
  opened this session. `investigable` — files already decompiled in-corpus (`organized/alarm/`).
- **B83-G3** — The plain-JSON (non-`'F'`-fragment) box frame path's own internal message-type/method-dispatch
  structure beyond the `p`/`v`/`id` envelope keys read in §83.2 — `BBoxService.handleBoxFrame`'s full body
  past its `frame.put(...)` header stamping was not read in full this session. `investigable` — same file,
  already decompiled.
- **B83-G4** — Re-attempt the actual B82-G4 check (a fresh `grep` of PANCCADIA's real `config.bog` for
  `uxMediaPrefersBrowserPreviewMode`/`rememberUserIdCookie` cross-contamination, §83.4) in a session/context
  where the sandbox's PII/client-data classifier does not block reading that specific client production file,
  or with an explicit, narrowly-scoped human authorization for it. `blocked-on-authorization`, not
  content-blocked — the file's existence and archive format are already confirmed.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | box `jetty-web.xml` sets `contextPath` to `/wsbox` (whole 6-line file, one directive) | [CERT] | `organized/box/extracted/WEB-INF/jetty-web.xml:3-5` |
| 2 | box `web.xml` declares zero `<filter>` elements (whole 20-line file) | [CERT] | `organized/box/extracted/WEB-INF/web.xml:1-19` |
| 3 | `AddSubjectFilter→TridiumSecurityFilter→LocaleFilter→ContextFilter` added at `/*`, in this order, for EVERY WAR module's `WebAppContext` unconditionally | [CERT] | `organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:1232-1233,1248,1287-1290` |
| 4 | `BoxWebSocketServlet extends JettyWebSocketServlet` (an ordinary filter-subject `HttpServlet`, per Jetty's own contract) | [CERT]+[INFER] | `organized/box/vineflower/com/tridium/box/BoxWebSocketServlet.java:15` (class decl. [CERT]; base-class filter behavior [INFER], Jetty framework not decompiled here) |
| 5 | box's binary opcode is exactly `'F'`/70; anything else parses as JSON with no opcode | [CERT] | `organized/box/vineflower/com/tridium/box/BBoxService.java:317-325` |
| 6 | fragment header field order: version;sessionId;envelopeId;fragmentCount;fragmentIndex;(u\|r);payload, encode+decode match | [CERT] | `organized/box/vineflower/com/tridium/box/mux/BoxEnvelope.java:241-259`; `organized/box/vineflower/com/tridium/box/BBoxService.java:327-346` |
| 7 | JSON frame path stamps `p`/`v`/`id` inside the JSON object instead of a wrapper opcode | [CERT] | `organized/box/vineflower/com/tridium/box/mux/BoxEnvelope.java:191-204` |
| 8 | `MBeanContainer` created/attached only when `diagnosticsEnabled` (default `false`) | [CERT] | `organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:235,498-499,561-565` |
| 9 | `MBeanContainer` targets the JVM's shared `getPlatformMBeanServer()`, not a private server | [CERT] | `organized/jetty/vineflower/com/tridium/jetty/BJettyWebServer.java:562` |
| 10 | zero first-party `JMXConnectorServer`/`RMIConnectorServer`/`jmxremote`/`JMXServiceURL` references corpus-wide | [CERT] | `find organized -name '*.java' -exec grep -l 'JMXConnectorServer\|RMIConnectorServer\|jmxremote\|JMXServiceURL' {} +` → 0 hits, this session |
| 11 | remote JMX reachability depends on external JVM flags outside any decompiled `.java` file | [INFER] | scope-boundary reasoning from claim 10 |
| 12 | PANCCADIA `config.bog` exists on host, is a zip archive; extraction attempt was denied by the sandbox's PII classifier before any byte was read | [CERT] | `file(1)` output this session; tool-denial event this session |
| 13 | 10 of 14 previously-uncensused servlets show zero hits for `\.set(\|\.invoke(\|\.submit(\|\.add(` | [CERT] | grep run this session against each named file |
| 14 | `QueryServlet`/`WbWebWidgetServlet`'s write-signal hits resolve to local, non-station collections | [CERT] | `organized/history/vineflower/com/tridium/history/servlets/QueryServlet.java:370-383`; `organized/bajaux/vineflower/com/tridium/ux/WbWebWidgetServlet.java:378-386` |
| 15 | `BObixServer`'s oBIX PUT/POST threads the real `WebOp`-resolved user/Context into `BComplex.set()`/`BComponent.invoke()`'s 3-arg overloads | [CERT] | `organized/obixDriver/vineflower/niagara/obix/driver/BObixServer.java:293,311-320`; `organized/obixDriver/vineflower/com/tridium/obix/util/ObixUtils.java:521-555,483-519,547,503` |
| 16 | `OrdTarget` and `BUser` both `implements Context`, matching `BComplex.set`/`BComponent.invoke`'s 3-arg parameter type | [CERT] | `organized/baja/vineflower/niagara/naming/OrdTarget.java:18`; `organized/baja/vineflower/niagara/user/BUser.java:169`; `organized/baja/vineflower/niagara/sys/BComplex.java:400`; `organized/baja/vineflower/niagara/sys/BComponent.java:571` |
| 17 | `BNaServlet`/`UpdateAlarms` threads `cx` into a live permission check and `Alarms.ackAlarm`, which writes attribution onto a `BAlarmRecord` OUTSIDE any `BComplex.set()`/`ComponentSlotMap` call | [CERT] | `organized/analytics/vineflower/com/tridiumx/analytics/ws/UpdateAlarms.java:50-57,90-98`; `organized/analytics/vineflower/com/tridiumx/analytics/util/Alarms.java:28-42,122-136` |
| 18 | the task-supplied B82-G4 text does not match `niagara5-block82.md`'s actual B82-G4 text | [CERT] | `niagara5-block82.md:527-532` |

Tally: 16 [CERT], 2 [INFER] (one claim double-marked [CERT]+[INFER]); ratio 2/16 = 0.13. Load-bearing tokens
confirmed present this session via direct `Read`/`grep` output (not recalled): the `jetty-web.xml`/`web.xml`
whole-file contents; `BJettyWebServer.java`'s exact filter-order lines; `BBoxService`/`BoxEnvelope`'s matching
encode/decode byte sequences; `diagnosticsEnabled`'s declared default; the zero-hit JMX-remote corpus search;
the 10 zero-hit servlet greps; `ObixUtils.java:547,503`'s exact `set`/`invoke` call sites; `Context`
implementation declarations on `OrdTarget`/`BUser`; `UpdateAlarms`/`Alarms`'s attribution chain; and
`niagara5-block82.md`'s own B82-G4 text. The corpus-wide JMX-remote-connector negative claim (#10) rests on a
whole-corpus `find -exec grep` that ran to completion, per METHODOLOGY's symmetric-opening rule. Claim #12
(the sandbox denial) is a first-hand event of this session, not a recalled fact.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; the official Jetty framework
behavior cited in claims 4 and 9/11 is `[INFER]` from well-known public API contract, not from an
`niagara_help.py`-sourced Niagara doc (Jetty is a third-party dependency, out of scope for that tool).

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block83.md`. No other file was
modified; `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration is left to the orchestrator's integration
step, per the assignment's own instruction not to touch them from this agent.
