# Upstream-sources report (T22 third-party half)

For third-party jars that are byte-identical (or vendor-resigned-only-different) to Maven Central, the original upstream `-sources.jar` is the most faithful representation of the code -- more faithful than any decompile. Source: `evidence/b117/maven-repo1.json` ([Block 117] "Third-party library identity against Maven Central").

Total third-party jars: 204 (matches evidence/b117's 204: 160 occurrences of 154 distinct upstream artifacts + 44 unidentified).

## Fetch status counts

| status | count |
|---|---|
| fetched | 154 |
| no-sources-published | 0 |
| checksum-mismatch | 0 |
| network-error | 0 |

## Class coverage by original upstream source

20991 of 22719 third-party classes (92.4%) in artifacts with a fetched sources jar have a matching top-level class name in that sources jar (class-name-set comparison, not a full compile).

Artifacts under 50% common-class coverage (own-source jar exists, but many binary classes have no same-path .java match in it -- typically Kotlin (.kt, not counted here) or a shaded/relocated dependency bundle):

| artifact | version | common/binary_total |
|---|---|---|
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

## Unidentified jars (no coordinates guessed)

44 jars, by reason: no-pom-properties=44

| kind | name | reason |
|---|---|---|
| LIB-INF | apachePoi.jar!LIB-INF/poi-5.5.1.jar | no-pom-properties |
| LIB-INF | apachePoi.jar!LIB-INF/poi-ooxml-5.5.1.jar | no-pom-properties |
| LIB-INF | apachePoi.jar!LIB-INF/poi-ooxml-lite-5.5.1.jar | no-pom-properties |
| LIB-INF | apachePoi.jar!LIB-INF/xmlbeans-5.3.0.jar | no-pom-properties |
| LIB-INF | devkit.jar!LIB-INF/kotlin-stdlib-2.3.0.jar | no-pom-properties |
| LIB-INF | gx.jar!LIB-INF/org.eclipse.swt.win32.win32.x86_64-3.134.0.jar | no-pom-properties |
| LIB-INF | gx.jar!LIB-INF/xml-apis-ext-1.3.05.jar | no-pom-properties |
| LIB-INF | jsonToolkit.jar!LIB-INF/json-path-2.10.0.jar | no-pom-properties |
| LIB-INF | opcUaCore.jar!LIB-INF/prosys-opc-ua-sdk-client-server-5.7.0-248.jar | no-pom-properties |
| LIB-INF | rdbHsqlDb.jar!LIB-INF/hsqldb-2.7.4.jar | no-pom-properties |
| LIB-INF | snmpLibs.jar!LIB-INF/mibble-mibs-2.10.1.jar | no-pom-properties |
| LIB-INF | test.jar!LIB-INF/jcommander-1.83.jar | no-pom-properties |
| LIB-INF | test.jar!LIB-INF/testng-7.12.0.jar | no-pom-properties |
| bin/ext | bin/ext/asm-9.10.1.jar | no-pom-properties |
| bin/ext | bin/ext/asm-commons-9.10.1.jar | no-pom-properties |
| bin/ext | bin/ext/asm-tree-9.10.1.jar | no-pom-properties |
| bin/ext | bin/ext/bcfips/bc-bcfkswrapprov-1.0.0.jar | no-pom-properties |
| bin/ext | bin/ext/bcfips/bc-fips-2.1.2.jar | no-pom-properties |
| bin/ext | bin/ext/bcfips/bcpkix-fips-2.1.12.jar | no-pom-properties |
| bin/ext | bin/ext/bcfips/bctls-fips-2.1.24.jar | no-pom-properties |
| bin/ext | bin/ext/bcfips/bcutil-fips-2.1.7.jar | no-pom-properties |
| bin/ext | bin/ext/bcstd/bcpkix-jdk18on-1.85.jar | no-pom-properties |
| bin/ext | bin/ext/bcstd/bcprov-jdk18on-1.85.2.jar | no-pom-properties |
| bin/ext | bin/ext/bcstd/bctls-jdk18on-1.85.jar | no-pom-properties |
| bin/ext | bin/ext/bcstd/bcutil-jdk18on-1.85.jar | no-pom-properties |
| bin/ext | bin/ext/jxbrowser/jxbrowser-9.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/jxbrowser/jxbrowser-javafx-9.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/jxbrowser/jxbrowser-swing-9.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/jxbrowser/jxbrowser-swt-9.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/jxbrowser/jxbrowser-win64-9.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/kotlin-stdlib-2.4.10.jar | no-pom-properties |
| bin/ext | bin/ext/kotlin-stdlib-jdk7-2.4.10.jar | no-pom-properties |
| bin/ext | bin/ext/kotlin-stdlib-jdk8-2.4.10.jar | no-pom-properties |
| bin/ext | bin/ext/libthrift-0.24.0.jar | no-pom-properties |
| bin/ext | bin/ext/okhttp-5.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/okhttp-jvm-5.5.0.jar | no-pom-properties |
| bin/ext | bin/ext/okio-jvm-3.18.1.jar | no-pom-properties |
| bin/ext | bin/ext/resilience4j-core-2.4.0.jar | no-pom-properties |
| bin/ext | bin/ext/resilience4j-retry-2.4.0.jar | no-pom-properties |
| bin/ext | bin/ext/system/asm-analysis-9.10.1.jar | no-pom-properties |
| bin/ext | bin/ext/system/asm-util-9.10.1.jar | no-pom-properties |
| bin/ext | bin/ext/system/jffi-1.4.0-native.jar | no-pom-properties |
| bin/ext | bin/ext/system/jna-5.19.1.jar | no-pom-properties |
| bin/ext | bin/ext/system/jna-platform-5.19.1.jar | no-pom-properties |

