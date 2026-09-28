"""Tests for tools/n5-upstream-sources.py: T22 third-party-jar upstream-source audit.

For third-party (non-Tridium) jars, the most faithful representation of the code is the
original upstream Maven Central `-sources.jar`, not a decompile. evidence/b117/maven-repo1.json
already identified 160 of 204 third-party jars by groupId:artifactId:version (79 LIB-INF exact +
1 differs + 5 etc/m2 exact + 72 bin/ext content-identical-except-META-INF + 3 GAV-recoverable
corrections this module makes: kotlin-reflect's etc/m2 path, mssql-jdbc's filename-embedded
version, oauth2-oidc-sdk's plain match). 44 jars carry no pom.properties and stay unidentified.

Unit tests are hermetic: no real network calls, no dependency on the N5 install being mounted.
A handful of smoke tests read the real evidence/b117/maven-repo1.json (committed, not installer-
dependent) to guard known corpus facts; they skip if that file is absent.
"""
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(TOOLS_DIR)
SCRIPT = os.path.join(TOOLS_DIR, "n5-upstream-sources.py")
EVIDENCE_JSON = os.path.join(REPO_ROOT, "evidence", "b117", "maven-repo1.json")


def _load():
    spec = importlib.util.spec_from_file_location("n5_upstream_sources", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _jar_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _jar_bytes_with_corrupt_entry(entries, corrupt_name):
    """Same as _jar_bytes, but flips one byte of corrupt_name's own stored file data so
    zipfile.ZipFile(...).read(corrupt_name) raises zipfile.BadZipFile ("Bad CRC-32 for file...")
    for that ONE entry -- a real-world simulation of a truncated/corrupted zip member -- while
    every other entry in the same jar stays perfectly readable. Used to test that one unreadable
    sources-jar entry does not zero out an entire jar's worth of coverage (R3/R4-entry-read-
    failure, orchestrator second-round review, 2026-09-28)."""
    import struct
    raw = bytearray(_jar_bytes(entries))
    with zipfile.ZipFile(io.BytesIO(bytes(raw))) as zf:
        offset = zf.getinfo(corrupt_name).header_offset
    fname_len, extra_len = struct.unpack("<HH", raw[offset + 26:offset + 30])
    data_offset = offset + 30 + fname_len + extra_len
    raw[data_offset] ^= 0xFF
    return bytes(raw)


class ParseMatchTest(unittest.TestCase):
    def test_parses_group_artifact_version(self):
        m = _load()
        self.assertEqual(
            m.parse_match("com.nimbusds:oauth2-oidc-sdk:11.26"),
            ("com.nimbusds", "oauth2-oidc-sdk", "11.26"),
        )

    def test_none_on_wrong_field_count(self):
        m = _load()
        self.assertIsNone(m.parse_match("com.nimbusds:oauth2-oidc-sdk"))
        self.assertIsNone(m.parse_match("a:b:c:d"))

    def test_none_on_empty_field(self):
        m = _load()
        self.assertIsNone(m.parse_match("com.nimbusds::11.26"))


class EtcM2GavFromPathTest(unittest.TestCase):
    def test_recovers_correct_group_for_kotlin_reflect(self):
        # evidence/b117/maven_repo1.py's etc/m2 fallback (no pom.properties in the jar) joins
        # path segments including the literal "repository" into the groupId, producing
        # "repository.org.jetbrains.kotlin" -- a URL that 404s on Central (verified 2026-09-28,
        # curl https://repo1.maven.org/maven2/repository/org/jetbrains/kotlin/... -> 404).
        # The plain relative path already matches Central's own repo layout.
        m = _load()
        name = "etc/m2/repository/org/jetbrains/kotlin/kotlin-reflect/2.1.21/kotlin-reflect-2.1.21.jar"
        self.assertEqual(
            m.etc_m2_gav_from_path(name),
            ("org.jetbrains.kotlin", "kotlin-reflect", "2.1.21"),
        )

    def test_none_when_not_an_etc_m2_repository_path(self):
        m = _load()
        self.assertIsNone(m.etc_m2_gav_from_path("abstractMqttDriver.jar!LIB-INF/foo-1.0.jar"))


class ClassifyThirdPartyTest(unittest.TestCase):
    def test_no_pom_properties_is_unidentified(self):
        m = _load()
        entry = {"kind": "bin/ext", "name": "bin/ext/foo.jar", "result": "no-pom-properties"}
        self.assertEqual(m.classify_third_party(entry), ("unidentified", "no-pom-properties"))

    def test_etc_m2_with_buggy_match_is_recovered_from_path(self):
        m = _load()
        entry = {
            "kind": "etc/m2",
            "name": "etc/m2/repository/org/jetbrains/kotlin/kotlin-reflect/2.1.21/kotlin-reflect-2.1.21.jar",
            "result": "not-on-central:HTTPError",
            "match": "repository.org.jetbrains.kotlin:kotlin-reflect:2.1.21",
        }
        self.assertEqual(
            m.classify_third_party(entry),
            ("identified", ("org.jetbrains.kotlin", "kotlin-reflect", "2.1.21")),
        )

    def test_lib_inf_exact_uses_match(self):
        m = _load()
        entry = {
            "kind": "LIB-INF",
            "name": "mod.jar!LIB-INF/foo-1.0.jar",
            "result": "exact",
            "match": "com.example:foo:1.0",
        }
        self.assertEqual(m.classify_third_party(entry), ("identified", ("com.example", "foo", "1.0")))

    def test_no_match_and_no_recoverable_path_is_unidentified(self):
        m = _load()
        entry = {"kind": "bin/ext", "name": "bin/ext/foo.jar", "result": "differs"}
        cat, reason = m.classify_third_party(entry)
        self.assertEqual(cat, "unidentified")


class DedupeArtifactsTest(unittest.TestCase):
    def test_groups_same_gav_and_collects_occurrences(self):
        m = _load()
        entries = [
            {"kind": "LIB-INF", "name": "a.jar!LIB-INF/foo-1.0.jar", "result": "exact",
             "match": "com.example:foo:1.0", "sha1": "aaa"},
            {"kind": "LIB-INF", "name": "b.jar!LIB-INF/foo-1.0.jar", "result": "exact",
             "match": "com.example:foo:1.0", "sha1": "aaa"},
        ]
        artifacts, unidentified = m.dedupe_artifacts(entries)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0]["groupId"], "com.example")
        self.assertEqual(artifacts[0]["artifactId"], "foo")
        self.assertEqual(artifacts[0]["version"], "1.0")
        self.assertEqual(len(artifacts[0]["occurrences"]), 2)
        self.assertEqual(unidentified, [])

    def test_separates_unidentified_with_reason(self):
        m = _load()
        entries = [{"kind": "bin/ext", "name": "bin/ext/foo.jar", "result": "no-pom-properties"}]
        artifacts, unidentified = m.dedupe_artifacts(entries)
        self.assertEqual(artifacts, [])
        self.assertEqual(len(unidentified), 1)
        self.assertEqual(unidentified[0]["reason"], "no-pom-properties")
        self.assertEqual(unidentified[0]["name"], "bin/ext/foo.jar")

    def test_preserves_first_seen_order(self):
        m = _load()
        entries = [
            {"kind": "LIB-INF", "name": "z.jar!LIB-INF/z-1.jar", "result": "exact", "match": "g:z:1"},
            {"kind": "LIB-INF", "name": "a.jar!LIB-INF/a-1.jar", "result": "exact", "match": "g:a:1"},
        ]
        artifacts, _ = m.dedupe_artifacts(entries)
        self.assertEqual([a["artifactId"] for a in artifacts], ["z", "a"])


class CandidateVersionsTest(unittest.TestCase):
    def test_pom_version_is_first_candidate(self):
        m = _load()
        versions = m.candidate_versions("rdbSqlServer.jar!LIB-INF/mssql-jdbc-13.4.0.jre11.jar", "mssql-jdbc", "13.4.0")
        self.assertEqual(versions[0], "13.4.0")

    def test_filename_fallback_added_when_it_differs(self):
        # mssql-jdbc's own embedded pom.properties says version=13.4.0, but the file is
        # named mssql-jdbc-13.4.0.jre11.jar and Central hosts it only under 13.4.0.jre11
        # (verified 2026-09-28: repo1.maven.org/.../mssql-jdbc/13.4.0/... -> 404,
        # .../13.4.0.jre11/... -> 200).
        m = _load()
        versions = m.candidate_versions("rdbSqlServer.jar!LIB-INF/mssql-jdbc-13.4.0.jre11.jar", "mssql-jdbc", "13.4.0")
        self.assertIn("13.4.0.jre11", versions)

    def test_no_duplicate_when_filename_matches_pom_version(self):
        m = _load()
        versions = m.candidate_versions("a.jar!LIB-INF/foo-1.0.jar", "foo", "1.0")
        self.assertEqual(versions, ["1.0"])

    def test_etc_m2_top_level_name_uses_plain_basename(self):
        m = _load()
        versions = m.candidate_versions(
            "etc/m2/repository/org/jetbrains/kotlin/kotlin-reflect/2.1.21/kotlin-reflect-2.1.21.jar",
            "kotlin-reflect", "2.1.21")
        self.assertEqual(versions, ["2.1.21"])


class SourcesJarUrlTest(unittest.TestCase):
    def test_builds_maven_central_layout_url(self):
        m = _load()
        url = m.sources_jar_url("com.microsoft.sqlserver", "mssql-jdbc", "13.4.0.jre11")
        self.assertEqual(
            url,
            "https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/13.4.0.jre11/mssql-jdbc-13.4.0.jre11-sources.jar",
        )


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FetchWithRetryTest(unittest.TestCase):
    def test_success_first_try(self):
        m = _load()
        calls = []

        def opener(url, timeout=30):
            calls.append(url)
            return _FakeResponse(b"hello")

        r = m.fetch_with_retry("http://x", opener, sleep=lambda s: None)
        self.assertTrue(r["ok"])
        self.assertEqual(r["bytes"], b"hello")
        self.assertEqual(len(calls), 1)

    def test_404_returns_not_found_without_retrying(self):
        m = _load()
        import urllib.error
        calls = []

        def opener(url, timeout=30):
            calls.append(url)
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        r = m.fetch_with_retry("http://x", opener, sleep=lambda s: None)
        self.assertFalse(r["ok"])
        self.assertEqual(r["kind"], "not-found")
        self.assertEqual(len(calls), 1)

    def test_transient_error_then_success(self):
        m = _load()
        attempts = {"n": 0}

        def opener(url, timeout=30):
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise TimeoutError("slow")
            return _FakeResponse(b"ok")

        slept = []
        r = m.fetch_with_retry("http://x", opener, sleep=slept.append, retries=3)
        self.assertTrue(r["ok"])
        self.assertEqual(attempts["n"], 2)
        self.assertEqual(len(slept), 1)

    def test_exhausts_retries_returns_error(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        r = m.fetch_with_retry("http://x", opener, sleep=lambda s: None, retries=3)
        self.assertFalse(r["ok"])
        self.assertEqual(r["kind"], "error")


class ResolveAndFetchSourcesTest(unittest.TestCase):
    def _artifact(self, versions):
        return {"groupId": "g", "artifactId": "a", "_candidate_versions": versions}

    def test_fetched_on_first_candidate(self):
        m = _load()
        jar_bytes = b"jar-content"
        sha1 = hashlib.sha1(jar_bytes).hexdigest()

        def opener(url, timeout=30):
            if url.endswith(".sha1"):
                return _FakeResponse(sha1.encode())
            return _FakeResponse(jar_bytes)

        r = m.resolve_and_fetch_sources(self._artifact(["1.0"]), opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "fetched")
        self.assertEqual(r["resolved_version"], "1.0")
        self.assertEqual(r["sha1"], sha1)

    def test_falls_back_to_second_candidate_on_404(self):
        # mssql-jdbc shape: pom.properties version 404s, filename-derived version works.
        m = _load()
        import urllib.error
        jar_bytes = b"jar-content-2"
        sha1 = hashlib.sha1(jar_bytes).hexdigest()

        def opener(url, timeout=30):
            if "/1.0/" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            if url.endswith(".sha1"):
                return _FakeResponse(sha1.encode())
            return _FakeResponse(jar_bytes)

        r = m.resolve_and_fetch_sources(self._artifact(["1.0", "1.0.special"]), opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "fetched")
        self.assertEqual(r["resolved_version"], "1.0.special")

    def test_checksum_mismatch(self):
        m = _load()
        jar_bytes = b"actual-bytes"

        def opener(url, timeout=30):
            if url.endswith(".sha1"):
                return _FakeResponse(b"0" * 40)
            return _FakeResponse(jar_bytes)

        r = m.resolve_and_fetch_sources(self._artifact(["1.0"]), opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "checksum-mismatch")

    def test_no_sources_published_when_all_candidates_404(self):
        m = _load()
        import urllib.error

        def opener(url, timeout=30):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        r = m.resolve_and_fetch_sources(self._artifact(["1.0", "1.0b"]), opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "no-sources-published")
        self.assertEqual(r["versions_tried"], ["1.0", "1.0b"])

    def test_network_error_when_non_404_failures(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        r = m.resolve_and_fetch_sources(self._artifact(["1.0"]), opener, sleep=lambda s: None, retries=1)
        self.assertEqual(r["status"], "network-error")


class ClassNamesFromZipTest(unittest.TestCase):
    def test_java_sources_top_level_names(self):
        m = _load()
        jar = _jar_bytes({
            "org/example/Foo.java": b"",
            "org/example/Bar.java": b"",
            "META-INF/MANIFEST.MF": b"",
        })
        names = m.class_names_from_zip(jar, ".java")
        self.assertEqual(names, {"org/example/Foo", "org/example/Bar"})

    def test_class_files_exclude_nested_and_anonymous(self):
        m = _load()
        jar = _jar_bytes({
            "org/example/Foo.class": b"",
            "org/example/Foo$Inner.class": b"",
            "org/example/Foo$1.class": b"",
            "org/example/Bar.class": b"",
        })
        names = m.class_names_from_zip(jar, ".class")
        self.assertEqual(names, {"org/example/Foo", "org/example/Bar"})


class NormalizeJavapTest(unittest.TestCase):
    def test_strips_raw_constant_pool_index_keeps_resolved_symbol(self):
        # Two independent javac runs of behaviourally-identical code assign constant-pool
        # slots in whatever order each compiler builds its pool -- the raw "#7" vs "#2" index
        # differs even when the resolved symbol (the // comment javap already prints) is
        # identical. Observed for real on jackson-core Base64Variant.class recompiled with
        # javac 25 vs the shipped class, 2026-09-28: same code, only indices differed.
        m = _load()
        a = "        10: putfield      #7                  // Field _asciiToBase64:[I"
        b = "        10: putfield      #2                  // Field _asciiToBase64:[I"
        self.assertEqual(m.normalize_javap(a), m.normalize_javap(b))

    def test_still_distinguishes_a_real_operand_difference(self):
        m = _load()
        a = "         5: sipush        128"
        b = "         5: sipush        64"
        self.assertNotEqual(m.normalize_javap(a), m.normalize_javap(b))

    def test_drops_compiled_from_and_blank_lines(self):
        m = _load()
        out = m.normalize_javap("Compiled from \"Foo.java\"\n\npublic class Foo {\n")
        self.assertEqual(out, ["public class Foo {"])


class ClassnameDiffTest(unittest.TestCase):
    def test_counts_common_and_only_sides(self):
        m = _load()
        d = m.classname_diff({"A", "B", "C"}, {"B", "C", "D"})
        self.assertEqual(d["common"], 2)
        self.assertEqual(d["sources_only"], ["A"])
        self.assertEqual(d["binary_only"], ["D"])
        self.assertEqual(d["sources_total"], 3)
        self.assertEqual(d["binary_total"], 3)


class RenderReportTest(unittest.TestCase):
    def test_includes_status_counts_paho_note_and_unidentified_count(self):
        m = _load()
        manifest = {
            "artifacts": [
                {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
                 "occurrences": [{"kind": "LIB-INF", "name": "x!y"}]},
                {"groupId": "g2", "artifactId": "b", "version": "2", "status": "checksum-mismatch",
                 "occurrences": [{"kind": "bin/ext", "name": "z"}]},
            ],
            "unidentified": [{"kind": "bin/ext", "name": "u.jar", "reason": "no-pom-properties"}],
        }
        paho = {"status": "rebuilt-by-vendor", "note": "2021 vs 2020 build timestamps"}
        text = m.render_report(manifest, paho_result=paho, classdiff_coverage={"classes_with_upstream_source": 1, "classes_total": 2})
        self.assertIn("fetched", text)
        self.assertIn("checksum-mismatch", text)
        self.assertIn("rebuilt-by-vendor", text)
        self.assertIn("1", text)
        self.assertIn("no-pom-properties", text)

    def test_lists_low_coverage_artifacts(self):
        m = _load()
        manifest = {
            "artifacts": [
                {"groupId": "g", "artifactId": "kt-lib", "version": "1", "status": "fetched",
                 "occurrences": [], "classdiff": {"common": 3, "binary_total": 70,
                                                    "sources_only": [], "binary_only": [], "sources_total": 3}},
            ],
            "unidentified": [],
        }
        text = m.render_report(manifest)
        self.assertIn("kt-lib", text)
        self.assertIn("3/70", text)

    def test_includes_javac_failure_detail(self):
        m = _load()
        manifest = {"artifacts": [], "unidentified": []}
        recompile_results = [{"artifactId": "lz4-java", "version": "1.11.2", "classes": [
            {"class": "net/jpountz/lz4/Foo", "release_used": 7, "javac_rc": 2,
             "javac_stderr": "error: release version 7 not supported\nmore"},
        ]}]
        text = m.render_report(manifest, recompile_results=recompile_results)
        self.assertIn("javac-failed", text)
        self.assertIn("release version 7 not supported", text)


@unittest.skipUnless(os.path.exists(EVIDENCE_JSON), "evidence/b117/maven-repo1.json not present")
class RealEvidenceSmokeTest(unittest.TestCase):
    def test_204_third_party_jars_split_into_identified_and_unidentified(self):
        m = _load()
        entries = json.load(open(EVIDENCE_JSON))
        self.assertEqual(len(entries), 204)
        artifacts, unidentified = m.dedupe_artifacts(entries)
        self.assertEqual(len(unidentified), 44)

    def test_kotlin_reflect_and_mssql_jdbc_are_identified_after_fixups(self):
        m = _load()
        entries = json.load(open(EVIDENCE_JSON))
        artifacts, _ = m.dedupe_artifacts(entries)
        keys = {(a["groupId"], a["artifactId"], a["version"]) for a in artifacts}
        self.assertIn(("org.jetbrains.kotlin", "kotlin-reflect", "2.1.21"), keys)
        self.assertIn(("com.microsoft.sqlserver", "mssql-jdbc", "13.4.0"), keys)


class MainPlanSubcommandTest(unittest.TestCase):
    def test_plan_writes_manifest_with_artifacts_and_unidentified(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            evidence_path = os.path.join(td, "maven-repo1.json")
            json.dump([
                {"kind": "LIB-INF", "name": "a.jar!LIB-INF/foo-1.0.jar", "result": "exact",
                 "match": "com.example:foo:1.0", "sha1": "aaa"},
                {"kind": "bin/ext", "name": "bin/ext/unk.jar", "result": "no-pom-properties"},
            ], open(evidence_path, "w"))
            out_dir = os.path.join(td, "_upstream-sources")
            rc = m.main(["plan", "--evidence", evidence_path, "--out", out_dir])
            self.assertEqual(rc, 0)
            plan_path = os.path.join(out_dir, "plan.json")
            self.assertTrue(os.path.exists(plan_path))
            plan = json.load(open(plan_path))
            self.assertEqual(len(plan["artifacts"]), 1)
            self.assertEqual(len(plan["unidentified"]), 1)




def _solr_response(docs):
    return json.dumps({"responseHeader": {"status": 0}, "response": {"numFound": len(docs), "start": 0, "docs": docs}}).encode()


class JarBasenameTest(unittest.TestCase):
    def test_strips_lib_inf_prefix_and_extension(self):
        m = _load()
        self.assertEqual(m.jar_basename("apachePoi.jar!LIB-INF/poi-5.5.1.jar"), "poi-5.5.1")

    def test_strips_bin_ext_path_and_extension(self):
        m = _load()
        self.assertEqual(m.jar_basename("bin/ext/bcfips/bc-fips-2.1.2.jar"), "bc-fips-2.1.2")


class ParseArtifactVersionFromBasenameTest(unittest.TestCase):
    def test_simple_artifact_and_version(self):
        m = _load()
        self.assertEqual(m.parse_artifact_version_from_basename("asm-9.10.1"), ("asm", "9.10.1"))

    def test_multi_segment_artifact_id(self):
        m = _load()
        self.assertEqual(
            m.parse_artifact_version_from_basename("kotlin-stdlib-jdk7-2.4.10"),
            ("kotlin-stdlib-jdk7", "2.4.10"),
        )

    def test_version_with_embedded_dash(self):
        # prosys-opc-ua-sdk-client-server-5.7.0-248: the version itself contains a dash, but the
        # artifact/version boundary is the FIRST "-<digit>" transition, not the last.
        m = _load()
        self.assertEqual(
            m.parse_artifact_version_from_basename("prosys-opc-ua-sdk-client-server-5.7.0-248"),
            ("prosys-opc-ua-sdk-client-server", "5.7.0-248"),
        )

    def test_dotted_artifact_id_with_underscore(self):
        m = _load()
        self.assertEqual(
            m.parse_artifact_version_from_basename("org.eclipse.swt.win32.win32.x86_64-3.134.0"),
            ("org.eclipse.swt.win32.win32.x86_64", "3.134.0"),
        )

    def test_none_when_no_version_boundary(self):
        m = _load()
        self.assertIsNone(m.parse_artifact_version_from_basename("nodigitshere"))


class SplitClassifierTest(unittest.TestCase):
    """Orchestrator finding (2026-09-28): oauth2-oidc-sdk-11.26-jdk11.jar and
    jffi-1.4.0-native.jar are CLASSIFIER builds (Maven's <artifact>-<version>-<classifier>.jar
    convention), not a different version or a whole-jar content difference. A whole-jar SHA-1
    compare against the classifier-LESS binary is comparing the wrong bytes entirely."""

    def test_letter_led_suffix_is_a_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("1.4.0-native"), ("1.4.0", "native"))

    def test_jdk_style_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("11.26-jdk11"), ("11.26", "jdk11"))

    def test_digit_led_suffix_is_not_a_classifier(self):
        # prosys-opc-ua-sdk-client-server-5.7.0-248: "248" starts with a digit -- part of the
        # version string itself (real Maven versions can contain dashes), not a classifier.
        m = _load()
        self.assertEqual(m.split_classifier("5.7.0-248"), ("5.7.0-248", None))

    def test_no_dash_returns_none_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("9.10.1"), ("9.10.1", None))

    def test_dot_fused_suffix_is_not_a_classifier(self):
        # mssql-jdbc's "13.4.0.jre11" is a literal Central version string (dot-fused, no dash) --
        # must not be touched by classifier splitting.
        m = _load()
        self.assertEqual(m.split_classifier("13.4.0.jre11"), ("13.4.0.jre11", None))

    def test_release_candidate_qualifier_is_not_a_classifier(self):
        # Real finding (R3-split-classifier-qualifier / R4-001): a Maven pre-release qualifier
        # like "-RC1" also starts with a letter, so the naive letter-led-suffix rule wrongly
        # split it off as a classifier -- "1.5.0-RC1" is one real Central version, not version
        # "1.5.0" with classifier "RC1".
        m = _load()
        self.assertEqual(m.split_classifier("1.5.0-RC1"), ("1.5.0-RC1", None))

    def test_snapshot_qualifier_is_not_a_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("3.1.0-SNAPSHOT"), ("3.1.0-SNAPSHOT", None))

    def test_beta_qualifier_is_not_a_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("2.0.0-beta"), ("2.0.0-beta", None))

    def test_numbered_milestone_qualifier_is_not_a_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("4.2.0-M1"), ("4.2.0-M1", None))

    def test_native_classifier_still_splits_despite_qualifier_guard(self):
        # Guardrail: the qualifier denylist must not swallow real classifiers that happen to
        # share a letter-led shape.
        m = _load()
        self.assertEqual(m.split_classifier("1.4.0-native"), ("1.4.0", "native"))

    def test_dash_separated_numbered_qualifier_is_not_a_classifier(self):
        # Real finding (R3-qualifier-guard-misses-dashed-and-dotted-qualifiers, orchestrator
        # second-round review, 2026-09-28): "-rc-1" is a DASH-separated qualifier+number (as
        # opposed to the fused "-RC1" the guard already handled) -- still one whole Central
        # version, "1.5.0-rc-1", not version "1.5.0" plus classifier "rc-1".
        m = _load()
        self.assertEqual(m.split_classifier("1.5.0-rc-1"), ("1.5.0-rc-1", None))

    def test_dot_separated_numbered_qualifier_is_not_a_classifier(self):
        # "-alpha.2" is a DOT-separated qualifier+number -- one whole Central version,
        # "1.0.0-alpha.2", not version "1.0.0" plus classifier "alpha.2".
        m = _load()
        self.assertEqual(m.split_classifier("1.0.0-alpha.2"), ("1.0.0-alpha.2", None))

    def test_dot_separated_rc_qualifier_is_not_a_classifier(self):
        m = _load()
        self.assertEqual(m.split_classifier("2.1.0-RC.1"), ("2.1.0-RC.1", None))


class DetectClassifierTest(unittest.TestCase):
    """For the ORIGINAL 154 pom.properties-identified artifacts, artifactId/version are already
    known precisely (from pom.properties), so classifier detection is a simple prefix check
    against the local occurrence's own basename."""

    def test_extracts_classifier_when_basename_has_extra_suffix(self):
        m = _load()
        self.assertEqual(
            m.detect_classifier("oauth2-oidc-sdk-11.26-jdk11", "oauth2-oidc-sdk", "11.26"),
            "jdk11",
        )

    def test_none_when_basename_matches_exactly(self):
        m = _load()
        self.assertIsNone(m.detect_classifier("asm-9.10.1", "asm", "9.10.1"))

    def test_none_for_dot_fused_version_not_dash_classifier(self):
        # mssql-jdbc-13.4.0.jre11 vs artifactId "mssql-jdbc" version "13.4.0.jre11": the basename
        # equals artifact-version exactly here (the ".jre11" is INSIDE the version), no classifier.
        m = _load()
        self.assertIsNone(m.detect_classifier("mssql-jdbc-13.4.0.jre11", "mssql-jdbc", "13.4.0.jre11"))


class LoadBinaryBytesFromMirrorTest(unittest.TestCase):
    def test_reads_lib_inf_nested_jar_from_mirror_modules_dir(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir = os.path.join(td, "modules")
            os.makedirs(modules_dir)
            outer = os.path.join(modules_dir, "outer.jar")
            with zipfile.ZipFile(outer, "w") as z:
                z.writestr("LIB-INF/inner-1.0.jar", b"inner-bytes")
            occ = {"kind": "LIB-INF", "name": "outer.jar!LIB-INF/inner-1.0.jar"}
            self.assertEqual(
                m.load_binary_bytes_from_mirror(occ, modules_dir=modules_dir, binext_dir=os.path.join(td, "bin-ext")),
                b"inner-bytes",
            )

    def test_reads_bin_ext_jar_from_mirror_binext_dir(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            binext_dir = os.path.join(td, "bin-ext", "bcfips")
            os.makedirs(binext_dir)
            with open(os.path.join(binext_dir, "bc-fips-2.1.2.jar"), "wb") as f:
                f.write(b"bc-bytes")
            occ = {"kind": "bin/ext", "name": "bin/ext/bcfips/bc-fips-2.1.2.jar"}
            self.assertEqual(
                m.load_binary_bytes_from_mirror(occ, modules_dir=os.path.join(td, "modules"),
                                                 binext_dir=os.path.join(td, "bin-ext")),
                b"bc-bytes",
            )

    def test_returns_none_when_mirror_jar_missing(self):
        m = _load()
        occ = {"kind": "bin/ext", "name": "bin/ext/nope.jar"}
        self.assertIsNone(m.load_binary_bytes_from_mirror(occ, modules_dir="/nonexistent/modules",
                                                            binext_dir="/nonexistent/bin-ext"))


class SearchMavenCentralBySha1Test(unittest.TestCase):
    def test_hit_returns_docs(self):
        m = _load()

        def opener(url, timeout=30):
            self.assertIn("q=1:aaaa", url)
            return _FakeResponse(_solr_response([{"g": "org.ow2.asm", "a": "asm", "v": "9.10.1"}]))

        r = m.search_maven_central_by_sha1("aaaa", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "hit")
        self.assertEqual(r["docs"][0]["a"], "asm")

    def test_no_hit_returns_no_hit(self):
        m = _load()

        def opener(url, timeout=30):
            return _FakeResponse(_solr_response([]))

        r = m.search_maven_central_by_sha1("bbbb", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "no-hit")

    def test_network_error_is_typed(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        r = m.search_maven_central_by_sha1("cccc", opener, sleep=lambda s: None, retries=1)
        self.assertEqual(r["status"], "network-error")

    def test_malformed_response_is_typed_network_error(self):
        m = _load()

        def opener(url, timeout=30):
            return _FakeResponse(b"not json")

        r = m.search_maven_central_by_sha1("dddd", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "network-error")


class BinarySha1FromCentralTest(unittest.TestCase):
    def test_found_returns_central_sha1(self):
        m = _load()

        def opener(url, timeout=30):
            self.assertTrue(url.endswith("asm-9.10.1.jar.sha1"))
            return _FakeResponse(b"deadbeef")

        r = m.binary_sha1_from_central("org.ow2.asm", "asm", "9.10.1", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "fetched")
        self.assertEqual(r["central_sha1"], "deadbeef")

    def test_404_is_not_found(self):
        m = _load()
        import urllib.error

        def opener(url, timeout=30):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        r = m.binary_sha1_from_central("g", "a", "v", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "not-found")

    def test_network_error_is_typed(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        r = m.binary_sha1_from_central("g", "a", "v", opener, sleep=lambda s: None, retries=1)
        self.assertEqual(r["status"], "network-error")

    def test_classifier_is_appended_to_the_filename(self):
        m = _load()

        def opener(url, timeout=30):
            self.assertTrue(url.endswith("oauth2-oidc-sdk-11.26-jdk11.jar.sha1"))
            return _FakeResponse(b"deadbeef")

        r = m.binary_sha1_from_central("com.nimbusds", "oauth2-oidc-sdk", "11.26", opener,
                                        sleep=lambda s: None, classifier="jdk11")
        self.assertEqual(r["status"], "fetched")

    def test_empty_body_is_a_typed_network_error_not_a_crash(self):
        # Real 2026-09-28 finding (R3-empty-sha1-body-crash): a 200 response with an empty (or
        # whitespace-only) body used to crash `.split()[0]` with IndexError instead of returning
        # a typed failure -- a malformed/empty server response should degrade to network-error,
        # never an unhandled exception.
        m = _load()

        def opener(url, timeout=30):
            return _FakeResponse(b"")

        r = m.binary_sha1_from_central("g", "a", "v", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "network-error")

    def test_whitespace_only_body_is_a_typed_network_error_not_a_crash(self):
        m = _load()

        def opener(url, timeout=30):
            return _FakeResponse(b"   \n")

        r = m.binary_sha1_from_central("g", "a", "v", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "network-error")


class IdentifyUnidentifiedEntryTest(unittest.TestCase):
    def test_sha1_search_hit_is_identified(self):
        m = _load()

        def opener(url, timeout=30):
            self.assertIn("solrsearch", url)
            return _FakeResponse(_solr_response([{"g": "org.apache.poi", "a": "poi", "v": "5.5.1"}]))

        entry = {"kind": "LIB-INF", "name": "apachePoi.jar!LIB-INF/poi-5.5.1.jar"}
        r = m.identify_unidentified_entry(entry, "aaaa", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "identified-by-sha1")
        self.assertEqual((r["groupId"], r["artifactId"], r["version"]), ("org.apache.poi", "poi", "5.5.1"))
        self.assertEqual(r["method"], "sha1-search")

    def test_no_hit_known_group_guess_confirmed_by_matching_sha1(self):
        m = _load()
        local_sha1 = "matchingsha1"

        def opener(url, timeout=30):
            if "solrsearch" in url:
                return _FakeResponse(_solr_response([]))
            self.assertIn("org/ow2/asm/asm/9.10.1/asm-9.10.1.jar.sha1", url)
            return _FakeResponse(local_sha1.encode())

        entry = {"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar"}
        r = m.identify_unidentified_entry(entry, local_sha1, opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "identified-by-sha1")
        self.assertEqual((r["groupId"], r["artifactId"], r["version"]), ("org.ow2.asm", "asm", "9.10.1"))
        self.assertEqual(r["method"], "filename-guess")

    def test_no_hit_known_group_guess_mismatched_sha1_is_vendor_modified(self):
        # Real 2026-09-28 finding: local bin/ext/asm-9.10.1.jar's sha1 does NOT match
        # org.ow2.asm:asm:9.10.1 on Central (verified live) -- same g:a:v, different bytes.
        m = _load()

        def opener(url, timeout=30):
            if "solrsearch" in url:
                return _FakeResponse(_solr_response([]))
            return _FakeResponse(b"ada2141c0cc52ee8f5c48cd5fa4ce0e794f22236")

        entry = {"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar"}
        r = m.identify_unidentified_entry(entry, "360d8f9fc733d7003c152487e9b55bbe3a5ac32f", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "vendor-modified")
        self.assertEqual((r["groupId"], r["artifactId"], r["version"]), ("org.ow2.asm", "asm", "9.10.1"))

    def test_filename_classifier_is_split_from_version_and_used_in_the_guess_lookup(self):
        # Real 2026-09-28 orchestrator finding: bin/ext/system/jffi-1.4.0-native.jar is the
        # "-native" CLASSIFIER build of com.github.jnr:jffi:1.4.0, not version "1.4.0-native".
        m = _load()
        local_sha1 = "matchingsha1"

        def opener(url, timeout=30):
            if "solrsearch" in url:
                return _FakeResponse(_solr_response([]))
            self.assertIn("com/github/jnr/jffi/1.4.0/jffi-1.4.0-native.jar.sha1", url)
            return _FakeResponse(local_sha1.encode())

        entry = {"kind": "bin/ext", "name": "bin/ext/system/jffi-1.4.0-native.jar"}
        r = m.identify_unidentified_entry(entry, local_sha1, opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "identified-by-sha1")
        self.assertEqual((r["groupId"], r["artifactId"], r["version"]), ("com.github.jnr", "jffi", "1.4.0"))
        self.assertEqual(r["classifier"], "native")

    def test_filename_classifier_mismatch_is_vendor_modified_with_classifier_recorded(self):
        m = _load()

        def opener(url, timeout=30):
            if "solrsearch" in url:
                return _FakeResponse(_solr_response([]))
            return _FakeResponse(b"different-central-sha1")

        entry = {"kind": "bin/ext", "name": "bin/ext/system/jffi-1.4.0-native.jar"}
        r = m.identify_unidentified_entry(entry, "local-sha1", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "vendor-modified")
        self.assertEqual(r["version"], "1.4.0")
        self.assertEqual(r["classifier"], "native")

    def test_no_hit_unknown_group_is_not_on_central(self):
        m = _load()

        def opener(url, timeout=30):
            self.assertIn("solrsearch", url)
            return _FakeResponse(_solr_response([]))

        entry = {"kind": "LIB-INF", "name": "snmpLibs.jar!LIB-INF/mibble-mibs-2.10.1.jar"}
        r = m.identify_unidentified_entry(entry, "aaaa", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "not-on-central")

    def test_no_hit_known_proprietary_group_is_not_on_central_without_guess_network_call(self):
        m = _load()
        calls = []

        def opener(url, timeout=30):
            calls.append(url)
            return _FakeResponse(_solr_response([]))

        entry = {"kind": "bin/ext", "name": "bin/ext/jxbrowser/jxbrowser-9.5.0.jar"}
        r = m.identify_unidentified_entry(entry, "aaaa", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "not-on-central")
        self.assertEqual(r["reason"], "known-proprietary-or-unpublished")
        # only the sha1-search call was made; no wasted guess-verify network call
        self.assertEqual(len(calls), 1)

    def test_guess_coordinate_404_is_not_on_central(self):
        m = _load()
        import urllib.error

        def opener(url, timeout=30):
            if "solrsearch" in url:
                return _FakeResponse(_solr_response([]))
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        entry = {"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar"}
        r = m.identify_unidentified_entry(entry, "aaaa", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "not-on-central")
        self.assertEqual(r["reason"], "guessed-coordinate-404")

    def test_sha1_search_network_error_is_typed(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        entry = {"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar"}
        r = m.identify_unidentified_entry(entry, "aaaa", opener, sleep=lambda s: None, retries=1)
        self.assertEqual(r["status"], "network-error")


class ComputeVendorModifiedOverlapTest(unittest.TestCase):
    def test_computes_overlap_percentage_against_central_binary(self):
        m = _load()
        central_jar = _jar_bytes({"a/Foo.class": b"", "a/Bar.class": b"", "a/Baz.class": b""})
        local_jar = _jar_bytes({"a/Foo.class": b"", "a/Bar.class": b""})

        def opener(url, timeout=30):
            self.assertTrue(url.endswith(".jar"))
            return _FakeResponse(central_jar)

        r = m.compute_vendor_modified_overlap(local_jar, "g", "a", "1.0", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "compared")
        self.assertEqual(r["overlap_pct"], 100.0)  # both local classes present in central

    def test_network_error_is_typed(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        r = m.compute_vendor_modified_overlap(b"", "g", "a", "1.0", opener, sleep=lambda s: None, retries=1)
        self.assertEqual(r["status"], "network-error")


class AllClassEntryHashesTest(unittest.TestCase):
    def test_hashes_every_class_entry_including_nested(self):
        m = _load()
        jar = _jar_bytes({"a/Foo.class": b"foo", "a/Foo$Inner.class": b"inner",
                           "META-INF/MANIFEST.MF": b"mf"})
        hashes = m.all_class_entry_hashes(jar)
        self.assertEqual(set(hashes), {"a/Foo.class", "a/Foo$Inner.class"})
        self.assertEqual(hashes["a/Foo.class"], hashlib.sha256(b"foo").hexdigest())


class ClassifyJarIdentityTest(unittest.TestCase):
    """Real 2026-09-28 orchestrator finding: bin/ext/asm-9.10.1.jar's 39/39 .class entries are
    byte-identical to org.ow2.asm:asm:9.10.1 on Central; only Niagara's added
    META-INF/NIAGARA4.SF + .RSA signature differs. A whole-jar SHA-1 mismatch (the previous T26a
    "vendor-modified" signal) is NOT enough to say the sources aren't ground truth -- only a
    per-.class comparison can."""

    def test_resigned_identical_when_every_class_matches_and_only_signature_differs(self):
        m = _load()
        local = _jar_bytes({"a/Foo.class": b"same", "a/Bar.class": b"same2",
                             "META-INF/NIAGARA4.SF": b"sig", "META-INF/NIAGARA4.RSA": b"sig2"})
        central = _jar_bytes({"a/Foo.class": b"same", "a/Bar.class": b"same2"})
        r = m.classify_jar_identity(local, central)
        self.assertEqual(r["status"], "resigned-identical")
        self.assertEqual(r["classes_identical"], 2)
        self.assertEqual(r["classes_different"], 0)
        self.assertEqual(r["classes_local_only"], 0)
        self.assertEqual(sorted(r["differing_non_class_entries"]),
                          ["META-INF/NIAGARA4.RSA", "META-INF/NIAGARA4.SF"])

    def test_partially_modified_when_some_classes_differ(self):
        m = _load()
        local = _jar_bytes({"a/Foo.class": b"same", "a/Bar.class": b"CHANGED"})
        central = _jar_bytes({"a/Foo.class": b"same", "a/Bar.class": b"original"})
        r = m.classify_jar_identity(local, central)
        self.assertEqual(r["status"], "partially-modified")
        self.assertEqual(r["classes_identical"], 1)
        self.assertEqual(r["classes_different"], 1)
        self.assertEqual(r["different_classes"], ["a/Bar.class"])

    def test_partially_modified_when_some_classes_are_local_only(self):
        m = _load()
        local = _jar_bytes({"a/Foo.class": b"same", "a/Extra.class": b"only-local"})
        central = _jar_bytes({"a/Foo.class": b"same"})
        r = m.classify_jar_identity(local, central)
        self.assertEqual(r["status"], "partially-modified")
        self.assertEqual(r["classes_local_only"], 1)
        self.assertEqual(r["local_only_classes"], ["a/Extra.class"])

    def test_vendor_modified_when_no_class_matches_at_all(self):
        m = _load()
        local = _jar_bytes({"a/Foo.class": b"local-version"})
        central = _jar_bytes({"a/Foo.class": b"central-version"})
        r = m.classify_jar_identity(local, central)
        self.assertEqual(r["status"], "vendor-modified")
        self.assertEqual(r["classes_identical"], 0)

    def test_no_classes_when_local_jar_has_no_class_entries_at_all(self):
        # Real finding: bin/ext/system/jffi-1.4.0-native.jar is pure native .so/.dll (JNI) content
        # -- ZERO .class entries. Lumping this in with "vendor-modified" (which means "we compared
        # classes and none matched") is misleading: there is nothing to compare at all.
        m = _load()
        local = _jar_bytes({"jni/libfoo.so": b"native-lib", "META-INF/MANIFEST.MF": b"mf"})
        central = _jar_bytes({"jni/libfoo.so": b"different-native-lib"})
        r = m.classify_jar_identity(local, central)
        self.assertEqual(r["status"], "no-classes")
        self.assertEqual(r["classes_total_local"], 0)


class MrjarPrefixTest(unittest.TestCase):
    def test_strips_versioned_prefix(self):
        m = _load()
        self.assertEqual(m.strip_mrjar_prefix("META-INF/versions/9/org/foo/Bar"), "org/foo/Bar")

    def test_no_prefix_returns_none(self):
        m = _load()
        self.assertIsNone(m.strip_mrjar_prefix("org/foo/Bar"))

    def test_variants_include_both_forms_when_prefixed(self):
        m = _load()
        self.assertEqual(m.mrjar_variants("META-INF/versions/17/a/B"), {"META-INF/versions/17/a/B", "a/B"})

    def test_variants_is_just_itself_when_unprefixed(self):
        m = _load()
        self.assertEqual(m.mrjar_variants("a/B"), {"a/B"})


class DeclaredPackageOfTest(unittest.TestCase):
    def test_parses_java_package(self):
        m = _load()
        self.assertEqual(m.declared_package_of("package org.foo.bar;\n\nclass X {}"), "org/foo/bar")

    def test_parses_kotlin_package_no_semicolon(self):
        m = _load()
        self.assertEqual(m.declared_package_of("package org.foo.bar\n\nclass X"), "org/foo/bar")

    def test_no_package_statement_returns_none(self):
        # Real finding (R2-001/R3-default-package-doc-test-mismatch, orchestrator second-round
        # review, 2026-09-28): this test's own NAME used to say "is_empty_string" while its body
        # asserted assertIsNone -- a stale rename that no longer matched the actual, and only
        # actually implementable, behavior (see declared_package_of's docstring: a bare regex
        # search cannot distinguish a genuine no-package "default package" file from any other
        # non-matching/malformed text, so both collapse to None, never "").
        m = _load()
        self.assertIsNone(m.declared_package_of("class X {}"))

    def test_skips_leading_comment_before_package(self):
        m = _load()
        text = "/* license header\n * more text\n */\npackage a.b.c;\nclass X {}"
        self.assertEqual(m.declared_package_of(text), "a/b/c")


class DeclaredNamesForSourceTest(unittest.TestCase):
    def test_java_file_declares_package_plus_stem(self):
        m = _load()
        names = m.declared_names_for_source("commonMain/Foo.java", b"package org.foo;\nclass Foo {}")
        self.assertEqual(names, {"org/foo/Foo"})

    def test_kotlin_file_declares_stem_and_default_kt_facade(self):
        # A Kotlin file "Arrays.kt" with top-level functions compiles them into a synthetic
        # "ArraysKt" facade class -- real finding: kotlin-stdlib's commonMain/generated/
        # _Arrays.kt declares "package kotlin.collections" and provides kotlin/collections/
        # ArraysKt (its actual compiled facade), not kotlin/collections/_Arrays (its own path).
        m = _load()
        names = m.declared_names_for_source(
            "commonMain/generated/_Arrays.kt", b"package kotlin.collections\n\nfun foo() {}")
        self.assertEqual(names, {"kotlin/collections/_Arrays", "kotlin/collections/_ArraysKt"})

    def test_kotlin_file_with_jvm_name_annotation_uses_that_name_not_stemkt(self):
        m = _load()
        source = b'@file:JvmName("ArraysKt")\npackage kotlin.collections\n\nfun foo() {}'
        names = m.declared_names_for_source("commonMain/generated/_Arrays.kt", source)
        self.assertEqual(names, {"kotlin/collections/_Arrays", "kotlin/collections/ArraysKt"})

    def test_no_package_statement_yields_no_candidates(self):
        m = _load()
        self.assertEqual(m.declared_names_for_source("Foo.kt", b"fun foo() {}"), set())

    def test_non_source_extension_yields_no_candidates(self):
        m = _load()
        self.assertEqual(m.declared_names_for_source("Foo.txt", b"package a.b;"), set())


class ClassHasMatchingSourceTest(unittest.TestCase):
    def test_direct_path_match(self):
        m = _load()
        src = {"path": {"org/foo/Bar"}, "declared": set()}
        self.assertTrue(m.class_has_matching_source("org/foo/Bar", src))

    def test_mrjar_stripped_binary_matches_unprefixed_source(self):
        m = _load()
        src = {"path": {"org/foo/Bar"}, "declared": set()}
        self.assertTrue(m.class_has_matching_source("META-INF/versions/9/org/foo/Bar", src))

    def test_unprefixed_binary_matches_mrjar_prefixed_source(self):
        # "accept a sources jar that itself stores META-INF/versions/<N>/...java" -- sources_top_
        # level_names already expands prefixed source entries via mrjar_variants at index time.
        m = _load()
        src = {"path": {"META-INF/versions/9/org/foo/Bar", "org/foo/Bar"}, "declared": set()}
        self.assertTrue(m.class_has_matching_source("org/foo/Bar", src))

    def test_declared_fallback_used_when_path_match_fails(self):
        m = _load()
        src = {"path": {"unrelated/path/Name"}, "declared": {"kotlin/collections/ArraysKt"}}
        self.assertTrue(m.class_has_matching_source("kotlin/collections/ArraysKt", src))

    def test_no_match_at_all(self):
        m = _load()
        src = {"path": {"a/B"}, "declared": {"c/D"}}
        self.assertFalse(m.class_has_matching_source("e/F", src))


class FetchCentralBinaryJarTest(unittest.TestCase):
    def test_fetched_and_sha1_verified(self):
        m = _load()
        jar_bytes = b"central-jar-bytes"
        sha1 = hashlib.sha1(jar_bytes).hexdigest()

        def opener(url, timeout=30):
            if url.endswith(".sha1"):
                return _FakeResponse(sha1.encode())
            return _FakeResponse(jar_bytes)

        r = m.fetch_central_binary_jar("g", "a", "1.0", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "fetched")
        self.assertEqual(r["bytes"], jar_bytes)
        self.assertEqual(r["sha1"], sha1)

    def test_not_found(self):
        m = _load()
        import urllib.error

        def opener(url, timeout=30):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        r = m.fetch_central_binary_jar("g", "a", "1.0", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "not-found")

    def test_checksum_mismatch(self):
        m = _load()

        def opener(url, timeout=30):
            if url.endswith(".sha1"):
                return _FakeResponse(b"0" * 40)
            return _FakeResponse(b"different-bytes")

        r = m.fetch_central_binary_jar("g", "a", "1.0", opener, sleep=lambda s: None)
        self.assertEqual(r["status"], "checksum-mismatch")

    def test_network_error_is_typed(self):
        m = _load()

        def opener(url, timeout=30):
            raise TimeoutError("slow")

        r = m.fetch_central_binary_jar("g", "a", "1.0", opener, sleep=lambda s: None, retries=1)
        self.assertEqual(r["status"], "network-error")

    def test_classifier_binary_is_fetched_not_the_classifier_less_one(self):
        # Real 2026-09-28 orchestrator finding: comparing against the classifier-LESS binary for
        # a classifier build gives a false 0/533 mismatch; the classifier binary is 533/533.
        m = _load()
        jar_bytes = b"classifier-jar-bytes"
        sha1 = hashlib.sha1(jar_bytes).hexdigest()
        seen = []

        def opener(url, timeout=30):
            seen.append(url)
            self.assertNotIn("oauth2-oidc-sdk-11.26.jar", url)  # never the classifier-less one
            if url.endswith(".sha1"):
                return _FakeResponse(sha1.encode())
            return _FakeResponse(jar_bytes)

        r = m.fetch_central_binary_jar("com.nimbusds", "oauth2-oidc-sdk", "11.26", opener,
                                        sleep=lambda s: None, classifier="jdk11")
        self.assertEqual(r["status"], "fetched")
        self.assertTrue(any("oauth2-oidc-sdk-11.26-jdk11.jar" in u for u in seen))


class RunIdentifyUnidentifiedTest(unittest.TestCase):
    def _mirror(self, td, entries):
        modules_dir = os.path.join(td, "modules")
        binext_dir = os.path.join(td, "bin-ext")
        os.makedirs(modules_dir, exist_ok=True)
        os.makedirs(binext_dir, exist_ok=True)
        return modules_dir, binext_dir

    def test_identified_entry_moves_from_unidentified_to_artifacts(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            with open(os.path.join(binext_dir, "asm-9.10.1.jar"), "wb") as f:
                f.write(b"asm-bytes")
            local_sha1 = hashlib.sha1(b"asm-bytes").hexdigest()

            def opener(url, timeout=30):
                return _FakeResponse(_solr_response([{"g": "org.ow2.asm", "a": "asm", "v": "9.10.1"}]))

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar", "reason": "no-pom-properties"},
            ]}
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["identified-by-sha1"], 1)
            self.assertEqual(len(plan["artifacts"]), 1)
            self.assertEqual(plan["artifacts"][0]["groupId"], "org.ow2.asm")
            self.assertEqual(plan["artifacts"][0]["occurrences"][0]["binary_sha1"], local_sha1)
            self.assertEqual(plan["unidentified"], [])

    def test_whole_jar_mismatch_but_every_class_identical_is_resigned_identical(self):
        # Real 2026-09-28 orchestrator finding: bin/ext/asm-9.10.1.jar's whole-jar SHA-1 differs
        # from Central's asm-9.10.1.jar only because Niagara ADDS a signature (META-INF/
        # NIAGARA4.SF/.RSA); every .class entry is byte-identical. The old whole-jar-SHA-1-only
        # check called this "vendor-modified" and excluded it from coverage -- wrong: a per-class
        # SHA-256 compare proves the sources ARE ground truth here.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            local_jar = _jar_bytes({"a/Foo.class": b"same", "META-INF/NIAGARA4.SF": b"sig",
                                     "META-INF/NIAGARA4.RSA": b"sig2"})
            with open(os.path.join(binext_dir, "asm-9.10.1.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"a/Foo.class": b"same"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()

            def opener(url, timeout=30):
                if "solrsearch" in url:
                    return _FakeResponse(_solr_response([]))
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar", "reason": "no-pom-properties"},
            ]}
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["resigned-identical"], 1)
            self.assertEqual(summary["vendor-modified"], 0)
            art = plan["artifacts"][0]
            self.assertEqual(art["content_identity"]["status"], "resigned-identical")
            self.assertEqual(art["content_identity"]["classes_identical"], 1)
            self.assertEqual(plan["unidentified"], [])

    def test_whole_jar_mismatch_with_real_class_differences_is_partially_modified(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            local_jar = _jar_bytes({"a/Foo.class": b"same", "a/Bar.class": b"CHANGED"})
            with open(os.path.join(binext_dir, "lib-1.0.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"a/Foo.class": b"same", "a/Bar.class": b"original"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()

            def opener(url, timeout=30):
                if "solrsearch" in url:
                    return _FakeResponse(_solr_response([]))
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/lib-1.0.jar", "reason": "no-pom-properties"},
            ]}
            # "lib" has no KNOWN_GROUP_GUESSES entry -- patch one in for this test only.
            m.KNOWN_GROUP_GUESSES["lib"] = "com.example"
            self.addCleanup(m.KNOWN_GROUP_GUESSES.pop, "lib", None)
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["partially-modified"], 1)
            art = plan["artifacts"][0]
            self.assertEqual(art["content_identity"]["status"], "partially-modified")
            self.assertEqual(art["content_identity"]["different_classes"], ["a/Bar.class"])

    def test_vendor_modified_when_deep_compare_finds_no_matching_class(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            local_jar = _jar_bytes({"a/Foo.class": b"local-version"})
            with open(os.path.join(binext_dir, "lib2-1.0.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"a/Foo.class": b"central-version"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()

            def opener(url, timeout=30):
                if "solrsearch" in url:
                    return _FakeResponse(_solr_response([]))
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/lib2-1.0.jar", "reason": "no-pom-properties"},
            ]}
            m.KNOWN_GROUP_GUESSES["lib2"] = "com.example"
            self.addCleanup(m.KNOWN_GROUP_GUESSES.pop, "lib2", None)
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["vendor-modified"], 1)
            self.assertEqual(plan["artifacts"][0]["content_identity"]["status"], "vendor-modified")

    def test_unverifiable_when_central_binary_cannot_be_fetched(self):
        m = _load()
        import urllib.error
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            with open(os.path.join(binext_dir, "lib3-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({"a/Foo.class": b"x"}))

            def opener(url, timeout=30):
                if "solrsearch" in url:
                    return _FakeResponse(_solr_response([]))
                if url.endswith(".sha1"):
                    return _FakeResponse(b"deadbeef")
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/lib3-1.0.jar", "reason": "no-pom-properties"},
            ]}
            m.KNOWN_GROUP_GUESSES["lib3"] = "com.example"
            self.addCleanup(m.KNOWN_GROUP_GUESSES.pop, "lib3", None)
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["unverifiable"], 1)
            self.assertEqual(plan["artifacts"][0]["content_identity"]["status"], "unverifiable")

    def test_not_on_central_entry_stays_in_unidentified_with_refined_reason(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            with open(os.path.join(binext_dir, "unknown-1.0.jar"), "wb") as f:
                f.write(b"unknown-bytes")

            def opener(url, timeout=30):
                return _FakeResponse(_solr_response([]))

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/unknown-1.0.jar", "reason": "no-pom-properties"},
            ]}
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["not-on-central"], 1)
            self.assertEqual(plan["artifacts"], [])
            self.assertEqual(len(plan["unidentified"]), 1)
            self.assertNotEqual(plan["unidentified"][0]["reason"], "no-pom-properties")

    def test_network_error_stays_retryable_no_pom_properties(self):
        # Real 2026-09-28 finding (R3-sticky-transient-failure / R4-identify-transient-failure-
        # not-retryable): a transient network error used to be written back with reason
        # "network-error:...", which no longer equals "no-pom-properties" -- the NEXT
        # identify-unidentified pass would then permanently SKIP this jar (the reason guard at
        # the top of the loop only re-processes entries whose reason IS "no-pom-properties")
        # instead of retrying what was just a network blip. "not-on-central" (a real, final
        # verdict) must still change the reason -- see the sibling test above.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            with open(os.path.join(binext_dir, "flaky-1.0.jar"), "wb") as f:
                f.write(b"flaky-bytes")

            calls = []

            def opener(url, timeout=30):
                calls.append(url)
                raise TimeoutError("slow")

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/flaky-1.0.jar", "reason": "no-pom-properties"},
            ]}
            summary1 = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir,
                                                     mirror_binext_dir=binext_dir, opener=opener,
                                                     sleep=lambda s: None, retries=1, pace=0)
            self.assertEqual(summary1["network-error"], 1)
            self.assertEqual(plan["unidentified"][0]["reason"], "no-pom-properties")

            calls_before_second_pass = len(calls)
            summary2 = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir,
                                                     mirror_binext_dir=binext_dir, opener=opener,
                                                     sleep=lambda s: None, retries=1, pace=0)
            self.assertEqual(summary2["network-error"], 1)
            self.assertGreater(len(calls), calls_before_second_pass,
                                "second pass must actually retry the network call, not skip it")

    def test_entries_with_other_reasons_are_left_untouched(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "x.jar", "reason": "some-other-reason"},
            ]}

            def opener(url, timeout=30):
                raise AssertionError("should not be called for non-no-pom-properties entries")

            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(plan["unidentified"], [{"kind": "bin/ext", "name": "x.jar", "reason": "some-other-reason"}])
            self.assertEqual(summary["identified-by-sha1"], 0)

    def test_mirror_jar_missing_is_reported_without_network_call(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])

            def opener(url, timeout=30):
                raise AssertionError("should not be called when the mirror jar is missing")

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/gone.jar", "reason": "no-pom-properties"},
            ]}
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["mirror-unavailable"], 1)
            self.assertEqual(plan["unidentified"][0]["reason"], "mirror-jar-not-found")

    def test_classifier_mismatch_deep_check_fetches_the_classifier_central_binary(self):
        # End-to-end real-shape reproduction of the jffi-1.4.0-native.jar finding: the deep
        # per-.class check after a whole-jar mismatch must compare against Central's CLASSIFIER
        # binary, not the classifier-less one, and record "classifier" on the artifact.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            system_dir = os.path.join(binext_dir, "system")
            os.makedirs(system_dir, exist_ok=True)
            local_jar = _jar_bytes({"jni/libfoo.so": b"local-native-lib"})
            with open(os.path.join(system_dir, "jffi-1.4.0-native.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"jni/libfoo.so": b"central-native-lib"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()
            seen_urls = []

            def opener(url, timeout=30):
                seen_urls.append(url)
                if "solrsearch" in url:
                    return _FakeResponse(_solr_response([]))
                self.assertIn("jffi-1.4.0-native.jar", url)  # never the classifier-less coordinate
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/system/jffi-1.4.0-native.jar", "reason": "no-pom-properties"},
            ]}
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir,
                                                    opener=opener, sleep=lambda s: None, pace=0)
            self.assertEqual(summary["no-classes"], 1)
            art = plan["artifacts"][0]
            self.assertEqual(art["groupId"], "com.github.jnr")
            self.assertEqual(art["content_identity"]["classifier"], "native")
            self.assertTrue(any("jffi-1.4.0-native.jar" in u for u in seen_urls))

    def test_classifier_propagates_to_the_overlap_fallback_when_central_jar_fetch_fails(self):
        # Real finding (R3-identified-classifier-propagation): when the classifier binary itself
        # can't be fetched (network/404, as opposed to a checksum mismatch), the code falls back
        # to compute_vendor_modified_overlap for a diagnostic class-name overlap -- but that
        # fallback used to build its URL WITHOUT the classifier suffix, comparing the local
        # classifier jar against the wrong (classifier-less) Central coordinate.
        m = _load()
        import urllib.error
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td, [])
            local_jar = _jar_bytes({"a/Foo.class": b"local"})
            with open(os.path.join(binext_dir, "widget-1.0-native.jar"), "wb") as f:
                f.write(local_jar)
            central_sha1 = hashlib.sha1(b"central-bytes-not-matching-local").hexdigest()
            seen_urls = []

            def opener(url, timeout=30):
                seen_urls.append(url)
                if "solrsearch" in url:
                    return _FakeResponse(_solr_response([]))
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

            plan = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/widget-1.0-native.jar", "reason": "no-pom-properties"},
            ]}
            m.KNOWN_GROUP_GUESSES["widget"] = "com.example"
            self.addCleanup(m.KNOWN_GROUP_GUESSES.pop, "widget", None)
            summary = m.run_identify_unidentified(plan, mirror_modules_dir=modules_dir,
                                                    mirror_binext_dir=binext_dir, opener=opener,
                                                    sleep=lambda s: None, pace=0)
            self.assertEqual(summary["unverifiable"], 1)
            jar_fetch_urls = [u for u in seen_urls if not u.endswith(".sha1") and "solrsearch" not in u]
            self.assertTrue(jar_fetch_urls, "the overlap fallback never attempted a jar fetch")
            self.assertTrue(all(u.endswith("widget-1.0-native.jar") for u in jar_fetch_urls),
                             f"a jar fetch used the classifier-less coordinate: {jar_fetch_urls}")


class RunFetchPropagatesSha1IdentificationFieldsTest(unittest.TestCase):
    """Real-run finding (2026-09-28): run_fetch rebuilds each manifest record from an explicit
    field allowlist, so a T26a-identified artifact's "content_identity" / "identification_method"
    silently vanished between plan.json and manifest.json -- the report's content-identity table
    rendered empty even though run_identify_unidentified found real classifications."""

    def test_content_identity_and_identification_method_survive_fetch(self):
        m = _load()
        jar_bytes = b"src"
        sha1 = hashlib.sha1(jar_bytes).hexdigest()

        def opener(url, timeout=30):
            if url.endswith(".sha1"):
                return _FakeResponse(sha1.encode())
            return _FakeResponse(jar_bytes)

        plan = {
            "unidentified": [],
            "artifacts": [{
                "groupId": "org.ow2.asm", "artifactId": "asm", "version": "9.10.1",
                "occurrences": [{"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar", "binary_sha1": "local"}],
                "_candidate_versions": ["9.10.1"],
                "identification_method": "filename-guess",
                "content_identity": {"status": "resigned-identical", "classes_identical": 39,
                                      "classes_different": 0, "classes_local_only": 0,
                                      "classes_total_local": 39},
            }],
        }
        # run_fetch writes sources jars under a path relative to REPO_ROOT (it records
        # sources_jar_path via .relative_to(REPO_ROOT)), so the out_dir must live under the repo,
        # not under an arbitrary system tempdir; use a throwaway subdir of the gitignored
        # organized/ tree and remove it afterwards.
        import shutil
        out_dir = m.REPO_ROOT / "organized" / "_test_tmp_run_fetch_propagation"
        self.addCleanup(shutil.rmtree, out_dir, True)
        manifest = m.run_fetch(plan, out_dir, opener=opener, sleep=lambda s: None, pace=0)
        art = manifest["artifacts"][0]
        self.assertEqual(art.get("identification_method"), "filename-guess")
        self.assertIn("content_identity", art)
        self.assertEqual(art["content_identity"]["status"], "resigned-identical")
        self.assertEqual(art["content_identity"]["classes_identical"], 39)


class RunAllThirdPartyCoverageTest(unittest.TestCase):
    """Orchestrator follow-up review (2026-09-28) on the first fix: the headline must use ONE
    consistent unit (real_class_entries: every real `.class` entry, nested/anonymous included,
    module-info/package-info excluded) for BOTH numerator and denominator, and "covered" must mean
    PROVEN identity (see run_all_third_party_coverage's docstring), not a bare classdiff name
    match -- that weaker signal moved to the separate classdiff_coverage report section."""

    def _mirror(self, td):
        modules_dir = os.path.join(td, "modules")
        binext_dir = os.path.join(td, "bin-ext")
        os.makedirs(modules_dir, exist_ok=True)
        os.makedirs(binext_dir, exist_ok=True)
        return modules_dir, binext_dir

    def _sources_jar_under_repo(self, name, entries):
        # sources_top_level_names reads art["sources_jar_path"] relative to REPO_ROOT (matching
        # run_fetch's own convention), so a real fetched-sources test needs a file under the repo,
        # not an arbitrary system tempdir; use a throwaway subdir of the gitignored organized/
        # tree and remove it afterwards.
        import shutil
        m = _load()
        out_dir = m.REPO_ROOT / "organized" / "_test_tmp_coverage_sources"
        out_dir.mkdir(parents=True, exist_ok=True)
        self.addCleanup(shutil.rmtree, out_dir, True)
        jar_path = out_dir / name
        jar_path.write_bytes(_jar_bytes(entries))
        return str(jar_path.relative_to(m.REPO_ROOT))

    def test_unidentified_jar_counts_toward_denominator_zero_covered(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "still-unknown.jar"), "wb") as f:
                f.write(_jar_bytes({"a/One.class": b"", "a/Two.class": b""}))
            manifest = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/still-unknown.jar", "reason": "not-on-central"},
            ]}
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertEqual(coverage["classes_total"], 2)

    def test_resigned_identical_covers_top_level_nested_and_anonymous_classes(self):
        # Reviewer follow-up finding: a synthetic jar with a top-level, a nested, and an anonymous
        # class. Whole-jar proof (resigned-identical) proves ALL of them; they are all covered
        # because their shared top-level class ("a/Widget") has a matching .java in the fetched
        # sources jar -- a nested/anonymous class lives INSIDE its top-level class's own source.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "widget-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({
                    "a/Widget.class": b"top", "a/Widget$Inner.class": b"nested",
                    "a/Widget$1.class": b"anon",
                }))
            sources_path = self._sources_jar_under_repo("widget-1.0-sources.jar",
                                                          {"a/Widget.java": b"class Widget {}"})
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "widget", "version": "1.0", "status": "fetched",
                     "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/widget-1.0.jar"}],
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 3)
            self.assertEqual(coverage["classes_with_upstream_source"], 3)

    def test_sha1_exact_content_identity_fully_covered(self):
        # A "sha1-exact" verdict (b117's own whole-jar SHA-1 match) is just as strong a proof as
        # "resigned-identical" -- every class in the jar is covered.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "asm-9.10.1.jar"), "wb") as f:
                f.write(_jar_bytes({f"a/C{i}.class": b"" for i in range(12)}))
            sources_path = self._sources_jar_under_repo(
                "asm-9.10.1-sources.jar", {f"a/C{i}.java": b"..." for i in range(12)})
            manifest = {
                "artifacts": [
                    {"groupId": "org.ow2.asm", "artifactId": "asm", "version": "9.10.1", "status": "fetched",
                     "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/asm-9.10.1.jar"}],
                     "content_identity": {"status": "sha1-exact",
                                           "source": "evidence/b117/maven-repo1.json"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_with_upstream_source"], 12)
            self.assertEqual(coverage["classes_total"], 12)

    def test_partially_modified_covers_only_the_proven_entries_nested_included(self):
        # Per-entry granularity: a/Good.class + its nested a/Good$Inner.class are proven and
        # sourced (covered); a/Bad.class is explicitly in different_classes (not proven), so it
        # is NOT covered even though it has a matching .java too.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "mix-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({
                    "a/Good.class": b"good", "a/Good$Inner.class": b"good-nested",
                    "a/Bad.class": b"bad",
                }))
            sources_path = self._sources_jar_under_repo(
                "mix-1.0-sources.jar", {"a/Good.java": b"...", "a/Bad.java": b"..."})
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "mix", "version": "1.0", "status": "fetched",
                     "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/mix-1.0.jar"}],
                     "content_identity": {"status": "partially-modified",
                                           "different_classes": ["a/Bad.class"],
                                           "local_only_classes": []}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 3)
            self.assertEqual(coverage["classes_with_upstream_source"], 2)

    def test_vendor_modified_content_identity_excluded_from_covered_but_included_in_total(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "bad-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({f"a/C{i}.class": b"" for i in range(5)}))
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "bad", "version": "1.0", "status": "fetched",
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/bad-1.0.jar"}],
                     "content_identity": {"status": "vendor-modified"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertEqual(coverage["classes_total"], 5)

    def test_jar_with_zero_real_classes_is_not_treated_as_missing(self):
        # Real 2026-09-28 finding: bin/ext/okhttp-5.5.0.jar (the Kotlin Multiplatform metadata
        # artifact, not okhttp-jvm) genuinely ships ZERO .class entries -- a legitimate value, not
        # a missing one; must not fall back to classdiff's stale/unrelated binary_total.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "okhttp-5.5.0.jar"), "wb") as f:
                f.write(_jar_bytes({"META-INF/MANIFEST.MF": b"x"}))  # no .class entries at all
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "okhttp", "version": "5.5.0", "status": "fetched",
                     "classdiff": {"common": 0, "binary_total": 999},  # a stale/unrelated fallback
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/okhttp-5.5.0.jar"}],
                     "content_identity": {"status": "no-classes"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertEqual(coverage["classes_total"], 0)  # NOT 999

    def test_artifact_without_content_identity_or_classdiff_is_not_silently_omitted(self):
        # Real 2026-09-28 finding (R3-headline-denominator-silent-omission /
        # R4-coverage-denominator-silently-shrinks): an artifact identified via pom.properties
        # whose sources jar was never fetched (status != "fetched": no-sources-published /
        # checksum-mismatch / network-error) never gets a "classdiff" key at all (run_classdiff
        # only processes status == "fetched") and, without a content_identity or
        # identification_method either, used to be `continue`-d out of the denominator entirely.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "orphan-2.0.jar"), "wb") as f:
                f.write(_jar_bytes({"a/One.class": b"", "a/Two.class": b"", "a/Three.class": b""}))
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "orphan", "version": "2.0",
                     "status": "no-sources-published",
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/orphan-2.0.jar"}]},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertEqual(coverage["classes_total"], 3)  # NOT 0 / silently omitted
            self.assertEqual(manifest["artifacts"][0]["class_count"], 3)

    def test_classdiff_only_artifact_denominator_counts_every_class_but_covers_none_without_proof(self):
        # Reviewer follow-up (2026-09-28): a bare classdiff name match (no content_identity, no
        # identification_method -- i.e. NO binary identity proof at all) no longer counts as
        # "covered" in this authoritative headline; that weaker, name-only signal still lives in
        # the separate "Class coverage by original upstream source" (classdiff_coverage) section.
        # The denominator still uses the real unit -- the nested class counts too.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "libx-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({"a/One.class": b"", "a/Two.class": b"", "a/Two$Inner.class": b""}))
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "libx", "version": "1.0", "status": "fetched",
                     "classdiff": {"common": 2, "binary_total": 2},
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/libx-1.0.jar"}]},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 3)  # NOT 2 -- the nested class counts too
            self.assertEqual(coverage["classes_with_upstream_source"], 0)  # NOT 2 -- name match isn't proof

    def test_identification_method_without_content_identity_is_whole_jar_proof(self):
        # Real 2026-09-28 finding: T26a's "identified-by-sha1" artifacts (the whole LOCAL jar's
        # bytes exactly match a Central SHA-1 -- via a sha1-search hit or an exact filename-guess
        # match) never get a content_identity at all, by design (see
        # run_identify_unidentified) -- but the whole-jar SHA-1 IS the strongest possible proof,
        # exactly as strong as resigned-identical/sha1-exact, and must cover nested classes too.
        # This is the real corpus gap the orchestrator's follow-up review flagged: poi, poi-ooxml,
        # xmlbeans, kotlin-stdlib(T26a), json-path, hsqldb, testng, jcommander all hit this path.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "poi-5.5.1.jar"), "wb") as f:
                f.write(_jar_bytes({"o/A.class": b"a", "o/A$B.class": b"nested"}))
            sources_path = self._sources_jar_under_repo("poi-5.5.1-sources.jar", {"o/A.java": b"..."})
            manifest = {
                "artifacts": [
                    {"groupId": "org.apache.poi", "artifactId": "poi", "version": "5.5.1",
                     "status": "fetched", "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/poi-5.5.1.jar"}],
                     "identification_method": "sha1-search"},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 2)
            self.assertEqual(coverage["classes_with_upstream_source"], 2)

    def test_module_info_and_package_info_excluded_from_the_unit(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "modtool-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({
                    "a/Real.class": b"real", "module-info.class": b"mod",
                    "a/package-info.class": b"pkg",
                }))
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "modtool", "version": "1.0",
                     "status": "no-sources-published",
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/modtool-1.0.jar"}]},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 1)  # module-info + package-info excluded
            self.assertEqual(manifest["artifacts"][0]["class_count"], 1)

    def test_kotlin_only_sources_jar_matched_via_kt_extension(self):
        # kotlin-stdlib and friends publish .kt sources, no .java at all -- a Kotlin-only sources
        # jar must still count as source coverage.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "kotlin-stdlib-2.3.0.jar"), "wb") as f:
                f.write(_jar_bytes({"kotlin/Foo.class": b"foo"}))
            sources_path = self._sources_jar_under_repo(
                "kotlin-stdlib-2.3.0-sources.jar", {"kotlin/Foo.kt": b"class Foo"})
            manifest = {
                "artifacts": [
                    {"groupId": "org.jetbrains.kotlin", "artifactId": "kotlin-stdlib", "version": "2.3.0",
                     "status": "fetched", "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/kotlin-stdlib-2.3.0.jar"}],
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 1)
            self.assertEqual(coverage["classes_with_upstream_source"], 1)

    def test_one_unreadable_sources_entry_does_not_zero_the_whole_jars_coverage(self):
        # Real finding (R3-upstream-entry-read-failure/R4-coverage-entry-read-failure-zeroes-
        # artifact, orchestrator second-round review, 2026-09-28): sources_top_level_names used to
        # wrap its ENTIRE zip-reading loop in one try/except that returned None (this artifact's
        # coverage entirely zeroed) the moment ANY single entry's z.read() failed -- one corrupt
        # class file in an otherwise-healthy sources jar must only drop THAT entry, not every
        # other, perfectly readable class's coverage too. Uses a Kotlin Multiplatform source-set
        # layout (commonMain/) so the match can ONLY happen via each entry's OWN declared-package
        # bytes (see declared_names_for_source) -- a path-based match needs no file content at
        # all, so it alone would not exercise the per-entry read failure this fix is about.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "mix-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({"kotlin/Good.class": b"good", "kotlin/Bad.class": b"bad"}))
            import shutil
            out_dir = m.REPO_ROOT / "organized" / "_test_tmp_corrupt_sources_entry"
            out_dir.mkdir(parents=True, exist_ok=True)
            self.addCleanup(shutil.rmtree, out_dir, True)
            jar_path = out_dir / "mix-1.0-sources.jar"
            jar_path.write_bytes(_jar_bytes_with_corrupt_entry(
                {"commonMain/Good.kt": b"package kotlin\nclass Good {}",
                 "commonMain/Bad.kt": b"package kotlin\nclass Bad {}"}, "commonMain/Bad.kt"))
            sources_path = str(jar_path.relative_to(m.REPO_ROOT))
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "mix", "version": "1.0", "status": "fetched",
                     "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/mix-1.0.jar"}],
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 2)
            # kotlin/Good is still covered (its OWN entry read fine) even though kotlin/Bad's
            # entry is unreadable -- not both zeroed by one bad entry elsewhere in the same jar.
            self.assertEqual(coverage["classes_with_upstream_source"], 1)

    def test_unidentified_jar_with_no_mirror_bytes_is_counted_not_silently_dropped(self):
        # Real finding (R3-no-mirror-content-identity-denominator-drop/R4-mirror-absent-proof-
        # discarded, orchestrator second-round review, 2026-09-28): an unidentified jar whose own
        # local-mirror copy has since gone missing used to just `continue`, leaving its class_count
        # None with NO record anywhere of how many classes (or how many entries) were dropped from
        # the denominator this way -- a silent gap, not merely an "honestly uncountable" one.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            # Deliberately do NOT create bin/ext/ghost-1.0.jar in either mirror dir.
            manifest = {"artifacts": [], "unidentified": [
                {"kind": "bin/ext", "name": "bin/ext/ghost-1.0.jar", "reason": "not-on-central"},
            ]}
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 0)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertEqual(coverage["classes_uncounted_no_mirror"], 1)
            self.assertIsNone(manifest["unidentified"][0]["class_count"])
            self.assertIn("no-mirror", manifest["unidentified"][0]["class_count_uncounted_reason"])

    def test_artifact_without_mirror_or_classdiff_fallback_is_counted_not_silently_dropped(self):
        # Same gap as above, for the OTHER loop: a T26a "identified-by-sha1" artifact (no
        # classdiff at all -- see run_identify_unidentified) whose local-mirror copy is missing
        # used to add NOTHING to the denominator and leave no trace of the drop.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            # Deliberately do NOT create bin/ext/poi-5.5.1.jar in either mirror dir.
            manifest = {
                "artifacts": [
                    {"groupId": "org.apache.poi", "artifactId": "poi", "version": "5.5.1",
                     "status": "fetched",
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/poi-5.5.1.jar"}],
                     "identification_method": "sha1-search"},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 0)
            self.assertEqual(coverage["classes_uncounted_no_mirror"], 1)
            self.assertIsNone(manifest["artifacts"][0]["class_count"])
            self.assertIn("no-mirror", manifest["artifacts"][0]["class_count_uncounted_reason"])

    def test_sources_jar_missing_on_disk_despite_fetched_status_is_reported_not_silent(self):
        # Related visibility gap: an artifact PROVEN byte-identical (so it WOULD contribute to
        # "covered") whose manifest says status=="fetched" but whose sources_jar_path no longer
        # points at a readable file on disk used to just silently contribute 0 to "covered", with
        # no distinction from a legitimately zero-source-overlap artifact.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "ghostsrc-1.0.jar"), "wb") as f:
                f.write(_jar_bytes({"a/One.class": b"one"}))
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "ghostsrc", "version": "1.0", "status": "fetched",
                     "sources_jar_path": "organized/_upstream-sources/g/ghostsrc/1.0/ghostsrc-1.0-sources.jar",
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/ghostsrc-1.0.jar"}],
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 1)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertEqual(coverage["artifacts_with_proof_but_unreadable_sources_jar"], 1)

    def test_no_mirror_bytes_falls_back_to_classdiff_binary_total_with_zero_covered(self):
        # Genuinely uncountable in the real unit (the mirror doesn't have the jar) -- better an
        # undercounted denominator (classdiff's narrower, top-level-only binary_total) than a
        # silently missing one; 0 covered, since no per-entry proof can be computed without bytes.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
                     "classdiff": {"common": 8, "binary_total": 10},
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 10)
            self.assertEqual(coverage["classes_with_upstream_source"], 0)
            self.assertIsNone(manifest["artifacts"][0]["class_count"])

    def test_mrjar_override_class_matched_via_unprefixed_source(self):
        # Real 2026-09-28 finding: bc-fips's binary ships a duplicate META-INF/versions/9/ copy
        # of every class (multi-release jar); the sources jar has only the un-prefixed path. The
        # override class is the SAME logical class -- its source IS the un-prefixed .java file.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "bc-fips-2.1.2.jar"), "wb") as f:
                f.write(_jar_bytes({
                    "org/bc/Foo.class": b"base",
                    "META-INF/versions/9/org/bc/Foo.class": b"override",
                }))
            sources_path = self._sources_jar_under_repo(
                "bc-fips-2.1.2-sources.jar", {"org/bc/Foo.java": b"package org.bc;\nclass Foo {}"})
            manifest = {
                "artifacts": [
                    {"groupId": "g", "artifactId": "bc-fips", "version": "2.1.2", "status": "fetched",
                     "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/bc-fips-2.1.2.jar"}],
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 2)
            self.assertEqual(coverage["classes_with_upstream_source"], 2)  # NOT 1

    def test_kotlin_multiplatform_source_set_layout_matched_via_declared_package(self):
        # Real 2026-09-28 finding: kotlin-stdlib's sources jar lays .kt files out by SOURCE SET
        # (commonMain/generated/_Arrays.kt), not by compiled package path -- path-based matching
        # alone can never find it. This covers both a plain top-level-functions file (default
        # "<Stem>Kt" facade) and an @file:JvmName-renamed one.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            modules_dir, binext_dir = self._mirror(td)
            with open(os.path.join(binext_dir, "kotlin-stdlib-2.3.0.jar"), "wb") as f:
                f.write(_jar_bytes({
                    "kotlin/collections/ArraysKt.class": b"facade",
                    "kotlin/collections/CustomNamed.class": b"jvmname-facade",
                }))
            sources_path = self._sources_jar_under_repo("kotlin-stdlib-2.3.0-sources.jar", {
                "commonMain/generated/Arrays.kt": b"package kotlin.collections\n\nfun sortedArray() {}",
                "commonMain/generated/_Named.kt":
                    b'@file:JvmName("CustomNamed")\npackage kotlin.collections\n\nfun namedThing() {}',
            })
            manifest = {
                "artifacts": [
                    {"groupId": "org.jetbrains.kotlin", "artifactId": "kotlin-stdlib", "version": "2.3.0",
                     "status": "fetched", "sources_jar_path": sources_path,
                     "occurrences": [{"kind": "bin/ext", "name": "bin/ext/kotlin-stdlib-2.3.0.jar"}],
                     "content_identity": {"status": "resigned-identical"}},
                ],
                "unidentified": [],
            }
            coverage = m.run_all_third_party_coverage(manifest, mirror_modules_dir=modules_dir, mirror_binext_dir=binext_dir)
            self.assertEqual(coverage["classes_total"], 2)
            self.assertEqual(coverage["classes_with_upstream_source"], 2)  # NOT 0


class RunRecheckPomIdentifiedGapsTest(unittest.TestCase):
    """Orchestrator follow-up: artifacts identified via pom.properties (the original 154, i.e. no
    T26a identification_method) whose evidence/b117 record shows a whole-jar SHA-1 mismatch were
    never class-level verified. Reuse b117's own "identical-non-META-INF" finding where present
    (no network); do a live per-class check for the rest (download-failed / real diffs)."""

    def _install(self, td):
        install_dir = os.path.join(td, "install")
        os.makedirs(os.path.join(install_dir, "bin", "ext"), exist_ok=True)
        return install_dir

    def test_skips_t26a_identified_artifacts(self):
        m = _load()
        manifest = {"artifacts": [
            {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
             "identification_method": "sha1-search",
             "occurrences": [{"kind": "bin/ext", "name": "bin/ext/a-1.jar"}]},
        ]}

        def opener(url, timeout=30):
            raise AssertionError("should not fetch for a T26a-identified artifact")

        summary = m.run_recheck_pom_identified_gaps(manifest, [], opener=opener, sleep=lambda s: None)
        self.assertNotIn("content_identity", manifest["artifacts"][0])

    def test_records_sha1_exact_whole_jar_match(self):
        # Orchestrator-found defect fix (2026-09-28): a b117 "exact" whole-jar SHA-1 match is the
        # STRONGEST possible proof -- it must never be silently skipped (the old behavior left 81
        # of 188 manifest artifacts with neither content_identity nor identification_method,
        # making tools/n5-best-source.py treat them as unproven). No further verification (and no
        # network call) is needed: b117 already proved it.
        m = _load()
        manifest = {"artifacts": [
            {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
             "occurrences": [{"kind": "bin/ext", "name": "bin/ext/a-1.jar"}]},
        ]}
        evidence = [{"kind": "bin/ext", "name": "bin/ext/a-1.jar", "result": "exact",
                     "sha1": "deadbeef"}]

        def opener(url, timeout=30):
            raise AssertionError("a b117 'exact' whole-jar match needs no further verification")

        summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener,
                                                      sleep=lambda s: None)
        self.assertEqual(summary["sha1-exact"], 1)
        ci = manifest["artifacts"][0]["content_identity"]
        self.assertEqual(ci["status"], "sha1-exact")
        self.assertEqual(ci["source"], "evidence/b117/maven-repo1.json")
        self.assertEqual(ci["sha1"], "deadbeef")
        occ_ci = manifest["artifacts"][0]["occurrences"][0]["content_identity"]
        self.assertEqual(occ_ci, ci)

    def test_unverified_when_occurrence_has_no_b117_record(self):
        # Defensive: every occurrence of an original pom.properties-identified artifact traces
        # back to a b117 entry by construction, but if one is ever missing, this must be recorded
        # explicitly as "unverified" -- never silently dropped (no content_identity at all).
        m = _load()
        manifest = {"artifacts": [
            {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
             "occurrences": [{"kind": "bin/ext", "name": "bin/ext/a-1.jar"}]},
        ]}

        def opener(url, timeout=30):
            raise AssertionError("no b117 record to check against; nothing to fetch")

        summary = m.run_recheck_pom_identified_gaps(manifest, [], opener=opener,
                                                      sleep=lambda s: None)
        self.assertEqual(summary["unverified"], 1)
        ci = manifest["artifacts"][0]["content_identity"]
        self.assertEqual(ci["status"], "unverified")
        self.assertIn("reason", ci)

    def test_multiple_exact_occurrences_roll_up_to_sha1_exact(self):
        # jackson-annotations-style real finding: TWO occurrences (LIB-INF + etc/m2), BOTH b117
        # "exact" -- they agree, so the artifact-level rollup collapses to one verdict, still
        # recorded per occurrence too.
        m = _load()
        manifest = {"artifacts": [
            {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
             "occurrences": [
                 {"kind": "LIB-INF", "name": "mod.jar!LIB-INF/a-1.jar"},
                 {"kind": "etc/m2", "name": "etc/m2/repository/g/a/1/a-1.jar"},
             ]},
        ]}
        evidence = [
            {"kind": "LIB-INF", "name": "mod.jar!LIB-INF/a-1.jar", "result": "exact", "sha1": "aaa"},
            {"kind": "etc/m2", "name": "etc/m2/repository/g/a/1/a-1.jar", "result": "exact", "sha1": "bbb"},
        ]

        def opener(url, timeout=30):
            raise AssertionError("both occurrences are already proven exact by b117")

        summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener,
                                                      sleep=lambda s: None)
        self.assertEqual(summary["sha1-exact"], 1)
        art = manifest["artifacts"][0]
        self.assertEqual(art["content_identity"]["status"], "sha1-exact")
        self.assertEqual(art["occurrences"][0]["content_identity"]["sha1"], "aaa")
        self.assertEqual(art["occurrences"][1]["content_identity"]["sha1"], "bbb")

    def test_disagreeing_occurrences_keep_per_occurrence_verdicts_not_collapsed(self):
        # Real finding (org.jetbrains:annotations:13.0 / jakarta.xml.bind-api:4.0.5 /
        # jakarta.activation-api:2.1.4): one occurrence is b117 "exact", the other is "differs"
        # with a REAL (non-reused, non-whole-trust) content difference -- these must NOT collapse
        # to a single artifact-level verdict; each occurrence keeps its own.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            install_dir = self._install(td)
            local_jar = _jar_bytes({"a/Foo.class": b"local", "a/Bar.class": b"only-local"})
            with open(os.path.join(install_dir, "bin", "ext", "a-1.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"a/Foo.class": b"local"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()

            def opener(url, timeout=30):
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            manifest = {"artifacts": [
                {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
                 "occurrences": [
                     {"kind": "LIB-INF", "name": "mod.jar!LIB-INF/a-1.jar"},
                     {"kind": "bin/ext", "name": "bin/ext/a-1.jar"},
                 ]},
            ]}
            evidence = [
                {"kind": "LIB-INF", "name": "mod.jar!LIB-INF/a-1.jar", "result": "exact", "sha1": "aaa"},
                {"kind": "bin/ext", "name": "bin/ext/a-1.jar", "result": "differs",
                 "content": "differs:1"},
            ]
            summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener,
                                                          sleep=lambda s: None,
                                                          install_dir=install_dir, pace=0)
            self.assertEqual(summary["mixed"], 1)
            art = manifest["artifacts"][0]
            self.assertEqual(art["content_identity"]["status"], "mixed")
            occ0_ci = art["occurrences"][0]["content_identity"]
            occ1_ci = art["occurrences"][1]["content_identity"]
            self.assertEqual(occ0_ci["status"], "sha1-exact")
            self.assertEqual(occ1_ci["status"], "partially-modified")
            # Per-occurrence linking data (n5-best-source.py's own jar-sha256 join) must be
            # present and DIFFERENT for the two occurrences -- never collapsed to one value.
            self.assertIsNotNone(art["occurrences"][1].get("binary_sha256"))

    def test_reuses_b117_identical_non_meta_inf_without_network(self):
        m = _load()
        manifest = {"artifacts": [
            {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
             "occurrences": [{"kind": "bin/ext", "name": "bin/ext/a-1.jar"}]},
        ]}
        evidence = [{"kind": "bin/ext", "name": "bin/ext/a-1.jar", "result": "differs",
                     "content": "identical-non-META-INF", "meta_inf_local": ["META-INF/NIAGARA4.SF"]}]

        def opener(url, timeout=30):
            raise AssertionError("should reuse b117's evidence, not fetch")

        summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener, sleep=lambda s: None)
        self.assertEqual(summary["reused-resigned-identical"], 1)
        ci = manifest["artifacts"][0]["content_identity"]
        self.assertEqual(ci["status"], "resigned-identical")
        self.assertEqual(ci["source"], "b117-reused")

    def test_live_checks_a_download_failed_b117_entry(self):
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            install_dir = self._install(td)
            local_jar = _jar_bytes({"a/Foo.class": b"same"})
            with open(os.path.join(install_dir, "bin", "ext", "a-1.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"a/Foo.class": b"same"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()

            def opener(url, timeout=30):
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            manifest = {"artifacts": [
                {"groupId": "g", "artifactId": "a", "version": "1", "status": "fetched",
                 "occurrences": [{"kind": "bin/ext", "name": "bin/ext/a-1.jar"}]},
            ]}
            evidence = [{"kind": "bin/ext", "name": "bin/ext/a-1.jar", "result": "differs",
                         "content": "download-failed"}]
            summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener,
                                                          sleep=lambda s: None, install_dir=install_dir, pace=0)
            self.assertEqual(summary["resigned-identical"], 1)
            ci = manifest["artifacts"][0]["content_identity"]
            self.assertEqual(ci["status"], "resigned-identical")
            self.assertEqual(ci["source"], "live-recheck")

    def test_uses_resolved_version_not_pom_version_for_central_lookup(self):
        # Real 2026-09-28 finding: mssql-jdbc's pom.properties version is "13.4.0" but the
        # artifact only exists on Central under "13.4.0.jre11" (candidate_versions' own
        # correction, already used to fetch its SOURCES jar via "resolved_version"). Looking up
        # the BINARY jar by the plain "version" 404s and wrongly reports "unverifiable".
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            install_dir = self._install(td)
            local_jar = _jar_bytes({"a/Foo.class": b"same"})
            with open(os.path.join(install_dir, "bin", "ext", "mssql-jdbc-13.4.0.jre11.jar"), "wb") as f:
                f.write(local_jar)
            central_jar = _jar_bytes({"a/Foo.class": b"same"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()
            seen_urls = []

            def opener(url, timeout=30):
                seen_urls.append(url)
                if "/13.4.0/" in url:
                    import urllib.error
                    raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            manifest = {"artifacts": [
                {"groupId": "com.microsoft.sqlserver", "artifactId": "mssql-jdbc", "version": "13.4.0",
                 "resolved_version": "13.4.0.jre11", "status": "fetched",
                 "occurrences": [{"kind": "bin/ext", "name": "bin/ext/mssql-jdbc-13.4.0.jre11.jar"}]},
            ]}
            evidence = [{"kind": "bin/ext", "name": "bin/ext/mssql-jdbc-13.4.0.jre11.jar",
                         "result": "not-on-central"}]
            summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener,
                                                          sleep=lambda s: None, install_dir=install_dir, pace=0)
            self.assertTrue(any("13.4.0.jre11" in u for u in seen_urls))
            self.assertEqual(summary["resigned-identical"], 1)
            self.assertEqual(manifest["artifacts"][0]["content_identity"]["status"], "resigned-identical")

    def test_detects_classifier_from_occurrence_basename_and_compares_against_it(self):
        # Real 2026-09-28 orchestrator finding: oauth2.jar!LIB-INF/oauth2-oidc-sdk-11.26-jdk11.jar
        # is the "jdk11" CLASSIFIER build. Comparing against the classifier-less Central binary
        # gives a false 0/533; the classifier binary is 533/533 byte-identical.
        m = _load()
        with tempfile.TemporaryDirectory() as td:
            install_dir = self._install(td)
            modules_dir = os.path.join(install_dir, "modules")
            os.makedirs(modules_dir, exist_ok=True)
            local_jar = _jar_bytes({"com/nimbusds/oauth2/sdk/Foo.class": b"same"})
            with zipfile.ZipFile(os.path.join(modules_dir, "oauth2.jar"), "w") as z:
                z.writestr("LIB-INF/oauth2-oidc-sdk-11.26-jdk11.jar", local_jar)
            central_jar = _jar_bytes({"com/nimbusds/oauth2/sdk/Foo.class": b"same"})
            central_sha1 = hashlib.sha1(central_jar).hexdigest()
            seen_urls = []

            def opener(url, timeout=30):
                seen_urls.append(url)
                self.assertNotIn("oauth2-oidc-sdk-11.26.jar", url)  # never the classifier-less one
                if url.endswith(".sha1"):
                    return _FakeResponse(central_sha1.encode())
                return _FakeResponse(central_jar)

            manifest = {"artifacts": [
                {"groupId": "com.nimbusds", "artifactId": "oauth2-oidc-sdk", "version": "11.26",
                 "resolved_version": "11.26", "status": "fetched",
                 "occurrences": [{"kind": "LIB-INF", "name": "oauth2.jar!LIB-INF/oauth2-oidc-sdk-11.26-jdk11.jar"}]},
            ]}
            evidence = [{"kind": "LIB-INF", "name": "oauth2.jar!LIB-INF/oauth2-oidc-sdk-11.26-jdk11.jar",
                         "result": "differs", "content": "differs:539"}]
            summary = m.run_recheck_pom_identified_gaps(manifest, evidence, opener=opener,
                                                          sleep=lambda s: None, mod_dir=modules_dir, pace=0)
            self.assertTrue(any("oauth2-oidc-sdk-11.26-jdk11.jar" in u for u in seen_urls))
            self.assertEqual(summary["resigned-identical"], 1)
            ci = manifest["artifacts"][0]["content_identity"]
            self.assertEqual(ci["status"], "resigned-identical")
            self.assertEqual(ci["classifier"], "jdk11")


class RenderReportAllThirdPartyHeadlineTest(unittest.TestCase):
    def test_headline_states_explicit_denominator(self):
        m = _load()
        manifest = {"artifacts": [], "unidentified": []}
        text = m.render_report(manifest, all_third_party_coverage={"classes_with_upstream_source": 21000, "classes_total": 47700})
        self.assertIn("21000", text)
        self.assertIn("47700", text)
        self.assertIn("ALL third-party classes", text)
        # This report's headline number and tools/n5-best-source.py's `by_best_kind.upstream`
        # count measure different things (one class-name-match-in-a-proven-sources-jar count over
        # distinct third-party jars, the other a per-population count where the same physical
        # class can recur across populations) -- the report must say so explicitly rather than
        # let a reader assume the two numbers should match 1:1.
        self.assertIn("n5-best-source.py", text)
        self.assertIn("per-population", text)

    def test_headline_caveats_the_all_claim_when_entries_were_uncounted(self):
        # R2-report-one-unit-claim-overstates (orchestrator second-round review, 2026-09-28): the
        # headline claims coverage over "ALL third-party classes" -- when some entries genuinely
        # could not be counted (no mirror bytes) or an artifact's proof couldn't translate into
        # "covered" because its sources jar isn't actually readable, that must be disclosed, not
        # silently rolled into an unqualified "ALL" claim.
        m = _load()
        manifest = {"artifacts": [], "unidentified": []}
        text = m.render_report(manifest, all_third_party_coverage={
            "classes_with_upstream_source": 100, "classes_total": 200,
            "classes_uncounted_no_mirror": 3,
            "artifacts_with_proof_but_unreadable_sources_jar": 2,
        })
        self.assertIn("3 artifact/unidentified-jar entries", text)
        self.assertIn("2 artifact(s) have PROVEN binary identity", text)

    def test_headline_omits_the_caveat_when_nothing_was_uncounted(self):
        m = _load()
        manifest = {"artifacts": [], "unidentified": []}
        text = m.render_report(manifest, all_third_party_coverage={
            "classes_with_upstream_source": 100, "classes_total": 200,
            "classes_uncounted_no_mirror": 0,
            "artifacts_with_proof_but_unreadable_sources_jar": 0,
        })
        self.assertNotIn("Caveat on the \"ALL\" claim", text)

    def test_identify_summary_rendered(self):
        m = _load()
        manifest = {"artifacts": [], "unidentified": [
            {"kind": "bin/ext", "name": "bin/ext/jxbrowser/jxbrowser-9.5.0.jar", "reason": "not-on-central:known-proprietary-or-unpublished"},
        ]}
        text = m.render_report(manifest, identify_summary={
            "identified-by-sha1": 10, "resigned-identical": 9, "partially-modified": 1,
            "vendor-modified": 2, "unverifiable": 0, "not-on-central": 30, "network-error": 0,
            "mirror-unavailable": 0,
        })
        self.assertIn("identified-by-sha1", text)
        self.assertIn("resigned-identical", text)
        self.assertIn("vendor-modified", text)
        self.assertIn("not-on-central:known-proprietary-or-unpublished", text)

    def test_content_identity_table_rendered(self):
        m = _load()
        manifest = {"unidentified": [], "artifacts": [
            {"artifactId": "asm", "version": "9.10.1", "groupId": "org.ow2.asm", "status": "fetched",
             "content_identity": {"status": "resigned-identical", "classes_identical": 39,
                                   "classes_different": 0, "classes_local_only": 0,
                                   "classes_total_local": 39,
                                   "differing_non_class_entries": ["META-INF/NIAGARA4.SF", "META-INF/NIAGARA4.RSA"],
                                   "source": "live-recheck"}},
            {"artifactId": "lz4-java", "version": "1.11.2", "groupId": "org.lz4", "status": "fetched",
             "content_identity": {"status": "partially-modified", "classes_identical": 7,
                                   "classes_different": 3, "classes_local_only": 0,
                                   "classes_total_local": 10, "different_classes": ["a/X.class"],
                                   "differing_non_class_entries": [], "source": "b117-reused"}},
        ]}
        text = m.render_report(manifest)
        self.assertIn("resigned-identical", text)
        self.assertIn("partially-modified", text)
        self.assertIn("NIAGARA4.SF", text)
        self.assertIn("a/X.class", text)

    def test_pom_recheck_summary_table_includes_new_statuses(self):
        # Orchestrator-found defect fix: the pom-recheck table must render "sha1-exact" (the b117
        # whole-jar-match reuse, previously silently skipped), "mixed" (occurrences that
        # disagree), and "unverified" (no b117 record at all) -- never a silently missing row.
        m = _load()
        manifest = {"artifacts": [], "unidentified": []}
        text = m.render_report(manifest, pom_recheck_summary={
            "reused-resigned-identical": 64, "sha1-exact": 78, "resigned-identical": 11,
            "partially-modified": 0, "vendor-modified": 1, "no-classes": 0, "unverifiable": 0,
            "unverified": 0, "mixed": 0,
        })
        self.assertIn("| sha1-exact | 78 |", text)
        self.assertIn("| mixed | 0 |", text)
        self.assertIn("| unverified | 0 |", text)


class TestJavapFailureIsNeverAMatch(unittest.TestCase):
    """Review review-38b7ff2daec0bf35: javap failing on both sides produced [] == [] -> a false MATCH."""

    def test_run_javap_raises_on_missing_class_file(self):
        mod = _load()
        with self.assertRaises(mod.JavapError):
            mod.run_javap("/nonexistent/definitely/missing.class")

    def test_run_javap_raises_when_javap_binary_is_missing(self):
        # CI runners have no JDK at the local path: a missing javap must be a typed JavapError too.
        mod = _load()
        with self.assertRaisesRegex(mod.JavapError, "javap not runnable"):
            mod.run_javap("/nonexistent/X.class", javap_bin="/nonexistent/bin/javap")

    def test_run_javap_raises_on_empty_output(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "fake-javap")
            with open(fake, "w") as f:
                f.write("#!/bin/sh\nexit 0\n")
            os.chmod(fake, 0o755)
            with self.assertRaises(mod.JavapError):
                mod.run_javap(os.path.join(d, "X.class"), javap_bin=fake)


if __name__ == "__main__":
    unittest.main()
