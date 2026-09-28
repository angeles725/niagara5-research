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


if __name__ == "__main__":
    unittest.main()
