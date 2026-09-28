# Upstream-sources report (T22 third-party half)

For third-party jars that are byte-identical (or vendor-resigned-only-different) to Maven Central, the original upstream `-sources.jar` is the most faithful representation of the code -- more faithful than any decompile. Source: `evidence/b117/maven-repo1.json` ([Block 117] "Third-party library identity against Maven Central").

Total third-party jars: 204 (matches evidence/b117's 204: 193 occurrences of 187 distinct upstream artifacts + 11 unidentified).

**Coverage over ALL third-party classes: 26915 of 48868 classes (55.1%) have a byte-adjacent original upstream source.** Denominator = every class in every third-party jar in this corpus (identified + still-unidentified), not only artifacts with a fetched sources jar; numerator excludes vendor-modified artifacts (same coordinate on Central, different bytes -- their "source" is for a different build, not ground truth for these classes). See T26a.

## Fetch status counts

| status | count |
|---|---|
| fetched | 187 |
| no-sources-published | 0 |
| checksum-mismatch | 0 |
| network-error | 0 |

## Class coverage by original upstream source

35508 of 41797 third-party classes (85.0%) in artifacts with a fetched sources jar have a matching top-level class name in that sources jar (class-name-set comparison, not a full compile).

Artifacts under 50% common-class coverage (own-source jar exists, but many binary classes have no same-path .java match in it -- typically Kotlin (.kt, not counted here) or a shaded/relocated dependency bundle):

| artifact | version | common/binary_total |
|---|---|---|
| kotlin-stdlib | 2.3.0 | 0/687 |
| kotlin-stdlib | 2.4.10 | 0/699 |
| kotlin-stdlib-jdk7 | 2.4.10 | 0/1 |
| kotlin-stdlib-jdk8 | 2.4.10 | 0/1 |
| okhttp-jvm | 5.5.0 | 0/181 |
| okio-jvm | 3.18.1 | 0/86 |
| jackson-module-kotlin | 2.22.0 | 3/70 |
| kotlin-reflect | 2.1.21 | 95/856 |
| woodstox-core | 7.2.0 | 178/717 |

## Paho mqttv3 1.2.5 (rebuilt-by-vendor)

Status: `rebuilt-by-vendor`.
Class set identical to upstream: True.
No method-signature diffs in 5 sampled classes (same public API, different build/bytes; B117's 2021-vs-2020 timestamp finding stands).

## Recompile cross-check (real javac 25 against the binary jar's own classpath)

- lz4-java 1.11.2 `net/jpountz/lz4/AbstractLZ4JNIFastResetCompressor` (--release 7): javac-failed -- error: release version 7 not supported
- lz4-java 1.11.2 `net/jpountz/lz4/LZ4BlockInputStream` (--release 7): javac-failed -- error: release version 7 not supported
- jackson-annotations 2.22 `com/fasterxml/jackson/annotation/JacksonAnnotation` (--release 8): MATCH
- jackson-annotations 2.22 `com/fasterxml/jackson/annotation/JacksonAnnotationValue` (--release 8): MATCH
- jackson-core 2.22.0 `com/fasterxml/jackson/core/Base64Variant` (--release 8): MISMATCH
- jackson-core 2.22.0 `com/fasterxml/jackson/core/Base64Variants` (--release 8): MATCH

## SHA-1 identification of pom-less jars (T26a)

For the jars evidence/b117 could not identify from pom.properties, this step hashes the exact shipped bytes (from the local jar mirror) and looks the SHA-1 up on Maven Central; on a miss, one filename-derived g:a:v guess is tried and accepted only if Central's own published binary-jar SHA-1 for that guess matches.

| outcome | count |
|---|---|
| identified-by-sha1 | 9 |
| vendor-modified | 24 |
| not-on-central | 11 |
| network-error | 0 |
| mirror-unavailable | 0 |

Vendor-modified: Central has the same groupId:artifactId:version, but with different bytes -- the fetched sources jar (if any) is for that different build, not ground truth for the shipped class files. Class-name overlap % is how much of the local jar's class set the same-coordinate upstream binary still shares.

| artifact | version | overlap % | local sha1 | central sha1 |
|---|---|---|---|---|
| asm | 9.10.1 | 100.0% | 360d8f9fc733d7003c152487e9b55bbe3a5ac32f | ada2141c0cc52ee8f5c48cd5fa4ce0e794f22236 |
| asm-analysis | 9.10.1 | 100.0% | f1d33ba6147ac7fa72c11288546423a26f301654 | 8d49f14d51f632cb1d87c88d1ceaf50db0d8af1b |
| asm-commons | 9.10.1 | 100.0% | 9ede26538ee8acb66daa6687cb548373bdfccf35 | 4229e4c55fd8e01c23f9fe9884075cc628aacc50 |
| asm-tree | 9.10.1 | 100.0% | 3380a0e926483b24eb26c9b103f61cf9905de055 | e244332a17564c1d1572449399a842de35881be2 |
| asm-util | 9.10.1 | 100.0% | 1da8b65e70ce5a1d44db6d01bfa330686e392806 | 7bb9d450e8d4cbf9f9e04096c44bbfe7fba80b15 |
| bc-fips | 2.1.2 | 100.0% | a7a8809caa1d6cbd142220d7376231c3850bd7ec | 061fbe8383f70489dda95a11a2a4739eb818ff2c |
| bcpkix-fips | 2.1.12 | 100.0% | ba73035c3108c65f3f561b344f4a1c8bc1214f2b | 9617cb32c55d8abba1929f5a228a63686106a388 |
| bcpkix-jdk18on | 1.85 | 100.0% | 9b0d47e9aaaded918f919bf1d47f57bac8963685 | b33d047adc6801a1cfc8ffe1634b23b306a670c1 |
| bcprov-jdk18on | 1.85.2 | 100.0% | 993ca5d60997653b2959b47a57d783daf09c1e21 | aeb3dac02f799ed4783d5ed5900513339880727f |
| bctls-fips | 2.1.24 | 100.0% | aa4e3d10a5a0b8cc02ace1ee442c3c853a1d695a | 91f6d18adf4e3c81ab5487485d1a5545d991f7bd |
| bctls-jdk18on | 1.85 | 100.0% | 672141926083ed3e9e98cff99f24e677759c149b | 97da3e2c93c0ce8b29eddf5012f6734c447dc7dc |
| bcutil-fips | 2.1.7 | 100.0% | 51a1c70b39499cbf4951b4a3be6270ba239f3536 | c6b5c948e154766f1c4df54e0e2359537c43358a |
| bcutil-jdk18on | 1.85 | 100.0% | 59159d3677ae413928903e0a34fc6d4786cb7193 | c41082d6f61628919b675970563f5615e4427c9f |
| jna | 5.19.1 | 100.0% | 44b9f6b6bd8a935bdc09dca094bba4d26afd5ec4 | ca303052cd617c1af2e2c8d344c98a706fb63143 |
| jna-platform | 5.19.1 | 100.0% | 39effdb4dec249ade65a223302f3b63527fb994a | d1e54d9231da5ca3fa730d52960deaa555475468 |
| kotlin-stdlib | 2.4.10 | 100.0% | e2dc611c57737994c1aeb11d8c3103072096b69c | 8943c84ddc6d5cc00a10dbc3736c397066eeaab5 |
| kotlin-stdlib-jdk7 | 2.4.10 | 100.0% | 3d4eb23a79f57a389bbc62d2bb9c0f97b71aa879 | 1a2328fa30364b3e20416f466f05ea9e5dc95ee8 |
| kotlin-stdlib-jdk8 | 2.4.10 | 100.0% | 7b6198198531361812c836c3f954e3bdeb9c7591 | 9502a89455064a43ac526d15d132a57bedfd8d8e |
| libthrift | 0.24.0 | 100.0% | d96a013d425cc45db95072fdf409cc3ee42663e6 | c33207007e07e60c8ee6dfa1b1680d99816f11cc |
| okhttp | 5.5.0 | 0.0% | 6392147b3cf7d7e1778bdb9b64b547ca474c83c9 | eb39f0d8a8bb9d0ad292551b830d662fea547d90 |
| okhttp-jvm | 5.5.0 | 100.0% | b5d5e1a1ceec6b9e2cc1d9873d69fd74aa9ad342 | cefe1eb26408176d30511420b7e36b065e38bca0 |
| okio-jvm | 3.18.1 | 100.0% | c1cbd747acb1a6a6afe98c3a8d69f417975f7203 | a3a8128bb3a0157d23ecc18c17e8330d9c0ac96c |
| resilience4j-core | 2.4.0 | 100.0% | 95c0dba5f15ce7990c47c2d45df8698f630935e3 | 917315545f2ae0221ef3d6c27337b9ba6cba2702 |
| resilience4j-retry | 2.4.0 | 100.0% | e56d7de3ba710ecec5d7cf7db6b7f40e04fbb645 | 7072ed9351dc3a38a7c5a4a1ca21d3355e1f6453 |

## Unidentified jars (no coordinates guessed)

11 jars, by reason: not-on-central:guessed-coordinate-404=1, not-on-central:known-proprietary-or-unpublished=10

| kind | name | reason |
|---|---|---|
| LIB-INF | gx.jar!LIB-INF/org.eclipse.swt.win32.win32.x86_64-3.134.0.jar | not-on-central:known-proprietary-or-unpublished |
| LIB-INF | gx.jar!LIB-INF/xml-apis-ext-1.3.05.jar | not-on-central:guessed-coordinate-404 |
| LIB-INF | opcUaCore.jar!LIB-INF/prosys-opc-ua-sdk-client-server-5.7.0-248.jar | not-on-central:known-proprietary-or-unpublished |
| LIB-INF | snmpLibs.jar!LIB-INF/mibble-mibs-2.10.1.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/bcfips/bc-bcfkswrapprov-1.0.0.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/jxbrowser/jxbrowser-9.5.0.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/jxbrowser/jxbrowser-javafx-9.5.0.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/jxbrowser/jxbrowser-swing-9.5.0.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/jxbrowser/jxbrowser-swt-9.5.0.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/jxbrowser/jxbrowser-win64-9.5.0.jar | not-on-central:known-proprietary-or-unpublished |
| bin/ext | bin/ext/system/jffi-1.4.0-native.jar | not-on-central:known-proprietary-or-unpublished |

