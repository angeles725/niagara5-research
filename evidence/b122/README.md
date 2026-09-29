# evidence/b122 - .NET assemblies in xprotect.jar and the ffmpeg.jar JNI surface

Block 122 (closes B117-G4). Nothing here is decompiled or vendor source. The ilspycmd output (14 C# trees, 4,005 files) and the
extracted FFmpeg source files live in the gitignored `organized/_evidence/b122/`; `net-decompile.tsv` identifies each C# tree by
sha256 (decompile-net.sh is deterministic: a re-run of the bridge exe gives the same hash). Binaries are identified by sha256 only.

## Re-run (from this directory, `python3 -B`)

    python3 net_inventory.py > pe-census.tsv                    # every PE by magic bytes: 247 module jars (nested jars followed), the install tree, organized/
    python3 clr_dump.py <nativeLib> --out . --ilspy             # assemblies.tsv, pinvoke.tsv, asmrefs.tsv (+ ilspycmd type-count cross-check)
    bash $KIT/toolbelt/decompile-net.sh <dll|exe> <out>/<name>  # primary instrument, per assembly (out of git)
    python3 net_tree_hash.py <out> > net-decompile.tsv
    python3 bridge_facts.py <XProtectBridgeService.exe>         # raw-PE second instrument for the bridge behaviour claims
    python3 n4_n5_signed_diff.py <n4 nativeLib> <n5 nativeLib>  # N4-4.15.3.28 vs N5: image hash equal, signature differs
    python3 jni_match.py <ffmpeg/extracted> <ffmpeg-wrapper.dll> > jni-match.tsv
    python3 ff_idents.py <nativeLib/x86_64> --src <ffsrc> > ffmpeg-idents-n5.tsv
    python3 dll_deps.py <nativeLib/x86_64> > dll-deps.tsv
    python3 loader_vs_shipped.py <organized> > loader-vs-shipped.tsv
    python3 jni_in_jars.py > jni-libs-in-jars.tsv
    ./verify_signatures.sh <organized> > authenticode-verify.tsv  # osslsigncode: digest recomputed + chain, 14 .NET + 8 FFmpeg files (network: CRL fetch)
    jni-probe/run.sh <dir with the 8 FFmpeg DLLs>               # local Windows-JRE binding probe (jni-probe/probe-output.txt)

## Files

| File | What |
|---|---|
| `pelib.py`, `clrlib.py` | stdlib PE reader (sections, exports, imports, Authenticode image hash) and ECMA-335 metadata reader (tables, #Strings/#Blob, Assembly, AssemblyRef, ImplMap, TargetFramework) |
| `net_inventory.py`, `pe-census.tsv` | 271 PE rows by source (`jars` 28, `org` 34 = same 28 plus 6 duplicates, `inst` 209); CLR flag per row: 14 in `jars`, 14 in `org`, 0 in `inst` |
| `clr_dump.py`, `assemblies.tsv`, `pinvoke.tsv`, `asmrefs.tsv` | 14 assemblies: identity, target framework, strong-name flag/token, Authenticode digest algorithm and leaf, table sizes, ilspycmd-vs-metadata type counts; 117 P/Invoke rows; 146 AssemblyRef rows |
| `net_tree_hash.py`, `net-decompile.tsv` | file, line and tree-sha256 identity of the out-of-git ilspycmd output |
| `bridge_facts.py`, `bridge-facts.tsv` | 23 checks on XProtectBridgeService.exe from raw bytes (user strings, MemberRefs, ldc.i4 9117, embedded manifest) |
| `n4_n5_signed_diff.py`, `n4-n5-net-diff.tsv` | 14 of 14 files have equal Authenticode image hash between N4-4.15.3.28 `xprotect-wb.jar` and N5 `xprotect.jar` |
| `jni_match.py`, `jni-match.tsv`, `jni-match-n4.15.tsv` | 26 declared natives vs 26 exports of ffmpeg-wrapper.dll (pelib = objdump -p = rabin2 -E); N4-4.15.3.28 result is byte-identical |
| `jni-probe/` | stub class (native signatures only) + probe run on the N5 Windows JRE; `probe-output.txt` is the observed result |
| `ff_idents.py`, `ffmpeg-idents-n5.tsv`, `ffmpeg-idents-n4.15.tsv` | version, configure-string and license-string hits per DLL with file offset, VA, and r2/strings agreement (22 of 22 both) |
| `dll_deps.py`, `dll-deps.tsv` | import closure per FFmpeg DLL (pelib = objdump), Authenticode leaf, external-codec markers |
| `loader_vs_shipped.py`, `loader-vs-shipped.tsv` | Java loader constants vs shipped natives (xprotect 13 of 14, ffmpeg 6 of 8) and the wrapper's import closure |
| `jni_in_jars.py`, `jni-libs-in-jars.tsv` | 13 PE files inside jars that export Java_ names (tests B117's "only JNI library shipped inside a jar") |
| `verify_signatures.sh`, `authenticode-verify.tsv` | osslsigncode result per file: digest match 22 of 22; chain ok for the 12 DigiCert-chained Tridium files, Microsoft root missing locally for 2, private Honeywell root for the 8 FFmpeg files |
| `claim-audit.tsv` | 23 claims from 14 blocks: 18 SAFE, 4 SUSPECT, 1 CONTRADICTED |

## Provenance of external artifacts

| Artifact | Identity |
|---|---|
| `ffmpeg.jar!doc/ffmpeg-8.1.1.tar.xz` | 11,709,440 bytes, sha256 `b6863adde98898f42602017462871b5f6333e65aec803fdd7a6308639c52edf3`; equal to `https://ffmpeg.org/releases/ffmpeg-8.1.1.tar.xz` downloaded 2026-09-29 (HTTP 200, same length and sha256; the .asc was not verified: no FFmpeg key imported) |
| ilspycmd | 11.0.0.9375, dotnet global tool, nupkg sha256 `8f555b3fca90a1d7a59050d78539c69deedaad421756bd4fe478d135bdac2dea` (already provisioned; `detect-tools.sh --require ilspycmd` AVAILABLE, .NET 10.0.400) |
| radare2 6.2.0, GNU objdump 2.47, openssl 3.6.4, javap 21.0.12.1 | second instruments; Windows JRE `jre/bin/java.exe` sha256 `0e1d7a36c3fc114e42eebd46b8f6a025bce75980f0e2aafc33588cbff3ab82af` (Zulu 25.0.4) |
| N4-4.15.3.28 `modules/{ffmpeg-wb,xprotect-wb}.jar` | comparison baseline, extracted to `organized/_evidence/b122/n4-415/` |
