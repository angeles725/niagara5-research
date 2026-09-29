# evidence/b121 - Kotlin-compiled Tridium jars: census, metadata recovery, Vineflower Kotlin plugin, claim audit

Block 121 (closes B117-G2). Nothing here is decompiled or reconstructed Tridium source: the per-class Kotlin declaration
listings (696 files, 3.1 MB) and the fresh Vineflower trees live in the gitignored `organized/_evidence/b121/`, identified by
sha256 in `kotlin-signatures.sha256` and `trees.sha256`. `sample-signatures.txt` quotes 3 short listings.

## Re-run

    python3 kotlin_census.py > kotlin-census-all.tsv            # all jars, nested jars followed; parses @kotlin.Metadata from the class file
    # tools (kotlin-metadata-jvm 2.4.10, ASM 9.10.1, kotlin-stdlib 2.4.10) - see "Provenance"
    ./run_audit.sh <outdir>                                     # KotlinAudit.java -> summary.tsv classes.tsv residual.tsv top.tsv + kotlin-signatures/
    ./run_vineflower.sh <outroot>                               # Vineflower 1.12.0 with and without its bundled Kotlin plugin
    python3 compare_trees.py > tree-compare.tsv                 # kt vs java vs corpus tree metrics
    python3 kt_plugin_audit.py .                                # kt-plugin-walls.tsv, kt-plugin-decl-agreement.tsv

## Files

| File | What |
|---|---|
| `kotlin_census.py`, `kotlin-census-all.tsv` | 475 jar entries (247 module jars + nested jars, bin/ext, etc/m2, lib, javadoc): classes, Kotlin classes, Tridium-prefix classes, kind histogram, metadata versions |
| `KotlinAudit.java`, `run_audit.sh` | ASM bytecode census + `kotlin.Metadata` decode (kotlin-metadata-jvm) over the 4 Tridium Kotlin jars |
| `summary.tsv` | jar x category: classes-with, occurrences (metadata `meta:*`, bytecode `bc:*`, declarations `decl:*`) |
| `classes.tsv` | one row per Kotlin class: kind, class-file major, declared functions/properties/ctors, JVM methods declared/generated/unexplained |
| `top.tsv` | JVM-method and field classification histograms per jar; top inline functions expanded; top stdlib `*Kt` static calls |
| `residual.tsv` | the JVM methods no rule explains (2) |
| `run_vineflower.sh`, `compare_trees.py`, `tree-compare.tsv` | Vineflower 1.12.0 `--kt-enable=true` vs `--kt-enable=false` vs the corpus `_etc-m2/*/vineflower2` tree |
| `kt_plugin_audit.py`, `kt-plugin-walls.tsv`, `kt-plugin-decl-agreement.tsv`, `kt-plugin-vf-markers.txt` | every method/class the plugin could not decompile; metadata function names vs `fun` names printed |
| `claim-audit.tsv` | B117-G2 audit: 42 claims from 15 blocks, SAFE / SUSPECT / CONTRADICTED / ADVANCED with the check that decided each |
| `kotlin-signatures.sha256`, `trees.sha256`, `sample-signatures.txt` | out-of-git artifact identity and a 3-class sample |

## Provenance (new external artifact, also in sources/SOURCES.md)

- `org.jetbrains.kotlin:kotlin-metadata-jvm:2.4.10` fetched 2026-09-29 from Maven Central
  (`https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-metadata-jvm/2.4.10/`). The jar's SHA-1 equals Central's
  `.sha1` file: `6bbc294143523b1d327772bd3a09d4a18a7ac837`; sha256 of the jar
  `233aaa84ca268e26d6d3a99ce30401e6dc111a7ae10e0a0b4794ce6351d7adc4`. Kept out of git under `organized/_evidence/b121/tools/`.
- ASM 9.10.1 (`asm-9.10.1.jar` sha256 `5e58298c...`, `asm-tree-9.10.1.jar` sha256 `39f76ae8...`) and `kotlin-stdlib-2.4.10.jar`
  (sha256 `555fda60...`) come from the local N5 install `bin/ext`.
- Vineflower 1.12.0 (`tools/decompilers/README.md`, sha256 `1dfcfe97...`) embeds `META-INF/plugins/vineflower-kotlin-0.1.0.jar`
  (sha256 of the embedded jar `56d988c6352685eb796c6b92533d4deb2bc013fb71286c6bd0a8961ccd61b3b0`); `--list-plugins` reports
  `Kotlin (loaded from JarPluginSource) - Detects and decompiles Kotlin class files`.
- Subject jars (install `etc/m2/repository/com/tridium/tools/`): n-plugin-5.0.54.9.2 sha256 `eb9831b6...`, n-conv-plugin-5.0.54.9.2
  `2769afff...`, settings-5.0.9.8.14 `b8672326...`, utils-5.0.7.8.14 `b5f0d6ee...`.
