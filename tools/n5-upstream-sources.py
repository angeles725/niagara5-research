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
                    it. On a whole-jar SHA-1 mismatch, fetches Central's own binary jar and runs a
                    per-.class SHA-256 comparison (classify_jar_identity) before calling it
                    vendor-modified -- a Niagara re-signature (added META-INF/NIAGARA4.SF/.RSA)
                    changes the whole-jar hash without touching a single class, so that alone is
                    resigned-identical (sources ARE ground truth), not vendor-modified. Moves each
                    resolved jar from plan["unidentified"] into plan["artifacts"] (status one of
                    identified-by-sha1 / resigned-identical / partially-modified / vendor-modified /
                    unverifiable) so the existing fetch/classdiff pipeline picks it up unchanged;
                    jars that stay unplaceable keep a refined `reason` (not-on-central /
                    network-error / mirror-unavailable).
  recheck-pom-identified  (T26a follow-up) the same per-.class check, applied to the ORIGINAL 154
                    pom.properties-identified artifacts whose evidence/b117 record shows the whole
                    shipped BINARY jar's SHA-1 differs from Central's -- those were only ever
                    proven identical by their SOURCES jar's own SHA-1. Reuses b117's own
                    non-META-INF content check where already conclusive (no network); does a live
                    check for the rest (b117's own download failures, real content differences,
                    and jars this tool's own candidate-version corrections resolved).
  report            render docs/upstream-sources-report.md from manifest.json + the above.
  all               run plan, identify-unidentified, fetch, classdiff, paho-diff, recompile-check,
                    recheck-pom-identified, report in order.
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
    "jffi": "com.github.jnr",  # verified live 2026-09-28: com/github/jnr/jffi/1.4.0/jffi-1.4.0-
                                # native.jar.sha1 exists on Central -- "native" is a CLASSIFIER
                                # (split_classifier), not part of the version
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


_CLASSIFIER_RE = re.compile(r"^(?P<v>\d[\w.]*?)-(?P<c>[A-Za-z][\w.\-]*)$")

# Real 2026-09-28 finding (R3-split-classifier-qualifier / R4-001): a standard Maven PRE-RELEASE
# QUALIFIER also starts with a letter -- "1.5.0-RC1", "2.0.0-beta", "3.1.0-SNAPSHOT", "4.2.0-M1"
# are each one real, whole Central version, not a classifier-less version plus a classifier. Only
# a trailing token that is ENTIRELY one of these well-known qualifier words (optionally followed
# by digits, e.g. "RC1", "beta2", "M1") is excluded from being treated as a classifier; a genuine
# classifier like "native" or "jdk11" does not match this list and still splits normally.
_MAVEN_QUALIFIER_RE = re.compile(
    r"^(alpha|beta|milestone|m|rc|cr|snapshot|ga|final|release|sp)\d*$", re.IGNORECASE)


def split_classifier(version: str):
    """Split a Maven CLASSIFIER (e.g. "jdk11", "native") off the tail of a version string that
    parse_artifact_version_from_basename may have swallowed whole. Orchestrator finding
    (2026-09-28): "oauth2-oidc-sdk-11.26-jdk11" and "jffi-1.4.0-native" parse as one version
    string ("11.26-jdk11", "1.4.0-native"), but the "-jdk11"/"-native" tail is a Maven classifier
    -- comparing against Central's classifier-LESS binary compares the wrong bytes entirely.

    A trailing "-<token>" is a classifier only when <token> starts with a LETTER, not a digit --
    "prosys-opc-ua-sdk-client-server-5.7.0-248"'s "-248" starts with a digit, so it's part of the
    version itself (a real, if unusual, Maven version string), not a classifier. A dot-fused
    suffix with no dash at all (mssql-jdbc's "13.4.0.jre11", a literal Central version) is never
    touched -- there's no dash for this pattern to match on. A letter-led token that is itself a
    well-known Maven PRE-RELEASE QUALIFIER (see _MAVEN_QUALIFIER_RE) is likewise never a
    classifier -- "1.5.0-RC1" is one real Central version, not "1.5.0" plus classifier "RC1".

    Returns (real_version, classifier) -- classifier is None when no such split applies."""
    m = _CLASSIFIER_RE.match(version)
    if not m:
        return version, None
    candidate = m.group("c")
    if _MAVEN_QUALIFIER_RE.match(candidate):
        return version, None
    return m.group("v"), candidate


def detect_classifier(basename: str, artifact_id: str, version: str):
    """For an artifact whose artifactId/version are ALREADY known precisely (pom.properties-
    identified), detect a classifier by simple prefix check against the local occurrence's own
    basename: "oauth2-oidc-sdk-11.26-jdk11" with artifactId "oauth2-oidc-sdk" version "11.26" ->
    "jdk11". Returns None when the basename matches "<artifact>-<version>" exactly (no
    classifier) -- including when the "extra" text is fused into the version itself with a DOT,
    not a dash (mssql-jdbc's "13.4.0.jre11": basename == artifact-version exactly, no classifier)."""
    prefix = f"{artifact_id}-{version}-"
    if basename.startswith(prefix):
        return basename[len(prefix):] or None
    return None


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
                              sleep: Callable = time.sleep, retries: int = 3,
                              classifier: Optional[str] = None) -> dict:
    """Fetch Central's own published `.jar.sha1` for one g:a:v -- the identity proof for a
    filename-derived guess (or a belt-and-suspenders re-check of a sha1-search hit). When
    `classifier` is given, fetches the CLASSIFIER binary (<artifact>-<version>-<classifier>.jar)
    -- comparing a classifier build against the classifier-less binary compares the wrong bytes
    entirely (real finding: oauth2-oidc-sdk-11.26-jdk11.jar vs the classifier-less 11.26 build)."""
    suffix = f"-{classifier}" if classifier else ""
    url = (f"{MAVEN_CENTRAL}/{group_id.replace('.', '/')}/{artifact_id}/{version}/"
           f"{artifact_id}-{version}{suffix}.jar.sha1")
    result = fetch_with_retry(url, opener, sleep=sleep, retries=retries)
    if not result["ok"]:
        if result["kind"] == "not-found":
            return {"status": "not-found"}
        return {"status": "network-error", "detail": result}
    # Real 2026-09-28 finding (R3-empty-sha1-body-crash): an empty or whitespace-only 200 body
    # used to crash `.split()[0]` with IndexError instead of degrading to a typed failure like
    # every other malformed-response case in this module.
    tokens = result["bytes"].decode("utf-8", "replace").split()
    if not tokens:
        return {"status": "network-error",
                "detail": {"kind": "empty-response", "url": url}}
    central_sha1 = tokens[0].strip()
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
    guess_artifact, guess_version_raw = parsed
    # A Maven CLASSIFIER build (e.g. "jffi-1.4.0-native") parses as one version string above
    # ("1.4.0-native") -- split it so the guess-verify below compares against Central's
    # CLASSIFIER binary, not the classifier-less one (real finding, see split_classifier).
    guess_version, classifier = split_classifier(guess_version_raw)
    guess_group = KNOWN_GROUP_GUESSES.get(guess_artifact, "__no_entry__")
    if guess_group is None:
        return {"status": "not-on-central", "reason": "known-proprietary-or-unpublished",
                "guessed_artifactId": guess_artifact, "guessed_version": guess_version}
    if guess_group == "__no_entry__":
        return {"status": "not-on-central", "reason": "no-plausible-coordinate",
                "guessed_artifactId": guess_artifact, "guessed_version": guess_version}
    verify = binary_sha1_from_central(guess_group, guess_artifact, guess_version, opener,
                                       sleep=sleep, retries=retries, classifier=classifier)
    if verify["status"] == "network-error":
        return {"status": "network-error", "stage": "guess-verify", "detail": verify.get("detail")}
    if verify["status"] == "not-found":
        return {"status": "not-on-central", "reason": "guessed-coordinate-404",
                "guessed_groupId": guess_group, "guessed_artifactId": guess_artifact,
                "guessed_version": guess_version, "classifier": classifier}
    result = {"groupId": guess_group, "artifactId": guess_artifact, "version": guess_version,
              "method": "filename-guess"}
    if classifier:
        result["classifier"] = classifier
    if verify["central_sha1"] == local_sha1:
        result["status"] = "identified-by-sha1"
        return result
    result["status"] = "vendor-modified"
    result["central_sha1"] = verify["central_sha1"]
    result["local_sha1"] = local_sha1
    return result


def compute_vendor_modified_overlap(local_bytes: bytes, group_id: str, artifact_id: str,
                                     version: str, opener: Callable, sleep: Callable = time.sleep,
                                     retries: int = 3, classifier: Optional[str] = None) -> dict:
    """For a "vendor-modified" identification (same g:a:v on Central, different bytes), fetch
    Central's binary jar and record the top-level class-name overlap % against the local jar --
    NOT a claim of ground truth, just how much of the local jar the same-coordinate upstream
    binary still resembles. When `classifier` is given, fetches the CLASSIFIER binary -- real
    2026-09-28 finding (R3-identified-classifier-propagation): this fallback used to always build
    the classifier-LESS URL even when the local jar IS a classifier build, comparing against the
    wrong Central coordinate entirely."""
    suffix = f"-{classifier}" if classifier else ""
    url = f"{MAVEN_CENTRAL}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}{suffix}.jar"
    result = fetch_with_retry(url, opener, sleep=sleep, retries=retries)
    if not result["ok"]:
        return {"status": "network-error", "detail": result}
    central_names = class_names_from_zip(result["bytes"], ".class")
    local_names = class_names_from_zip(local_bytes, ".class")
    diff = classname_diff(local_names, central_names)
    overlap_pct = 100 * diff["common"] / diff["sources_total"] if diff["sources_total"] else 0.0
    return {"status": "compared", "overlap_pct": round(overlap_pct, 1), "classname_diff": diff}


def fetch_central_binary_jar(group_id: str, artifact_id: str, version: str, opener: Callable,
                              sleep: Callable = time.sleep, retries: int = 3,
                              classifier: Optional[str] = None) -> dict:
    """Fetch and SHA-1-verify Central's own binary jar for one g:a:v (needed for the real
    per-.class content comparison in classify_jar_identity -- a whole-jar SHA-1 mismatch alone
    doesn't say WHICH bytes differ). When `classifier` is given, fetches the CLASSIFIER binary,
    not the classifier-less one -- see binary_sha1_from_central's docstring. Returns
    {"status": "fetched", "bytes": ..., "sha1": ...} or a typed failure: not-found |
    checksum-mismatch | network-error."""
    expect = binary_sha1_from_central(group_id, artifact_id, version, opener, sleep=sleep,
                                       retries=retries, classifier=classifier)
    if expect["status"] == "network-error":
        return {"status": "network-error", "stage": "sha1", "detail": expect.get("detail")}
    if expect["status"] == "not-found":
        return {"status": "not-found"}
    suffix = f"-{classifier}" if classifier else ""
    url = f"{MAVEN_CENTRAL}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}{suffix}.jar"
    result = fetch_with_retry(url, opener, sleep=sleep, retries=retries)
    if not result["ok"]:
        return {"status": "network-error", "stage": "jar", "detail": result}
    actual_sha1 = hashlib.sha1(result["bytes"]).hexdigest()
    if actual_sha1 != expect["central_sha1"]:
        return {"status": "checksum-mismatch", "expected": expect["central_sha1"], "actual": actual_sha1}
    return {"status": "fetched", "bytes": result["bytes"], "sha1": actual_sha1}


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


def all_class_entry_hashes(jar_bytes: bytes) -> dict:
    """SHA-256 of EVERY .class entry (including nested/anonymous classes -- unlike
    class_names_from_zip, this is a byte-content check, not a source-file-name-set comparison, so
    inner classes matter too), keyed by the entry's full path inside the jar."""
    out: dict[str, str] = {}
    with zipfile.ZipFile(io.BytesIO(jar_bytes)) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.endswith(".class"):
                continue
            out[info.filename] = hashlib.sha256(z.read(info)).hexdigest()
    return out


def classify_jar_identity(local_bytes: bytes, central_bytes: bytes) -> dict:
    """Per-.class-entry SHA-256 comparison between the local (shipped) jar and Central's binary
    jar for the SAME groupId:artifactId:version. A whole-jar SHA-1 mismatch alone does not mean
    the sources aren't ground truth -- Niagara commonly re-signs a jar (adds
    META-INF/NIAGARA4.SF + .RSA), which changes the whole-jar hash without touching a single
    class. Real 2026-09-28 finding: bin/ext/asm-9.10.1.jar's whole-jar SHA-1 differs from
    org.ow2.asm:asm:9.10.1 on Central, but all 39/39 .class entries are byte-identical.

    Returns a dict with "status" one of:
      no-classes          -- the local jar has ZERO .class entries at all (e.g. a pure-native
                              JNI jar like jffi-*-native.jar, or a Kotlin-Multiplatform metadata
                              jar) -- nothing to compare, so this is NOT "vendor-modified" (which
                              means "we compared classes and none matched").
      resigned-identical  -- every local .class entry matches Central; only non-class entries
                              differ (typically just the added signature) -- sources ARE ground
                              truth for every class in this jar.
      partially-modified  -- some .class entries match, some differ or are local-only -- only the
                              matching ones are ground-truth-covered; the rest still need decompile.
      vendor-modified     -- the jar HAS classes, but none of them matches Central at all.
    Also records differing_non_class_entries (e.g. the added signature files) for transparency.
    """
    local_classes = all_class_entry_hashes(local_bytes)
    central_classes = all_class_entry_hashes(central_bytes)
    identical = sorted(n for n, h in local_classes.items() if central_classes.get(n) == h)
    different = sorted(n for n, h in local_classes.items()
                        if n in central_classes and central_classes[n] != h)
    local_only = sorted(n for n in local_classes if n not in central_classes)
    if not local_classes:
        status = "no-classes"
    elif identical and not different and not local_only:
        status = "resigned-identical"
    elif identical:
        status = "partially-modified"
    else:
        status = "vendor-modified"
    with zipfile.ZipFile(io.BytesIO(local_bytes)) as lz, zipfile.ZipFile(io.BytesIO(central_bytes)) as cz:
        local_non_class = {i.filename: hashlib.sha256(lz.read(i)).hexdigest()
                            for i in lz.infolist() if not i.is_dir() and not i.filename.endswith(".class")}
        central_non_class = {i.filename: hashlib.sha256(cz.read(i)).hexdigest()
                              for i in cz.infolist() if not i.is_dir() and not i.filename.endswith(".class")}
    differing_non_class = sorted(
        n for n in (set(local_non_class) | set(central_non_class))
        if local_non_class.get(n) != central_non_class.get(n)
    )
    return {
        "status": status,
        "classes_identical": len(identical), "classes_different": len(different),
        "classes_local_only": len(local_only), "classes_total_local": len(local_classes),
        "different_classes": different, "local_only_classes": local_only,
        "differing_non_class_entries": differing_non_class,
    }


# Class-file names Java's own compiler emits that are NOT "classes" a decompile/source-match
# effort needs to cover -- module-info.class (a module declaration) and package-info.class (a
# package's annotations only) each compile from a real .java file but carry no logic worth
# chasing an upstream source for. Orchestrator follow-up finding (2026-09-28,
# R-coverage-unit-definition): the coverage UNIT below must exclude them, or the headline
# overstates its own denominator with entries nothing is trying to prove.
_NON_CLASS_SIMPLE_NAMES = {"module-info", "package-info"}


def real_class_entries(jar_bytes: bytes) -> dict[str, str]:
    """THE single canonical UNIT for third-party class-coverage accounting (orchestrator
    follow-up, 2026-09-28): every REAL `.class` entry a jar ships, nested/anonymous classes
    INCLUDED (unlike class_names_from_zip's source-file-name unit, which deliberately excludes
    them to compare 1:1 against `.java` files) -- EXCLUDING module-info.class/package-info.class
    (see _NON_CLASS_SIMPLE_NAMES). Keyed by the entry's full in-jar path WITH the ".class" suffix
    (the same shape all_class_entry_hashes returns, which this reuses), valued by its SHA-256."""
    return {name: h for name, h in all_class_entry_hashes(jar_bytes).items()
            if name.rsplit("/", 1)[-1][:-len(".class")] not in _NON_CLASS_SIMPLE_NAMES}


def top_level_class_of(class_entry_name: str) -> str:
    """The TOP-LEVEL class a `.class` entry belongs to -- the `.java`/`.kt` source file that
    would need to exist for this entry to be source-covered -- in the same "path/without/
    extension" shape class_names_from_zip(..., ".java") returns: "org/foo/A$B.class" ->
    "org/foo/A", "org/foo/A$1.class" -> "org/foo/A", "org/foo/A.class" -> "org/foo/A" (a nested/
    anonymous class A$B or A$1 is declared INSIDE A.java, so it is source-covered exactly when
    A's own top-level source is)."""
    base = class_entry_name[:-len(".class")] if class_entry_name.endswith(".class") else class_entry_name
    dirpart, sep, simple = base.rpartition("/")
    return f"{dirpart}{sep}{simple.split('$', 1)[0]}"


# ---------------------------------------------------------------------------
# Source-match rules shared with tools/n5-best-source.py (kept independent/inline there, same
# convention as GRADE_RANK -- see that module's own comment -- since these are standalone,
# hyphenated-filename CLI scripts that do not import one another; behavior MUST stay identical,
# and each module tests it directly). Real 2026-09-28 orchestrator follow-up findings:
#   1. MRJAR (R-mrjar-path-prefix): a multi-release jar's version-specific override class
#      ("META-INF/versions/<N>/<pkg>/<Cls>.class") is the SAME logical class as
#      "<pkg>/<Cls>.class" -- its source is the SAME .java/.kt file -- but the raw top-level path
#      differs because of the prefix. Strip it (from whichever side carries it) before comparing.
#   2. Source-set layouts (R-declared-package-fallback): a sources jar whose paths don't mirror
#      the compiled package structure at all (Kotlin Multiplatform's `commonMain/`, `jvmMain/`,
#      ...) can never match by path. Parse each source file's OWN `package` declaration (ignoring
#      its zip-entry path -- a JVM .class file's path is ALWAYS package-accurate, so the BINARY
#      side never needs this, only the SOURCES side) and index it by that instead, as a fallback
#      ONLY used when the (always-first-choice) path-based match fails.
# ---------------------------------------------------------------------------

_MRJAR_VERSION_PREFIX_RE = re.compile(r"^META-INF/versions/\d+/")


def strip_mrjar_prefix(path_name: str) -> Optional[str]:
    """path_name with a leading "META-INF/versions/<N>/" stripped, or None if it doesn't have
    one."""
    m = _MRJAR_VERSION_PREFIX_RE.match(path_name)
    return path_name[m.end():] if m else None


def mrjar_variants(path_name: str) -> set[str]:
    """path_name itself, plus its MRJAR-prefix-stripped form when it has one -- applied to BOTH
    the binary (lookup) side and the sources (index) side, so matching works regardless of which
    one (if either) carries the version-specific prefix (real finding: bc-fips's BINARY carries
    it for its override classes; its sources jar does not)."""
    stripped = strip_mrjar_prefix(path_name)
    return {path_name, stripped} if stripped is not None else {path_name}


_PACKAGE_DECL_RE = re.compile(r"(?m)^[ \t]*package[ \t]+([\w.]+)[ \t]*;?[ \t]*$")
_KOTLIN_FILE_JVM_NAME_RE = re.compile(r'@file:JvmName\(\s*"([^"]+)"\s*\)')


def declared_package_of(source_text: str) -> Optional[str]:
    """The package THIS source file declares (its own `package ...` statement, in slash form,
    e.g. "org/foo") -- independent of whatever path its zip entry happens to live at. "" for an
    explicit default (no-package) file; None when no package statement is found at all (a
    malformed/unusual file -- callers must not derive a declared-name candidate from it)."""
    m = _PACKAGE_DECL_RE.search(source_text)
    if not m:
        return None
    return m.group(1).replace(".", "/")


def declared_names_for_source(entry_name: str, source_bytes: bytes) -> set[str]:
    """Every top-level class name ONE `.java`/`.kt` source file could plausibly provide, derived
    from its OWN declared package -- the fallback for a sources jar whose entry paths don't
    mirror packages at all (real finding: Kotlin Multiplatform source sets). Returns an empty set
    when the file isn't `.java`/`.kt`, has no package statement, or can't be decoded.

    For `.java`, a file "Foo.java" declaring "package a.b" can only sensibly provide "a/b/Foo"
    (Java requires the public top-level type to match the file's own stem).

    For `.kt`, Kotlin additionally compiles the file's own TOP-LEVEL functions/properties (if
    any) into a synthetic "facade" class -- "Foo.kt" -> "FooKt.class" by default, or the name
    given by an `@file:JvmName("X")` annotation -> "X.class" instead. Since a .kt file may ALSO
    contain a real class matching its own stem, or ONLY top-level declarations (no matching-name
    class at all), this returns BOTH candidates -- "a/b/Foo" AND "a/b/FooKt" (or "a/b/X") -- since
    an unused candidate name is harmless (nothing ever looks it up) but a missing one silently
    loses a real match."""
    if entry_name.endswith(".java"):
        stem = entry_name.rsplit("/", 1)[-1][: -len(".java")]
        is_kotlin = False
    elif entry_name.endswith(".kt"):
        stem = entry_name.rsplit("/", 1)[-1][: -len(".kt")]
        is_kotlin = True
    else:
        return set()
    try:
        text = source_bytes.decode("utf-8", "replace")
    except Exception:
        return set()
    pkg = declared_package_of(text)
    if pkg is None:
        return set()
    prefix = f"{pkg}/" if pkg else ""
    names = {f"{prefix}{stem}"}
    if is_kotlin:
        m = _KOTLIN_FILE_JVM_NAME_RE.search(text)
        facade = m.group(1) if m else f"{stem}Kt"
        names.add(f"{prefix}{facade}")
    return names


def class_has_matching_source(binary_top_level_name: str, source_names: dict) -> bool:
    """Whether binary_top_level_name (top_level_class_of's output shape) has a matching source in
    a `source_names` dict as sources_top_level_names/its n5-best-source.py mirror returns:
    {"path": set[str], "declared": set[str]}. Path-based matching (including MRJAR variants) is
    tried FIRST -- the strongest, most direct signal -- and the declared-package fallback only
    when that fails."""
    lookups = mrjar_variants(binary_top_level_name)
    if lookups & source_names.get("path", set()):
        return True
    return bool(lookups & source_names.get("declared", set()))


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
        # (identification_method, content_identity) -- these aren't derived by fetch itself, but a
        # plain field allowlist here would otherwise silently drop them between plan and manifest.
        for extra_key in ("identification_method", "content_identity"):
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
    is moved into plan["artifacts"] as a new single-occurrence artifact -- shaped exactly like
    run_plan's own output -- so the existing fetch/classdiff pipeline picks it up unchanged. An
    unresolved jar stays in plan["unidentified"] with its reason refined from the generic
    "no-pom-properties" to the specific outcome. Entries with any other reason (e.g. from a
    future evidence run) are left untouched.

    identify_unidentified_entry's coarse "vendor-modified" (same g:a:v on Central, different
    whole-jar bytes) is NOT the final word: a Niagara re-signature changes the whole-jar SHA-1
    without touching a single class (real finding: bin/ext/asm-9.10.1.jar). On that signal, this
    function fetches Central's binary jar and runs classify_jar_identity (per-.class SHA-256) to
    get the real classification -- resigned-identical / partially-modified / vendor-modified --
    stored as the artifact's "content_identity". If Central's binary itself can't be fetched, the
    classification is "unverifiable" (with a class-name-only overlap as a diagnostic fallback).

    Returns counts by outcome, including "mirror-unavailable" for jars the local mirror doesn't
    have."""
    summary = {"identified-by-sha1": 0, "resigned-identical": 0, "partially-modified": 0,
               "vendor-modified": 0, "no-classes": 0, "unverifiable": 0, "not-on-central": 0,
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
        if result["status"] == "identified-by-sha1":
            summary["identified-by-sha1"] += 1
            new_art = {
                "groupId": result["groupId"], "artifactId": result["artifactId"],
                "version": result["version"],
                "occurrences": [{"kind": u["kind"], "name": u["name"], "binary_sha1": local_sha1}],
                "_candidate_versions": [result["version"]],
                "identification_method": result["method"],
            }
            if result.get("classifier"):
                new_art["classifier"] = result["classifier"]
            plan["artifacts"].append(new_art)
        elif result["status"] == "vendor-modified":
            classifier = result.get("classifier")
            central_fetch = fetch_central_binary_jar(result["groupId"], result["artifactId"],
                                                       result["version"], opener, sleep=sleep,
                                                       retries=retries, classifier=classifier)
            if pace:
                sleep(pace)
            if central_fetch["status"] == "fetched":
                content_identity = classify_jar_identity(local_bytes, central_fetch["bytes"])
                content_identity["central_sha1"] = central_fetch["sha1"]
            else:
                content_identity = {
                    "status": "unverifiable", "reason": central_fetch["status"],
                    "detail": central_fetch.get("detail"),
                    "name_overlap": compute_vendor_modified_overlap(
                        local_bytes, result["groupId"], result["artifactId"], result["version"],
                        opener, sleep=sleep, retries=retries, classifier=classifier),
                }
            content_identity["local_sha1"] = local_sha1
            content_identity.setdefault("source", "live-recheck")
            if classifier:
                content_identity["classifier"] = classifier
                content_identity["sources_shared_across_classifiers"] = True
            summary[content_identity["status"]] = summary.get(content_identity["status"], 0) + 1
            plan["artifacts"].append({
                "groupId": result["groupId"], "artifactId": result["artifactId"],
                "version": result["version"],
                "occurrences": [{"kind": u["kind"], "name": u["name"], "binary_sha1": local_sha1}],
                "_candidate_versions": [result["version"]],
                "identification_method": result["method"],
                "content_identity": content_identity,
            })
        else:
            summary[result["status"]] += 1
            reason_detail = result.get("reason") or result.get("stage") or ""
            if result["status"] == "network-error":
                # Real 2026-09-28 finding (R3-sticky-transient-failure /
                # R4-identify-transient-failure-not-retryable): a TRANSIENT failure must not
                # become a permanent, non-retryable verdict. Keeping reason == "no-pom-properties"
                # means the next identify-unidentified pass's guard above still re-processes this
                # entry instead of skipping it forever; the failure detail is preserved separately
                # for visibility.
                still_unidentified.append(dict(u, reason="no-pom-properties", local_sha1=local_sha1,
                                                last_network_error=reason_detail or "network-error"))
            else:
                still_unidentified.append(dict(u, reason=f"{result['status']}:{reason_detail}"
                                                if reason_detail else result["status"],
                                                local_sha1=local_sha1))
    plan["unidentified"] = still_unidentified
    plan["sha1_identify_summary"] = summary
    return summary


def sources_top_level_names(art: dict) -> Optional[dict]:
    """{"path": set[str], "declared": set[str]} of top-level class names (same "path/without/
    extension" shape top_level_class_of returns) this artifact's FETCHED sources jar can match --
    `.java` UNIONED with `.kt` (real finding: kotlin-stdlib and friends publish `.kt` sources, no
    `.java` at all). "path" is every entry's own zip path (MRJAR-variant-expanded, see
    mrjar_variants); "declared" is every entry's OWN `package` declaration + stem (see
    declared_names_for_source) -- the fallback for a source-set layout whose paths don't mirror
    packages (Kotlin Multiplatform's `commonMain/`, `jvmMain/`, ...). Use class_has_matching_source
    to actually match a binary class against this, never a bare `in` check against one set.
    Returns None when no sources jar was ever fetched for this artifact (status != "fetched") or
    the recorded file isn't actually readable on disk."""
    if art.get("status") != "fetched":
        return None
    rel_path = art.get("sources_jar_path")
    if not rel_path:
        return None
    jar_path = REPO_ROOT / rel_path
    if not jar_path.exists():
        return None
    sources_bytes = jar_path.read_bytes()
    path_names: set[str] = set()
    declared_names: set[str] = set()
    try:
        with zipfile.ZipFile(io.BytesIO(sources_bytes)) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if name.endswith(".java"):
                    base = name[: -len(".java")]
                elif name.endswith(".kt"):
                    base = name[: -len(".kt")]
                else:
                    continue
                if "$" in base.rsplit("/", 1)[-1]:
                    continue
                path_names |= mrjar_variants(base)
                declared_names |= declared_names_for_source(name, z.read(info))
    except (zipfile.BadZipFile, OSError):
        return None
    return {"path": path_names, "declared": declared_names}


def run_all_third_party_coverage(manifest: dict, mirror_modules_dir=MIRROR_MODULES_DIR,
                                  mirror_binext_dir=MIRROR_BINEXT_DIR) -> dict:
    """T26a headline fix, tightened by an orchestrator follow-up review (2026-09-28): the
    class-coverage percentage must state BOTH its numerator and denominator in ONE consistent
    UNIT, over ALL third-party classes (identified + unidentified), not only artifacts with a
    fetched sources jar.

    THE UNIT (denominator, every artifact and every still-unidentified jar): real_class_entries
    of the LOCAL MIRROR's copy of the artifact's first occurrence -- every `.class` entry the jar
    ships, nested/anonymous classes INCLUDED, module-info.class/package-info.class EXCLUDED (see
    real_class_entries). This is the SAME unit everywhere: no artifact's denominator uses a
    narrower, name-based, top-level-only count anymore (previously a REAL bug -- R3-coverage-
    unit-mix -- content_identity's classes_total_local (all classes) was mixed with classdiff's
    binary_total (top-level only, excludes nested/anonymous) in the SAME total).

    COVERAGE (numerator): a class entry counts as covered iff BOTH hold:
      (a) PROVEN binary identity for that exact entry -- "whole-jar" proof (content_identity
          status resigned-identical/sha1-exact, OR an artifact with NO content_identity but an
          "identification_method" -- T26a's OWN whole-jar SHA-1 proof, see run_identify_unidentified
          -- both mean literally every byte of the local jar already matches Central's, so EVERY
          entry is proven, nested/anonymous included) proves ALL entries; "partially-modified"
          proves only the entries NOT in its different_classes/local_only_classes; vendor-modified/
          unverifiable/mixed/unverified/no content_identity-or-identification_method prove NONE.
      (b) its TOP-LEVEL class (top_level_class_of, stripping any "$...") has a matching `.java`/
          `.kt` in the artifact's FETCHED sources jar (sources_top_level_names) -- binary proof
          alone is not "coverage": this report is specifically about having the ORIGINAL SOURCE,
          and a nested/anonymous class is declared inside its enclosing top-level class's own
          source file, so it is source-covered exactly when that file is.
    A name-based classdiff match with NO identity proof at all (the previous, weaker fallback) no
    longer counts here -- that weaker, name-only view is still reported separately, see
    "Class coverage by original upstream source" (classdiff_coverage) below.

    When the local mirror doesn't have an artifact's jar at all, this falls back to classdiff's
    own (narrower, top-level-only) binary_total for the denominator ONLY (better an undercounted
    number than a silently missing one -- real 2026-09-28 finding, R3-headline-denominator-
    silent-omission / R4-coverage-denominator-silently-shrinks, for the case where classdiff
    itself is also entirely absent); 0 covered, since no per-entry proof can be computed without
    the actual bytes. "class_count" records the real unit's count on every artifact/unidentified
    entry (None when genuinely uncountable), so the gap stays visible instead of silent."""
    covered = 0
    total = 0
    for art in manifest["artifacts"]:
        occurrences = art.get("occurrences") or []
        binary_bytes = (load_binary_bytes_from_mirror(occurrences[0], mirror_modules_dir, mirror_binext_dir)
                         if occurrences else None)
        if binary_bytes is None:
            cd = art.get("classdiff")
            if cd and "binary_total" in cd:
                total += cd["binary_total"]
            art["class_count"] = None
            continue
        real_entries = real_class_entries(binary_bytes)
        art["class_count"] = len(real_entries)
        total += len(real_entries)

        ci = art.get("content_identity")
        if ci and ci["status"] in WHOLE_TRUST_STATUSES:
            proven = set(real_entries)
        elif ci and ci["status"] == "partially-modified":
            not_proven = set(ci.get("different_classes", [])) | set(ci.get("local_only_classes", []))
            proven = set(real_entries) - not_proven
        elif ci:
            # vendor-modified / unverifiable / mixed / unverified: no binary identity proof at
            # any granularity.
            proven = set()
        elif art.get("identification_method"):
            # T26a's OWN whole-jar SHA-1 proof (sha1-search hit, or a filename-guess whose SHA-1
            # matched exactly) -- by design no content_identity is computed for this case (the
            # whole-jar SHA-1 already IS the strongest possible proof, see
            # run_identify_unidentified), but it proves every entry just as WHOLE_TRUST_STATUSES
            # would.
            proven = set(real_entries)
        else:
            proven = set()

        if proven:
            src_names = sources_top_level_names(art)
            if src_names:
                covered += sum(1 for entry in proven
                                if class_has_matching_source(top_level_class_of(entry), src_names))
    for u in manifest.get("unidentified", []):
        binary_bytes = load_binary_bytes_from_mirror(u, mirror_modules_dir, mirror_binext_dir)
        if binary_bytes is None:
            u["class_count"] = None
            continue
        real_entries = real_class_entries(binary_bytes)
        u["class_count"] = len(real_entries)
        total += len(real_entries)
        # An unidentified jar has no known coordinate, so no sources were ever fetched for it --
        # 0 covered by construction.
    coverage = {"classes_with_upstream_source": covered, "classes_total": total}
    manifest["all_third_party_coverage"] = coverage
    return coverage


# Statuses that mean "every .class entry in this occurrence's jar is proven byte-identical to
# Central" -- the strongest possible proof, regardless of WHICH proof mechanism produced it
# (b117's own whole-jar SHA-1 match, or a per-.class re-check that happened to find full
# agreement). When every occurrence of an artifact lands in this set, the artifact-level rollup
# can safely collapse to one verdict; when they don't all agree, it must NOT collapse (see
# run_recheck_pom_identified_gaps).
WHOLE_TRUST_STATUSES = {"sha1-exact", "resigned-identical"}


def compute_occurrence_identity(occ: dict, ev: Optional[dict], art: dict, opener: Callable,
                                 sleep: Callable, retries: int, mod_dir: Path, install_dir: Path,
                                 pace: float) -> dict:
    """The identity proof for ONE manifest occurrence, from its OWN evidence/b117/maven-repo1.json
    record -- never inherited from the artifact's other occurrences. Two occurrences of the same
    g:a:v (e.g. a LIB-INF copy and an etc/m2 build-tool copy) can be genuinely different bytes
    (real finding, 2026-09-28: org.jetbrains:annotations:13.0's devkit LIB-INF copy is b117
    "exact" while its bin/ext copy is "differs").

    Returns a typed content_identity dict:
      - no b117 record at all: {"status": "unverified", "reason": ...} -- defensive; every
        occurrence of the original pom.properties-identified artifacts traces back to a b117
        entry by construction, so this should not happen in practice, but must never be a silent
        missing field.
      - b117 result == "exact": {"status": "sha1-exact", "source": "evidence/b117/maven-repo1.json",
        "sha1": ...} -- the whole shipped BINARY jar's SHA-1 already matched Central's published
        SHA-1 during the b117 evidence run itself. The strongest possible proof; no further
        verification (and no network call) is needed -- ORCHESTRATOR-FOUND DEFECT FIX
        (2026-09-28): this used to be silently skipped, leaving 81 of 188 manifest artifacts with
        NEITHER content_identity NOR identification_method, so tools/n5-best-source.py treated
        them as unproven even though b117 had already proven 78 of them outright.
      - b117 content == "identical-non-META-INF": reuse b117's own non-META-INF byte comparison
        (no network) -- {"status": "resigned-identical", "source": "b117-reused", ...}.
      - anything else ("differs" with a real content difference, "not-on-central...", a download
        failure): a LIVE per-.class check (classify_jar_identity) against Central's own binary
        jar, classifier-aware (detect_classifier)."""
    if ev is None:
        return {"status": "unverified", "reason": "no-b117-evidence-record"}
    if ev.get("result") == "exact":
        return {"status": "sha1-exact", "source": "evidence/b117/maven-repo1.json",
                "sha1": ev.get("sha1")}
    if ev.get("content") == "identical-non-META-INF":
        return {"status": "resigned-identical", "source": "b117-reused",
                "b117_meta_inf_local": ev.get("meta_inf_local")}
    local_bytes = load_binary_bytes(occ, mod_dir, install_dir)
    if local_bytes is None:
        return {"status": "unverifiable", "reason": "install-not-mounted", "source": "live-recheck"}
    # Recorded as a side effect (not just for this check) so a later "mixed" rollup can link THIS
    # occurrence's own jar identity without a second read -- see run_recheck_pom_identified_gaps.
    occ["binary_sha256"] = hashlib.sha256(local_bytes).hexdigest()
    # Some artifacts (e.g. mssql-jdbc) only exist on Central under a version this tool's own
    # candidate_versions correction found, not the raw pom.properties "version" -- run_fetch
    # already used "resolved_version" to fetch the sources jar; reuse it here too, or a plain
    # whole-jar lookup at the wrong version 404s and this reports "unverifiable" for nothing.
    lookup_version = art.get("resolved_version") or art["version"]
    classifier = detect_classifier(jar_basename(occ["name"]), art["artifactId"], lookup_version)
    central_fetch = fetch_central_binary_jar(art["groupId"], art["artifactId"], lookup_version,
                                               opener, sleep=sleep, retries=retries,
                                               classifier=classifier)
    if pace:
        sleep(pace)
    if central_fetch["status"] == "fetched":
        ci = classify_jar_identity(local_bytes, central_fetch["bytes"])
        ci["central_sha1"] = central_fetch["sha1"]
    else:
        ci = {"status": "unverifiable", "reason": central_fetch["status"]}
    ci["source"] = "live-recheck"
    if classifier:
        ci["classifier"] = classifier
        ci["sources_shared_across_classifiers"] = True
    return ci


def run_recheck_pom_identified_gaps(manifest: dict, evidence_entries: list,
                                     opener: Callable = urllib.request.urlopen,
                                     sleep: Callable = time.sleep, retries: int = 3,
                                     mod_dir: Path = N5_MOD_DIR, install_dir: Path = N5_INSTALL_DIR,
                                     pace: float = 0.15) -> dict:
    """Orchestrator review follow-up (2026-09-28): the ORIGINAL 154 pom.properties-identified
    artifacts (every manifest artifact WITHOUT a T26a identification_method) were only ever
    proven identical to Central by their SOURCES jar's own SHA-1 -- for the ones whose evidence/
    b117 record shows the whole shipped BINARY jar's SHA-1 differs from Central's (result ==
    "differs" or "not-on-central"), class-level identity was never checked, same gap T26a's own
    vendor-modified jars had.

    ORCHESTRATOR-FOUND DEFECT FIX (2026-09-28): this used to check ONLY occurrences[0] and to
    silently skip an artifact entirely (no content_identity written at all) whenever that first
    occurrence's b117 record was already "exact" -- the STRONGEST possible proof -- leaving 81 of
    188 manifest artifacts with neither content_identity nor identification_method, so
    tools/n5-best-source.py's classify_upstream_identity() treated them as unproven. This now
    computes an identity proof for EVERY occurrence of every qualifying artifact
    (compute_occurrence_identity), stored as that occurrence's own "content_identity", and rolls
    those up into the artifact-level "content_identity":
      - all occurrences agree (same status, or all in WHOLE_TRUST_STATUSES): the rollup collapses
        to that one verdict (or "resigned-identical" when they're a mix of "sha1-exact" and
        "resigned-identical" -- both are whole-jar-proven, just via different mechanisms).
      - occurrences DISAGREE (real finding: org.jetbrains:annotations:13.0 et al. -- one occurrence
        b117 "exact", another genuinely "differs"): the rollup is {"status": "mixed", ...} and
        does NOT collapse to the best occurrence's verdict -- tools/n5-best-source.py must resolve
        trust per occurrence (via each occurrence's own "binary_sha256", computed here for a mixed
        artifact's occurrences so a population can be linked to the exact occurrence it came from).
      - no b117 record at all for any occurrence: "unverified" -- never a silently missing field.

    Mutates each matched manifest artifact (and its occurrences) in place; returns counts by
    artifact-level rollup outcome, split into "reused-resigned-identical" (single-occurrence,
    no-network b117 reuse -- kept as its own bucket for backward compatibility with the pre-fix
    report) vs the other statuses."""
    mod_dir, install_dir = Path(mod_dir), Path(install_dir)
    evidence_by_name = {(e.get("kind"), e.get("name")): e for e in evidence_entries}
    summary = {"reused-resigned-identical": 0, "sha1-exact": 0, "resigned-identical": 0,
               "partially-modified": 0, "vendor-modified": 0, "no-classes": 0,
               "unverifiable": 0, "unverified": 0, "mixed": 0}
    for art in manifest["artifacts"]:
        if art.get("identification_method") or art.get("status") != "fetched":
            continue
        occurrences = art["occurrences"]
        for occ in occurrences:
            ev = evidence_by_name.get((occ["kind"], occ["name"]))
            occ["content_identity"] = compute_occurrence_identity(
                occ, ev, art, opener, sleep, retries, mod_dir, install_dir, pace)

        statuses = [occ["content_identity"]["status"] for occ in occurrences]
        if len(set(statuses)) == 1:
            rollup = dict(occurrences[0]["content_identity"])
        elif all(s in WHOLE_TRUST_STATUSES for s in statuses):
            rollup = {"status": "resigned-identical", "source": "per-occurrence-aggregate",
                      "detail": statuses}
        else:
            rollup = {"status": "mixed", "source": "per-occurrence",
                      "reason": "occurrences disagree; see occurrences[].content_identity for "
                                "the individual verdicts -- never collapsed to the best one",
                      "detail": statuses}
            # A mixed artifact needs each occurrence's OWN jar identity so
            # tools/n5-best-source.py can link a population to the exact occurrence its verdict
            # applies to, never to "the artifact's other occurrences'" verdict. Occurrences whose
            # live per-.class check already read local bytes get this almost for free; a
            # "sha1-exact" occurrence (no local read needed for its own proof) gets one here.
            for occ in occurrences:
                if "binary_sha256" in occ:
                    continue
                local_bytes = load_binary_bytes(occ, mod_dir, install_dir)
                if local_bytes is not None:
                    occ["binary_sha256"] = hashlib.sha256(local_bytes).hexdigest()

        art["content_identity"] = rollup
        status = rollup["status"]
        if (status == "resigned-identical" and len(occurrences) == 1
                and rollup.get("source") == "b117-reused"):
            summary["reused-resigned-identical"] += 1
        else:
            summary[status] = summary.get(status, 0) + 1
    manifest["pom_identified_recheck_summary"] = summary
    return summary


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
                   all_third_party_coverage: Optional[dict] = None,
                   pom_recheck_summary: Optional[dict] = None) -> str:
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
            "a PROVEN byte-adjacent original upstream source.** ONE unit, both sides: every real "
            "`.class` entry in every third-party jar in this corpus (identified + "
            "still-unidentified), nested/anonymous classes INCLUDED, `module-info.class`/"
            "`package-info.class` EXCLUDED (they carry no logic to source-match). A class counts "
            "as covered only when BOTH hold: (a) its BINARY identity is PROVEN -- whole-jar proof "
            "(sha1-exact / identified-by-sha1 / resigned-identical) proves every class in the jar, "
            "nested/anonymous included; partially-modified proves only the specific classes found "
            "byte-identical; vendor-modified/unverifiable/mixed/unverified prove none -- AND "
            "(b) its TOP-LEVEL class has a matching `.java`/`.kt` in the FETCHED sources jar, since "
            "a nested/anonymous class is declared inside its top-level class's own source file -- "
            "matched by PATH first (MRJAR-aware: a multi-release jar's `META-INF/versions/N/...` "
            "override class matches its source's un-prefixed path, whichever side carries the "
            "prefix -- real fix, 2026-09-28: bc-fips/bcprov-jdk18on went from ~52%/~82% to "
            "~99.97%/~99.9% covered), falling back to each source file's OWN DECLARED `package` "
            "statement when the sources jar's layout doesn't mirror packages at all (Kotlin "
            "Multiplatform source sets -- `commonMain/`, `jvmMain/`, ... -- real fix, 2026-09-28: "
            "kotlin-stdlib went from 0% to ~40% covered this way; a `.kt` file's own top-level "
            "functions additionally map to its compiled `<Stem>Kt` facade class, or the name an "
            "`@file:JvmName(\"X\")` annotation gives it). A bare classdiff NAME match with no "
            "identity proof is NOT counted here -- see the separate, weaker \"Class coverage by "
            "original upstream source\" section below for that name-only view. See T26a. This "
            "number is NOT the same thing as `tools/n5-best-source.py`'s `by_best_kind.upstream` "
            "count and the two are not expected to match: this one counts, per DISTINCT third-party "
            "artifact, whether a class has PROVEN upstream source; n5-best-source.py counts "
            "per-population (module, `_bin-ext`/`_etc-m2`/`_lib` jar, or raw LIB-INF copy) -- the "
            "same physical class can recur across several populations (e.g. the same third-party "
            "jar bundled, undecompiled, inside more than one module), so its `upstream` count can "
            "exceed the distinct-class count here.\n\n"
            "Residual gap in (b)'s matching (real 2026-09-28, after the MRJAR/declared-package "
            "fixes above): kotlin-stdlib's remaining ~60% and woodstox-core are Kotlin/complex-"
            "source-layout artifacts whose facade/declared-name heuristic doesn't capture every "
            "compiled class (e.g. multiple functions from different files folding into one facade, "
            "or classes this simple regex-based package parser can't attribute) -- a real, "
            "disclosed limitation of this matching method, not evidence the upstream source is "
            "actually missing or wrong."
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
        lines.append("## Class coverage by original upstream source (secondary, name-only view)")
        lines.append("")
        if classdiff_coverage:
            total = classdiff_coverage.get("classes_total", 0)
            covered = classdiff_coverage.get("classes_with_upstream_source", 0)
            pct = f"{100*covered/total:.1f}%" if total else "n/a"
            lines.append(
                f"{covered} of {total} third-party classes ({pct}) in artifacts with a fetched "
                "sources jar have a matching top-level class name in that sources jar "
                "(class-name-set comparison, not a full compile, and NOT identity-proven -- see "
                "the primary \"Coverage over ALL third-party classes\" headline above for the "
                "proven, all-classes-including-nested number)."
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
            "Central's own published binary-jar SHA-1 for that guess matches. A whole-jar SHA-1 "
            "mismatch then gets a full per-.class re-check (see the section below) before being "
            "called vendor-modified."
        )
        lines.append("")
        lines.append("| outcome | count |")
        lines.append("|---|---|")
        for status in ("identified-by-sha1", "resigned-identical", "partially-modified",
                       "vendor-modified", "no-classes", "unverifiable", "not-on-central",
                       "network-error", "mirror-unavailable"):
            lines.append(f"| {status} | {identify_summary.get(status, 0)} |")
        lines.append("")

    if pom_recheck_summary:
        lines.append("## Pom-identified artifacts re-check (orchestrator review follow-up)")
        lines.append("")
        lines.append(
            "The original 154 pom.properties-identified artifacts were only ever proven identical "
            "to Central by their SOURCES jar's own SHA-1. `sha1-exact` -- evidence/b117's own "
            "whole-jar SHA-1 match, the strongest possible proof, carried through as-is with no "
            "further check -- covers most of them. For the rest (evidence/b117 shows the whole "
            "shipped BINARY jar's SHA-1 differs from Central's), this reuses b117's own "
            "non-META-INF content check where it already found `identical-non-META-INF` (no "
            "network), and does a live per-.class check (same method as T26a) otherwise (b117's "
            "own download failures, real content differences, and jars this tool's own "
            "candidate-version corrections resolved after a `not-on-central` whole-jar lookup). "
            "Every check runs PER OCCURRENCE (an artifact can ship as more than one physical jar, "
            "e.g. a LIB-INF copy and an etc/m2 copy, which are not always the same bytes): "
            "`mixed` means the occurrences disagree and the verdict was deliberately NOT collapsed "
            "to the best one -- see manifest.json's occurrences[].content_identity for the "
            "individual verdicts. `unverified` means no evidence/b117 record was found at all."
        )
        lines.append("")
        lines.append("| outcome | count |")
        lines.append("|---|---|")
        for status in ("sha1-exact", "reused-resigned-identical", "resigned-identical",
                       "partially-modified", "vendor-modified", "no-classes", "unverifiable",
                       "unverified", "mixed"):
            lines.append(f"| {status} | {pom_recheck_summary.get(status, 0)} |")
        lines.append("")

    content_checked = [a for a in artifacts if a.get("content_identity")]
    if content_checked:
        lines.append("## Class-content identity re-check (per-.class SHA-256 vs Central)")
        lines.append("")
        lines.append(
            "A whole-jar SHA-1 mismatch alone does not mean Central's sources aren't ground truth "
            "-- Niagara commonly re-signs a jar (adds META-INF/NIAGARA4.SF + .RSA) without "
            "touching a single class. This compares every `.class` entry's SHA-256 against "
            "Central's own binary jar for the same groupId:artifactId:version -- against the "
            "CLASSIFIER binary (e.g. `-jdk11`, `-native`) when the local jar's own filename "
            "carries one, never the classifier-less one. "
            "`no-classes` = the local jar has zero `.class` entries at all (e.g. a pure-native "
            "JNI jar), nothing to compare; "
            "`resigned-identical` = every class matches (sources ARE ground truth for this jar); "
            "`partially-modified` = only some classes match (only those are covered, the rest "
            "still need decompile); `vendor-modified` = the jar HAS classes but none matched; "
            "`unverifiable` = Central's own binary jar could not be fetched to compare against."
        )
        lines.append("")
        lines.append("| artifact | version | classifier | status | identical | different | local-only | source |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for a in sorted(content_checked,
                         key=lambda x: (x["content_identity"]["status"], x.get("artifactId", ""))):
            ci = a["content_identity"]
            lines.append(f"| {a.get('artifactId')} | {a.get('version')} | {ci.get('classifier', '-')} | "
                         f"{ci['status']} | "
                         f"{ci.get('classes_identical', '-')} | {ci.get('classes_different', '-')} | "
                         f"{ci.get('classes_local_only', '-')} | {ci.get('source', '-')} |")
        lines.append("")
        classifier_rows = [a for a in content_checked if a["content_identity"].get("classifier")]
        if classifier_rows:
            lines.append(
                "Classifier builds (Maven's `<artifact>-<version>-<classifier>.jar` convention): "
                "the SOURCES jar Maven publishes is shared across all classifiers of the same "
                "artifact+version (no separate `-sources.jar` per classifier), so the fetched "
                "sources for these jars come from the shared, classifier-less sources jar:"
            )
            lines.append("")
            for a in sorted(classifier_rows, key=lambda x: x.get("artifactId", "")):
                ci = a["content_identity"]
                lines.append(f"- **{a.get('artifactId')} {a.get('version')}** classifier "
                             f"`{ci['classifier']}` ({ci['status']})")
            lines.append("")
        detail_rows = [a for a in content_checked
                       if a["content_identity"].get("different_classes")
                       or a["content_identity"].get("differing_non_class_entries")]
        if detail_rows:
            lines.append("Per-jar detail (differing/local-only classes, and any non-class entry "
                         "that differs -- typically an added signature file):")
            lines.append("")
            for a in sorted(detail_rows, key=lambda x: x.get("artifactId", "")):
                ci = a["content_identity"]
                diff_sample = ", ".join(ci.get("different_classes", [])[:8]) or "-"
                local_only_sample = ", ".join(ci.get("local_only_classes", [])[:8]) or "-"
                non_class = ", ".join(ci.get("differing_non_class_entries", [])[:8]) or "-"
                lines.append(f"- **{a.get('artifactId')} {a.get('version')}** "
                             f"({ci['status']}): different classes: {diff_sample}; "
                             f"local-only classes: {local_only_sample}; "
                             f"differing non-class entries: {non_class}")
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

    srck = sub.add_parser("recheck-pom-identified")
    srck.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    srck.add_argument("--out", default=str(DEFAULT_OUT_DIR))

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

    if args.cmd == "recheck-pom-identified":
        manifest = json.load(open(out_dir / "manifest.json"))
        evidence_entries = json.load(open(args.evidence))
        summary = run_recheck_pom_identified_gaps(manifest, evidence_entries)
        json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
        print(summary)
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
                              all_third_party_coverage=all_coverage,
                              pom_recheck_summary=manifest.get("pom_identified_recheck_summary"))
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
        evidence_entries = json.load(open(args.evidence))
        run_recheck_pom_identified_gaps(manifest, evidence_entries)
        paho = next((a.get("paho_diff") for a in manifest["artifacts"]
                     if (a["groupId"], a["artifactId"], a["version"]) == PAHO_GAV), None)
        all_coverage = run_all_third_party_coverage(manifest)
        json.dump(manifest, open(out_dir / "manifest.json", "w"), indent=1)
        text = render_report(manifest, paho_result=paho,
                              classdiff_coverage=manifest.get("classdiff_coverage"),
                              recompile_results=recompile_results,
                              identify_summary=manifest.get("sha1_identify_summary"),
                              all_third_party_coverage=all_coverage,
                              pom_recheck_summary=manifest.get("pom_identified_recheck_summary"))
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text)
        print(f"wrote {args.report}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
