# Block 120 — Pattern-switch decompile fidelity: 26 of 27 `typeSwitch` sites render as valid, faithful Java in Vineflower, one site (`PlatformStationManager.createStation`) is pseudo-Java in every tree and now has a bytecode-verified reconstruction

> Research task for gap **B116-G5** ([Block 116] §116.6 census row and child-gap list: "review the 27 `typeSwitch` and 10
> `MatchException` classes' decompiles for A28-style pseudo-Java or wrong guards"). Answers: (1) is the 27/10 census
> reproducible; (2) per site, does each decompiled tree (Vineflower v1 `vineflower/`, v2 `vineflower2/`, conservative
> `vineflower-cons/`, CFR 0.152, Procyon 0.6.0) render the pattern switch as valid Java with the right case order, guards,
> `MatchException` default and record deconstruction; (3) a verified reconstruction where every tree fails. Does **not**
> cover: whether the resugaring failure has a fixable root cause in Vineflower (B120-G2); decompile fidelity of anything
> other than the 49 switch-bearing methods; the `enumSwitch` and `MatchException` sites beyond the fidelity comparison
> (they are included because they share the census scope, not because B116-G5 named them); behaviour of the switches at
> run time.
>
> Type: evidence. **Subject version:** Niagara N5 5.0.0.28 (Beta), shipped class files
> `organized/<module>/extracted/` (byte-exact jar contents, [Block 117] §117.1), decompiles `organized/<module>/{vineflower,vineflower2,vineflower-cons}/`.
> Ground truth = `javap -c -p -v` of the shipped class (bootstrap-method arguments = case-label list; order matters) plus the
> normalized-bytecode comparison of a javac 25 (`--release 25 -g`) recompile of each tree's file (`tools/n5-fidelity.py`
> functions imported, not modified). Markers: `[CERT-hw]` = executed this session with the script/output under
> `evidence/b120/`; `[CERT]` = read at a `file:line`; `[INFER]` = derived.
> **Repo hygiene:** the repository is public; no decompiled or reconstructed Tridium source is committed. Reconstructed method
> text, patched trees and CFR/Procyon output live in the gitignored `organized/_evidence/b120/`, identified by sha256 in
> `evidence/b120/artifacts.sha256`; this block quotes at most a few lines per site.
>
> **ALREADY-COVERED check (literal queries, 2026-09-29):** `rg -il "typeSwitch|MatchException" niagara5-block*.md` → [Block 116]
> only (census row + G5), plus [Block 118] and [Block 84] mentions of one pattern switch; `rg -il "BStationCopier|doInvokeAsync"
> niagara5-block*.md` → [Block 71] only (unrelated); `python3 tools/check-coverage.py typeSwitch MatchException` → prior coverage
> in B116 (the gap that opened this block), no per-site answer. `rg -n unnamed niagara5-block116.md` → §116.3 A27 (unnamed `_`
> in for-each/catch/record component), not in a pattern-switch arm.

---

## 120.1 — B116-G5 CLOSED (census): 27 `typeSwitch` sites in 23 classes, 15 `MatchException` methods in 10 classes, 7 `enumSwitch` sites in 7 classes; B116's 27 and 10 are reproduced exactly `[CERT-hw]`

`evidence/b120/census_switch.py` re-derives the counts without reading B116: byte prefilter for the UTF8 constants
`typeSwitch` / `enumSwitch` / `java/lang/MatchException`, then `javap -c -p -v` of every candidate, counting `invokedynamic`
instructions whose `BootstrapMethods` entry is `SwitchBootstraps.typeSwitch|enumSwitch`, and classes whose constant pool holds
a `MatchException` class entry that is instantiated (`new`). Scope is B116's (`organized/*/extracted` + `organized/_bin-ext/*/extracted`,
docSource excluded): **21,751 classes scanned**, the same total as [Block 116] §116.6.

| Feature | This census | B116 §116.6 |
|---|---|---|
| `typeSwitch` indy sites | **27**, in 23 classes, one site per method (27 methods) | 27 |
| `enumSwitch` indy sites | **7**, in 7 classes | 7 |
| classes that `new java/lang/MatchException` | **10**, holding 15 methods | 10 |

Two readings of the numbers matter for later claims: "27" counts **sites (= methods)**, not classes (23 classes; four classes
hold two sites — `EntitlementApi`, `CertUtils`, `IStyle`, `BDistribution` — and `BAbstractButton` and its anonymous `$1` hold one each);
and **no class is in both lists** — the 10 `MatchException` classes contain no `typeSwitch` indy (their switches are
`tableswitch`/`lookupswitch` on an enum ordinal, or record-pattern accessor wrappers). `evidence/b120/matchexc-kinds.tsv`
splits the 15 methods: **13 `exhaustive-default`** (the synthetic default arm of an exhaustive enum switch expression) and **2
`record-deconstruction`** (`WiFiServlet$CcInfo.equals`, `NSSTupleAdvice.compareTo`, where the `MatchException` is built from a caught `Throwable`).
Nine of the 27 `typeSwitch` sites carry javac's **guard restart loop** (a branch after the indy jumping back to it; `evidence/b120/site-labels.tsv`,
`guard_loop=yes`): `sanitizeMessage`, `makeChildOf`, the four `*Writable.getOldValueForPendingActionAuditEvent`, `doInvokeAsync`,
`createStation`, `dumpMenu`. Six sites repeat one label class three times (`Action`×3, `Version`×3): there the guards, not the labels, discriminate.

The same script over the other class roots finds **0** sites: `organized/_lib-inf-3p/*/extracted` (33,713 classes) and `organized/_etc-m2/*/extracted`
(945 classes) contain no `typeSwitch`, `enumSwitch` or `MatchException` (`evidence/b120/census-switch-3p.out`, `census-switch-etcm2.out`;
census over both roots, class-level, all jars). Whole-tree text census of the decompiles (`evidence/b120/tree-pseudo-census.out`): files containing
`typeSwitch<`/`enumSwitch<`/`SwitchBootstraps` — `vineflower/` **1**, `vineflower2/` **1** (both `PlatformStationManager.java`), `vineflower-cons/` **29**.

## 120.2 — Method: bytecode-exact where javac can be made to accept the file, and a stated reason where it cannot `[CERT-hw]`

`evidence/b120/grade_sites.py` groups the 49 switch-bearing methods into 39 top-level units and, for each of five trees, (1) takes the
tree's file (CFR/Procyon are run on the shipped top-level class), (2) recompiles it with javac 25 against the jar-mirror classpath,
(3) compares, per switch-bearing method, the **normalized bytecode** of shipped vs recompiled. [Block 116]'s normalizer drops constant-pool
indices, so the label list would be invisible; the script therefore appends each `SwitchBootstraps` bootstrap argument list to its
`invokedynamic` line before normalizing. Equal normalized code therefore means: same labels in the same order, same restart-index loop and
guards, same default and `MatchException` arm, same everything else in the method (locals renumbered by first use).

Verdict codes: **X** identical normalized bytecode · **S** same labels, same effect sequence (or same effect multiset, arms permuted), different
branch layout · **U** only difference is an extra `checkcast` for an unused binding (§120.6) · **D** effects differ, reviewed by hand (§120.7) ·
**PSEUDO** javac rejects the file and it prints `SwitchBootstraps` pseudo-Java · **NC** javac rejects the file for a reason outside the switch ·
**EMPTY** the decompiler wrote a 0-byte file. Two mechanical helpers stop unrelated defects from hiding a switch verdict, and neither touches a
switch method: an overload-pinning shim for `reference to doPrivileged is ambiguous` (the [Block 116] §116.5 family; applied to 10 of the 39 units)
and `javac --system <Niagara jre>` for the JavaFX imports of `BWbProfile`. Classpath: n5-fidelity's glob does not reach `bin-ext/<subdir>/*.jar`
(bouncycastle), so the script adds them. Caveat that applies to every X/S/U/D: the comparison covers the switch-bearing *method*, not the class.

## 120.3 — Verdicts per tree: v1/v2 render 23 of 27 `typeSwitch` sites as compilable, bytecode-comparable Java; conservative, CFR and Procyon never do `[CERT-hw]`

Counts are methods (`evidence/b120/tally.txt`, from `site-table.tsv`):

| Kind | Tree | X | S | U | D | NC | PSEUDO | EMPTY |
|---|---|---|---|---|---|---|---|---|
| typeSwitch (27) | v1 `vineflower` | 17 | 3 | 2 | 1 | 3 | 1 | – |
| typeSwitch (27) | v2 `vineflower2` | 17 | 3 | 3 | 1 | 2 | 1 | – |
| typeSwitch (27) | cons `vineflower-cons` | – | – | – | – | – | 27 | – |
| typeSwitch (27) | CFR 0.152 | – | – | – | – | – | 27 | – |
| typeSwitch (27) | Procyon 0.6.0 | – | – | – | – | – | 21 | 6 |
| enumSwitch (7) | v1 / v2 | 7 / 7 | – | – | – | – | – | – |
| enumSwitch (7) | cons / CFR / Procyon | – | – | – | – | – | 7 / 7 / – | – / – / 7 |
| MatchException (15) | v1 | 13 | 2 | – | – | – | – | – |
| MatchException (15) | v2 | 14 | 1 | – | – | – | – | – |
| MatchException (15) | cons | – | 13 | – | – | 2 | – | – |
| MatchException (15) | CFR | 10 | 1 | – | – | 4 | – | – |
| MatchException (15) | Procyon | 8 | 1 | – | – | 6 | – | – |

Reading: **(a)** in v1/v2 the pattern switches are real Java: 17 sites round-trip to identical bytecode, and the other differences are branch layout (S), an unused
binding (U) or files javac rejects for reasons outside the switch (NC). **(b)** The conservative tree prints every `typeSwitch`/`enumSwitch` as pseudo-Java by
construction ([Block 118] §118.1: it is the non-resugared, line-mapped view) — 27/27 and 7/7, so a citation from `vineflower-cons/` of a pattern switch is never source. **(c)** CFR 0.152
prints all 34 `typeSwitch`/`enumSwitch` sites as `SwitchBootstraps.typeSwitch("typeSwitch", new Object[]{A.class, …}, sel, n)` (not Java); on the 15 `MatchException` methods it is the best
non-Vineflower tree (10 X). **(d)** Procyon crashes on 10 of the 29 top-level units (`NullPointerException` in `InvokeDynamicRewriter$IndyHelperBuilder.buildEnsureHandleMethod`, `evidence/b120/procyon-npe.txt`), leaving
0-byte files (6 `typeSwitch` methods, all 7 `enumSwitch`), and prints the rest through a fake `ProcyonInvokeDynamicHelper_1.invoke(sel, n)`. **(e)** The exhaustive-enum `MatchException` default is kept by
every tree that compiles: no row lost the default arm, and both record deconstructions survive as record patterns in v1/v2
(`organized/_bin-ext/niagarad/vineflower2/com/tridium/niagarad/servlet/WiFiServlet.java:1275` `o instanceof WiFiServlet.CcInfo(String otherCode, String otherName)`;
`organized/bajaui/vineflower2/com/tridium/ui/theme/custom/nss/query/NSSTupleAdvice.java:28` `o instanceof NSSTupleAdvice(NSSTuple otherTuple, boolean otherInherited)`).
None of the five trees produced a wrong case order, a missing guard or a lost record deconstruction on a comparable row.

## 120.4 — Per-site table (27 `typeSwitch` sites; full 49-row table in `evidence/b120/site-table.tsv`) `[CERT-hw]`

Labels are the shipped `BootstrapMethods` argument list in order (simple names). "best faithful rendering" = the tree/patch whose text is safest to quote.

| # | class · method | labels (BSM order) | guard loop | v1 | v2 | cons | CFR | Procyon | best faithful rendering |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `CertUtils.getPrivateKeyFromObject` | PrivateKeyInfo, PEMKeyPair, PEMEncryptedKeyPair, PKCS8EncryptedPrivateKeyInfo | no | S | S | PSEUDO | PSEUDO | PSEUDO | v2 (layout-only diff) |
| 2 | `CertUtils.signCertificate` | RSAPrivateKey, ECPrivateKey, DSAPrivateKey | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 3 | `CoreCryptoManager.getPublicKeyType` | DSAPublicKey, ECPublicKey, RSAPublicKey | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 4 | `UserLoginHistoryStore$EventThread.serviceEvent` | AddUserLoginEvent, RenameUserLoginEvent, RemoveUserLoginEvent | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 5 | `PermissionFactory.makeNiagaraPermission` | GrantFilePermission, GrantKeyRingPermission, GrantNiagaraBasicPermission, GrantSigningPasswordPermission, GrantKeyStorePermission, … (+2) | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 6 | `EntitlementApi.sanitizeMessage` | publicKey, refreshIncrement, restoreId | yes | X | X | PSEUDO | PSEUDO | EMPTY | v2 (= v1) |
| 7 | `EntitlementApi.sendRequestMessageAndHandleResponse` | HttpStatusException, SocketTimeoutException, NoRouteToHostException, UnknownHostException | no | U | U | PSEUDO | PSEUDO | EMPTY | v2 + `_` (exact) |
| 8 | `Introspector.getModule` | ModuleSetClassLoader, BootstrapClassLoader | no | U | U | PSEUDO | PSEUDO | PSEUDO | v2 + `_` (exact) |
| 9 | `BAbstractButton$1.hasPseudoClass` | active | no | X | X | PSEUDO | PSEUDO | EMPTY | v2 (= v1) |
| 10 | `BAbstractButton.hasPseudoClass` | active | no | X | X | PSEUDO | PSEUDO | EMPTY | v2 (= v1) |
| 11 | `IStyle.toSimple` | Double, Float, Long, Integer, String, … (+2) | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 12 | `IStyle.toStyleValue` | BDouble, BFloat, BLong, BInteger, BString, BBoolean | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 13 | `StylableAdapter.makeChildOf` | HasId, HasClass, HasPseudoClass, HasAttribute, IsTag | yes | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 14 | `BBooleanWritable.getOldValueForPendingActionAuditEvent` | Action, Action, Action | yes | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 15 | `BEnumWritable.getOldValueForPendingActionAuditEvent` | Action, Action, Action | yes | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 16 | `BNumericWritable.getOldValueForPendingActionAuditEvent` | Action, Action, Action | yes | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 17 | `BStringWritable.getOldValueForPendingActionAuditEvent` | Action, Action, Action | yes | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 18 | `EmailUtil.extractContent` | String, InputStream, MimeMultipart | no | S | S | PSEUDO | PSEUDO | PSEUDO | v2 (layout-only diff) |
| 19 | `BBrokerChannel.loadType` | SyntheticEnumType, SyntheticComplexType, SimpleType | no | NC | NC | PSEUDO | PSEUDO | PSEUDO | v2 text; reconstruction effects-equal |
| 20 | `BJettyWebServer.walkContextHandler` | ServletContextHandler, Wrapper, Container | no | NC | NC | PSEUDO | PSEUDO | PSEUDO | reconstruction (exact) |
| 21 | `BStationCopier$WizardCommand.doInvokeAsync` | Version, Version, Version | yes | D | D | PSEUDO | PSEUDO | PSEUDO | v2 (construct verified; enclosing layout differs) |
| 22 | `BDistribution.getEntryDestPath` | niagara_user_home, niagara_config_home, niagara_home | no | S | S | PSEUDO | PSEUDO | EMPTY | v2 (layout-only diff) |
| 23 | `BDistribution.getEntryDestPath` | niagara_user_home, niagara_config_home, niagara_home | no | X | X | PSEUDO | PSEUDO | EMPTY | v2 (= v1) |
| 24 | `PlatformStationManager.createStation` | Version, Version, Version | yes | PSEUDO | PSEUDO | PSEUDO | PSEUDO | PSEUDO | reconstruction (exact) |
| 25 | `BScheduleFE.makeFor` | BCustomSchedule, BScheduleReference, BWeekAndDaySchedule, BDateSchedule, BDateRangeSchedule, … (+6) | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 26 | `TestHelper.toNumber` | Double, Integer, Float, Long, Number | no | X | X | PSEUDO | PSEUDO | PSEUDO | v2 (= v1) |
| 27 | `BWbProfile.dumpMenu` | BSeparator, BSubMenuItem, BMenuItem | yes | NC | U | PSEUDO | PSEUDO | PSEUDO | v2 + `_` (exact) |

`MatchException` methods (13 exhaustive enum/sealed defaults, 2 record deconstructions; cons NC/CFR NC/Procyon NC rows are files javac rejects for causes outside the switch, not switch defects):

| # | class · method | kind | v1 | v2 | cons | CFR | Procyon |
|---|---|---|---|---|---|---|---|
| 1 | `WiFiServlet$CcInfo.equals` | record-deconstruction | S | S | NC | NC | S |
| 2 | `PermissionManager.isPermissionValidForEnvironment` | exhaustive-default | S | X | S | NC | NC |
| 3 | `ModuleManager$NiagaraJPMSAccessModifier.toString` | exhaustive-default | X | X | S | NC | NC |
| 4 | `DstRule.convertJavaMonthToNiagaraMonth` | exhaustive-default | X | X | S | X | NC |
| 5 | `DstRule.convertJavaTimeModeToNiagaraTimeMode` | exhaustive-default | X | X | S | X | NC |
| 6 | `DstRule.convertJavaWeekdayToNiagaraWeekday` | exhaustive-default | X | X | S | X | NC |
| 7 | `AbstractBoxLayoutStrategy.computeCrossLength` | exhaustive-default | X | X | S | X | X |
| 8 | `AbstractBoxLayoutStrategy.computeCrossPosition` | exhaustive-default | X | X | S | X | X |
| 9 | `AbstractLayoutStrategy.isIncludedInLayout` | exhaustive-default | X | X | S | X | X |
| 10 | `FlexBoxLayoutStrategy.computeCrossLength` | exhaustive-default | X | X | S | X | X |
| 11 | `FlexBoxLayoutStrategy.computeCrossPosition` | exhaustive-default | X | X | S | X | X |
| 12 | `NSSTupleAdvice.compareTo` | record-deconstruction | X | X | NC | S | NC |
| 13 | `SignatureDispositionEnum.getDispositionIcon` | exhaustive-default | X | X | S | X | X |
| 14 | `SignatureDispositionEnum.getDispositionMessage` | exhaustive-default | X | X | S | X | X |
| 15 | `SignatureStatusEnum.getStatusIcon` | exhaustive-default | X | X | S | NC | X |

`enumSwitch` sites (included for completeness; the census scope is shared):

| # | class · method | labels | v1 | v2 | cons | CFR | Procyon |
|---|---|---|---|---|---|---|---|
| 1 | `DerivedSelectionResult.invalidate` | PSEUDOCLASSES_CHANGED | X | X | PSEUDO | PSEUDO | EMPTY |
| 2 | `BToggleButton.hasPseudoClass` | CHECKED | X | X | PSEUDO | PSEUDO | EMPTY |
| 3 | `BToggleMenuItem.hasPseudoClass` | CHECKED | X | X | PSEUDO | PSEUDO | EMPTY |
| 4 | `BWidget$DefaultPseudoClassChecker.test` | FOCUS, FIRST_CHILD, HOVER, LAST_CHILD, ACTIVE, … (+3) | X | X | PSEUDO | PSEUDO | EMPTY |
| 5 | `Item.hasPseudoClass` | FIRST_CHILD, LAST_CHILD, ACTIVE | X | X | PSEUDO | PSEUDO | EMPTY |
| 6 | `BLabelPane.hasPseudoClass` | HOVER | X | X | PSEUDO | PSEUDO | EMPTY |
| 7 | `TreeNode.hasPseudoClass` | HOVER, FOCUS | X | X | PSEUDO | PSEUDO | EMPTY |

## 120.5 — The one all-tree failure: `PlatformStationManager.createStation` is pseudo-Java in v1, v2, cons, CFR and Procyon; the reconstruction recompiles to identical bytecode `[CERT-hw]`

Shipped labels: `Version, Version, Version` with the restart loop (guards). Vineflower v1 and v2 (line 69 in both) and cons print `switch (SwitchBootstraps.typeSwitch<"typeSwitch",Version,Version,Version>(pwChars, var14))`
inside `while (true)` with `var14 = 1; continue;` between arms; CFR prints `SwitchBootstraps.typeSwitch("typeSwitch", new Object[]{Version.class, Version.class, Version.class}, (Version)version2, n)`
inside a labelled loop; Procyon prints `ProcyonInvokeDynamicHelper_1.invoke(version, n)`. All five keep the three labels in order and the loop-and-restart structure of the guards — none is source, none
compiles, and CFR and Procyon (not Vineflower) also print the `Objects.requireNonNull(version)` that javac emits for a `switch` without `case null`.
Vineflower's failure is **not** [Block 116]'s A28 trigger: A28 needs a `CONSTANT_Dynamic` primitive label, and the census found 0 condy constants ([Block 116] §116.6); this site is a plain three-`Version` guarded switch, and 26 sibling sites
(including the identical-shape `BStationCopier$WizardCommand.doInvokeAsync`) resugar correctly.

`evidence/b120/reconstruct.py` derives the source from the v2 tree mechanically: the loop and restart variable become one guarded switch, the loop's closing brace goes, and the tail
`if (min N4) {…} throw …` becomes `if (min N4) {checks} else { throw … }` followed by the transfer (bytecode: `goto` over the throw). Head of the result:

```
switch (bogVersion) {
   case Version v when v.compareTo(ValueDocEncoder.BOG_VERSION_5) >= 0 -> { … }
   case Version v when v.equals(ValueDocEncoder.BOG_VERSION_4) -> { … }
   case Version v when v.equals(ValueDocEncoder.BOG_VERSION_1) -> { … }
   default -> throw new IllegalArgumentException("Cannot transfer unknown versioned station: " + bogVersion);
```

Recompiled with javac 25, the **whole `createStation` method has identical normalized bytecode** (labels injected), including the `requireNonNull`, the guard restart loop and the default arm
(`evidence/b120/recon-results.json`; the method text and patched tree are out of git, sha256 in `evidence/b120/artifacts.sha256`). Arrow versus colon form and block braces compile identically, so the reconstruction
is bytecode-equivalent, not a claim about Tridium's exact formatting.

## 120.6 — Unnamed patterns (`case T _`) are real in N5 bytecode and Vineflower renders them as an unused named binding `[CERT-hw]`

Three v2 rows (`EntitlementApi.sendRequestMessageAndHandleResponse`: 3 arms, `Introspector.getModule`: 1 arm, `BWbProfile.dumpMenu`: 1 arm; plus `BBrokerChannel.loadType`) recompile with labels equal and exactly one
difference: the recompiled method has an extra `checkcast` (and `astore`) per arm where the shipped method has none. javac stores a named binding even when unused, so the shipped bytecode can only come from the JEP 456 unnamed
pattern `case T _` (Java 22+). Renaming the binding to `_` in the tree text (`var7`→`_`, `var25`..`var27`→`_`) makes all three methods recompile to **identical** bytecode (`reconstruct.py`), and the vendor original confirms
the form: `organized/docSource/workbench/niagara/workbench/BWbProfile.java:598` `case BSeparator _ -> System.out.println(itemIndent + "---");` (`[CERT]`; the only `case T _` in docSource). The same docSource method uses
`if (…getCommand() instanceof WbCommands.ToolCommand) { continue; }` twice where Vineflower folds them into one `!a && !b` condition (same effects, different layout; the reconstruction with two `continue` ifs is exact).
This extends [Block 116] §116.3 A27 (unnamed `_` for for-each/catch/record component rendered as `varN`) to **switch-arm type patterns**. Consequence for citations: a `var<N>` binding of a pattern arm that is never used in the
arm body is Vineflower's spelling of `_`; the label class and arm body are faithful.

## 120.7 — Files that do not compile for unrelated reasons, and the layout-only rows `[CERT-hw]`

**NC (v1 3, v2 2).** `BBrokerChannel.loadType`, `BJettyWebServer.walkContextHandler` (both trees) and `BWbProfile` (v1 only) are rejected by javac for defects outside the switch: `reference to doPrivileged is ambiguous`,
`X has protected access in Y` (`ModuleSetClassLoader.LoadedModule`, `BWebServer.ServerState`, `ServerConnector.ServerConnectorManager`), `variable defaultValue is already defined` (colon-form arms of an inner string switch
share one scope), `javafx` imports. With those unrelated members patched (import removal, arm-local renames, one unrelated method neutralised; recorded in `reconstruct.py`), `walkContextHandler` recompiles **exact**
(3 labels `ServletContextHandler, Handler$Wrapper, Handler$Container`, `case null`/default kept) and `loadType` compiles with labels equal and identical effect sequence (residual: local-slot allocation, because the original arms had
their own scopes; the `SimpleType` arm is another `case T _`).
**S.** v1 and v2 each have 3 typeSwitch rows (`CertUtils.getPrivateKeyFromObject`, `EmailUtil.extractContent`, `BDistribution.getEntryDestPath(String)`) and 1–2 `MatchException` rows where labels and effect sequence are equal but branch layout
differs (`return` vs `goto` duplication, folded conditions). [INFER] behaviour-equivalent: effect equality is necessary, not sufficient (B120-G1).
**D (v1 and v2).** `BStationCopier$WizardCommand.doInvokeAsync`: labels (`Version`×3) and the guard loop are preserved (the switch arms print as `case Version v when v.compareTo(…) >= 0:` …), but the enclosing method differs: the tree swaps the
`if/else` arms under a negated condition and adds two redundant `return;`, which javac turns into more inlined `finally` copies (9 extra effects). Reading shows an arm swap plus duplicated exits; [INFER] behaviour-preserving,
not proven. It is not a switch defect.

## 120.8 — The pseudo-Java trees keep the label lists exactly; guards are not machine-checked `[CERT-hw]`

`evidence/b120/pseudo_labels.py` parses every printed bootstrap call and compares the label list to the shipped one (simple names, order kept, multiset per class): **cons 29/29** top-level classes, **CFR 29/29**, **Procyon 19/19** non-empty
(10 empty, §120.3) print exactly the shipped labels — including the `String`-constant labels (`"active"`, `"niagara_user_home"…`) and the enum-constant labels of the 7 `enumSwitch` sites. So the wrong-case-order failure mode has **0**
occurrences in any tree. The `when` guards of pseudo-Java are visible only as restart-index assignments (`var14 = 1; continue;`); they were read by eye at `createStation` (all five trees) and are not machine-checked for the other
8 guard-loop sites in cons/CFR/Procyon (B120-G3).

## 120.9 — Claim rules for citing N5 pattern switches `[INFER]`

1. From `vineflower2/` (or `vineflower/`), a pattern-switch arm list, guard, `default`, `case null` and record pattern may be quoted as-is for 26 of 27 `typeSwitch` sites, 7 of 7 `enumSwitch` sites and all 15 `MatchException` methods.
   Cite `javap`/the label list, not the tree, for the sentence "arm N binds a variable": an unused binding is `_`.
2. Never quote a pattern switch from `vineflower-cons/`, CFR or Procyon; they print `SwitchBootstraps` pseudo-Java (34 of 34 `typeSwitch`+`enumSwitch` sites in cons and in CFR; 21 of 34 in Procyon, plus 13 sites in empty files).
3. `PlatformStationManager.createStation` (v1/v2 line 69): quote the reconstruction's three `case Version v when …` heads, or the docSource-equivalent shape; never the `while (true)`/`var14` loop.
4. Before claiming a *Tridium language-feature adoption* from these sites, use the bytecode evidence in §120.1/§120.6 (`typeSwitch` bootstrap, unnamed-pattern `checkcast` absence, docSource `BWbProfile.java:598`), not the decompiled text ([Block 115]).

## 120.10 — Corrections to earlier blocks

No number in [Block 116] is wrong: 27 `typeSwitch` sites and 10 `MatchException` classes are reproduced. Two clarifications for the orchestrator's §14 pointer if it wants one:
[Block 116] §116.6 and G5 say "27 `typeSwitch` … classes": they are 27 sites in 23 classes; and "1 renders as pseudo-Java in the tree" holds for **both** `vineflower/` and `vineflower2/` (the same file), while
`vineflower-cons/` prints 29 files of pseudo-Java by design (§120.1). [Block 116] §116.3 A27 (unnamed `_` renders as `varN`) also applies to pattern-switch arms (§120.6).

## 120.11 — Connections

- [Block 116] §116.6/G5 (the gap); A28 (pseudo-Java trigger, not the trigger at `createStation`); A27 (extended by §120.6); §116.5 `doPrivileged is ambiguous` family (worked around here with a shim, 10 of 39 units).
- [Block 118] §118.1: the conservative tree is pseudo-Java for pattern switches by design; §120.3 measures it (27/27, 7/7); its `BNumericWritable` guarded-switch example is one of the four X rows.
- [Block 115]/[Block 90]: the resugaring rule; the labels-from-bytecode step of §120.2 is what makes a pattern-switch claim checkable.
- [Block 117]: byte-exact `extracted/` trees are the ground truth used here.

## 120.12 — Child gaps opened

- **B120-G1** (medium, investigable read-only) — Promote the layout-only rows to exact: reconstruct the 7 S/D rows in v2 (`CertUtils.getPrivateKeyFromObject`, `EmailUtil.extractContent`, `BDistribution.getEntryDestPath(String)`,
  `WiFiServlet$CcInfo.equals`, `BBrokerChannel.loadType`, `BStationCopier$WizardCommand.doInvokeAsync`, plus `PermissionManager` v1) until the normalized bytecode is identical, and decide whether the `BStationCopier` arm swap and duplicated exits are
  behaviour-preserving. coverage-check: `rg -il "BStationCopier|doInvokeAsync" niagara5-block*.md` → [Block 71] only (unrelated). measured-by: rows exact / 7 (baseline 0 of 7).
- **B120-G2** (medium, requires-execution) — Root cause of Vineflower's resugar failure at `createStation` only: bisect a minimal class (three guarded `Version` arms + `default`, `requireNonNull` selector) with javac 25, run Vineflower 1.12.0 with and
  without `-e` library context and pattern flags, and record which construct defeats it. coverage-check: `rg -il "resugar" niagara5-block*.md` → [Block 90]/[Block 115]/[Block 116] describe the rule and A28, none bisects a non-condy failure.
  measured-by: `typeSwitch` sites still printed as pseudo-Java in v2 of 27 (baseline 1).
- **B120-G3** (low, investigable read-only) — Machine-check the `when` guards of the pseudo-Java trees: count restart-index assignments per site in cons/CFR/Procyon and compare with the shipped guard structure at the 9 guard-loop sites (extend `pseudo_labels.py`).
  coverage-check: `rg -il "restart index|guarded pattern" niagara5-block*.md` → [Block 118] only, as one docSource example. measured-by: guard-loop sites whose pseudo tree has the shipped number of guards, of 9 per tree (baseline: `createStation` read by eye in 5 trees).
- **B120-G4** (low, requires-execution) — Census the Procyon 0.6.0 `NullPointerException` in `InvokeDynamicRewriter` across the whole tree (every class with any `invokedynamic`) so a bake-off claim that counts Procyon output knows the empty-file rate; here 10 of 29
  switch-bearing top-level units are empty. coverage-check: `rg -il procyon niagara5-block*.md docs/decompiler-bakeoff.md` → [Block 13], [Block 25], [Block 90], [Block 98], [Block 116], [Block 117], [Block 118], docs/decompiler-bakeoff.md; none counts empty outputs on indy sites.
  measured-by: 0-byte Procyon files / classes with a non-lambda, non-concat indy site.
- **B120-G5** (low, investigable read-only) — Reconcile class counts of non-N5-module roots: this census read 33,713 classes under `organized/_lib-inf-3p/*/extracted` and 945 under `organized/_etc-m2/*/extracted`; [Block 117] cites 24,896 nested-jar and 958 out-of-pipeline classes. Find whether
  the difference is multi-release/duplicate extraction. coverage-check: `rg -n "24,896|958" niagara5-block117.md` → the B117 figures; no block recounts `extracted/` per root. measured-by: `find … -name '*.class' | wc -l` per root vs B117's figures (baseline 33,713 vs 24,896; 945 vs 958).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 21,751 classes scanned; 27 `typeSwitch` indy sites in 23 classes (27 methods), 7 `enumSwitch` in 7 classes, 10 classes / 15 methods executing `new MatchException`; matches B116 §116.6 | [CERT-hw] | `evidence/b120/census_switch.py`, `evidence/b120/census-switch.out`, `evidence/b120/census-switch.json` |
| 2 | Class-level census of `_lib-inf-3p` (33,713 classes) and `_etc-m2` (945) finds 0 sites | [CERT-hw] | `evidence/b120/census-switch-3p.out`, `evidence/b120/census-switch-etcm2.out` |
| 3 | Label list per site in BSM order; 9 of 27 sites carry the guard restart loop; no class is in both the `typeSwitch` and `MatchException` lists | [CERT-hw] | `evidence/b120/site_labels.py`, `evidence/b120/site-labels.tsv`, `evidence/b120/census-switch.json` |
| 4 | 13 exhaustive-default and 2 record-deconstruction `MatchException` methods | [CERT-hw] | `evidence/b120/matchexc_kinds.py`, `evidence/b120/matchexc-kinds.tsv` |
| 5 | v1 verdicts 17 X · 3 S · 2 U · 1 D · 3 NC · 1 PSEUDO; v2 17 · 3 · 3 · 1 · 2 · 1; cons/CFR 27 PSEUDO; Procyon 21 PSEUDO + 6 EMPTY; enumSwitch 7/7 X in v1/v2 | [CERT-hw] | `evidence/b120/grade_sites.py`, `evidence/b120/grades.json`, `evidence/b120/site_table.py`, `evidence/b120/tally.txt`, `evidence/b120/site-table.tsv` |
| 6 | MatchException 15 methods: v1 13 X/2 S, v2 14 X/1 S, CFR 10 X/1 S/4 NC, Procyon 8 X/1 S/6 NC, cons 13 S/2 NC | [CERT-hw] | `evidence/b120/tally.txt`, `evidence/b120/site-table.tsv` |
| 7 | Whole-tree pseudo-Java files: v1 1, v2 1, cons 29 | [CERT-hw] | `evidence/b120/tree_pseudo_census.sh`, `evidence/b120/tree-pseudo-census.out` |
| 8 | `PlatformStationManager.createStation`: pseudo-Java in all 5 trees; the reconstruction recompiles to identical normalized bytecode (labels injected) | [CERT-hw] | `evidence/b120/recon-results.json`, `evidence/b120/reconstruct.py`, `evidence/b120/grades.json`; method text sha256 in `evidence/b120/artifacts.sha256` (out of git) |
| 9 | Unnamed-pattern arms: extra `checkcast` only in the recompile; `_` rename gives identical bytecode (Entitlement, Introspector, BWbProfile) | [CERT-hw] | `evidence/b120/recon-results.json`, `evidence/b120/grades.json` (`effect_diff`) |
| 10 | Vendor original uses `case BSeparator _` and two `if … continue` | [CERT] | `organized/docSource/workbench/niagara/workbench/BWbProfile.java:598` |
| 11 | Record patterns survive in v2 | [CERT] | `organized/_bin-ext/niagarad/vineflower2/com/tridium/niagarad/servlet/WiFiServlet.java:1275`; `organized/bajaui/vineflower2/com/tridium/ui/theme/custom/nss/query/NSSTupleAdvice.java:28` |
| 12 | Label lists printed by cons 29/29, CFR 29/29, Procyon 19/19 classes equal the shipped lists; 10 Procyon units empty (NPE) | [CERT-hw] | `evidence/b120/pseudo_labels.py`, `evidence/b120/pseudo-labels.tsv`, `evidence/b120/procyon-npe.txt` |
| 13 | `walkContextHandler` reconstruction exact; `loadType` reconstruction effects-equal (slot allocation differs) | [CERT-hw] | `evidence/b120/recon-results.json`, `evidence/b120/recon.out` |
| 14 | `BStationCopier.doInvokeAsync` labels equal, effects differ by 9 (finally copies), arms swapped | [CERT-hw] | `evidence/b120/grades.json` (`effect_diff`, `first_diff`) |
| 15 | S and D rows are behaviour-equivalent | [INFER] | effect-sequence/multiset equality is necessary, not sufficient; B120-G1 |
| 16 | Vineflower failure at `createStation` is not the A28 (condy) trigger | [INFER] | B116 §116.6 condy census = 0; this site has no primitive label; root cause open (B120-G2) |
| 17 | Guards in pseudo-Java trees preserved | [INFER] | read at `createStation` only; B120-G3 |

**Tally:** 11 `[CERT-hw]` · 2 `[CERT]` · 3 `[INFER]` (one row per claim group; the INFERs are the three explicitly gapped ones).

**Artifacts:** `evidence/b120/` (scripts, verdict tables, comparison results, README; 280 KB, no binaries, no decompiled or reconstructed source); out of git under `organized/_evidence/b120/`: reconstructed method
text, patched trees, CFR/Procyon output and `patch-blocks.json`, sha256 in `evidence/b120/artifacts.sha256`. No new `tools/` code (evidence scripts only; no unit tests).
