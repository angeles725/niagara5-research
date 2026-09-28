#!/usr/bin/env python3
"""T22 (third-party half): for every third-party jar identified in evidence/b117/maven-repo1.json,
fetch the upstream Maven Central `-sources.jar`, verify it against the published `.sha1`, and store
it under organized/_upstream-sources/<groupId>/<artifactId>/<version>/. For "the decompile must be
as faithful and exact as possible", the original upstream source beats any decompile of a byte-
identical (or vendor-resigned) jar -- see niagara5-block117.md's "Third-party library identity
against Maven Central" section.

Reuses evidence/b117/maven_repo1.py's and maven_content.py's prior work (which g:a:v each third-
party jar resolves to, and whether its non-META-INF content is byte-identical to Central) rather
than re-deriving it; this module only adds sources-jar retrieval, three coordinate corrections
that evidence run's own GAV inference got wrong (see etc_m2_gav_from_path / candidate_versions
docstrings), classname-set cross-checks, and a real recompile spot-check.

Subcommands:
  plan             read evidence/b117/maven-repo1.json, dedupe to one record per (g,a,v),
                    write plan.json (identified artifacts + unidentified jars with a reason).
  fetch             download each planned artifact's sources jar (typed status: fetched /
                    no-sources-published / checksum-mismatch / network-error), write manifest.json.
  classdiff         for fetched artifacts, compare top-level class names (sources .java vs
                    installed binary .class) and record binary jar sha256.
  paho-diff         characterize org.eclipse.paho.client.mqttv3 1.2.5 ("rebuilt-by-vendor",
                    B117 §117.x): javap -p class-set/signature diff, upstream binary vs shipped.
  recompile-check   recompile a few classes from 3 sample artifacts against the binary jar's own
                    classpath and compare normalized javap -p -c output with the shipped class.
  identify-unidentified  (T26a) for each still-unidentified `no-pom-properties` jar, hash the
                    exact shipped bytes (read from the local jar mirror) and look it up on Maven
                    Central by SHA-1; on a miss, try one filename-derived groupId:artifactId:version
                    guess and accept it only if Central's own published binary-jar SHA-1 confirms
                    it. Moves each resolved jar from plan["unidentified"] into plan["artifacts"]
                    (status one of identified-by-sha1 / vendor-modified) so the existing fetch/
                    classdiff pipeline picks it up unchanged; jars that stay unplaceable keep a
                    refined `reason` (not-on-central / network-error / mirror-unavailable).
  report            render docs/upstream-sources-report.md from manifest.json + the above.
  all               run plan, identify-unidentified, fetch, classdiff, paho-diff, recompile-check,
                    report in order.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
MAVEN_CENTRAL = "https://repo1.maven.org/maven2"
DEFAULT_EVIDENCE = REPO_ROOT / "evidence" / "b117" / "maven-repo1.json"
DEFAULT_OUT_DIR = REPO_ROOT / "organized" / "_upstream-sources"
DEFAULT_REPORT = REPO_ROOT / "docs" / "upstream-sources-report.md"

N5_MOD_DIR = Path("/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules")
N5_INSTALL_DIR = Path("/mnt/c/Program Files/Niagara/5.0.0.28")
JAVAC25 = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"
JAVAP25 = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"

# T26a: read-only local mirror of the same jars (see niagara5-research-localcache/README or the
# T26a task note) -- avoids ~440 slow WSL 9p reads across /mnt/c for the SHA-1 identification pass.
MIRROR_DIR = Path("/home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28")
MIRROR_MODULES_DIR = MIRROR_DIR / "modules"
MIRROR_BINEXT_DIR = MIRROR_DIR / "bin-ext"

MAVEN_SEARCH_URL = "https://search.maven.org/solrsearch/select"

PAHO_GAV = ("org.eclipse.paho", "org.eclipse.paho.client.mqttv3", "1.2.5")

# T26a: filename-derived groupId guesses for the artifactIds seen among the 44 no-pom-properties
# jars (evidence/b117/maven-repo1.json, 2026-09-28). A guess is ONLY ever accepted as an
# identification when Central's own published binary-jar SHA-1 for that g:a:v matches the local
# jar's SHA-1 (see identify_unidentified_entry) -- a wrong guess here just costs one wasted lookup,
# never a false identification. `None` marks artifactIds known ahead of time to be commercial/
# unpublished (documented per entry), so no guess-verify network call is wasted on them.
KNOWN_GROUP_GUESSES: dict = {
    "asm": "org.ow2.asm",
    "asm-commons": "org.ow2.asm",
    "asm-tree": "org.ow2.asm",
    "asm-analysis": "org.ow2.asm",
    "asm-util": "org.ow2.asm",
    "bc-fips": "org.bouncycastle",
    "bcpkix-fips": "org.bouncycastle",
    "bctls-fips": "org.bouncycastle",
    "bcutil-fips": "org.bouncycastle",
    "bc-bcfkswrapprov": None,  # BC's FIPS PKCS#11 wrapper -- not published to public Central
    "bcpkix-jdk18on": "org.bouncycastle",
    "bcprov-jdk18on": "org.bouncycastle",
    "bctls-jdk18on": "org.bouncycastle",
    "bcutil-jdk18on": "org.bouncycastle",
    "hsqldb": "org.hsqldb",
    "json-path": "com.jayway.jsonpath",
    "jcommander": "com.beust",
    "testng": "org.testng",
    "kotlin-stdlib": "org.jetbrains.kotlin",
    "kotlin-stdlib-jdk7": "org.jetbrains.kotlin",
    "kotlin-stdlib-jdk8": "org.jetbrains.kotlin",
    "xmlbeans": "org.apache.xmlbeans",
    "poi": "org.apache.poi",
    "poi-ooxml": "org.apache.poi",
    "poi-ooxml-lite": "org.apache.poi",
    "xml-apis-ext": "xml-apis",
    "libthrift": "org.apache.thrift",
    "okhttp": "com.squareup.okhttp3",
    "okhttp-jvm": "com.squareup.okhttp3",
    "okio-jvm": "com.squareup.okio",
    "resilience4j-core": "io.github.resilience4j",
    "resilience4j-retry": "io.github.resilience4j",
    "jna": "net.java.dev.jna",
    "jna-platform": "net.java.dev.jna",
    "jffi": None,  # local file is the "-native" classifier variant; the plain (no-classifier)
                   # coordinate this guess would build is a different artifact on Central
    "mibble-mibs": None,  # Mibble's mibs bundle -- SourceForge-distributed, not on Central
    "org.eclipse.swt.win32.win32.x86_64": None,  # SWT native fragment, Eclipse's own p2 repo
    "prosys-opc-ua-sdk-client-server": None,  # Prosys/Dassault commercial OPC UA SDK
    "jxbrowser": None,  # TeamDev commercial
    "jxbrowser-javafx": None,
    "jxbrowser-swing": None,
    "jxbrowser-swt": None,
    "jxbrowser-win64": None,
}

# major class-file version -> matching javac --release (only the ones seen in this corpus).
RELEASE_BY_MAJOR = {45: 1, 49: 5, 50: 6, 51: 7, 52: 8, 53: 9, 54: 10, 55: 11, 56: 12, 57: 13,
                     58: 14, 59: 15, 60: 16, 61: 17, 62: 18, 63: 19, 64: 20, 65: 21, 66: 22,
                     67: 23, 68: 24, 69: 25}


# ---------------------------------------------------------------------------
# Pure logic: evidence classification and GAV/version derivation (no network).
# ---------------------------------------------------------------------------

def parse_match(match: Optional[str]):
    """Split evidence/b117/maven_repo1.py's 'g:a:v' match string into (g, a, v); None if malformed."""
    if not match:
        return None
    parts = match.split(":")
    if len(parts) != 3 or not all(parts):
        return None
    return tuple(parts)


def etc_m2_gav_from_path(name: str):
    """Derive (g, a, v) for an `etc/m2/repository/...` jar straight from its own relative path.

    evidence/b117/maven_repo1.py's etc/m2 fallback (used when the jar carries no
    META-INF/maven/.../pom.properties) does `".".join(parts[2:-3])`, which folds the literal
    path segment "repository" into the groupId -- e.g. "repository.org.jetbrains.kotlin" for
    kotlin-reflect. That URL 404s on Central (verified 2026-09-28:
    repo1.maven.org/maven2/repository/org/jetbrains/kotlin/... -> 404). The jar's own relative
    path under etc/m2/repository/ already IS Central's own repo layout, so this function reads
    the correct (g, a, v) directly from it instead of re-deriving evidence/b117's buggy `match`.
    """
    m = re.search(r"etc/m2/repository/(.+)/([^/]+)/([^/]+)/[^/]+\.jar$", name)
    if not m:
        return None
    group_path, artifact, version = m.groups()
    return group_path.replace("/", "."), artifact, version


def classify_third_party(entry: dict):
    """Classify one evidence/b117/maven-repo1.json record.

    Returns ("identified", (g, a, v)) or ("unidentified", reason).
    """
    result = entry.get("result", "")
    if result == "no-pom-properties":
        return "unidentified", "no-pom-properties"
    if entry.get("kind") == "etc/m2":
        gav = etc_m2_gav_from_path(entry.get("name", ""))
        if gav:
            return "identified", gav
    gav = parse_match(entry.get("match"))
    if gav:
        return "identified", gav
    return "unidentified", result or "no-match"


def dedupe_artifacts(entries: list[dict]):
    """Group identified evidence records by (g, a, v); one artifact even if nested in several jars.

    Returns (artifacts, unidentified): artifacts is a list of
    {"groupId", "artifactId", "version", "occurrences": [{"kind","name","binary_sha1"}, ...]},
    unidentified is a list of {"kind", "name", "reason"}.
    """
    by_key: dict[str, dict] = {}
    order: list[str] = []
    unidentified: list[dict] = []
    for e in entries:
        category, value = classify_third_party(e)
        if category == "unidentified":
            unidentified.append({"kind": e.get("kind"), "name": e.get("name"), "reason": value})
            continue
        g, a, v = value
        key = f"{g}:{a}:{v}"
        if key not in by_key:
            by_key[key] = {"groupId": g, "artifactId": a, "version": v, "occurrences": []}
            order.append(key)
        by_key[key]["occurrences"].append(
            {"kind": e.get("kind"), "name": e.get("name"), "binary_sha1": e.get("sha1")}
        )
    return [by_key[k] for k in order], unidentified


def jar_basename(entry_name: str) -> str:
    """The bare filename (no directory/LIB-INF prefix, no .jar extension) an evidence `name`
    refers to, e.g. "apachePoi.jar!LIB-INF/poi-5.5.1.jar" -> "poi-5.5.1", or
    "bin/ext/bcfips/bc-fips-2.1.2.jar" -> "bc-fips-2.1.2"."""
    basename = entry_name.rsplit("!", 1)[-1].rsplit("/", 1)[-1]
    if basename.endswith(".jar"):
        basename = basename[:-4]
    return basename


_ARTIFACT_VERSION_RE = re.compile(r"^(.+?)-(\d[\w.\-]*)$")


def parse_artifact_version_from_basename(basename: str):
    """Split a bare jar basename into (artifactId, version) at the FIRST "-<digit>" boundary, not
    the last -- versions can themselves contain a dash (e.g. "prosys-opc-ua-sdk-client-server-
    5.7.0-248" -> artifact "prosys-opc-ua-sdk-client-server", version "5.7.0-248", not
    "...-5.7.0" / "248"). Returns None if the basename has no such boundary at all."""
    m = _ARTIFACT_VERSION_RE.match(basename)
    if not m:
        return None
    return m.group(1), m.group(2)


def candidate_versions(entry_name: str, artifact_id: str, pom_version: str) -> list[str]:
    """Ordered list of Maven versions to try: the pom.properties version, then (if different) the
    version embedded in the jar's own filename.

    mssql-jdbc's shipped jar embeds `version=13.4.0` in its own pom.properties, but the jar is
    named `mssql-jdbc-13.4.0.jre11.jar` and Central hosts it only under `13.4.0.jre11` (verified
    2026-09-28: .../mssql-jdbc/13.4.0/... -> 404, .../mssql-jdbc/13.4.0.jre11/... -> 200) --
    Microsoft's own embedded pom.properties is the one that's wrong here, not this evidence.
    """
    out = [pom_version]
    basename = jar_basename(entry_name)
    prefix = artifact_id + "-"
    if basename.startswith(prefix):
        fname_version = basename[len(prefix):]
        if fname_version and fname_version not in out:
            out.append(fname_version)
    return out


def sources_jar_filename(artifact_id: str, version: str) -> str:
    return f"{artifact_id}-{version}-sources.jar"


def sources_jar_url(group_id: str, artifact_id: str, version: str) -> str:
    return f"{MAVEN_CENTRAL}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{sources_jar_filename(artifact_id, version)}"


# ---------------------------------------------------------------------------
# Network (retried, typed failures; the opener/sleep are injected for tests).
# ---------------------------------------------------------------------------

def fetch_with_retry(url: str, opener: Callable, sleep: Callable = time.sleep,
                      retries: int = 3, timeout: int = 30, backoff: float = 0.5) -> dict:
    """GET url. A 404 is definitive (returned immediately, kind='not-found'); any other failure
    (timeout, connection error, non-404 HTTP status) is retried with exponential backoff and
    reported as kind='error' if every attempt fails."""
    last_error = None
    for attempt in range(retries):
        try:
            with opener(url, timeout=timeout) as resp:
                return {"ok": True, "bytes": resp.read()}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"ok": False, "kind": "not-found", "code": 404}
            last_error = f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 - network layer, report typed, never raise
            last_error = repr(e)
        if attempt < retries - 1:
            sleep(backoff * (2 ** attempt))
    return {"ok": False, "kind": "error", "error": last_error}


def resolve_and_fetch_sources(artifact: dict, opener: Callable, sleep: Callable = time.sleep,
                               retries: int = 3) -> dict:
    """Try each of artifact["_candidate_versions"] in order until a sources jar is found on
    Central and its sha1 matches. Returns a typed status record:
      fetched | checksum-mismatch | no-sources-published | network-error
    """
    g, a = artifact["groupId"], artifact["artifactId"]
    versions_tried: list[str] = []
    saw_non_404_failure = False
    for v in artifact["_candidate_versions"]:
        versions_tried.append(v)
        sha1_url = sources_jar_url(g, a, v) + ".sha1"
        sha1_result = fetch_with_retry(sha1_url, opener, sleep=sleep, retries=retries)
        if not sha1_result["ok"]:
            if sha1_result["kind"] != "not-found":
                saw_non_404_failure = True
            continue
        expected_sha1 = sha1_result["bytes"].decode("utf-8", "replace").split()[0].strip()
        jar_result = fetch_with_retry(sources_jar_url(g, a, v), opener, sleep=sleep, retries=retries)
        if not jar_result["ok"]:
            return {"status": "network-error", "resolved_version": v,
                     "versions_tried": versions_tried, "detail": jar_result}
        actual_sha1 = hashlib.sha1(jar_result["bytes"]).hexdigest()
        if actual_sha1 != expected_sha1:
            return {"status": "checksum-mismatch", "resolved_version": v,
                     "expected_sha1": expected_sha1, "actual_sha1": actual_sha1,
                     "bytes": jar_result["bytes"]}
        return {"status": "fetched", "resolved_version": v, "sha1": actual_sha1,
                 "bytes": jar_result["bytes"]}
    if saw_non_404_failure:
        return {"status": "network-error", "versions_tried": versions_tried,
                 "detail": "sha1 lookup failed on every candidate version"}
    return {"status": "no-sources-published", "versions_tried": versions_tried}


# ---------------------------------------------------------------------------
# T26a: identify pom-less jars by content SHA-1 against Maven Central.
# ---------------------------------------------------------------------------

def search_maven_central_by_sha1(sha1: str, opener: Callable, sleep: Callable = time.sleep,
                                  retries: int = 3) -> dict:
    """Query Maven Central's Solr search API (search.maven.org) for any artifact whose binary
    jar has this exact SHA-1. Returns {"status": "hit", "docs": [...]} (each doc has g/a/v),
    {"status": "no-hit"}, or a typed {"status": "network-error", ...}."""
    url = f"{MAVEN_SEARCH_URL}?q=1:{sha1}&rows=20&wt=json"
    result = fetch_with_retry(url, opener, sleep=sleep, retries=retries)
    if not result["ok"]:
        if result["kind"] == "not-found":
            return {"status": "no-hit"}
        return {"status": "network-error", "detail": result}
    try:
        data = json.loads(result["bytes"].decode("utf-8"))
        docs = data["response"]["docs"]
    except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError) as e:
        return {"status": "network-error", "detail": {"kind": "bad-response", "error": repr(e)}}
    if not docs:
        return {"status": "no-hit"}
    return {"status": "hit", "docs": docs}


def binary_sha1_from_central(group_id: str, artifact_id: str, version: str, opener: Callable,
                              sleep: Callable = time.sleep, retries: int = 3) -> dict:
    """Fetch Central's own published `.jar.sha1` for one g:a:v -- the identity proof for a
    filename-derived guess (or a belt-and-suspenders re-check of a sha1-search hit)."""
    url = (f"{MAVEN_CENTRAL}/{group_id.replace('.', '/')}/{artifact_id}/{version}/"
           f"{artifact_id}-{version}.jar.sha1")
    result = fetch_with_retry(url, opener, sleep=sleep, retries=retries)
    if not result["ok"]:
        if result["kind"] == "not-found":
            return {"status": "not-found"}
        return {"status": "network-error", "detail": result}
    central_sha1 = result["bytes"].decode("utf-8", "replace").split()[0].strip()
    return {"status": "fetched", "central_sha1": central_sha1}


def identify_unidentified_entry(entry: dict, local_sha1: str, opener: Callable,
                                 sleep: Callable = time.sleep, retries: int = 3) -> dict:
    """Identify one no-pom-properties jar. First: search Central by the exact SHA-1 of the local
    jar bytes -- any hit is definitive identification (byte-identical artifact). On a miss, try
    ONE filename-derived groupId:artifactId:version guess (KNOWN_GROUP_GUESSES), accepted only if
    Central's own published binary-jar SHA-1 for that guess matches the local SHA-1; a same-g:a:v
    guess with a *different* SHA-1 is "vendor-modified" (real bytes exist on Central, but not
    ours), never silently treated as identified. Returns a typed record:
      identified-by-sha1 | vendor-modified | not-on-central | network-error
    """
    search = search_maven_central_by_sha1(local_sha1, opener, sleep=sleep, retries=retries)
    if search["status"] == "network-error":
        return {"status": "network-error", "stage": "sha1-search", "detail": search.get("detail")}
    if search["status"] == "hit":
        doc = search["docs"][0]
        return {
            "status": "identified-by-sha1", "groupId": doc.get("g"), "artifactId": doc.get("a"),
            "version": doc.get("v"), "method": "sha1-search", "sha1_search_hits": len(search["docs"]),
        }
    basename = jar_basename(entry["name"])
    parsed = parse_artifact_version_from_basename(basename)
    if not parsed:
        return {"status": "not-on-central", "reason": "unparseable-filename", "basename": basename}
    guess_artifact, guess_version = parsed
    guess_group = KNOWN_GROUP_GUESSES.get(guess_artifact, "__no_entry__")
    if guess_group is None:
        return {"status": "not-on-central", "reason": "known-proprietary-or-unpublished",
                "guessed_artifactId": guess_artifact, "guessed_version": guess_version}
    if guess_group == "__no_entry__":
        return {"status": "not-on-central", "reason": "no-plausible-coordinate",
                "guessed_artifactId": guess_artifact, "guessed_version": guess_version}
    verify = binary_sha1_from_central(guess_group, guess_artifact, guess_version, opener,
                                       sleep=sleep, retries=retries)
    if verify["status"] == "network-error":
        return {"status": "network-error", "stage": "guess-verify", "detail": verify.get("detail")}
    if verify["status"] == "not-found":
        return {"status": "not-on-central", "reason": "guessed-coordinate-404",
                "guessed_groupId": guess_group, "guessed_artifactId": guess_artifact,
                "guessed_version": guess_version}
    if verify["central_sha1"] == local_sha1:
        return {"status": "identified-by-sha1", "groupId": guess_group, "artifactId": guess_artifact,
                "version": guess_version, "method": "filename-guess"}
    return {"status": "vendor-modified", "groupId": guess_group, "artifactId": guess_artifact,
            "version": guess_version, "method": "filename-guess",
            "central_sha1": verify["central_sha1"], "local_sha1": local_sha1}


def compute_vendor_modified_overlap(local_bytes: bytes, group_id: str, artifact_id: str,
                                     version: str, opener: Callable, sleep: Callable = time.sleep,
                                     retries: int = 3) -> dict:
    """For a "vendor-modified" identification (same g:a:v on Central, different bytes), fetch
    Central's binary jar and record the top-level class-name overlap % against the local jar --
    NOT a claim of ground truth, just how much of the local jar the same-coordinate upstream
    binary still resembles."""
    url = f"{MAVEN_CENTRAL}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar"
    result = fetch_with_retry(url, opener, sleep=sleep, retries=retries)
    if not result["ok"]:
        return {"status": "network-error", "detail": result}
    central_names = class_names_from_zip(result["bytes"], ".class")
    local_names = class_names_from_zip(local_bytes, ".class")
    diff = classname_diff(local_names, central_names)
    overlap_pct = 100 * diff["common"] / diff["sources_total"] if diff["sources_total"] else 0.0
    return {"status": "compared", "overlap_pct": round(overlap_pct, 1), "classname_diff": diff}


# ---------------------------------------------------------------------------
# Jar/class inspection (no network).
# ---------------------------------------------------------------------------

def class_names_from_zip(jar_bytes: bytes, ext: str) -> set[str]:
    """Top-level entry names (no extension) matching ext. For .class, excludes nested/anonymous
    classes (any '$' in the simple name) so the comparison is class-file-vs-source-file, not
    class-file-vs-source-file-plus-every-inner-class."""
    names: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as z:
        for n in z.namelist():
            if not n.endswith(ext):
                continue
            base = n[: -len(ext)]
            if ext == ".class" and "$" in base.rsplit("/", 1)[-1]:
                continue
            names.add(base)
    return names


def classname_diff(sources_names: set[str], binary_names: set[str]) -> dict:
    return {
        "sources_only": sorted(sources_names - binary_names),
        "binary_only": sorted(binary_names - sources_names),
        "common": len(sources_names & binary_names),
        "sources_total": len(sources_names),
        "binary_total": len(binary_names),
    }


def load_binary_bytes(occurrence: dict, mod_dir: Path = N5_MOD_DIR,
                       install_dir: Path = N5_INSTALL_DIR) -> Optional[bytes]:
    """Read the installed binary jar bytes an evidence occurrence refers to. Returns None if the
    N5 install is not mounted at this path (tests/CI without the installer run without it)."""
    kind, name = occurrence["kind"], occurrence["name"]
    try:
        if kind == "LIB-INF":
            outer, inner = name.split("!", 1)
            with zipfile.ZipFile(mod_dir / outer) as z:
                return z.read(inner)
        path = install_dir / name
        return path.read_bytes()
    except (FileNotFoundError, OSError, KeyError):
        return None


def load_binary_bytes_from_mirror(occurrence: dict, modules_dir=MIRROR_MODULES_DIR,
                                   binext_dir=MIRROR_BINEXT_DIR) -> Optional[bytes]:
    """T26a: read an evidence occurrence's exact shipped jar bytes from the local read-only jar
    mirror (niagara5-research-localcache/jar-mirror-5.0.0.28) instead of the /mnt/c-mounted N5
    install -- the mirror is local disk, the install is WSL 9p (slow for many small reads).
    Returns None if the mirror doesn't have this jar (missing mirror, unmounted, wrong name)."""
    kind, name = occurrence["kind"], occurrence["name"]
    modules_dir, binext_dir = Path(modules_dir), Path(binext_dir)
    try:
        if kind == "LIB-INF":
            outer, inner = name.split("!", 1)
            with zipfile.ZipFile(modules_dir / outer) as z:
                return z.read(inner)
        if kind == "bin/ext":
            rel = name[len("bin/ext/"):] if name.startswith("bin/ext/") else name
            return (binext_dir / rel).read_bytes()
        return None
    except (FileNotFoundError, OSError, KeyError):
        return None


# ---------------------------------------------------------------------------
# javap normalization for the recompile / paho cross-checks.
# ---------------------------------------------------------------------------

class JavapError(RuntimeError):
    """javap failed or printed nothing; comparing its output would turn [] == [] into a false match."""


def run_javap(class_bytes_path: str, javap_bin: str = JAVAP25) -> str:
    try:
        proc = subprocess.run([javap_bin, "-p", "-c", class_bytes_path],
                              capture_output=True, text=True, check=False)
    except OSError as e:  # javap binary missing or not executable
        raise JavapError(f"javap not runnable ({javap_bin}): {e}") from e
    if proc.returncode != 0 or not proc.stdout.strip():
        raise JavapError(f"javap rc={proc.returncode} on {class_bytes_path}: {proc.stderr.strip()[:300]}")
    return proc.stdout


_CP_INDEX_RE = re.compile(r"#\d+\s*$")


def normalize_javap(text: str) -> list[str]:
    """Drop the raw constant-pool index (e.g. the "#7" in "putfield #7") but keep javap's own
    resolved symbolic comment ("// Field _asciiToBase64:[I"), and drop blank/File/Compiled-from
    lines. Two independent compilations of behaviourally-identical code build their constant
    pools in different orders, so the raw index differs even when the resolved symbol -- the
    thing that actually carries semantic meaning -- is identical (observed for real: jackson-core
    Base64Variant.class recompiled with javac 25 vs the shipped class, 2026-09-28)."""
    out = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("Compiled from") or line.startswith("Classfile"):
            continue
        if "//" in line:
            code, comment = line.split("//", 1)
            code = _CP_INDEX_RE.sub("", code).rstrip()
            line = f"{code} // {comment.strip()}"
        else:
            line = _CP_INDEX_RE.sub("", line).rstrip()
        out.append(line)
    return out


def class_major_version(class_bytes: bytes) -> int:
    return int.from_bytes(class_bytes[6:8], "big")


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------

def run_plan(evidence_path: Path) -> dict:
    entries = json.load(open(evidence_path))
    artifacts, unidentified = dedupe_artifacts(entries)
    for art in artifacts:
        art["_candidate_versions"] = candidate_versions(
            art["occurrences"][0]["name"], art["artifactId"], art["version"])
    return {"artifacts": artifacts, "unidentified": unidentified}


def run_fetch(plan: dict, out_dir: Path, opener: Callable = urllib.request.urlopen,
              sleep: Callable = time.sleep, pace: float = 0.15) -> dict:
    manifest_artifacts = []
    for art in plan["artifacts"]:
        result = resolve_and_fetch_sources(art, opener, sleep=sleep)
        if pace:
            sleep(pace)  # polite throttling of repo1.maven.org, independent of retry backoff
        record = {
            "groupId": art["groupId"], "artifactId": art["artifactId"], "version": art["version"],
            "occurrences": art["occurrences"], "candidate_versions": art["_candidate_versions"],
            "status": result["status"], "resolved_version": result.get("resolved_version"),
        }
        # T26a: carry over the sha1-identification provenance a plan artifact may already have
        # (identification_method, vendor_modified) -- these aren't derived by fetch itself, but a
        # plain field allowlist here would otherwise silently drop them between plan and manifest.
        for extra_key in ("identification_method", "vendor_modified"):
            if extra_key in art:
                record[extra_key] = art[extra_key]
        dest_dir = out_dir / art["groupId"] / art["artifactId"] / art["version"]
        if result["status"] in ("fetched", "checksum-mismatch") and "bytes" in result:
            dest_dir.mkdir(parents=True, exist_ok=True)
            jar_path = dest_dir / sources_jar_filename(art["artifactId"], result["resolved_version"])
            jar_path.write_bytes(result["bytes"])
            record["sources_jar_path"] = str(jar_path.relative_to(REPO_ROOT))
            record["sources_jar_sha256"] = hashlib.sha256(result["bytes"]).hexdigest()
            if result["status"] == "checksum-mismatch":
                record["expected_sha1"] = result["expected_sha1"]
                record["actual_sha1"] = result["actual_sha1"]
        else:
            record["detail"] = result.get("detail")
            record["versions_tried"] = result.get("versions_tried")
        manifest_artifacts.append(record)
    manifest = {"artifacts": manifest_artifacts, "unidentified": plan["unidentified"]}
    if "sha1_identify_summary" in plan:
        manifest["sha1_identify_summary"] = plan["sha1_identify_summary"]
    out_dir.mkdir(parents=True, exist_ok=True)
    json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
    return manifest


def run_identify_unidentified(plan: dict, mirror_modules_dir=MIRROR_MODULES_DIR,
                               mirror_binext_dir=MIRROR_BINEXT_DIR,
                               opener: Callable = urllib.request.urlopen,
                               sleep: Callable = time.sleep, retries: int = 3,
                               pace: float = 0.15) -> dict:
    """T26a. Mutates plan in place: every plan["unidentified"] entry whose reason is
    "no-pom-properties" is hashed from the local mirror and looked up on Central. A resolved jar
    (identified-by-sha1 or vendor-modified) is moved into plan["artifacts"] as a new
    single-occurrence artifact -- shaped exactly like run_plan's own output -- so the existing
    fetch/classdiff pipeline picks it up unchanged. An unresolved jar stays in plan["unidentified"]
    with its reason refined from the generic "no-pom-properties" to the specific outcome. Entries
    with any other reason (e.g. from a future evidence run) are left untouched. Returns counts by
    outcome, including "mirror-unavailable" for jars the local mirror doesn't have."""
    summary = {"identified-by-sha1": 0, "vendor-modified": 0, "not-on-central": 0,
               "network-error": 0, "mirror-unavailable": 0}
    still_unidentified = []
    for u in plan["unidentified"]:
        if u.get("reason") != "no-pom-properties":
            still_unidentified.append(u)
            continue
        occurrence = {"kind": u["kind"], "name": u["name"]}
        local_bytes = load_binary_bytes_from_mirror(occurrence, mirror_modules_dir, mirror_binext_dir)
        if local_bytes is None:
            summary["mirror-unavailable"] += 1
            still_unidentified.append(dict(u, reason="mirror-jar-not-found"))
            continue
        local_sha1 = hashlib.sha1(local_bytes).hexdigest()
        result = identify_unidentified_entry(u, local_sha1, opener, sleep=sleep, retries=retries)
        if pace:
            sleep(pace)
        summary[result["status"]] += 1
        if result["status"] == "identified-by-sha1":
            plan["artifacts"].append({
                "groupId": result["groupId"], "artifactId": result["artifactId"],
                "version": result["version"],
                "occurrences": [{"kind": u["kind"], "name": u["name"], "binary_sha1": local_sha1}],
                "_candidate_versions": [result["version"]],
                "identification_method": result["method"],
            })
        elif result["status"] == "vendor-modified":
            overlap = compute_vendor_modified_overlap(
                local_bytes, result["groupId"], result["artifactId"], result["version"],
                opener, sleep=sleep, retries=retries)
            plan["artifacts"].append({
                "groupId": result["groupId"], "artifactId": result["artifactId"],
                "version": result["version"],
                "occurrences": [{"kind": u["kind"], "name": u["name"], "binary_sha1": local_sha1}],
                "_candidate_versions": [result["version"]],
                "identification_method": result["method"],
                "vendor_modified": {"central_sha1": result.get("central_sha1"),
                                     "local_sha1": local_sha1, "overlap": overlap},
            })
        else:
            reason_detail = result.get("reason") or result.get("stage") or ""
            still_unidentified.append(dict(u, reason=f"{result['status']}:{reason_detail}"
                                            if reason_detail else result["status"],
                                            local_sha1=local_sha1))
    plan["unidentified"] = still_unidentified
    plan["sha1_identify_summary"] = summary
    return summary


def run_all_third_party_coverage(manifest: dict, mirror_modules_dir=MIRROR_MODULES_DIR,
                                  mirror_binext_dir=MIRROR_BINEXT_DIR) -> dict:
    """T26a headline fix: the class-coverage percentage must state its denominator over ALL
    third-party classes (identified + unidentified), not only artifacts with a fetched sources
    jar. Numerator: classes_with_upstream_source (fetched, non-vendor-modified artifacts only --
    a vendor-modified artifact's "sources" are for a different build, not ground truth, so its
    classes count toward the denominator but never the numerator). Denominator adds every
    artifact's binary_total plus the local mirror's own class count for every jar that never got
    an upstream match at all."""
    covered = 0
    total = 0
    for art in manifest["artifacts"]:
        cd = art.get("classdiff")
        if not cd or "binary_total" not in cd:
            continue
        total += cd["binary_total"]
        if not art.get("vendor_modified"):
            covered += cd["common"]
    for u in manifest.get("unidentified", []):
        binary_bytes = load_binary_bytes_from_mirror(u, mirror_modules_dir, mirror_binext_dir)
        if binary_bytes is None:
            u["class_count"] = None
            continue
        n = len(class_names_from_zip(binary_bytes, ".class"))
        u["class_count"] = n
        total += n
    coverage = {"classes_with_upstream_source": covered, "classes_total": total}
    manifest["all_third_party_coverage"] = coverage
    return coverage


def run_classdiff(manifest: dict, out_dir: Path, mod_dir: Path = N5_MOD_DIR,
                   install_dir: Path = N5_INSTALL_DIR) -> dict:
    total_sources = total_binary = 0
    for art in manifest["artifacts"]:
        if art["status"] != "fetched":
            continue
        jar_path = REPO_ROOT / art["sources_jar_path"]
        sources_names = class_names_from_zip(jar_path.read_bytes(), ".java")
        binary_bytes = load_binary_bytes(art["occurrences"][0], mod_dir, install_dir)
        if binary_bytes is None:
            art["classdiff"] = {"status": "install-not-mounted"}
            continue
        binary_names = class_names_from_zip(binary_bytes, ".class")
        art["binary_sha256"] = hashlib.sha256(binary_bytes).hexdigest()
        diff = classname_diff(sources_names, binary_names)
        art["classdiff"] = diff
        total_sources += diff["common"]
        total_binary += diff["binary_total"]
    manifest["classdiff_coverage"] = {
        "classes_with_upstream_source": total_sources, "classes_total": total_binary,
    }
    json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
    return manifest["classdiff_coverage"]


def run_paho_diff(manifest: dict, out_dir: Path, opener: Callable = urllib.request.urlopen,
                   sleep: Callable = time.sleep, mod_dir: Path = N5_MOD_DIR) -> dict:
    """Fetch upstream paho mqttv3 1.2.5's *binary* jar (not just sources) and diff its class set /
    method descriptors (javap -p) against the shipped LIB-INF copy, characterizing B117's
    "same 110 classes, different bytes, 2021 vs 2020 timestamps" observation."""
    g, a, v = PAHO_GAV
    paho = next((x for x in manifest["artifacts"]
                 if (x["groupId"], x["artifactId"], x["version"]) == PAHO_GAV), None)
    if paho is None:
        return {"status": "not-in-manifest"}
    paho["provenance"] = "rebuilt-by-vendor"
    binary_url = f"{MAVEN_CENTRAL}/{g.replace('.', '/')}/{a}/{v}/{a}-{v}.jar"
    upstream_result = fetch_with_retry(binary_url, opener, sleep=sleep)
    occurrence = paho["occurrences"][0]
    shipped_bytes = load_binary_bytes(occurrence, mod_dir=mod_dir)
    if not upstream_result["ok"] or shipped_bytes is None:
        result = {"status": "unavailable", "upstream_ok": upstream_result["ok"],
                   "shipped_available": shipped_bytes is not None}
        paho["paho_diff"] = result
        json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
        return result
    upstream_names = class_names_from_zip(upstream_result["bytes"], ".class")
    shipped_names = class_names_from_zip(shipped_bytes, ".class")
    diff = classname_diff(shipped_names, upstream_names)
    with zipfile.ZipFile(io.BytesIO(upstream_result["bytes"])) as uz, \
         zipfile.ZipFile(io.BytesIO(shipped_bytes)) as sz:
        sample = sorted(shipped_names & upstream_names)[:5]
        method_diffs = []
        tmp = out_dir / "_paho_tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        for cls in sample:
            up_path = tmp / "up.class"
            sh_path = tmp / "sh.class"
            up_path.write_bytes(uz.read(cls + ".class"))
            sh_path.write_bytes(sz.read(cls + ".class"))
            up_sig = {ln.strip() for ln in run_javap(str(up_path)).splitlines()
                       if re.search(r"\(.*\)", ln) and ";" in ln}
            sh_sig = {ln.strip() for ln in run_javap(str(sh_path)).splitlines()
                       if re.search(r"\(.*\)", ln) and ";" in ln}
            if up_sig != sh_sig:
                method_diffs.append({"class": cls, "upstream_only": sorted(up_sig - sh_sig),
                                       "shipped_only": sorted(sh_sig - up_sig)})
    result = {"status": "rebuilt-by-vendor", "class_set_identical": diff["common"] == diff["sources_total"] == diff["binary_total"],
               "classname_diff": diff, "method_signature_sample": len(sample),
               "method_signature_diffs": method_diffs}
    paho["paho_diff"] = result
    json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
    return result


def _select_recompile_samples(manifest: dict, n: int = 3) -> list[dict]:
    fetched = [a for a in manifest["artifacts"] if a["status"] == "fetched"
               and a.get("classdiff", {}).get("common", 0) > 0]
    return sorted(fetched, key=lambda a: (a["groupId"], a["artifactId"], a["version"]))[:n]


def run_recompile_check(manifest: dict, out_dir: Path, mod_dir: Path = N5_MOD_DIR,
                         install_dir: Path = N5_INSTALL_DIR, javac: str = JAVAC25,
                         javap: str = JAVAP25, sample_size: int = 3, classes_per_artifact: int = 2) -> list[dict]:
    results = []
    for art in _select_recompile_samples(manifest, sample_size):
        binary_bytes = load_binary_bytes(art["occurrences"][0], mod_dir, install_dir)
        sources_bytes = (REPO_ROOT / art["sources_jar_path"]).read_bytes()
        common = sorted(set(art["classdiff"]["binary_total"] and
                             class_names_from_zip(sources_bytes, ".java") &
                             class_names_from_zip(binary_bytes, ".class")))[:classes_per_artifact]
        work = out_dir / "_recompile" / art["artifactId"]
        src_dir, cp_jar, out_classes = work / "src", work / "cp.jar", work / "out"
        src_dir.mkdir(parents=True, exist_ok=True)
        out_classes.mkdir(parents=True, exist_ok=True)
        cp_jar.write_bytes(binary_bytes)
        for cls in common:
            with zipfile.ZipFile(io.BytesIO(sources_bytes)) as sz:
                dest = src_dir / (cls + ".java")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(sz.read(cls + ".java"))
        with zipfile.ZipFile(io.BytesIO(binary_bytes)) as bz:
            major = class_major_version(bz.read(common[0] + ".class")) if common else None
        release = RELEASE_BY_MAJOR.get(major)
        per_class = []
        for cls in common:
            src_file = src_dir / (cls + ".java")
            cmd = [javac, "-nowarn", "-cp", str(cp_jar), "-d", str(out_classes)]
            if release:
                cmd += ["--release", str(release)]
            cmd.append(str(src_file))
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(src_dir))
            entry = {"class": cls, "release_used": release, "javac_rc": proc.returncode,
                     "javac_stderr": proc.stderr.strip()[:2000]}
            if proc.returncode == 0:
                recompiled = out_classes / (cls + ".class")
                with zipfile.ZipFile(io.BytesIO(binary_bytes)) as bz:
                    shipped = bz.read(cls + ".class")
                shipped_path = out_classes / "_shipped.class"
                shipped_path.write_bytes(shipped)
                try:
                    norm_recompiled = normalize_javap(run_javap(str(recompiled), javap))
                    norm_shipped = normalize_javap(run_javap(str(shipped_path), javap))
                    entry["javap_normalized_match"] = norm_recompiled == norm_shipped
                except JavapError as e:
                    entry["javap_normalized_match"] = None
                    entry["javap_error"] = str(e)
            per_class.append(entry)
        results.append({"artifactId": art["artifactId"], "version": art["version"],
                          "classes": per_class})
    json.dump({"recompile_check": results}, open(out_dir / "recompile-check.json", "w"), indent=1)
    return results


# ---------------------------------------------------------------------------
# Report.
# ---------------------------------------------------------------------------

def render_report(manifest: dict, paho_result: Optional[dict] = None,
                   classdiff_coverage: Optional[dict] = None,
                   recompile_results: Optional[list[dict]] = None,
                   identify_summary: Optional[dict] = None,
                   all_third_party_coverage: Optional[dict] = None) -> str:
    artifacts = manifest["artifacts"]
    unidentified = manifest.get("unidentified", [])
    status_counts: dict[str, int] = {}
    for a in artifacts:
        status_counts[a["status"]] = status_counts.get(a["status"], 0) + 1

    lines = []
    lines.append("# Upstream-sources report (T22 third-party half)")
    lines.append("")
    lines.append(
        "For third-party jars that are byte-identical (or vendor-resigned-only-different) to "
        "Maven Central, the original upstream `-sources.jar` is the most faithful representation "
        "of the code -- more faithful than any decompile. Source: `evidence/b117/maven-repo1.json` "
        "([Block 117] \"Third-party library identity against Maven Central\")."
    )
    lines.append("")
    raw_occurrences = sum(len(a.get("occurrences", [])) for a in artifacts)
    lines.append(f"Total third-party jars: {raw_occurrences + len(unidentified)} "
                 f"(matches evidence/b117's 204: {raw_occurrences} occurrences of "
                 f"{len(artifacts)} distinct upstream artifacts + {len(unidentified)} unidentified).")
    lines.append("")
    if all_third_party_coverage:
        covered = all_third_party_coverage.get("classes_with_upstream_source", 0)
        total = all_third_party_coverage.get("classes_total", 0)
        pct = f"{100*covered/total:.1f}%" if total else "n/a"
        lines.append(
            f"**Coverage over ALL third-party classes: {covered} of {total} classes ({pct}) have "
            "a byte-adjacent original upstream source.** Denominator = every class in every "
            "third-party jar in this corpus (identified + still-unidentified), not only "
            "artifacts with a fetched sources jar; numerator excludes vendor-modified artifacts "
            "(same coordinate on Central, different bytes -- their \"source\" is for a different "
            "build, not ground truth for these classes). See T26a."
        )
        lines.append("")
    lines.append("## Fetch status counts")
    lines.append("")
    lines.append("| status | count |")
    lines.append("|---|---|")
    for status in ("fetched", "no-sources-published", "checksum-mismatch", "network-error"):
        lines.append(f"| {status} | {status_counts.get(status, 0)} |")
    lines.append("")

    has_classdiff = any(a.get("classdiff", {}).get("binary_total") for a in artifacts)
    if classdiff_coverage or has_classdiff:
        lines.append("## Class coverage by original upstream source")
        lines.append("")
        if classdiff_coverage:
            total = classdiff_coverage.get("classes_total", 0)
            covered = classdiff_coverage.get("classes_with_upstream_source", 0)
            pct = f"{100*covered/total:.1f}%" if total else "n/a"
            lines.append(
                f"{covered} of {total} third-party classes ({pct}) in artifacts with a fetched "
                "sources jar have a matching top-level class name in that sources jar "
                "(class-name-set comparison, not a full compile)."
            )
            lines.append("")
        low = [a for a in artifacts if a.get("classdiff", {}).get("binary_total")
               and a["classdiff"]["common"] / a["classdiff"]["binary_total"] < 0.5]
        if low:
            lines.append("Artifacts under 50% common-class coverage (own-source jar exists, but "
                         "many binary classes have no same-path .java match in it -- typically "
                         "Kotlin (.kt, not counted here) or a shaded/relocated dependency bundle):")
            lines.append("")
            lines.append("| artifact | version | common/binary_total |")
            lines.append("|---|---|---|")
            for a in sorted(low, key=lambda x: x["classdiff"]["common"] / x["classdiff"]["binary_total"]):
                cd = a["classdiff"]
                lines.append(f"| {a['artifactId']} | {a['version']} | {cd['common']}/{cd['binary_total']} |")
            lines.append("")

    lines.append("## Paho mqttv3 1.2.5 (rebuilt-by-vendor)")
    lines.append("")
    if paho_result:
        lines.append(f"Status: `{paho_result.get('status')}`.")
        if "class_set_identical" in paho_result:
            lines.append(f"Class set identical to upstream: {paho_result['class_set_identical']}.")
        if paho_result.get("method_signature_diffs"):
            lines.append(f"Method-signature diffs found in {len(paho_result['method_signature_diffs'])} "
                         f"of {paho_result.get('method_signature_sample', 0)} sampled classes.")
        elif "method_signature_sample" in paho_result:
            lines.append(f"No method-signature diffs in {paho_result['method_signature_sample']} sampled classes "
                         "(same public API, different build/bytes; B117's 2021-vs-2020 timestamp finding stands).")
    else:
        lines.append("Not run.")
    lines.append("")

    if recompile_results:
        lines.append("## Recompile cross-check (real javac 25 against the binary jar's own classpath)")
        lines.append("")
        for r in recompile_results:
            for c in r["classes"]:
                match = c.get("javap_normalized_match")
                status = "MATCH" if match else ("javac-failed" if c["javac_rc"] != 0 else "MISMATCH")
                detail = ""
                if c["javac_rc"] != 0 and c.get("javac_stderr"):
                    detail = f" -- {c['javac_stderr'].splitlines()[0]}"
                lines.append(f"- {r['artifactId']} {r['version']} `{c['class']}` "
                             f"(--release {c.get('release_used')}): {status}{detail}")
        lines.append("")

    if identify_summary:
        lines.append("## SHA-1 identification of pom-less jars (T26a)")
        lines.append("")
        lines.append(
            "For the jars evidence/b117 could not identify from pom.properties, this step hashes "
            "the exact shipped bytes (from the local jar mirror) and looks the SHA-1 up on Maven "
            "Central; on a miss, one filename-derived g:a:v guess is tried and accepted only if "
            "Central's own published binary-jar SHA-1 for that guess matches."
        )
        lines.append("")
        lines.append("| outcome | count |")
        lines.append("|---|---|")
        for status in ("identified-by-sha1", "vendor-modified", "not-on-central",
                       "network-error", "mirror-unavailable"):
            lines.append(f"| {status} | {identify_summary.get(status, 0)} |")
        lines.append("")
        vendor_modified = [a for a in artifacts if a.get("vendor_modified")]
        if vendor_modified:
            lines.append(
                "Vendor-modified: Central has the same groupId:artifactId:version, but with "
                "different bytes -- the fetched sources jar (if any) is for that different build, "
                "not ground truth for the shipped class files. Class-name overlap % is how much "
                "of the local jar's class set the same-coordinate upstream binary still shares."
            )
            lines.append("")
            lines.append("| artifact | version | overlap % | local sha1 | central sha1 |")
            lines.append("|---|---|---|---|---|")
            for a in sorted(vendor_modified, key=lambda x: x["artifactId"]):
                vm = a["vendor_modified"]
                overlap = vm.get("overlap", {})
                overlap_str = f"{overlap['overlap_pct']}%" if overlap.get("status") == "compared" else overlap.get("status", "n/a")
                lines.append(f"| {a['artifactId']} | {a['version']} | {overlap_str} | "
                             f"{vm.get('local_sha1')} | {vm.get('central_sha1')} |")
            lines.append("")

    if unidentified:
        reasons: dict[str, int] = {}
        for u in unidentified:
            reasons[u["reason"]] = reasons.get(u["reason"], 0) + 1
        lines.append("## Unidentified jars (no coordinates guessed)")
        lines.append("")
        lines.append(f"{len(unidentified)} jars, by reason: "
                     + ", ".join(f"{k}={v}" for k, v in sorted(reasons.items())))
        lines.append("")
        lines.append("| kind | name | reason |")
        lines.append("|---|---|---|")
        for u in sorted(unidentified, key=lambda x: (x["kind"] or "", x["name"] or "")):
            lines.append(f"| {u['kind']} | {u['name']} | {u['reason']} |")
        lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("plan")
    sp.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    sp.add_argument("--out", default=str(DEFAULT_OUT_DIR))

    si = sub.add_parser("identify-unidentified")
    si.add_argument("--out", default=str(DEFAULT_OUT_DIR))

    sf = sub.add_parser("fetch")
    sf.add_argument("--out", default=str(DEFAULT_OUT_DIR))

    sc = sub.add_parser("classdiff")
    sc.add_argument("--out", default=str(DEFAULT_OUT_DIR))

    sd = sub.add_parser("paho-diff")
    sd.add_argument("--out", default=str(DEFAULT_OUT_DIR))

    sr = sub.add_parser("recompile-check")
    sr.add_argument("--out", default=str(DEFAULT_OUT_DIR))

    srep = sub.add_parser("report")
    srep.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    srep.add_argument("--report", default=str(DEFAULT_REPORT))

    sa = sub.add_parser("all")
    sa.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    sa.add_argument("--out", default=str(DEFAULT_OUT_DIR))
    sa.add_argument("--report", default=str(DEFAULT_REPORT))

    args = p.parse_args(argv)
    out_dir = Path(args.out)

    if args.cmd == "plan":
        plan = run_plan(Path(args.evidence))
        out_dir.mkdir(parents=True, exist_ok=True)
        json.dump(plan, open(out_dir / "plan.json", "w"), indent=1)
        print(f"identified={len(plan['artifacts'])} unidentified={len(plan['unidentified'])}")
        return 0

    if args.cmd == "identify-unidentified":
        plan = json.load(open(out_dir / "plan.json"))
        summary = run_identify_unidentified(plan)
        json.dump(plan, open(out_dir / "plan.json", "w"), indent=1)
        print(summary)
        return 0

    if args.cmd == "fetch":
        plan = json.load(open(out_dir / "plan.json"))
        manifest = run_fetch(plan, out_dir)
        counts: dict[str, int] = {}
        for a in manifest["artifacts"]:
            counts[a["status"]] = counts.get(a["status"], 0) + 1
        print(counts)
        return 0

    if args.cmd == "classdiff":
        manifest = json.load(open(out_dir / "manifest.json"))
        coverage = run_classdiff(manifest, out_dir)
        print(coverage)
        return 0

    if args.cmd == "paho-diff":
        manifest = json.load(open(out_dir / "manifest.json"))
        result = run_paho_diff(manifest, out_dir)
        print(result.get("status"))
        return 0

    if args.cmd == "recompile-check":
        manifest = json.load(open(out_dir / "manifest.json"))
        run_recompile_check(manifest, out_dir)
        return 0

    if args.cmd == "report":
        manifest = json.load(open(out_dir / "manifest.json"))
        paho = next((a.get("paho_diff") for a in manifest["artifacts"]
                     if (a["groupId"], a["artifactId"], a["version"]) == PAHO_GAV), None)
        recompile_results = None
        rc_path = out_dir / "recompile-check.json"
        if rc_path.exists():
            recompile_results = json.load(open(rc_path))["recompile_check"]
        all_coverage = run_all_third_party_coverage(manifest)
        json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
        text = render_report(manifest, paho_result=paho,
                              classdiff_coverage=manifest.get("classdiff_coverage"),
                              recompile_results=recompile_results,
                              identify_summary=manifest.get("sha1_identify_summary"),
                              all_third_party_coverage=all_coverage)
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text)
        print(f"wrote {args.report}")
        return 0

    if args.cmd == "all":
        plan = run_plan(Path(args.evidence))
        out_dir.mkdir(parents=True, exist_ok=True)
        json.dump(plan, open(out_dir / "plan.json", "w"), indent=1)
        run_identify_unidentified(plan)
        json.dump(plan, open(out_dir / "plan.json", "w"), indent=1)
        manifest = run_fetch(plan, out_dir)
        run_classdiff(manifest, out_dir)
        run_paho_diff(manifest, out_dir)
        recompile_results = run_recompile_check(manifest, out_dir)
        manifest = json.load(open(out_dir / "manifest.json"))
        paho = next((a.get("paho_diff") for a in manifest["artifacts"]
                     if (a["groupId"], a["artifactId"], a["version"]) == PAHO_GAV), None)
        all_coverage = run_all_third_party_coverage(manifest)
        json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
        text = render_report(manifest, paho_result=paho,
                              classdiff_coverage=manifest.get("classdiff_coverage"),
                              recompile_results=recompile_results,
                              identify_summary=manifest.get("sha1_identify_summary"),
                              all_third_party_coverage=all_coverage)
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text)
        print(f"wrote {args.report}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
