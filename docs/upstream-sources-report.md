# Upstream-sources report (T22 third-party half)

For third-party jars that are byte-identical (or vendor-resigned-only-different) to Maven Central, the original upstream `-sources.jar` is the most faithful representation of the code -- more faithful than any decompile. Source: `evidence/b117/maven-repo1.json` ([Block 117] "Third-party library identity against Maven Central").

Total third-party jars: 204 (matches evidence/b117's 204: 194 occurrences of 188 distinct upstream artifacts + 10 unidentified).

**Coverage over ALL third-party classes: 52436 of 60314 classes (86.9%) have a byte-adjacent original upstream source.** Denominator = every class in every third-party jar in this corpus (identified + still-unidentified), not only artifacts with a fetched sources jar; numerator excludes vendor-modified artifacts (same coordinate on Central, different bytes -- their "source" is for a different build, not ground truth for these classes). See T26a. This number is NOT the same thing as `tools/n5-best-source.py`'s `by_best_kind.upstream` count and the two are not expected to match: this one counts, per DISTINCT third-party artifact, whether a class name has a same-path proven-identical `.java` in its fetched sources jar; n5-best-source.py counts per-population (module, `_bin-ext`/`_etc-m2`/`_lib` jar, or raw LIB-INF copy) -- the same physical class can recur across several populations (e.g. the same third-party jar bundled, undecompiled, inside more than one module), so its `upstream` count can exceed the distinct-class count here.

## Fetch status counts

| status | count |
|---|---|
| fetched | 188 |
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

For the jars evidence/b117 could not identify from pom.properties, this step hashes the exact shipped bytes (from the local jar mirror) and looks the SHA-1 up on Maven Central; on a miss, one filename-derived g:a:v guess is tried and accepted only if Central's own published binary-jar SHA-1 for that guess matches. A whole-jar SHA-1 mismatch then gets a full per-.class re-check (see the section below) before being called vendor-modified.

| outcome | count |
|---|---|
| identified-by-sha1 | 9 |
| resigned-identical | 23 |
| partially-modified | 0 |
| vendor-modified | 0 |
| no-classes | 2 |
| unverifiable | 0 |
| not-on-central | 10 |
| network-error | 0 |
| mirror-unavailable | 0 |

## Pom-identified artifacts re-check (orchestrator review follow-up)

The original 154 pom.properties-identified artifacts were only ever proven identical to Central by their SOURCES jar's own SHA-1. `sha1-exact` -- evidence/b117's own whole-jar SHA-1 match, the strongest possible proof, carried through as-is with no further check -- covers most of them. For the rest (evidence/b117 shows the whole shipped BINARY jar's SHA-1 differs from Central's), this reuses b117's own non-META-INF content check where it already found `identical-non-META-INF` (no network), and does a live per-.class check (same method as T26a) otherwise (b117's own download failures, real content differences, and jars this tool's own candidate-version corrections resolved after a `not-on-central` whole-jar lookup). Every check runs PER OCCURRENCE (an artifact can ship as more than one physical jar, e.g. a LIB-INF copy and an etc/m2 copy, which are not always the same bytes): `mixed` means the occurrences disagree and the verdict was deliberately NOT collapsed to the best one -- see manifest.json's occurrences[].content_identity for the individual verdicts. `unverified` means no evidence/b117 record was found at all.

| outcome | count |
|---|---|
| sha1-exact | 78 |
| reused-resigned-identical | 64 |
| resigned-identical | 11 |
| partially-modified | 0 |
| vendor-modified | 1 |
| no-classes | 0 |
| unverifiable | 0 |
| unverified | 0 |
| mixed | 0 |

## Class-content identity re-check (per-.class SHA-256 vs Central)

A whole-jar SHA-1 mismatch alone does not mean Central's sources aren't ground truth -- Niagara commonly re-signs a jar (adds META-INF/NIAGARA4.SF + .RSA) without touching a single class. This compares every `.class` entry's SHA-256 against Central's own binary jar for the same groupId:artifactId:version -- against the CLASSIFIER binary (e.g. `-jdk11`, `-native`) when the local jar's own filename carries one, never the classifier-less one. `no-classes` = the local jar has zero `.class` entries at all (e.g. a pure-native JNI jar), nothing to compare; `resigned-identical` = every class matches (sources ARE ground truth for this jar); `partially-modified` = only some classes match (only those are covered, the rest still need decompile); `vendor-modified` = the jar HAS classes but none matched; `unverifiable` = Central's own binary jar could not be fetched to compare against.

| artifact | version | classifier | status | identical | different | local-only | source |
|---|---|---|---|---|---|---|---|
| jffi | 1.4.0 | native | no-classes | 0 | 0 | 0 | live-recheck |
| okhttp | 5.5.0 | - | no-classes | 0 | 0 | 0 | live-recheck |
| angus-activation | 2.0.3 | - | resigned-identical | - | - | - | b117-reused |
| annotations | 13.0 | - | resigned-identical | - | - | - | per-occurrence-aggregate |
| asm | 9.10.1 | - | resigned-identical | 39 | 0 | 0 | live-recheck |
| asm-analysis | 9.10.1 | - | resigned-identical | 15 | 0 | 0 | live-recheck |
| asm-commons | 9.10.1 | - | resigned-identical | 28 | 0 | 0 | live-recheck |
| asm-tree | 9.10.1 | - | resigned-identical | 39 | 0 | 0 | live-recheck |
| asm-util | 9.10.1 | - | resigned-identical | 28 | 0 | 0 | live-recheck |
| bc-fips | 2.1.2 | - | resigned-identical | 6784 | 0 | 0 | live-recheck |
| bcpkix-fips | 2.1.12 | - | resigned-identical | 857 | 0 | 0 | live-recheck |
| bcpkix-jdk18on | 1.85 | - | resigned-identical | 1029 | 0 | 0 | live-recheck |
| bcprov-jdk18on | 1.85.2 | - | resigned-identical | 7163 | 0 | 0 | live-recheck |
| bctls-fips | 2.1.24 | - | resigned-identical | 1000 | 0 | 0 | live-recheck |
| bctls-jdk18on | 1.85 | - | resigned-identical | 1013 | 0 | 0 | live-recheck |
| bcutil-fips | 2.1.7 | - | resigned-identical | 639 | 0 | 0 | live-recheck |
| bcutil-jdk18on | 1.85 | - | resigned-identical | 618 | 0 | 0 | live-recheck |
| byte-buddy | 1.18.12 | - | resigned-identical | - | - | - | b117-reused |
| commons-codec | 1.22.1 | - | resigned-identical | - | - | - | b117-reused |
| commons-lang3 | 3.20.0 | - | resigned-identical | - | - | - | b117-reused |
| commons-logging | 1.4.0 | - | resigned-identical | - | - | - | b117-reused |
| concurrentlinkedhashmap-lru | 1.4.2 | - | resigned-identical | - | - | - | b117-reused |
| encoder | 1.4.0 | - | resigned-identical | - | - | - | b117-reused |
| httpclient5 | 5.6.4 | - | resigned-identical | - | - | - | b117-reused |
| httpcore5 | 5.4.3 | - | resigned-identical | - | - | - | b117-reused |
| httpcore5-h2 | 5.4.3 | - | resigned-identical | - | - | - | b117-reused |
| istack-commons-runtime | 4.2.0 | - | resigned-identical | - | - | - | b117-reused |
| jakarta.activation-api | 2.1.4 | - | resigned-identical | - | - | - | per-occurrence-aggregate |
| jakarta.annotation-api | 3.0.0 | - | resigned-identical | - | - | - | b117-reused |
| jakarta.el-api | 6.0.1 | - | resigned-identical | - | - | - | b117-reused |
| jakarta.enterprise.cdi-api | 4.1.0 | - | resigned-identical | - | - | - | b117-reused |
| jakarta.enterprise.lang-model | 4.1.0 | - | resigned-identical | 26 | 0 | 0 | live-recheck |
| jakarta.inject-api | 2.0.1 | - | resigned-identical | 7 | 0 | 0 | live-recheck |
| jakarta.interceptor-api | 2.2.0 | - | resigned-identical | 11 | 0 | 0 | live-recheck |
| jakarta.servlet-api | 6.1.0 | - | resigned-identical | 85 | 0 | 0 | live-recheck |
| jakarta.transaction-api | 2.0.1 | - | resigned-identical | 20 | 0 | 0 | live-recheck |
| jakarta.xml.bind-api | 4.0.5 | - | resigned-identical | - | - | - | per-occurrence-aggregate |
| jaxb-core | 4.0.9 | - | resigned-identical | - | - | - | b117-reused |
| jaxb-runtime | 4.0.9 | - | resigned-identical | - | - | - | b117-reused |
| jetty-alpn-client | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-annotations | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-client | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-compression-common | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-compression-gzip | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-compression-server | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-deploy | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee-webapp | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-annotations | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-plus | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-servlet | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-servlets | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-webapp | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-websocket-jetty-server | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-ee11-websocket-servlet | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-http | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-io | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-jmx | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-jndi | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-plus | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-security | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-server | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-session | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-util | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-core-client | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-core-common | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-core-server | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-jetty-api | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-jetty-client | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-jetty-common | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-websocket-jetty-server | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jetty-xml | 12.1.13 | - | resigned-identical | - | - | - | b117-reused |
| jffi | 1.4.0 | - | resigned-identical | - | - | - | b117-reused |
| jna | 5.19.1 | - | resigned-identical | 125 | 0 | 0 | live-recheck |
| jna-platform | 5.19.1 | - | resigned-identical | 1333 | 0 | 0 | live-recheck |
| jnr-a64asm | 1.0.0 | - | resigned-identical | - | - | - | b117-reused |
| jnr-constants | 0.11.0 | - | resigned-identical | - | - | - | b117-reused |
| jnr-ffi | 2.3.1 | - | resigned-identical | - | - | - | b117-reused |
| jnr-posix | 3.2.2 | - | resigned-identical | - | - | - | b117-reused |
| jnr-x86asm | 1.0.2 | - | resigned-identical | - | - | - | b117-reused |
| jose4j | 0.9.6 | - | resigned-identical | - | - | - | b117-reused |
| json | 20260814 | - | resigned-identical | - | - | - | b117-reused |
| kotlin-reflect | 2.1.21 | - | resigned-identical | 1965 | 0 | 0 | live-recheck |
| kotlin-stdlib | 2.4.10 | - | resigned-identical | 990 | 0 | 0 | live-recheck |
| kotlin-stdlib-jdk7 | 2.4.10 | - | resigned-identical | 1 | 0 | 0 | live-recheck |
| kotlin-stdlib-jdk8 | 2.4.10 | - | resigned-identical | 1 | 0 | 0 | live-recheck |
| libthrift | 0.24.0 | - | resigned-identical | 262 | 0 | 0 | live-recheck |
| lz4-java | 1.11.2 | - | resigned-identical | - | - | - | b117-reused |
| mssql-jdbc | 13.4.0 | - | resigned-identical | 458 | 0 | 0 | live-recheck |
| oauth2-oidc-sdk | 11.26 | jdk11 | resigned-identical | 533 | 0 | 0 | live-recheck |
| okhttp-jvm | 5.5.0 | - | resigned-identical | 384 | 0 | 0 | live-recheck |
| okio-jvm | 3.18.1 | - | resigned-identical | 121 | 0 | 0 | live-recheck |
| orientdb-client | 3.2.55 | - | resigned-identical | - | - | - | b117-reused |
| orientdb-core | 3.2.55 | - | resigned-identical | - | - | - | b117-reused |
| orientdb-server | 3.2.55 | - | resigned-identical | - | - | - | b117-reused |
| orientdb-tools | 3.2.55 | - | resigned-identical | - | - | - | b117-reused |
| resilience4j-core | 2.4.0 | - | resigned-identical | 77 | 0 | 0 | live-recheck |
| resilience4j-retry | 2.4.0 | - | resigned-identical | 31 | 0 | 0 | live-recheck |
| slf4j-api | 2.0.18 | - | resigned-identical | - | - | - | b117-reused |
| slf4j-jdk14 | 2.0.18 | - | resigned-identical | - | - | - | b117-reused |
| txw2 | 4.0.9 | - | resigned-identical | - | - | - | b117-reused |
| FastInfoset | 2.1.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| SparseBitSet | 1.3 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| accessors-smart | 2.6.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-anim | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-awt-util | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-bridge | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-constants | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-css | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-dom | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-ext | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-gvt | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-i18n | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-parser | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-script | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-svg-dom | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-transcoder | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-util | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| batik-xml | 1.19 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| biweekly | 0.6.8 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-codec | 1.18.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-collections4 | 4.5.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-compress | 1.28.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-dbcp2 | 2.14.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-io | 2.22.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-math3 | 3.6.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| commons-pool2 | 2.13.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| content-type | 2.3 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| core | 3.5.4 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| curvesapi | 1.08 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| error_prone_annotations | 2.48.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| gmbal | 4.1.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| gmbal-api-only | 4.1.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| gson | 2.14.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| ha-api | 3.1.13 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jackson-annotations | 2.22 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jackson-core | 2.22.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jackson-core | 2.22.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jackson-databind | 2.22.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jackson-databind | 2.22.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jackson-module-kotlin | 2.22.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jakarta.authentication-api | 3.1.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jakarta.mail | 2.0.5 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jakarta.transaction-api | 1.3.3 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jakarta.xml.soap-api | 3.0.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jakarta.xml.ws-api | 4.0.3 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| java-saml-core | 2.9.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| javaparser-core | 3.28.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jcip-annotations | 1.0-1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jjwt-api | 0.13.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jjwt-impl | 0.13.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| jjwt-jackson | 0.13.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| joda-time | 2.14.3 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| json-smart | 2.6.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| lang-tag | 1.7 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| log4j-api | 2.24.3 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| management-api | 3.3.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| mimepull | 1.11.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| nimbus-jose-jwt | 10.0.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| pfl-basic | 5.1.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| pfl-dynamic | 5.1.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| pfl-tf | 5.1.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| policy | 4.0.5 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| proton-j | 0.34.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| qpid-proton-j-extensions | 1.2.7 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| rt | 4.0.5 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| rt-fi | 4.0.5 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| saaj-impl | 3.0.6 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| slf4j-api | 1.7.36 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| stax-ex | 2.1.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| stax2-api | 4.3.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| streambuffer | 2.1.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| velocity-engine-core | 2.4.1 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| vinnie | 2.0.2 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| woodstox-core | 7.2.0 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| wsit-api | 4.0.7 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| wsit-impl | 4.0.7 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| xmlgraphics-commons | 2.11 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| xmlsec | 4.0.4 | - | sha1-exact | - | - | - | evidence/b117/maven-repo1.json |
| org.eclipse.paho.client.mqttv3 | 1.2.5 | - | vendor-modified | 0 | 110 | 0 | live-recheck |

Classifier builds (Maven's `<artifact>-<version>-<classifier>.jar` convention): the SOURCES jar Maven publishes is shared across all classifiers of the same artifact+version (no separate `-sources.jar` per classifier), so the fetched sources for these jars come from the shared, classifier-less sources jar:

- **jffi 1.4.0** classifier `native` (no-classes)
- **oauth2-oidc-sdk 11.26** classifier `jdk11` (resigned-identical)

Per-jar detail (differing/local-only classes, and any non-class entry that differs -- typically an added signature file):

- **asm 9.10.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **asm-analysis 9.10.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **asm-commons 9.10.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **asm-tree 9.10.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **asm-util 9.10.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bc-fips 2.1.2** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bcpkix-fips 2.1.12** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bcpkix-jdk18on 1.85** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bcprov-jdk18on 1.85.2** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bctls-fips 2.1.24** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bctls-jdk18on 1.85** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bcutil-fips 2.1.7** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **bcutil-jdk18on 1.85** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jakarta.enterprise.lang-model 4.1.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jakarta.inject-api 2.0.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jakarta.interceptor-api 2.2.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jakarta.servlet-api 6.1.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jakarta.transaction-api 2.0.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jffi 1.4.0** (no-classes): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jna 5.19.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **jna-platform 5.19.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **kotlin-stdlib 2.4.10** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **kotlin-stdlib-jdk7 2.4.10** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **kotlin-stdlib-jdk8 2.4.10** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **libthrift 0.24.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **okhttp 5.5.0** (no-classes): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **okhttp-jvm 5.5.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **okio-jvm 3.18.1** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **org.eclipse.paho.client.mqttv3 1.2.5** (vendor-modified): different classes: org/eclipse/paho/client/mqttv3/BufferedMessage.class, org/eclipse/paho/client/mqttv3/DisconnectedBufferOptions.class, org/eclipse/paho/client/mqttv3/IMqttActionListener.class, org/eclipse/paho/client/mqttv3/IMqttAsyncClient.class, org/eclipse/paho/client/mqttv3/IMqttClient.class, org/eclipse/paho/client/mqttv3/IMqttDeliveryToken.class, org/eclipse/paho/client/mqttv3/IMqttMessageListener.class, org/eclipse/paho/client/mqttv3/IMqttToken.class; local-only classes: -; differing non-class entries: META-INF/ECLIPSE_.RSA, META-INF/ECLIPSE_.SF, META-INF/MANIFEST.MF, META-INF/maven/org.eclipse.paho/org.eclipse.paho.client.mqttv3/pom.properties
- **resilience4j-core 2.4.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF
- **resilience4j-retry 2.4.0** (resigned-identical): different classes: -; local-only classes: -; differing non-class entries: META-INF/MANIFEST.MF, META-INF/NIAGARA4.RSA, META-INF/NIAGARA4.SF

## Unidentified jars (no coordinates guessed)

10 jars, by reason: not-on-central:guessed-coordinate-404=1, not-on-central:known-proprietary-or-unpublished=9

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

