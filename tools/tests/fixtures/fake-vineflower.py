#!/usr/bin/env python3
"""Fake Vineflower for the "T24" section of tools/tests/n5-decompile.bats
(isolating classes that hang Vineflower instead of losing the whole module to
CFR). Wired in as $N5_JAVA via fake-vineflower-java.sh — see that script's
header for how n5-decompile.sh's real "$N5_JAVA" -jar "$N5_VINEFLOWER" ...
invocations reach this file.

Behaves like the real Vineflower for the options n5-decompile.sh passes:
  - writes one trivial .java per TOP-LEVEL class (no '$' in the class file's
    basename) found in the input jar, into the output dir, mirroring the
    class's package directory — enough for every test assertion (file
    presence/absence), without a real decompile;
  - honors --excluded-classes=<regex> with the SAME semantics verified
    empirically against the real Vineflower 1.12.0 jar (a FULL match —
    Python's re.fullmatch, matching Java's Matcher#matches() — against the
    class's internal, '/'-separated name; see tools/n5-decompile.sh's
    vf_build_excluded_classes_regex doc comment for the experiment);
  - ignores every other flag it does not need (--log-level=..,
    --include-runtime=.., -e=.., ...);
  - hangs forever (a huge sleep, comfortably longer than any test's tiny
    N5_PRIMARY_TIMEOUT/N5_ISOLATE_TIMEOUT budget) when asked to decompile a
    class named by $FAKE_HANG_CLASS (unless that exact class was excluded by
    --excluded-classes) OR when the number of classes it would decompile is
    >= $FAKE_HANG_MIN_CLASSES (T24c: a combination hang no SINGLE class
    reproduces alone — every package/class isolation subset stays under the
    threshold, only the whole module reaches it). --decompile-inner=false
    NEVER hangs, regardless of the two conditions above: this mirrors T24's
    real motivating bug (Vineflower's inner-class/local-record handling is
    what actually hangs on bajaui's NSS2SelectionResult) and lets the T24
    "noinner" secondary view genuinely succeed in these tests instead of
    always being a forced best-effort failure.
  - exits 1 immediately, instead of decompiling anything, when
    $FAKE_EXCLUDED_RERUN_FAIL=1 and this invocation carries
    --excluded-classes=... (i.e. it IS T24's post-isolation excluded re-run) —
    lets a test exercise the "excluded re-run itself fails" branch
    (vf_handle_primary_timeout's isolation_status=excluded_rerun_error path),
    which a hang-only fake could never reach (the plain hang/no-hang decision
    above always resolves to a clean "ok" once the hung class is excluded).
  - exits 1 immediately, instead of decompiling anything, when
    $FAKE_NOINNER_FAIL=1 and this invocation carries
    --decompile-inner=false — lets a test exercise vf_render_noinner_view's
    non-"ok" (best-effort-failed) branch deterministically, since
    --decompile-inner=false otherwise never hangs or errors in this fake.
"""
import os
import re
import sys
import time
import zipfile


def main():
    args = sys.argv[1:]
    excluded_regex = None
    no_inner = False
    positional = []
    for a in args:
        if a.startswith("--excluded-classes="):
            excluded_regex = a[len("--excluded-classes="):]
        elif a == "--decompile-inner=false":
            no_inner = True
        elif a.startswith("-"):
            continue
        else:
            positional.append(a)

    if len(positional) < 2:
        sys.stderr.write("fake-vineflower.py: expected <jar> <outdir>, got %r\n" % (positional,))
        sys.exit(1)
    in_jar, out_dir = positional[-2], positional[-1]
    os.makedirs(out_dir, exist_ok=True)

    if excluded_regex is not None and os.environ.get("FAKE_EXCLUDED_RERUN_FAIL") == "1":
        sys.stderr.write("fake-vineflower.py: FAKE_EXCLUDED_RERUN_FAIL=1, simulating an excluded re-run error\n")
        sys.exit(1)
    if no_inner and os.environ.get("FAKE_NOINNER_FAIL") == "1":
        sys.stderr.write("fake-vineflower.py: FAKE_NOINNER_FAIL=1, simulating a --decompile-inner=false error\n")
        sys.exit(1)

    excluded_re = re.compile(excluded_regex) if excluded_regex else None

    with zipfile.ZipFile(in_jar) as z:
        names = [n[:-len(".class")] for n in z.namelist() if n.endswith(".class")]
    top_level = sorted(n for n in names if "$" not in os.path.basename(n))
    if excluded_re is not None:
        top_level = [n for n in top_level if not excluded_re.fullmatch(n)]

    if not no_inner:
        hang_class = os.environ.get("FAKE_HANG_CLASS", "")
        hang_min_classes_raw = os.environ.get("FAKE_HANG_MIN_CLASSES", "0") or "0"
        hang_min_classes = int(hang_min_classes_raw)
        should_hang = bool(hang_class) and hang_class in top_level
        if hang_min_classes and len(top_level) >= hang_min_classes:
            should_hang = True
        if should_hang:
            time.sleep(10 ** 9)

    for internal in top_level:
        outpath = os.path.join(out_dir, internal + ".java")
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        simple = os.path.basename(internal)
        pkg = os.path.dirname(internal).replace("/", ".")
        with open(outpath, "w") as fh:
            if pkg:
                fh.write("package %s;\n" % pkg)
            fh.write("public class %s {}\n" % simple)


if __name__ == "__main__":
    main()
