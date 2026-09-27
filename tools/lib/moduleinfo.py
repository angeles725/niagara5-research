"""moduleinfo.py — pure-Python parser for a JPMS `module-info.class` file.

WHY: n5-modules.py needs each N5 module's `requires`/`exports` (JPMS Module
attribute, JVMS §4.7.25) to build the module dependency graph. Shelling out to
`javap -v` works but adds an external-tool dependency with a hardcoded path;
this is a small, dependency-free classfile reader that decodes just enough of
the classfile format (constant pool + the `Module` attribute) to answer that,
without pulling in a JVM at all. `parse_module_info(data)` returns a dict:
    {"name": str, "requires": [{"name": str, "transitive": bool}, ...],
     "exports": [{"package": str, "to": [str, ...]}, ...]}

Reference: JVMS 4.4 (constant pool), JVMS 4.7.25 (Module attribute).
Stdlib only.
"""
from __future__ import annotations

import struct

# Constant pool tag -> (name, extra bytes to skip after the tag byte, or None
# for the variable-length Utf8 case which is handled specially).
CONSTANT_Utf8 = 1
CONSTANT_Integer = 3
CONSTANT_Float = 4
CONSTANT_Long = 5
CONSTANT_Double = 6
CONSTANT_Class = 7
CONSTANT_String = 8
CONSTANT_Fieldref = 9
CONSTANT_Methodref = 10
CONSTANT_InterfaceMethodref = 11
CONSTANT_NameAndType = 12
CONSTANT_MethodHandle = 15
CONSTANT_MethodType = 16
CONSTANT_Dynamic = 17
CONSTANT_InvokeDynamic = 18
CONSTANT_Module = 19
CONSTANT_Package = 20

# Fixed-size constant pool entries: tag -> byte length AFTER the tag byte.
_FIXED_SIZE = {
    CONSTANT_Integer: 4,
    CONSTANT_Float: 4,
    CONSTANT_Long: 8,
    CONSTANT_Double: 8,
    CONSTANT_Class: 2,
    CONSTANT_String: 2,
    CONSTANT_Fieldref: 4,
    CONSTANT_Methodref: 4,
    CONSTANT_InterfaceMethodref: 4,
    CONSTANT_NameAndType: 4,
    CONSTANT_MethodHandle: 3,
    CONSTANT_MethodType: 2,
    CONSTANT_Dynamic: 4,
    CONSTANT_InvokeDynamic: 4,
    CONSTANT_Module: 2,
    CONSTANT_Package: 2,
}

# Constant pool entries that reference a Utf8/Module/Package pool slot for a name.
_NAME_INDEX_TAGS = {CONSTANT_Class, CONSTANT_Module, CONSTANT_Package}

ACC_TRANSITIVE = 0x0020


class ClassFileError(ValueError):
    """The input is not a well-formed classfile (or not the Module attribute)."""


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def u1(self) -> int:
        v = self.data[self.pos]
        self.pos += 1
        return v

    def u2(self) -> int:
        v = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return v

    def u4(self) -> int:
        v = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return v

    def skip(self, n: int) -> None:
        self.pos += n

    def bytes(self, n: int) -> bytes:
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        return b


def _parse_constant_pool(r: _Reader) -> list:
    """Return a list indexed 1..count-1 (index 0 and Long/Double's second slot
    are None, matching JVMS constant_pool numbering quirks)."""
    count = r.u2()
    pool: list = [None] * count
    i = 1
    while i < count:
        tag = r.u1()
        if tag == CONSTANT_Utf8:
            length = r.u2()
            raw = r.bytes(length)
            # JVM "modified UTF-8" is a superset of ASCII/most UTF-8 text seen
            # in module/package names; decode leniently.
            pool[i] = raw.decode("utf-8", errors="replace")
        elif tag in _FIXED_SIZE:
            pool[i] = r.bytes(_FIXED_SIZE[tag])
            if tag in (CONSTANT_Long, CONSTANT_Double):
                # Long/Double occupy two consecutive constant pool indices.
                i += 1
        else:
            raise ClassFileError(f"unknown constant pool tag {tag} at index {i}")
        pool[i - 0] if False else None  # no-op, keeps intent obvious
        i += 1
    return pool


def _utf8(pool: list, index: int) -> str:
    v = pool[index]
    if not isinstance(v, str):
        raise ClassFileError(f"constant pool index {index} is not Utf8")
    return v


def _name_ref(pool: list, index: int) -> str:
    """index points at a Class/Module/Package constant pool entry, whose
    stored payload is itself a 2-byte name_index into a Utf8 entry."""
    raw = pool[index]
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != 2:
        raise ClassFileError(f"constant pool index {index} is not a Module/Package/Class ref")
    (name_index,) = struct.unpack(">H", raw)
    return _utf8(pool, name_index)


def _skip_attributes(r: _Reader, n: int) -> None:
    for _ in range(n):
        r.u2()          # attribute_name_index
        length = r.u4()
        r.skip(length)


def parse_module_info(data: bytes) -> dict:
    """Parse a module-info.class byte string into {name, requires, exports}."""
    r = _Reader(data)
    magic = r.u4()
    if magic != 0xCAFEBABE:
        raise ClassFileError("not a Java classfile (bad magic)")
    r.u2()  # minor_version
    r.u2()  # major_version

    pool = _parse_constant_pool(r)

    r.u2()  # access_flags
    r.u2()  # this_class
    r.u2()  # super_class

    interfaces_count = r.u2()
    r.skip(2 * interfaces_count)

    fields_count = r.u2()
    for _ in range(fields_count):
        r.u2(); r.u2(); r.u2()  # access_flags, name_index, descriptor_index
        _skip_attributes(r, r.u2())

    methods_count = r.u2()
    for _ in range(methods_count):
        r.u2(); r.u2(); r.u2()
        _skip_attributes(r, r.u2())

    attributes_count = r.u2()
    for _ in range(attributes_count):
        name_index = r.u2()
        length = r.u4()
        attr_name = _utf8(pool, name_index)
        if attr_name != "Module":
            r.skip(length)
            continue
        return _parse_module_attribute(pool, r)

    raise ClassFileError("no Module attribute found (not a module-info.class?)")


def _parse_module_attribute(pool: list, r: _Reader) -> dict:
    module_name_index = r.u2()
    r.u2()  # module_flags
    r.u2()  # module_version_index (0 if absent)
    module_name = _name_ref(pool, module_name_index)

    requires = []
    requires_count = r.u2()
    for _ in range(requires_count):
        req_index = r.u2()
        req_flags = r.u2()
        r.u2()  # requires_version_index
        req_name = _name_ref(pool, req_index)
        requires.append({
            "name": req_name,
            "transitive": bool(req_flags & ACC_TRANSITIVE),
        })

    exports = []
    exports_count = r.u2()
    for _ in range(exports_count):
        exp_index = r.u2()
        r.u2()  # exports_flags
        to_count = r.u2()
        to_list = []
        for _ in range(to_count):
            to_index = r.u2()
            to_list.append(_name_ref(pool, to_index))
        # CONSTANT_Package stores the binary name with '/' separators
        # (JVMS 4.2.3); javap and everyone else display it with '.'.
        exp_package = _name_ref(pool, exp_index).replace("/", ".")
        exports.append({"package": exp_package, "to": to_list})

    # opens/uses/provides are parsed-and-discarded (JVMS order is fixed) so the
    # cursor stays valid even though this tool does not report them.
    opens_count = r.u2()
    for _ in range(opens_count):
        r.u2(); r.u2()
        to_count = r.u2()
        r.skip(2 * to_count)

    uses_count = r.u2()
    r.skip(2 * uses_count)

    provides_count = r.u2()
    for _ in range(provides_count):
        r.u2()
        with_count = r.u2()
        r.skip(2 * with_count)

    return {"name": module_name, "requires": requires, "exports": exports}
