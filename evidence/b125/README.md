# evidence/b125 — Kotlin-plugin wall sites: Java-mode counterpart and its measured fidelity

Gap B121-G1. Scripts and tables only; no decompiled or reconstructed vendor source is committed. Out of git under
`organized/_evidence/b125/`: `java-mode/<jar>/` (Vineflower 1.12.0 `--kt-enable=false`, byte-identical to `organized/_evidence/b121/vf-java/` for all four jars),
`javap/<jar>/<class>.javap.txt` (51 files, `javap -c -p -l -s` of every wall class, 1.7 MB) and `tools-snapshot/` (frozen copies of `tools/n5-fidelity.py` and `tools/n5_canon.py`; sha256 in `tools-snapshot.sha256`).

Order of execution (from this directory, corpus at `/home/cristian/niagara5-research`, override with `N5_CORPUS`):

    ./run_java_mode.sh                          # step 1: Java-mode decompile of the 4 jars (about 30 s)
    python3 wall_sites.py .                     # wall-sites-map.tsv: 67 method walls + 6 class walls -> JVM class/method/descriptor (about 5 min under load)
    python3 grade_sites.py wall-sites-map.tsv java-grades.tsv 4                       # javac recompile + per-method grade (<= 4 javac at once)
    B125_PATCH_UNREP=1 python3 grade_sites.py wall-sites-map.tsv java-grades-patched.tsv 4   # probe: every `<unrepresentable>` placeholder replaced by `null`
    python3 java_body_metrics.py wall-sites-map.tsv java-body-metrics.tsv             # placeholders and constant/call coverage in the Java-mode method text
    python3 plugin_bytecode_dump.py > plugin-bytecode-dump.tsv                        # `// Bytecode:` listing kept inside each plugin wall vs javap
    python3 build_index.py                      # wall-sites.tsv (durable index) + the javap ground-truth files
    python3 claim_audit.py > claim-audit.tsv    # corpus claims that cite wall methods, checked against javap -v

Inputs pinned by sha256: `n-plugin-5.0.54.9.2.jar` eb9831b65465f7f06831f875215ba7b0511aae9572b866ad21135752d6d93356, `n-conv-plugin-5.0.54.9.2.jar` 2769afff5668cde85aee0a75a0af68cbee253c3771488a324c405211aacc98a8,
`settings-5.0.9.8.14.jar` b86723268e2aa691e26daff5c6162c170ff9a5ddce272680f45d5c28aa40d865, `utils-5.0.7.8.14.jar` b5f0d6ee21fb5216169dbe8292338ec6b0494a807f8a7558fbe7a50b3de843f. Recompile classpath: shipped classes of the four jars and of the other `_etc-m2` jars, `kotlin-stdlib-2.3.0`
(sha256 887587c91713250ad52fe14ad9166d042c33835049890e9437f355ffc5a195b1, in `organized/_v2-libcache/`), Gradle 9.2.1 `generated-gradle-jars/gradle-api-9.2.1.jar`
(sha256 b5b2c024e2e46b100995c71430437c4ea9194870b4d90b8795e05876987a5c14) and `groovy-4.0.28.jar`; javac and javap from openjdk 25.

Tables: `wall-sites.tsv` (75 rows, 73 wall ids; the index), `wall-sites-map.tsv` (mapping and failure text), `java-grades.tsv`, `java-grades-patched.tsv`, `java-body-metrics.tsv`, `plugin-bytecode-dump.tsv`, `claim-audit.tsv`.
Method grades (`grade_sites.py`): `exact` (normalized bytecode equal), `equivalent` (width allowlist), `canonical` / `canonical-t2` (n5_canon rules), `anon-name-only`, `mismatch`, `missing`, `no-compile`.
