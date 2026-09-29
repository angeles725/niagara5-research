"""Tests for tools/n5_classfile.py: minimal class-file readers used by the C2b third-party grading
(shipped class-file major version -> javac --release, the kotlin.Metadata marker).

Fixtures are REAL classes compiled by the local JDK 25 javac (skipped when it is absent).
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

JAVAC = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"

KOTLIN_METADATA_SRC = ("package kotlin;\nimport java.lang.annotation.*;\n"
                       "@Retention(RetentionPolicy.RUNTIME) public @interface Metadata { int k() default 1; }\n")


def _compile(td, name, source, extra_args=(), package_dir=""):
    src_dir = os.path.join(td, "src", package_dir)
    os.makedirs(src_dir, exist_ok=True)
    src = os.path.join(src_dir, f"{name}.java")
    with open(src, "w") as f:
        f.write(source)
    out = os.path.join(td, "out")
    os.makedirs(out, exist_ok=True)
    subprocess.run([JAVAC, "-nowarn", "-proc:none", "-d", out, *extra_args, "-cp", out, src],
                   check=True, capture_output=True)
    return out


@unittest.skipUnless(os.path.isfile(JAVAC), "JDK 25 javac not installed")
class TestClassMajorAndRelease(unittest.TestCase):
    def _major_of(self, release):
        import n5_classfile
        with tempfile.TemporaryDirectory() as td:
            out = _compile(td, "A", "public class A {}", ["--release", str(release)])
            with open(os.path.join(out, "A.class"), "rb") as f:
                return n5_classfile.class_major_version(f.read())

    def test_major_version_of_real_classes(self):
        self.assertEqual(self._major_of(8), 52)
        self.assertEqual(self._major_of(17), 61)
        self.assertEqual(self._major_of(25), 69)

    def test_release_is_derived_from_the_shipped_major_never_a_default(self):
        import n5_classfile
        self.assertEqual(n5_classfile.javac_release_for_major(52), 8)
        self.assertEqual(n5_classfile.javac_release_for_major(55), 11)
        self.assertEqual(n5_classfile.javac_release_for_major(61), 17)
        self.assertEqual(n5_classfile.javac_release_for_major(69), 25)

    def test_majors_javac_25_cannot_target_are_unsupported(self):
        import n5_classfile
        for major in (49, 50, 51, 70, 0):   # Java 5/6/7 and a class newer than the grader's javac
            self.assertIsNone(n5_classfile.javac_release_for_major(major), major)

    def test_the_supported_range_matches_what_the_real_javac_accepts(self):
        # guards the MIN/MAX constants against the installed javac
        import n5_classfile
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "A.java"), "w") as f:
                f.write("class A {}")
            def rc(release):
                return subprocess.run([JAVAC, "--release", str(release), "-d", td, os.path.join(td, "A.java")],
                                      capture_output=True).returncode
            self.assertEqual(rc(n5_classfile.JAVAC_MIN_RELEASE), 0)
            self.assertNotEqual(rc(n5_classfile.JAVAC_MIN_RELEASE - 1), 0)
            self.assertEqual(rc(n5_classfile.JAVAC_MAX_RELEASE), 0)
            self.assertNotEqual(rc(n5_classfile.JAVAC_MAX_RELEASE + 1), 0)

    def test_truncated_or_non_class_bytes_raise(self):
        import n5_classfile
        with self.assertRaises(ValueError):
            n5_classfile.class_major_version(b"PK\x03\x04junk")
        with self.assertRaises(ValueError):
            n5_classfile.class_major_version(b"\xca\xfe")


@unittest.skipUnless(os.path.isfile(JAVAC), "JDK 25 javac not installed")
class TestKotlinMetadataMarker(unittest.TestCase):
    def _bytes(self, td, name):
        with open(os.path.join(td, "out", name), "rb") as f:
            return f.read()

    def test_class_annotated_with_kotlin_metadata_is_detected(self):
        import n5_classfile
        with tempfile.TemporaryDirectory() as td:
            _compile(td, "Metadata", KOTLIN_METADATA_SRC, package_dir="kotlin")
            _compile(td, "K", "@kotlin.Metadata(k = 1) public class K { int f; void m() {} }")
            self.assertTrue(n5_classfile.has_kotlin_metadata(self._bytes(td, "K.class")))

    def test_plain_class_is_not_kotlin(self):
        import n5_classfile
        with tempfile.TemporaryDirectory() as td:
            _compile(td, "P", "public class P { int f; void m() {} }")
            self.assertFalse(n5_classfile.has_kotlin_metadata(self._bytes(td, "P.class")))

    def test_class_that_merely_mentions_the_annotation_type_is_not_kotlin(self):
        # a field/parameter of type kotlin.Metadata puts the very same "Lkotlin/Metadata;" Utf8 in
        # the constant pool; only a class-level RuntimeVisibleAnnotations entry counts
        import n5_classfile
        with tempfile.TemporaryDirectory() as td:
            _compile(td, "Metadata", KOTLIN_METADATA_SRC, package_dir="kotlin")
            _compile(td, "Holder", "public class Holder { kotlin.Metadata md; void m(kotlin.Metadata x) {} }")
            self.assertFalse(n5_classfile.has_kotlin_metadata(self._bytes(td, "Holder.class")))

    def test_member_level_annotation_is_not_a_class_marker(self):
        import n5_classfile
        with tempfile.TemporaryDirectory() as td:
            _compile(td, "Metadata", KOTLIN_METADATA_SRC, package_dir="kotlin")
            _compile(td, "M", "public class M { @kotlin.Metadata(k = 2) void m() {} }")
            self.assertFalse(n5_classfile.has_kotlin_metadata(self._bytes(td, "M.class")))

    def test_bad_bytes_are_not_kotlin_never_a_crash(self):
        import n5_classfile
        self.assertFalse(n5_classfile.has_kotlin_metadata(b"not a class"))


if __name__ == "__main__":
    unittest.main()
