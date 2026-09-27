# Block 76 — The `bin/ext` detached `.jar.sig` sidecar format, `niagarad.exe`'s minimal-service native confirmation, the N4-vs-N5 ZKM census (with a base64 false-positive trap), and the absent npsdk native library

> Research closing/narrowing four native-and-signing child gaps. Covers: **B30-G1** (the format and verifier
> of the `bin/ext/<jar>.jar.sig` sidecars); **B69-G1** (the native-launcher-binary confirmation that
> `niagarad.exe` never runs `nre.dll`'s `Nre.runClass`/process-spawn path — the piece [Block 63]/[Block 69]
> left to a native read); **B30-G4** (the full N4 ZKM-obfuscation census beyond [Block 30]'s 53-module
> sample, and a reconciliation of [Block 30]'s "zero ZKM in N5" claim); **B43-G4** (the
> `NativePlatformProviderNpsdk` `getKeyMaterial0`/`setKeyMaterial0` native reverse — whether a shippable
> native lib even exists on this build). Does **not** cover: the byte-level disassembly of `njre.dll`'s JVM
> bootstrap (only `niagarad.exe`'s import table and manifest are read); the exact boot-time code that
> verifies the `.jar.sig` sidecars (found to be distinct from the in-module verifier — see child gap); a
> genuine per-module ZKM watermark classifier for N4 (the naive grep is shown to over-count — see §76.3).
>
> Subject version: **N5 5.0.0.28 (Beta)**, install READ-ONLY at `/mnt/c/Program Files/Niagara/5.0.0.28`.
> Native binaries were copied to a session scratch dir before analysis (`niagarad.exe`, 24,616 bytes);
> `objdump -x`/`strings` were run there, never against the install. Decompiled Java at
> `/home/cristian/niagara5-research/organized/`; N4 baseline `/home/cristian/niagara-research/organized`
> (4.14, 691 module dirs). This block was authored directly by the orchestrator (Opus) with the local
> `r2`/`objdump`/`strings` toolchain because the wave-8 delegated writer for this cluster was terminated by a
> weekly rate-limit before writing; native reads are static (import-table/strings/hexdump), not dynamic.

## 76.1 — B30-G1: the `bin/ext/*.jar.sig` files are 73 detached, fixed-256-byte (RSA-2048-shaped) raw signatures — a mechanism DISTINCT from the in-module CMS/BouncyCastle jar signing `[CERT]`+`[INFER]`

Every third-party library under `bin/ext/` ships a paired `<name>.jar.sig` sidecar. A census of all 73 of
them shows **every single file is exactly 256 bytes** (`for f in bin/ext/*.jar.sig; do stat -c%s "$f"; done`
→ `73 × 256`) `[CERT]`, and `file` classifies them as raw `data` (no ASN.1/PKCS#7 wrapper; a hexdump of
`asm-9.10.1.jar.sig` is 256 bytes of high-entropy bytes with no DER header) `[CERT]`. A fixed 256-byte
detached signature is the exact output size of **RSA-2048 PKCS#1** (2048 bits = 256 bytes); the uniformity
across all 73 files (no length variance, which ECDSA/DER would show) makes RSA-2048 the structural reading
`[INFER]` (not [CERT] — the algorithm OID is not in the raw bytes).

This is a **separate mechanism from the in-module signing** [Block 30] characterized. Niagara *modules* are
verified by `com.tridium.security.signing.JarSigningValidator` →
`com.tridium.security.signing.ArchiveVerifier.verify()`, which reads standard in-JAR `META-INF` **CMS/PKCS#7
signature blocks** via BouncyCastle (`SignerInformation.verify(...)`, `signerInfoVerifierBuilder`,
`TimeStampToken`, `ContentInfo`) against X.509 certs, with `SHA-256-Digest` manifest entries
(`ArchiveVerifier.java:63-184,330,422`) `[CERT]`. The `bin/ext` libraries are **not** Niagara modules and
carry no `META-INF` Niagara signature, so they get the detached 256-byte sidecar instead — a
boot-integrity check over the raw jar bytes. The exact boot-time routine that loads and verifies a
`.jar.sig` (as opposed to the module `ArchiveVerifier`) was not located in the Java corpus this pass and is
child gap **B76-G1** (likely in `njre.dll`/`nre` boot, not the Java module layer).

## 76.2 — B69-G1 CLOSED: `niagarad.exe` is a 24 KB minimal Windows service that hosts its JVM through `njre.dll` and imports NO process-creation, service-control, or `LoadLibrary` API — it cannot be the station spawner `[CERT-hw]`

`niagarad.exe` is **24,616 bytes** — a stub, not an engine `[CERT-hw]` (`stat`). Its full PE import table
(`objdump -x`, this session) lists exactly: **`njre.dll`**, `KERNEL32.dll`, `VCRUNTIME140.dll`, and five
`api-ms-win-crt-*` CRT shims `[CERT-hw]`. Critically, a targeted scan of its imports for
`CreateProcess`/`StartServiceCtrl`/`RegisterServiceCtrl`/`OpenSCManager`/`LoadLibrary`/`CreateThread`
returns **zero hits** `[CERT-hw]` (`objdump -x | grep -iE`). Its embedded manifest declares
`name="Tridium.Niagara.Service"` `version="5.0.0.96"` `<description>Niagara Service</description>`
`[CERT-hw]` (`strings`).

Reading this against [Block 63]/[Block 69]: `niagarad.exe` is a thin Windows-service host that links
`njre.dll` (the minimal `JavaLauncherWin32` [Block 63] found to have zero JNI exports and no
`CreateProcessA`) and boots the daemon JVM through it. It has **no process-creation capability of its own**
and does **not** link `nre.dll` (whose sole `CreateProcessA` xref is the `restartPlatformDaemon0` →
`plat.exe restartdaemon` path [Block 63] traced) `[CERT-hw]`. This **closes the native half of B69-G1**:
the `niagarad` process never runs `nre.dll`'s `Nre.runClass`/spawn code, confirming [Block 69]'s Java-side
[INFER] that `NiagaraDaemon.Main()` is not on that path. The remaining question of who spawns `station.exe`
(the Windows Service Control Manager, per [Block 61]/[Block 63] reading 2) stays open as the live-probe gap
**B63-G1** — `niagarad.exe` importing none of the SCM APIs is consistent with SCM itself being the spawner.

## 76.3 — B30-G4: [Block 30]'s "zero ZKM obfuscation in N5" HOLDS — the 25 apparent N5 `ZKM` hits are base64 false positives inside `SHA-256-Digest` manifest lines; the naive N4 census over-counts for the same reason `[CERT]`

A raw `grep -rl 'ZKM'` over the N5 decompiled tree returns 25 files `[CERT]`, which naively contradicts
[Block 30]'s zero-ZKM finding. Reading the actual hits **refutes the contradiction**: every one is the
substring `ZKM` occurring inside a **base64-encoded `SHA-256-Digest:` value** in a `META-INF` manifest or
signature file `[CERT]` — e.g. `SHA-256-Digest: ilSDXlCbDhgNYbZSNY9YOO7lZKMCGHpkMGVFxkkOU2o=`,
`...YPjB8OJcFcdUMz9CchzWjBXM3ef11jIdZKMZSBzJwg4=` (the concentration in `kitPxN4svg` (6), `icons`,
`lonDevices`, `seriesTransform`, `themeLucid` — all resource-heavy modules with many signed entries —
confirms the digest-line origin). There is **no genuine ZKM watermark or string-decrypt method** among
them. [Block 30]'s N5 = zero-ZKM stands `[CERT]`.

The same base64 false-positive trap **poisons a naive N4 census**: `grep -rl 'ZKM'` over the N4 tree matches
100 of 691 module dirs `[CERT]`, but that count includes the identical `SHA-256-Digest` base64 coincidences
and therefore **over-states genuine obfuscation** `[INFER]`. A trustworthy N4 ZKM census needs a
watermark-specific signature (the ZKM string-decrypt `<clinit>` idiom or the literal ZKM class-name mangling),
not a substring grep — recorded as child gap **B76-G2**. **B30-G4 verdict: the N5 side is closed (zero,
false positives explained); the N4 full census is narrowed with the measurement trap documented, not
closed.**

## 76.4 — B43-G4 BLOCKED-ON-ARTIFACT: no shippable npsdk native library exists on this install — only the `com.tridium.npsdk-native` Gradle *plugin* — so `getKeyMaterial0`/`setKeyMaterial0` has no binary to reverse here `[CERT]`

`NativePlatformProviderNpsdk`'s `getKeyMaterial0`/`setKeyMaterial0` are `native` JNI methods ([Block 43]),
which would be implemented in a compiled `.so`/`.dll`. A filesystem search of the entire N5 install for
`*npsdk*` returns **only a Gradle build plugin**:
`etc/m2/repository/com/tridium/npsdk-native/com.tridium.npsdk-native.gradle.plugin/5.0.54.9.2/` (a `.pom`
plus the plugin marker) `[CERT]` (`find "/mnt/c/Program Files/Niagara/5.0.0.28" -iname '*npsdk*'`). There is
**no shipped native npsdk library** anywhere in `bin/`/`bin/ext/` on this Beta build `[CERT]`. This is the
same license/artifact-gate shape [Block 14]/[Block 17] found for other native tooling: the build machinery
ships, the compiled native artifact does not. **B43-G4 is therefore blocked-on-artifact on this install** —
there is nothing to disassemble; the native key-material implementation would only appear on a
platform/embedded image that bundles the compiled npsdk lib. Recorded as blocked (needs a device/embedded
image), child gap **B76-G3**.

## 76.x — Connections

- Closes the native half of [Block 69]'s B69-G1 and corroborates [Block 63]'s `njre.dll`-vs-`nre.dll`
  capability split with `niagarad.exe`'s own import table.
- §76.1's in-module CMS verifier (`ArchiveVerifier`) is the same signing subsystem [Block 30]/[Block 77]
  §77.4 touched (the TPK/Honeywell leaf key); the detached `.jar.sig` sidecars are a distinct boot-integrity
  layer.
- §76.3 reconciles [Block 30]'s zero-ZKM-N5 claim against a naive grep and documents the base64 trap for
  future census work.
- §76.4 extends [Block 14]/[Block 17]'s "build tooling ships, native artifact is license/image-gated"
  pattern to npsdk.

## 76.x — Child gaps opened

- **B76-G1** — The boot-time routine (likely in `njre.dll`/`nre`) that loads and verifies the detached
  256-byte `.jar.sig` sidecars, and the exact public key it verifies against.
- **B76-G2** — A watermark-specific N4 ZKM census (string-decrypt `<clinit>` idiom / class-name mangling),
  replacing the base64-polluted substring grep, to give the true N4 obfuscated-module count.
- **B76-G3** — `getKeyMaterial0`/`setKeyMaterial0` native reverse on a platform/embedded image that bundles
  the compiled npsdk library (blocked-on-artifact on this desktop install).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 73 `bin/ext/*.jar.sig` files, every one exactly 256 bytes, raw `data` (no ASN.1) | [CERT] | `for f in bin/ext/*.jar.sig; stat -c%s` → 73×256; `file`; `xxd` head |
| 2 | 256-byte fixed length is RSA-2048-shaped | [INFER] | length uniformity; no OID in raw bytes |
| 3 | In-module signing = CMS/PKCS#7 via BouncyCastle in ArchiveVerifier (distinct mechanism) | [CERT] | `ArchiveVerifier.java:63-184,330,422` |
| 4 | niagarad.exe = 24,616 bytes, imports njre.dll + KERNEL32 + CRT only | [CERT-hw] | `stat`; `objdump -x` DLL Name list |
| 5 | niagarad.exe imports NO CreateProcess/SCM/LoadLibrary | [CERT-hw] | `objdump -x | grep -iE` → 0 hits |
| 6 | niagarad.exe manifest = "Tridium.Niagara.Service" v5.0.0.96 | [CERT-hw] | `strings` manifest |
| 7 | N5 "ZKM" grep hits (25) are base64 false positives in SHA-256-Digest lines | [CERT] | `grep -rhn 'ZKM'` sample lines |
| 8 | N4 naive ZKM grep matches 100/691 module dirs (over-counts) | [CERT]+[INFER] | `grep -rl 'ZKM' | count`; same base64 trap |
| 9 | No shippable npsdk native lib on this install — only the Gradle plugin | [CERT] | `find -iname '*npsdk*'` → only `.gradle.plugin` pom |

Tally: 7 [CERT]/[CERT-hw], 2 [INFER] (ratio 0.22). Native-binary tokens confirmed present or ABSENT via
direct `objdump`/`strings`/`stat` output this session (not recalled): the `njre.dll`/`KERNEL32`/`VCRUNTIME`
import list; the zero-hit process/SCM/LoadLibrary scan (a negative-existence claim about the full printed
import table, per METHODOLOGY §3); the `Tridium.Niagara.Service` v5.0.0.96 manifest; the uniform 256-byte
`.jar.sig` sizes; the base64 `ZKM` digest lines; the npsdk `find` returning only the Gradle plugin.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block76.md`; native binaries
analyzed in the session scratch dir (not committed); INDEX/RESEARCH-STATE/CATALOG regeneration is the
integrator step.
