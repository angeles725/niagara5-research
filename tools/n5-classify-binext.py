#!/usr/bin/env python3
"""
n5-classify-binext.py <jar> — is this N5 install bin/ext/*.jar Tridium-owned code,
or a third-party library that happens to ship alongside it?

Rule (empirically verified against all 109 jars under bin/ext/ in N5 5.0.0.28 —
see docs/decompiler-bakeoff.md "bin/ext classification"): a jar is Tridium-owned if
more than half of its .class files live under a Tridium/Niagara package namespace
(com/tridium/, niagara/, javax/baja/). On the real corpus this is not a borderline
call — every jar came back either ~0% (pure third-party: jetty, bouncycastle
(bcfips/bcstd), kotlin, jackson-esque deps under etc/m2, asm, jna/jnr, okhttp, etc.)
or >=67% (six jars: niagaraAnnotationProcessors.jar, niagarad.jar, nre.jar,
niagara-remote-client-*.jar, securityBridge/securityBridge.jar, splash.jar) — so the
0.5 threshold has wide margin on both sides rather than being a fragile cutoff.

Exit code 0 = include (Tridium-owned), 1 = skip (third-party), 2 = usage/read error.
Prints one line: "<include|skip> <ratio> <tridium_classes>/<total_classes> <jar>".
"""
import sys
import zipfile

TRIDIUM_PREFIXES = ("com/tridium/", "niagara/", "javax/baja/")


def classify(jar_path):
    zf = zipfile.ZipFile(jar_path)
    total = 0
    tridium = 0
    for name in zf.namelist():
        if not name.endswith(".class"):
            continue
        total += 1
        if name.startswith(TRIDIUM_PREFIXES):
            tridium += 1
    ratio = (tridium / total) if total else 0.0
    return total, tridium, ratio


def main():
    if len(sys.argv) != 2:
        print("usage: n5-classify-binext.py <jar>", file=sys.stderr)
        return 2
    jar = sys.argv[1]
    try:
        total, tridium, ratio = classify(jar)
    except (OSError, zipfile.BadZipFile) as e:
        print(f"error reading {jar}: {e}", file=sys.stderr)
        return 2
    verdict = "include" if ratio > 0.5 else "skip"
    print(f"{verdict} {ratio:.3f} {tridium}/{total} {jar}")
    return 0 if verdict == "include" else 1


if __name__ == "__main__":
    sys.exit(main())
