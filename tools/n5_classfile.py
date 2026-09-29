"""Minimal class-file readers for the C2b third-party fidelity grading.

- class_major_version / javac_release_for_major: the shipped class-file major version decides the
  `javac --release` a class is recompiled with (never a global default). A major javac 25 cannot
  target maps to None (the grader records the typed state `release-unsupported`).
- has_kotlin_metadata: True only when the CLASS carries a RuntimeVisibleAnnotations entry of type
  `Lkotlin/Metadata;` (a member annotation or a bare mention of the type in a descriptor is not the
  Kotlin marker).
"""
from __future__ import annotations

import struct

# javac 25 accepts --release 8..25 (checked against the installed javac by the tests).
JAVAC_MIN_RELEASE = 8
JAVAC_MAX_RELEASE = 25
_MAJOR_OFFSET = 44  # class-file major = release + 44 (52 = Java 8)
KOTLIN_METADATA_DESCRIPTOR = "Lkotlin/Metadata;"


def class_major_version(data: bytes) -> int:
    if len(data) < 8 or data[:4] != b"\xca\xfe\xba\xbe":
        raise ValueError("not a class file")
    return struct.unpack(">H", data[6:8])[0]


def javac_release_for_major(major: int):
    """`--release` value for a shipped class-file major, or None when javac 25 cannot target it."""
    release = major - _MAJOR_OFFSET
    return release if JAVAC_MIN_RELEASE <= release <= JAVAC_MAX_RELEASE else None


def _skip_constant_pool(data: bytes, pos: int, count: int):
    """Walk the constant pool; return (utf8 {index: str}, position after the pool)."""
    utf8: dict[int, str] = {}
    i = 1
    while i < count:
        tag = data[pos]
        if tag == 1:
            (length,) = struct.unpack(">H", data[pos + 1:pos + 3])
            utf8[i] = data[pos + 3:pos + 3 + length].decode("utf-8", "replace")
            pos += 3 + length
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag in (5, 6):
            pos += 9
            i += 1  # long/double take two slots
        elif tag in (7, 8, 16, 19, 20):
            pos += 3
        elif tag == 15:
            pos += 4
        else:
            raise ValueError(f"bad constant pool tag {tag}")
        i += 1
    return utf8, pos


def _skip_members(data: bytes, pos: int) -> int:
    (n,) = struct.unpack(">H", data[pos:pos + 2])
    pos += 2
    for _ in range(n):
        pos += 6  # access, name, descriptor
        (attrs,) = struct.unpack(">H", data[pos:pos + 2])
        pos += 2
        for _ in range(attrs):
            (length,) = struct.unpack(">I", data[pos + 2:pos + 6])
            pos += 6 + length
    return pos


def has_kotlin_metadata(data: bytes) -> bool:
    """True iff the class-level attributes include RuntimeVisibleAnnotations with a kotlin.Metadata
    annotation. Anything that cannot be parsed is reported as not-Kotlin (never raises)."""
    try:
        class_major_version(data)
        (cp_count,) = struct.unpack(">H", data[8:10])
        utf8, pos = _skip_constant_pool(data, 10, cp_count)
        pos += 6  # access, this, super
        (n_if,) = struct.unpack(">H", data[pos:pos + 2])
        pos += 2 + 2 * n_if
        pos = _skip_members(data, pos)  # fields
        pos = _skip_members(data, pos)  # methods
        (n_attr,) = struct.unpack(">H", data[pos:pos + 2])
        pos += 2
        for _ in range(n_attr):
            name_idx, length = struct.unpack(">HI", data[pos:pos + 6])
            body = pos + 6
            if utf8.get(name_idx) == "RuntimeVisibleAnnotations":
                (n_ann,) = struct.unpack(">H", data[body:body + 2])
                if n_ann and _annotation_types(data, body + 2, n_ann, utf8) & {KOTLIN_METADATA_DESCRIPTOR}:
                    return True
            pos = body + length
        return False
    except (ValueError, IndexError, struct.error):
        return False


def _annotation_types(data: bytes, pos: int, count: int, utf8: dict) -> set:
    """Type descriptors of the top-level annotations of a RuntimeVisibleAnnotations attribute
    (element values are skipped structurally)."""
    types = set()
    for _ in range(count):
        type_idx, pairs = struct.unpack(">HH", data[pos:pos + 4])
        types.add(utf8.get(type_idx, ""))
        pos += 4
        for _ in range(pairs):
            pos += 2  # element name
            pos = _skip_element_value(data, pos)
    return types


def _skip_element_value(data: bytes, pos: int) -> int:
    tag = chr(data[pos])
    pos += 1
    if tag in "BCDFIJSZs":
        return pos + 2
    if tag == "e":
        return pos + 4
    if tag == "c":
        return pos + 2
    if tag == "@":
        type_idx, pairs = struct.unpack(">HH", data[pos:pos + 4])
        pos += 4
        for _ in range(pairs):
            pos = _skip_element_value(data, pos + 2)
        return pos
    if tag == "[":
        (n,) = struct.unpack(">H", data[pos:pos + 2])
        pos += 2
        for _ in range(n):
            pos = _skip_element_value(data, pos)
        return pos
    raise ValueError(f"bad element_value tag {tag!r}")
