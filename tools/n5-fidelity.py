#!/usr/bin/env python3
"""n5-fidelity.py — per-class, machine-checked semantic decompiler fidelity grader.

Ground truth is the shipped Tridium .class files under organized/<mod>/extracted/.
For every top-level class C, the decompiled Vineflower .java is recompiled with
`javac --release 25` against a classpath of ALL N5 jars (classpath/unnamed-module
mode — everything except C binds to the ORIGINAL bytecode) and the resulting
.class is compared to the shipped .class with a normalizer built over
`javap -v -p` output: constant-pool indices are dropped in favor of the symbolic
comments javap already resolves, LineNumberTable/LocalVariableTable/StackMapTable
are ignored entirely, local-variable slots are canonicalized by first-use order,
and branch targets are canonicalized to a position relative to the branching
instruction. See docs/decompile-fidelity-report.md for the aggregate results and
docs/decompiler-bakeoff.md for the sibling recompile methodology this reuses
(javac --release 25, classpath = all module jars + bin/ext jars).

Redundancy ladder for a class that does not round-trip under Vineflower: retry
the SAME class recompiled from CFR 0.152, then Procyon 0.6.0, then (if
provisioned — see --jd-cli-jar) JD-CLI, keeping the first engine that reaches
roundtrip-exact/equivalent (`best_decompiler`). Every attempted engine's grade
is recorded (`attempted`) so disagreement between engines is visible, and
`consensus.count` records how many independently reached round-trip.

Grades (worst to best): no-compile, compiles-mismatch, bytecode-only (recorded
only when redundancy was exhausted and nothing round-tripped — see
compute_consensus), roundtrip-equivalent, roundtrip-exact.

Usage:
  python3 tools/n5-fidelity.py --modules control,alarm,schedule [--report]
  python3 tools/n5-fidelity.py --all --jobs 6 [--class-jobs 4] [--limit-per-module 50]
  (--jobs parallelizes across modules; --class-jobs parallelizes classes within a module)

Resumable: a module is skipped when organized/<mod>/fidelity.json already
records the module jar's current sha256 and this tool's SCHEMA_VERSION.
"""
from __future__ import annotations

import argparse
import atexit
import concurrent.futures
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import struct
import sys
import tempfile
import threading
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORGANIZED_DIR = REPO_ROOT / "organized"
DEFAULT_MODULES_DIR = Path("/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules")
DEFAULT_BIN_EXT_DIR = Path("/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext")

DEFAULT_JAVAC = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"
DEFAULT_JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"

DECOMPILERS_DIR = REPO_ROOT / "tools" / "decompilers"
DEFAULT_CFR_JAR = DECOMPILERS_DIR / "cfr-0.152.jar"
DEFAULT_PROCYON_JAR = DECOMPILERS_DIR / "procyon-decompiler-0.6.0.jar"
DEFAULT_JAVA = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/java"

NIAGARA_HELP_SCRIPT = REPO_ROOT / "niagara-help" / "tools" / "niagara_help.py"

# Subprocess timeouts (R4-no-subprocess-timeouts): every javac/javap/decompiler/
# krak2 invocation is capped so one hung or pathological class can never wedge
# an entire grading run. A timeout produces the typed "timeout" grade (see
# _GRADE_RANK), never a silent hang or an uncaught TimeoutExpired.
DEFAULT_JAVAC_TIMEOUT_SECONDS = 120
DEFAULT_JAVAP_TIMEOUT_SECONDS = 60
DEFAULT_DECOMPILE_TIMEOUT_SECONDS = 120
DEFAULT_KRAK2_TIMEOUT_SECONDS = 30
DEFAULT_NIAGARA_HELP_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Stage 1: bytecode normalizer
# ---------------------------------------------------------------------------

# A bare "#<digits>" or "#<digits>.#<digits>" constant-pool index token. javap -v
# already resolves what it refers to into an adjacent symbolic comment (or, for
# most non-Code lines, into the printed name itself) — dropping the index loses
# nothing semantic and removes noise that differs purely because two compiles
# built their constant pools in a different order.
_CP_INDEX_RE = re.compile(r"#\d+(?:\.#\d+)?")

_BRANCH_OPCODES = {
    "goto", "goto_w", "jsr", "jsr_w",
    "ifeq", "ifne", "iflt", "ifge", "ifgt", "ifle",
    "ifnull", "ifnonnull",
    "if_icmpeq", "if_icmpne", "if_icmplt", "if_icmpge", "if_icmpgt", "if_icmple",
    "if_acmpeq", "if_acmpne",
}

# mnemonic -> True if it addresses a local-variable slot via an explicit operand
# (e.g. "aload 4"); the _0.._3 short forms are handled separately since the slot
# is embedded in the mnemonic itself.
_SLOT_OPCODE_PREFIXES = ("aload", "astore", "iload", "istore", "lload", "lstore",
                          "fload", "fstore", "dload", "dstore", "ret")

_SLOT_SHORTFORM_RE = re.compile(
    r"^(aload|astore|iload|istore|lload|lstore|fload|fstore|dload|dstore)_([0-3])$"
)
_SLOT_LONGFORM_RE = re.compile(
    r"^(aload|astore|iload|istore|lload|lstore|fload|fstore|dload|dstore|ret)$"
)
_IINC_RE = re.compile(r"^\s*iinc\s+(\d+)\s*,?\s*(-?\d+)\s*$")

_INSTR_LINE_RE = re.compile(r"^\s*(\d+):\s*(\S+)(.*)$")


def strip_cp_indices(line: str) -> str:
    """Drop constant-pool index tokens from one javap output line.

    javap already prints the symbolic name/comment for anything a CP index
    points to (e.g. ``invokespecial #1  // Method Foo."<init>":()V``), so the
    numeric index itself carries no information the corpus needs to compare
    two compiles of "the same" code — it only encodes constant-pool build
    order, which is compiler-internal, not semantic.
    """
    out = _CP_INDEX_RE.sub("", line)
    out = re.sub(r"[ \t]+", " ", out).strip()
    return out


def _slot_of(mnemonic: str, operand: str) -> Optional[int]:
    m = _SLOT_SHORTFORM_RE.match(mnemonic)
    if m:
        return int(m.group(2))
    if _SLOT_LONGFORM_RE.match(mnemonic):
        operand = operand.strip().split()[0] if operand.strip() else ""
        if operand.isdigit():
            return int(operand)
    return None


# javap prints a negative case key bare (e.g. "-5: 36", verified against a real
# javac 25 compile of a `switch` with negative int case labels) -- the target
# offset itself is never negative in practice, but "-?\d+" is used for both so
# a malformed/unexpected negative offset is captured (and compared) rather than
# silently dropped, which is the false-exact bug this regex previously caused:
# an unmatched row was skipped by _parse_code_stream instead of being added to
# `entries`, so two switches differing ONLY in a negative-key arm's target
# could normalize identical.
_SWITCH_CASE_RE = re.compile(r"^\s*(-?\d+|default)\s*:\s*(-?\d+)\s*$")


def _parse_code_stream(raw_lines: list[str]) -> list[dict]:
    """Parse raw ``Code`` lines into a list of instruction records.

    javap prints ``tableswitch``/``lookupswitch`` as a MULTI-LINE block::

        1: lookupswitch  { // 2
                       5: 28
                     200: 31
                 default: 34
              }

    Each ``<key>: <target>`` row inside that block is switch OPERAND data, not
    a separate instruction — but it is syntactically indistinguishable from a
    regular ``<offset>: <mnemonic>`` line by regex alone. Treating it as one
    (the previous implementation's bug) corrupts offset->position numbering
    for every instruction that follows: a switch with an arm at raw offset 28
    would register a *second*, bogus "instruction" at offset 5 (the case key)
    before the real instruction at offset 28 is ever seen. This function
    explicitly consumes a switch's block as part of the switch record instead.
    """
    records: list[dict] = []
    i = 0
    while i < len(raw_lines):
        m = _INSTR_LINE_RE.match(raw_lines[i])
        if not m:
            i += 1
            continue
        offset = int(m.group(1))
        mnemonic = m.group(2)
        rest = m.group(3)
        if mnemonic in ("tableswitch", "lookupswitch"):
            entries: list[tuple[int, int]] = []
            default_target = None
            i += 1
            while i < len(raw_lines):
                line = raw_lines[i].strip()
                if line == "}":
                    i += 1
                    break
                cm = _SWITCH_CASE_RE.match(line)
                if cm:
                    key, target = cm.group(1), int(cm.group(2))
                    if key == "default":
                        default_target = target
                    else:
                        entries.append((int(key), target))
                i += 1
            records.append({
                "kind": "switch", "offset": offset, "mnemonic": mnemonic,
                "entries": entries, "default": default_target,
            })
        else:
            records.append({"kind": "insn", "offset": offset, "mnemonic": mnemonic, "rest": rest})
            i += 1
    return records


def _offset_to_pos_map(records: list[dict]) -> dict[int, int]:
    return {r["offset"]: i for i, r in enumerate(records)}


def normalize_method_instructions(raw_lines: list[str]) -> list[str]:
    """Canonicalize one method's disassembled instruction stream.

    ``raw_lines`` are the ``<offset>: <mnemonic> [operand] [// comment]`` lines
    of a single method's ``Code`` body (LineNumberTable/LocalVariableTable/
    StackMapTable/Exception table and the ``stack=.., locals=.., args_size=..``
    header line already excluded by the caller — see ``parse_javap_verbose``;
    the exception table gets its own comparable representation via
    ``normalize_exception_table``, using this same offset->position mapping).

    Canonicalizations that make two semantically-identical compiles compare
    equal even when the raw bytes differ:

    1. constant-pool indices dropped (``strip_cp_indices``);
    2. local-variable slot numbers renumbered by FIRST USE order, so two
       methods that reference the same locals in the same order compare equal
       regardless of which raw slot number either compiler happened to pick;
    3. branch targets (goto/if*/jsr) rewritten as a position *relative to the
       branching instruction's own position in the instruction sequence*, so a
       shift in absolute byte offsets (e.g. from a wide/narrow instruction
       encoding difference elsewhere in the method) does not, by itself, make
       two otherwise-identical methods compare unequal;
    4. tableswitch/lookupswitch: each case KEY is kept literal (it is
       semantic — which input value selects which branch), only its TARGET is
       relativized the same way; the default target is relativized too.
    """
    records = _parse_code_stream(raw_lines)
    offset_to_pos = _offset_to_pos_map(records)

    slot_map: dict[int, int] = {}

    def canonical_slot(raw_slot: int) -> int:
        if raw_slot not in slot_map:
            slot_map[raw_slot] = len(slot_map)
        return slot_map[raw_slot]

    def _relabel(target_offset: Optional[int], pos: int) -> str:
        if target_offset is None:
            return "none"
        target_pos = offset_to_pos.get(target_offset)
        if target_pos is None:
            return f"abs{target_offset}"
        return f"rel{target_pos - pos:+d}"

    out: list[str] = []
    for pos, rec in enumerate(records):
        if rec["kind"] == "switch":
            entries_str = ", ".join(f"{k}:{_relabel(t, pos)}" for k, t in sorted(rec["entries"]))
            default_str = _relabel(rec["default"], pos)
            line = f"insn{pos}: {rec['mnemonic']} {{{entries_str}, default:{default_str}}}"
            out.append(strip_cp_indices(line))
            continue

        mnemonic = rec["mnemonic"]
        rest = rec["rest"]

        # local-slot canonicalization: the OUTPUT form (short "aload_N" vs long
        # "aload N") depends only on the canonical slot number, never on
        # whether the raw instruction happened to use the short or long form —
        # otherwise two semantically-identical methods that differ only in
        # which literal slot numbers the compiler picked (and therefore which
        # form is syntactically available) would normalize to different text.
        slot = _slot_of(mnemonic, rest)
        if slot is not None:
            canon = canonical_slot(slot)
            shortform_m = _SLOT_SHORTFORM_RE.match(mnemonic)
            base = shortform_m.group(1) if shortform_m else mnemonic
            if canon <= 3:
                mnemonic = f"{base}_{canon}"
                rest = ""
            else:
                mnemonic = base
                rest = f" {canon}"
        elif mnemonic == "iinc":
            # javap prints "iinc          2, 3" (comma-separated, verified
            # against a real javac 25 compile) -- a plain-whitespace-only
            # pattern never matched, so the slot leaked through uncanonicalized.
            im = re.match(r"^\s*(\d+)\s*,?\s*(-?\d+)\s*(.*)$", rest)
            if im:
                canon = canonical_slot(int(im.group(1)))
                rest = f" {canon} {im.group(2)}{im.group(3)}"

        # branch-target canonicalization (relative to this instruction's position)
        if mnemonic in _BRANCH_OPCODES:
            tm = re.match(r"^\s*(\d+)(.*)$", rest)
            if tm:
                rest = f" {_relabel(int(tm.group(1)), pos)}{tm.group(2)}"

        line = f"insn{pos}: {mnemonic}{rest}"
        out.append(strip_cp_indices(line))
    return out


def normalize_exception_table(raw_lines: list[str], rows: list[tuple[int, int, int, str]]) -> list[str]:
    """Canonicalize a method's exception table (try/catch/finally wiring).

    ``rows`` are ``(from_offset, to_offset, target_offset, type)`` as parsed
    from javap's ``Exception table:`` section (``type`` already symbolic,
    e.g. ``"Class java/lang/ArithmeticException"`` or ``"any"`` for finally).
    ``raw_lines`` is the SAME method's Code lines, reused only to rebuild the
    offset->position map — the handler TYPE is never normalized away (which
    exception a range is protected against is semantic), and the from/to/target
    offsets are relativized to instruction position the same way branch
    targets are, so a byte-offset shift elsewhere doesn't spuriously differ.
    """
    records = _parse_code_stream(raw_lines)
    offset_to_pos = _offset_to_pos_map(records)

    def pos_of(offset: int) -> str:
        p = offset_to_pos.get(offset)
        return f"insn{p}" if p is not None else f"abs{offset}"

    out = [f"[{pos_of(frm)}-{pos_of(to)}) -> {pos_of(target)}: {etype}" for frm, to, target, etype in rows]
    return sorted(out)


# ---------------------------------------------------------------------------
# Stage 2: javap -v -p parsing + structural comparator
# ---------------------------------------------------------------------------

# "Exception table:" and "MethodParameters:" are handled explicitly (captured,
# not skipped) — see _parse_member_block.
_SKIP_SUBSECTION_HEADERS = (
    "LineNumberTable:", "LocalVariableTable:", "LocalVariableTypeTable:",
    "StackMapTable:", "RuntimeVisibleAnnotations:", "RuntimeInvisibleAnnotations:",
    "RuntimeVisibleParameterAnnotations:", "RuntimeInvisibleParameterAnnotations:",
    "AnnotationDefault:",
)


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


# ---------------------------------------------------------------------------
# Optional persistent javac/javap server (--tool-server)
#
# Per-class JVM startup + a ~440-jar classpath scan dominates grading time. With
# --tool-server each worker thread owns ONE long-lived JVM
# (tools/n5-toolserver/ToolServer.java) that runs javac/javap in-process via
# ToolProvider; results are identical to the subprocess path. Any failure to
# start or talk to the server falls back to the subprocess path (logged once).
# ---------------------------------------------------------------------------

TOOL_SERVER_SRC = str(REPO_ROOT / "tools" / "n5-toolserver" / "ToolServer.java")
TOOL_SERVER_START_TIMEOUT_SECONDS = 60
# a long-lived javac accumulates heap/class-loader state; recycle the JVM periodically
TOOL_SERVER_MAX_REQUESTS = 400
_TOOL_SERVER_JVM_FLAGS = ["-Xmx1g", "-XX:+UseSerialGC", "-Xshare:auto"]


class ToolServerError(RuntimeError):
    """The tool server could not start, died, or spoke garbage (NOT a timeout)."""


class ToolServer:
    """Client for one ToolServer.java JVM. Not thread-safe: one per worker thread."""

    def __init__(self, java_bin: str = DEFAULT_JAVA):
        self.java_bin = java_bin
        self.proc: Optional[subprocess.Popen] = None
        self._requests = 0

    # -- lifecycle ---------------------------------------------------------
    def _read(self, n: int) -> bytes:
        buf = self.proc.stdout.read(n)
        if buf is None or len(buf) != n:
            raise ToolServerError("tool server closed its pipe")
        return buf

    def _kill(self) -> None:
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            proc.kill()
        except OSError:
            pass
        for stream in (proc.stdin, proc.stdout):
            try:
                stream.close()
            except OSError:
                pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass

    def start(self) -> None:
        self._kill()
        try:
            self.proc = subprocess.Popen(
                [self.java_bin, *_TOOL_SERVER_JVM_FLAGS, TOOL_SERVER_SRC],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                # buffered pipes: read(n) must return exactly n bytes (raw reads return short)
            )
        except OSError as exc:
            raise ToolServerError(f"cannot launch tool server: {exc}") from exc
        timer = threading.Timer(TOOL_SERVER_START_TIMEOUT_SECONDS, self.proc.kill)
        timer.start()
        try:
            if self._read(1) != b"R":
                raise ToolServerError("tool server handshake mismatch")
        except ToolServerError:
            self._kill()
            raise
        finally:
            timer.cancel()
        self._requests = 0

    def close(self) -> None:
        self._kill()

    # -- requests ----------------------------------------------------------
    def run(self, tool: str, args: list, timeout: Optional[float] = None) -> tuple[int, str, str]:
        """Run `tool` (javac/javap) with `args`; returns (returncode, stdout, stderr).
        Raises subprocess.TimeoutExpired (server is killed; the next call restarts it)
        or ToolServerError."""
        if self.proc is None or self.proc.poll() is not None or self._requests >= TOOL_SERVER_MAX_REQUESTS:
            self.start()
        parts = [tool, *[str(a) for a in args]]
        payload = bytearray(struct.pack(">i", len(parts)))
        for part in parts:
            raw = part.encode("utf-8")
            payload += struct.pack(">i", len(raw)) + raw
        timed_out = threading.Event()

        def _expire():
            timed_out.set()
            try:
                self.proc.kill()
            except (OSError, AttributeError):
                pass

        timer = threading.Timer(timeout, _expire) if timeout is not None else None
        if timer:
            timer.start()
        try:
            self.proc.stdin.write(bytes(payload))
            self.proc.stdin.flush()
            rc = struct.unpack(">i", self._read(4))[0]
            out = self._read(struct.unpack(">i", self._read(4))[0])
            err = self._read(struct.unpack(">i", self._read(4))[0])
        except (ToolServerError, OSError, struct.error) as exc:
            self._kill()
            if timed_out.is_set():
                raise subprocess.TimeoutExpired([tool, *args], timeout) from exc
            raise ToolServerError(f"tool server died during {tool}: {exc}") from exc
        finally:
            if timer:
                timer.cancel()
        if timed_out.is_set():  # finished as the timer fired: treat the killed server as a timeout
            self._kill()
            raise subprocess.TimeoutExpired([tool, *args], timeout)
        self._requests += 1
        return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


_tool_server_local = threading.local()
_tool_servers: list = []
_tool_servers_lock = threading.Lock()
_tool_server_disabled = False


def _thread_tool_server(java_bin: str) -> Optional[ToolServer]:
    """This thread's ToolServer (started lazily), or None if unusable (caller falls back)."""
    global _tool_server_disabled
    if _tool_server_disabled:
        return None
    server = getattr(_tool_server_local, "server", None)
    if server is None:
        server = ToolServer(java_bin)
        _tool_server_local.server = server
        with _tool_servers_lock:
            _tool_servers.append(server)
    return server


def _disable_tool_server(reason: str) -> None:
    global _tool_server_disabled
    with _tool_servers_lock:
        first = not _tool_server_disabled
        _tool_server_disabled = True
    if first:
        print(f"n5-fidelity: --tool-server unavailable ({reason}); falling back to subprocess javac/javap", file=sys.stderr)


def shutdown_tool_servers() -> None:
    """Close every tool-server JVM and re-arm the feature (used at end of a run and by tests)."""
    global _tool_server_disabled
    with _tool_servers_lock:
        servers = list(_tool_servers)
        _tool_servers.clear()
        _tool_server_disabled = False
    for server in servers:
        server.close()
    _tool_server_local.__dict__.clear()


atexit.register(lambda: shutdown_tool_servers())


def _run_jdk_tool(tool: str, tool_bin: str, args: list, timeout: Optional[float], tool_server: bool) -> tuple[int, str, str]:
    """(returncode, stdout, stderr) of a javac/javap invocation, via the per-thread
    tool server when enabled, else (or on any server failure) via a fresh subprocess.
    subprocess.TimeoutExpired propagates in both paths."""
    if tool_server:
        server = _thread_tool_server(str(Path(tool_bin).with_name("java")) if os.sep in tool_bin else DEFAULT_JAVA)
        if server is not None:
            try:
                return server.run(tool, args, timeout)
            except ToolServerError as exc:
                _disable_tool_server(str(exc))
    proc = subprocess.run([tool_bin, *args], capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def run_javap_verbose(
    classfile: str, javap_bin: str = DEFAULT_JAVAP, timeout: Optional[float] = DEFAULT_JAVAP_TIMEOUT_SECONDS,
    tool_server: bool = False,
) -> str:
    # subprocess.TimeoutExpired is intentionally NOT caught here (this function's
    # contract stays "returns javap's stdout, or raises") -- callers that need a
    # typed "timeout" grade instead of a propagating exception catch it
    # themselves (see recompile_and_grade), since only they know what grade
    # dict shape to return for their call site.
    return _run_jdk_tool("javap", javap_bin, ["-v", "-p", classfile], timeout, tool_server)[1]


def parse_javap_verbose(text: str) -> dict:
    """Parse `javap -v -p` output into the comparable structural dict used by
    diff_normalized_classes: fields, methods (with normalized Code), and the
    class attributes that matter (Record/PermittedSubclasses/NestMembers/
    InnerClasses). Annotation content and the constant-pool table itself are
    intentionally out of scope (see module docstring / task spec).
    """
    lines = text.splitlines()

    # class declaration: first non-volatile line before "  minor version:"
    class_decl = ""
    for line in lines:
        if line.startswith("  minor version:"):
            break
        if line.startswith(("Classfile ", "  Last modified", "  SHA-256 checksum", "  Compiled from")):
            continue
        if line.strip():
            class_decl = line.strip()

    try:
        body_start = lines.index("{")
        body_end = lines.index("}", body_start)
    except ValueError:
        body_start = body_end = -1

    fields: dict = {}
    methods: dict = {}

    if body_start != -1:
        i = body_start + 1
        while i < body_end:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if _indent_of(line) == 2:
                block_end = i + 1
                while block_end < body_end and (not lines[block_end].strip() or _indent_of(lines[block_end]) > 2):
                    block_end += 1
                _parse_member_block(lines[i:block_end], fields, methods)
                i = block_end
            else:
                i += 1

    trailer = lines[body_end + 1:] if body_end != -1 else []
    attributes = _parse_trailer_attributes(trailer)

    return {
        "class_decl": class_decl,
        "fields": fields,
        "methods": methods,
        "attributes": attributes,
    }


def _parse_member_block(block: list[str], fields: dict, methods: dict) -> None:
    decl = block[0].strip().rstrip(";")
    descriptor = ""
    flags: list[str] = []
    idx = 1
    if idx < len(block) and block[idx].strip().startswith("descriptor:"):
        descriptor = block[idx].strip().split("descriptor:", 1)[1].strip()
        idx += 1
    if idx < len(block) and block[idx].strip().startswith("flags:"):
        flags_part = block[idx].split(")", 1)
        if len(flags_part) == 2:
            flags = [f.strip() for f in flags_part[1].split(",") if f.strip()]
        idx += 1

    is_method = descriptor.startswith("(")
    name = _member_name_from_decl(decl, is_method)

    if is_method:
        exceptions: list[str] = []
        code: list[str] = []
        exception_table: list[str] = []
        has_method_parameters = False
        j = idx
        while j < len(block):
            line = block[j]
            stripped = line.strip()
            indent = _indent_of(line)
            if indent == 4 and stripped == "Code:":
                j += 1
                # optional stack=/locals=/args_size= line — informational, skipped
                if j < len(block) and block[j].strip().startswith("stack="):
                    j += 1
                raw_instr_lines = []
                raw_exception_rows: list[tuple[int, int, int, str]] = []
                while j < len(block):
                    inner = block[j]
                    inner_indent = _indent_of(inner)
                    inner_stripped = inner.strip()
                    if inner_indent <= 4:
                        break
                    if inner_stripped.startswith("Exception table:"):
                        header_indent = inner_indent
                        j += 1
                        while j < len(block) and (not block[j].strip() or _indent_of(block[j]) > header_indent):
                            row = block[j].strip()
                            j += 1
                            if row.startswith("from") or not row:
                                continue
                            rm = re.match(r"^(\d+)\s+(\d+)\s+(\d+)\s+(.+)$", row)
                            if rm:
                                raw_exception_rows.append(
                                    (int(rm.group(1)), int(rm.group(2)), int(rm.group(3)), strip_cp_indices(rm.group(4)))
                                )
                        continue
                    if any(inner_stripped.startswith(h) for h in _SKIP_SUBSECTION_HEADERS):
                        header_indent = inner_indent
                        j += 1
                        while j < len(block) and (not block[j].strip() or _indent_of(block[j]) > header_indent):
                            j += 1
                        continue
                    raw_instr_lines.append(inner_stripped)
                    j += 1
                code = normalize_method_instructions(raw_instr_lines)
                exception_table = normalize_exception_table(raw_instr_lines, raw_exception_rows)
            elif indent == 4 and stripped == "Exceptions:":
                j += 1
                while j < len(block) and (not block[j].strip() or _indent_of(block[j]) > 4):
                    ex = block[j].strip()
                    if ex.startswith("throws"):
                        exceptions = [t.strip() for t in ex[len("throws"):].split(",") if t.strip()]
                    j += 1
            elif indent == 4 and stripped.startswith("MethodParameters:"):
                has_method_parameters = True
                header_indent = indent
                j += 1
                while j < len(block) and (not block[j].strip() or _indent_of(block[j]) > header_indent):
                    j += 1
            elif indent == 4 and any(stripped.startswith(h) for h in _SKIP_SUBSECTION_HEADERS):
                header_indent = indent
                j += 1
                while j < len(block) and (not block[j].strip() or _indent_of(block[j]) > header_indent):
                    j += 1
            else:
                j += 1
        methods[(name, descriptor)] = {
            "flags": sorted(flags),
            "code": code,
            "exceptions": sorted(exceptions),
            "exception_table": exception_table,
            "has_method_parameters": has_method_parameters,
        }
    else:
        constant_value = None
        j = idx
        while j < len(block):
            stripped = block[j].strip()
            if stripped.startswith("ConstantValue:"):
                constant_value = strip_cp_indices(stripped.split("ConstantValue:", 1)[1].strip())
            j += 1
        fields[(name, descriptor)] = {"flags": sorted(flags), "constant_value": constant_value}


def _member_name_from_decl(decl: str, is_method: bool) -> str:
    # decl examples:
    #   "public static final niagara.sys.Property in1"          (field)
    #   "public niagara.status.BStatusNumeric getIn1()"          (method)
    #   "public niagara.control.BNumericWritable()"              (constructor)
    #   "static {}"                                              (static initializer, <clinit>)
    if is_method:
        if decl.strip() == "static {}":
            return "<clinit>"
        m = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*(throws.*)?$", decl)
        if m:
            return m.group(1)
        return decl
    m = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)$", decl)
    return m.group(1) if m else decl


def _parse_trailer_attributes(trailer: list[str]) -> dict:
    attrs = {
        "record": False,
        "permitted_subclasses": None,
        "nest_members": None,
        "inner_classes": None,
    }
    i = 0
    while i < len(trailer):
        line = trailer[i]
        stripped = line.strip()
        if _indent_of(line) == 0 and stripped:
            header = stripped
            j = i + 1
            body: list[str] = []
            while j < len(trailer) and (not trailer[j].strip() or _indent_of(trailer[j]) > 0):
                if trailer[j].strip():
                    body.append(strip_cp_indices(trailer[j].strip()))
                j += 1
            if header.startswith("PermittedSubclasses:"):
                attrs["permitted_subclasses"] = sorted(body)
            elif header.startswith("NestMembers:"):
                attrs["nest_members"] = sorted(body)
            elif header.startswith("InnerClasses:"):
                attrs["inner_classes"] = sorted(body)
            elif header.startswith("Record:"):
                attrs["record"] = True
            i = j
        else:
            i += 1
    return attrs


def diff_normalized_classes(a: dict, b: dict) -> dict:
    """Structural + per-method diff between two parsed classes (see
    parse_javap_verbose). Does not itself decide a grade — see grade_class_result.
    """
    fields_match = a["fields"] == b["fields"]
    attrs_match = a["attributes"] == b["attributes"]

    a_methods = a["methods"]
    b_methods = b["methods"]
    common = set(a_methods) & set(b_methods)
    missing = sorted(set(a_methods) - set(b_methods))
    extra = sorted(set(b_methods) - set(a_methods))

    mismatched = []
    method_bodies = {}
    for key in sorted(common):
        am = a_methods[key]
        bm = b_methods[key]
        if (
            am["flags"] != bm["flags"]
            or am["code"] != bm["code"]
            or am["exceptions"] != bm["exceptions"]
            or am.get("exception_table", []) != bm.get("exception_table", [])
            or am.get("has_method_parameters", False) != bm.get("has_method_parameters", False)
        ):
            mismatched.append(key)
            method_bodies[key] = {"a": am["code"], "b": bm["code"]}

    return {
        "fields_match": fields_match,
        "attrs_match": attrs_match,
        "mismatched_methods": mismatched,
        "missing_methods": missing,
        "extra_methods": extra,
        "method_bodies": method_bodies,
    }


# ---------------------------------------------------------------------------
# Stage 3: allowlist + grader decisions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AllowlistEntry:
    name: str
    justification: str
    predicate: Callable[[list[str], list[str]], bool]


# ---------------------------------------------------------------------------
# Allowlist entries: narrow/wide instruction-variant pairs.
#
# JVMS 6.5 defines each of these pairs as performing the IDENTICAL runtime
# operation — the compiler's choice between the narrow and wide form is a pure
# encoding decision driven by how large that specific compile's constant pool
# (ldc/ldc_w) or branch-offset range (goto/goto_w, jsr/jsr_w) happened to grow,
# never a semantic one:
#   - ldc / ldc_w:   both push the SAME resolved constant-pool entry; ldc's
#     operand is a 1-byte index (pool slots 0-255), ldc_w's is 2-byte (wide).
#   - goto / goto_w: both perform an unconditional jump to the same target;
#     goto's branch offset is a signed 16-bit value, goto_w's is signed 32-bit.
#   - jsr / jsr_w:   both push a return address and jump to a subroutine (the
#     instruction is deprecated/never emitted since Java 7, but the JVMS
#     equivalence argument is identical to goto/goto_w).
#
# Recompiling ONE decompiled class standalone (this grader's method — see
# recompile_and_grade) gives javac a SMALLER classpath-local constant pool
# than the original whole-module compile built for that same class, so javac
# can pick the narrow form (ldc) where the shipped class needed the wide form
# (ldc_w) for the exact same constant — a pure recompile-isolation artifact
# this grader's own methodology introduces, not a decompiler-fidelity defect.
# See docs/decompile-fidelity-report.md "Allowlist" for the measured effect.
# ---------------------------------------------------------------------------

_WIDE_VARIANT_PAIRS = (("ldc", "ldc_w"), ("goto", "goto_w"), ("jsr", "jsr_w"))


def _make_wide_variant_collapser(narrow: str, wide: str) -> Callable[[str], str]:
    pattern = re.compile(rf"^(insn\d+:\s*){re.escape(wide)}\b(.*)$")

    def _collapse(line: str) -> str:
        m = pattern.match(line)
        if m:
            return f"{m.group(1)}{narrow}{m.group(2)}"
        return line

    return _collapse


def _make_wide_variant_predicate(narrow: str, wide: str) -> Callable[[list[str], list[str]], bool]:
    """Build the allowlist predicate for one narrow/wide instruction pair (see
    _WIDE_VARIANT_PAIRS). True iff `a_code`/`b_code` (two methods' normalized
    instruction lists, equal length required — a genuine missing/extra
    instruction is never allowlisted here) differ ONLY on lines where one side
    uses `narrow` and the other `wide`, and every OTHER part of that line
    (operand/symbolic-comment — i.e. WHICH constant/target, not how it's
    encoded) is identical. A line pair that both fail to collapse-equal for
    any other reason (a genuinely different constant, a different target, an
    unrelated opcode change) fails the predicate, so the base grade
    (compiles-mismatch) still applies.
    """
    collapse = _make_wide_variant_collapser(narrow, wide)
    narrow_prefix_re = re.compile(rf"^insn\d+:\s*{re.escape(narrow)}\b")
    wide_prefix_re = re.compile(rf"^insn\d+:\s*{re.escape(wide)}\b")

    def _predicate(a_code: list[str], b_code: list[str]) -> bool:
        if len(a_code) != len(b_code) or a_code == b_code:
            return False
        saw_a_variant_line = False
        for la, lb in zip(a_code, b_code):
            if la == lb:
                continue
            if collapse(la) != collapse(lb):
                return False
            # at least one side of a differing line must actually BE this
            # pair's narrow/wide mnemonic -- guards against two unrelated
            # already-identical-after-collapse lines being miscounted (can't
            # happen given the anchored per-pair regex, but keep it explicit).
            is_variant_line = (
                narrow_prefix_re.match(la) or wide_prefix_re.match(la)
                or narrow_prefix_re.match(lb) or wide_prefix_re.match(lb)
            )
            if not is_variant_line:
                return False
            saw_a_variant_line = True
        return saw_a_variant_line

    return _predicate


ALLOWLIST: list[AllowlistEntry] = [
    AllowlistEntry(
        name=f"{narrow}-vs-{wide}-width",
        justification=(
            f"JVMS 6.5: `{narrow}`/`{wide}` perform the identical runtime operation on the identical "
            f"operand — only the encoding width differs, chosen purely by the compiler's constant-pool/"
            f"branch-offset size at compile time. Recompiling one decompiled class standalone (this "
            f"grader's own method) gives javac a smaller local pool/offset range than the shipped "
            f"module-wide compile, so the two can legitimately pick different widths for the SAME "
            f"constant/target. See docs/decompile-fidelity-report.md 'Allowlist'."
        ),
        predicate=_make_wide_variant_predicate(narrow, wide),
    )
    for narrow, wide in _WIDE_VARIANT_PAIRS
]


def grade_class_result(compiled_ok: bool, diff: Optional[dict], first_error: Optional[str]) -> dict:
    if not compiled_ok:
        return {"grade": "no-compile", "first_error": first_error, "mismatched_methods": [], "allowlist_matches": []}

    if diff["fields_match"] and diff["attrs_match"] and not diff["mismatched_methods"] \
            and not diff["missing_methods"] and not diff["extra_methods"]:
        return {"grade": "roundtrip-exact", "first_error": None, "mismatched_methods": [], "allowlist_matches": []}

    # missing/extra members and field/attribute mismatches are never allowlist-eligible:
    # the allowlist only ever downgrades a *method-body* mismatch, never a structural one.
    if not diff["fields_match"] or not diff["attrs_match"] or diff["missing_methods"] or diff["extra_methods"]:
        return {
            "grade": "compiles-mismatch",
            "first_error": None,
            "mismatched_methods": list(diff["mismatched_methods"]),
            "allowlist_matches": [],
        }

    allowlist_matches = []
    all_allowed = True
    method_bodies = diff.get("method_bodies", {})
    for key in diff["mismatched_methods"]:
        bodies = method_bodies.get(key)
        matched_this_method = False
        if bodies:
            for entry in ALLOWLIST:
                if entry.predicate(bodies["a"], bodies["b"]):
                    if entry.name not in allowlist_matches:
                        allowlist_matches.append(entry.name)
                    matched_this_method = True
                    break
        if not matched_this_method:
            all_allowed = False

    if all_allowed and diff["mismatched_methods"]:
        return {
            "grade": "roundtrip-equivalent",
            "first_error": None,
            "mismatched_methods": list(diff["mismatched_methods"]),
            "allowlist_matches": allowlist_matches,
        }

    return {
        "grade": "compiles-mismatch",
        "first_error": None,
        "mismatched_methods": list(diff["mismatched_methods"]),
        "allowlist_matches": allowlist_matches,
    }


_GRADE_RANK = {
    "no-compile": 0,
    "timeout": 0,  # a harness/subprocess timeout, not a fidelity finding -- see recompile_and_grade
    "harness-error": 0,  # missing ground-truth/source file -- a corpus/setup bug, not a fidelity finding
    "compiles-mismatch": 1,
    "bytecode-only": 1,  # same rank as compiles-mismatch; distinct meaning (see compute_consensus)
    "roundtrip-equivalent": 2,
    "roundtrip-exact": 3,
}


def _is_clean(grade: str) -> bool:
    return grade in ("roundtrip-exact", "roundtrip-equivalent")


# ---------------------------------------------------------------------------
# Stage 4: redundancy / fallback ladder
# ---------------------------------------------------------------------------

def run_redundancy_ladder(ladder: list[tuple[str, Callable[[], dict]]]) -> dict:
    """Run each (name, thunk) in order, stopping at the first clean grade.

    Every engine actually invoked is recorded in `attempted` (for disagreement
    visibility), but engines after a clean hit are never run — this is the
    "keep the first that round-trips" rule from the task spec, made cheap.
    """
    attempted: list[tuple[str, dict]] = []
    for name, thunk in ladder:
        result = thunk()
        attempted.append((name, result))
        if _is_clean(result["grade"]):
            break
    return select_best_decompiler(attempted)


def select_best_decompiler(attempts: list[tuple[str, dict]]) -> dict:
    best_name = None
    best_result = None
    for name, result in attempts:
        if _is_clean(result["grade"]):
            best_name = name
            best_result = result
            break
    if best_result is None:
        grade = "bytecode-only"
    else:
        grade = best_result["grade"]
    return {"best_decompiler": best_name, "grade": grade, "attempted": attempts}


def compute_consensus(attempted: list[tuple[str, dict]]) -> dict:
    reaching = [name for name, result in attempted if _is_clean(result["grade"])]
    return {"reaching_roundtrip": reaching, "count": len(reaching)}


# ---------------------------------------------------------------------------
# Stage 5: krak2 independent bytecode-disassembly cross-check
# ---------------------------------------------------------------------------

_KRAK2_MNEMONIC_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*:\s*([a-z][a-z0-9_]*)")


def _krak2_mnemonic_sequence(krak2_text: str) -> list[str]:
    """Best-effort extraction of the bare opcode mnemonic sequence from a krak2
    `.j` disassembly listing (one 'LABEL: mnemonic ...' line per instruction).
    """
    out = []
    for line in krak2_text.splitlines():
        m = _KRAK2_MNEMONIC_RE.match(line)
        if m:
            out.append(m.group(1))
    return out


_NORMALIZED_MNEMONIC_RE = re.compile(r"^insn\d+:\s*(\S+)")


def _normalized_mnemonic_sequence(normalized: list[str]) -> list[str]:
    out = []
    for line in normalized:
        m = _NORMALIZED_MNEMONIC_RE.match(line)
        if m:
            out.append(m.group(1))
    return out


_KRAK2_METHOD_HEADER_RE = re.compile(r"^\.method\b.*?\s([A-Za-z_$<][A-Za-z0-9_$>]*)\s*:\s*(\([^)]*\)\S+)\s*$")


def _extract_krak2_method_block(krak2_text: str, method_name: str, descriptor: str) -> Optional[str]:
    lines = krak2_text.splitlines()
    for i, line in enumerate(lines):
        m = _KRAK2_METHOD_HEADER_RE.match(line.strip())
        if m and m.group(1) == method_name and m.group(2) == descriptor:
            block = []
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == ".end method":
                    break
                block.append(lines[j])
            return "\n".join(block)
    return None


def krak2_cross_check(
    classfile: str,
    normalized_instructions: list[str],
    method_name: str,
    descriptor: str,
    krak2_bin: str = "krak2",
    timeout: float = DEFAULT_KRAK2_TIMEOUT_SECONDS,
) -> dict:
    """Independent check that our own javap-based normalizer did not drop or
    reorder an instruction, by disassembling the SAME .class with a completely
    different tool (Krakatau2's krak2, a Rust bytecode disassembler that has no
    dependency on javap or the JDK's own class-file reader) and comparing the
    bare opcode mnemonic sequence for ONE method (`method_name`/`descriptor`,
    JVM-descriptor form e.g. "(II)I") — krak2 disassembles the whole class, so
    the comparison is scoped to that method's block to avoid picking up
    unrelated methods (e.g. the implicit constructor).

    This validates the *normalizer*, not the decompiler — it never itself
    produces a fidelity grade.
    """
    resolved = shutil.which(krak2_bin) or (krak2_bin if os.path.isfile(krak2_bin) else None)
    if resolved is None or not os.path.isfile(classfile):
        return {"status": "unavailable", "reason": "krak2 binary or class file not found"}

    with tempfile.TemporaryDirectory() as td:
        try:
            proc = subprocess.run([resolved, "dis", "-o", td, classfile], capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"status": "unavailable", "reason": f"krak2 timed out after {timeout}s"}
        if proc.returncode != 0:
            return {"status": "unavailable", "reason": f"krak2 exited {proc.returncode}: {proc.stderr.strip()[:200]}"}
        # krak2 writes under <td>/<package-path>/<Class>.j, exactly like javac's
        # own -d output — every real N5 class is packaged, so this must be
        # recursive (see recompile_and_grade's identical fix for javac output).
        j_files = list(Path(td).rglob("*.j"))
        if not j_files:
            return {"status": "unavailable", "reason": "krak2 produced no .j output"}
        krak2_text = j_files[0].read_text(errors="replace")

    method_block = _extract_krak2_method_block(krak2_text, method_name, descriptor)
    if method_block is None and method_name not in ("<init>", "<clinit>"):
        # parse_javap_verbose keys a constructor by the enclosing class's
        # simple name (javap prints "public Ctor(int);"), but krak2 always
        # names it "<init>" — retry once under that name before giving up.
        method_block = _extract_krak2_method_block(krak2_text, "<init>", descriptor)
    if method_block is None:
        return {"status": "unavailable", "reason": f"krak2 output has no method {method_name}:{descriptor}"}

    krak2_seq = _krak2_mnemonic_sequence(method_block)
    our_seq = _normalized_mnemonic_sequence(normalized_instructions)

    def _base(op: str) -> str:
        for prefix in ("aload_", "astore_", "iload_", "istore_", "lload_", "lstore_",
                        "fload_", "fstore_", "dload_", "dstore_"):
            if op.startswith(prefix):
                return prefix[:-1]
        return op

    krak2_norm = [_base(o) for o in krak2_seq]
    our_norm = [_base(o) for o in our_seq]

    if krak2_norm == our_norm:
        return {"status": "match", "krak2_count": len(krak2_norm), "our_count": len(our_norm)}
    return {
        "status": "mismatch",
        "krak2_count": len(krak2_norm),
        "our_count": len(our_norm),
        "krak2_sample": krak2_norm[:20],
        "our_sample": our_norm[:20],
    }


# ---------------------------------------------------------------------------
# Stage 6: member-set agreement against niagara_help.py (bajadoc index)
# ---------------------------------------------------------------------------

def member_set_agreement(ours: set[tuple[str, str]], theirs: set[str]) -> dict:
    """`ours` = {(name, descriptor)} extracted from bytecode; `theirs` = bare
    member names from niagara_help.py's independent bajadoc/javadoc index.
    Agreement is computed on bare names (bajadoc does not expose JVM
    descriptors), so this is a coarse, intentionally conservative check.
    """
    our_names = {name for name, _ in ours}
    if not our_names:
        return {"ratio": 1.0, "missing_from_docs": [], "extra_in_docs": sorted(theirs)}
    missing = sorted(our_names - theirs)
    ratio = (len(our_names) - len(missing)) / len(our_names)
    return {
        "ratio": ratio,
        "missing_from_docs": missing,
        "extra_in_docs": sorted(theirs - our_names),
    }


_NIAGARA_HELP_SLOT_RE = re.compile(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*)\s*[:(]")


def niagara_help_member_lookup(fqcn: str, niagara_help_script: str = str(NIAGARA_HELP_SCRIPT)) -> Optional[set[str]]:
    """Independent member-set source: niagara_help.py's `class <ShortName>`
    command reads the bajadoc/javadoc index (a pipeline entirely separate from
    decompilation) and lists a Niagara BComponent's PROPERTIES/ACTIONS/TOPICS —
    the framework "slots" that correspond 1:1 to the `public static final
    niagara.sys.{Property,Action,Topic}` fields our own bytecode extraction
    finds (see `slot_field_names`). `niagara_help.py class` takes the bare
    class name, not the FQCN (its own CLI contract — see its --help), so this
    strips the package.
    """
    if not os.path.isfile(niagara_help_script):
        return None
    short_name = fqcn.rsplit(".", 1)[-1].rsplit("/", 1)[-1]
    try:
        proc = subprocess.run(
            [sys.executable, niagara_help_script, "class", short_name],
            capture_output=True, text=True, timeout=DEFAULT_NIAGARA_HELP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    if "not found in class-index" in proc.stdout:
        return None
    names = set()
    for line in proc.stdout.splitlines():
        m = _NIAGARA_HELP_SLOT_RE.match(line)
        if m:
            names.add(m.group(1))
    return names


_SLOT_FIELD_TYPES = (
    "niagara.sys.Property", "niagara.sys.Action", "niagara.sys.Topic",
    "Lniagara/sys/Property;", "Lniagara/sys/Action;", "Lniagara/sys/Topic;",
)


def slot_field_names(parsed_class: dict) -> set[tuple[str, str]]:
    """The (name, descriptor) pairs among `parsed_class["fields"]` whose
    declared type is a Niagara Property/Action/Topic slot field — the bytecode
    counterpart to niagara_help.py's PROPERTIES/ACTIONS/TOPICS listing.
    """
    return {
        (name, descriptor)
        for (name, descriptor) in parsed_class["fields"]
        if descriptor in _SLOT_FIELD_TYPES
    }


# ---------------------------------------------------------------------------
# Recompile orchestration (uses the JDK directly; real N5 classpath is only
# needed for real corpus classes, not for the self-contained unit tests)
# ---------------------------------------------------------------------------

def run_javap_instructions(
    classfile: str, method_name: str, descriptor: str, javap_bin: str = DEFAULT_JAVAP, tool_server: bool = False
) -> list[str]:
    text = run_javap_verbose(classfile, javap_bin=javap_bin, tool_server=tool_server)
    parsed = parse_javap_verbose(text)
    method = parsed["methods"].get((method_name, descriptor))
    if method is None:
        return []
    # method["code"] is already normalized by parse_javap_verbose's call into
    # normalize_method_instructions; re-derive the pre-normalization raw lines
    # is not needed by callers that only want the normalized form, so this
    # helper exists for callers (like the krak2 cross-check test) that want
    # the *normalized* instruction list keyed by a specific method signature.
    return method["code"]


def _first_javac_error(stderr: str) -> Optional[str]:
    for line in stderr.splitlines():
        if "error:" in line:
            return line.strip()
    return stderr.strip().splitlines()[0] if stderr.strip() else "javac failed with no diagnostic output"


def recompile_and_grade(
    java_file: str,
    class_name: str,
    classpath: str,
    ground_truth_class: str,
    out_dir: str,
    javac_bin: str = DEFAULT_JAVAC,
    javap_bin: str = DEFAULT_JAVAP,
    javac_timeout: float = DEFAULT_JAVAC_TIMEOUT_SECONDS,
    javap_timeout: float = DEFAULT_JAVAP_TIMEOUT_SECONDS,
    tool_server: bool = False,
) -> dict:
    """Recompile one decompiled .java (top-level class `class_name`, may define
    nested classes too) and grade the top-level class's .class against
    `ground_truth_class`. This is the single-engine grading step the
    redundancy ladder calls once per engine (vineflower/cfr/procyon/jd-cli).
    """
    # A missing ground-truth class or missing decompiled source is a HARNESS
    # problem (a corpus/setup bug -- e.g. a class the extraction step never
    # wrote, or a decompile pass that silently produced nothing) -- checked
    # BEFORE attempting to compile, so it can never be misreported as "the
    # decompiled source doesn't compile" (no-compile), which is a decompiler-
    # fidelity finding, a completely different claim.
    if not os.path.isfile(ground_truth_class):
        return {
            "grade": "harness-error",
            "first_error": f"ground truth class file missing: {ground_truth_class}",
            "mismatched_methods": [],
            "allowlist_matches": [],
        }
    if not os.path.isfile(java_file):
        return {
            "grade": "harness-error",
            "first_error": f"decompiled source file missing: {java_file}",
            "mismatched_methods": [],
            "allowlist_matches": [],
        }

    os.makedirs(out_dir, exist_ok=True)
    javac_args = ["--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn", "-d", out_dir]
    if classpath:
        javac_args += ["-cp", classpath]
    javac_args.append(java_file)
    try:
        javac_rc, _javac_out, javac_err = _run_jdk_tool("javac", javac_bin, javac_args, javac_timeout, tool_server)
    except subprocess.TimeoutExpired:
        return {
            "grade": "timeout",
            "first_error": f"javac timed out after {javac_timeout}s",
            "mismatched_methods": [],
            "allowlist_matches": [],
        }

    if javac_rc != 0:
        return {
            "grade": "no-compile",
            "first_error": _first_javac_error(javac_err),
            "mismatched_methods": [],
            "allowlist_matches": [],
        }

    # javac writes to <out_dir>/<package-path-from-the-source's-`package`-decl>/<Class>.class,
    # not flat into out_dir — search for it by simple name rather than assuming
    # a flat layout (a flat assumption silently false-negatived every
    # non-default-package class, i.e. nearly the entire real corpus).
    candidates = list(Path(out_dir).rglob(f"{class_name}.class"))
    if not candidates:
        return {
            "grade": "no-compile",
            "first_error": f"javac exited 0 but no {class_name}.class was produced anywhere under {out_dir}",
            "mismatched_methods": [],
            "allowlist_matches": [],
        }
    recompiled_class = str(candidates[0])

    try:
        a = parse_javap_verbose(run_javap_verbose(ground_truth_class, javap_bin=javap_bin, timeout=javap_timeout, tool_server=tool_server))
        b = parse_javap_verbose(run_javap_verbose(recompiled_class, javap_bin=javap_bin, timeout=javap_timeout, tool_server=tool_server))
    except subprocess.TimeoutExpired:
        return {
            "grade": "timeout",
            "first_error": "javap timed out",
            "mismatched_methods": [],
            "allowlist_matches": [],
        }
    diff = diff_normalized_classes(a, b)
    return grade_class_result(compiled_ok=True, diff=diff, first_error=None)


# ---------------------------------------------------------------------------
# Classpath cache: extract every module jar + bin/ext jar + nested LIB-INF
# jars ONCE into a scratch cache dir, return a ':'-joined javac classpath.
# ---------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_classpath(
    cache_dir: Path,
    modules_dir: Path = DEFAULT_MODULES_DIR,
    bin_ext_dir: Path = DEFAULT_BIN_EXT_DIR,
    force: bool = False,
) -> str:
    """Idempotent: on a cache hit (manifest recorded and every listed jar still
    present) this only reads a file; nested LIB-INF jars are extracted at most
    once per cache dir. Intended cache_dir: a scratch/session directory, not
    the repo (see module docstring / task spec: "extract once to a cache dir
    under the scratchpad").
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = cache_dir / "classpath.txt"
    if not force and manifest_path.is_file():
        entries = [line.strip() for line in manifest_path.read_text().splitlines() if line.strip()]
        if entries and all(os.path.isfile(e) for e in entries):
            return ":".join(entries)

    entries: list[str] = []
    nested_dir = cache_dir / "_nested-libinf"
    nested_dir.mkdir(parents=True, exist_ok=True)

    for jar_dir in (modules_dir, bin_ext_dir):
        if not jar_dir.is_dir():
            continue
        for jar in sorted(jar_dir.glob("*.jar")):
            entries.append(str(jar))
            entries.extend(_extract_nested_libinf(jar, nested_dir))

    manifest_path.write_text("\n".join(entries) + "\n")
    return ":".join(entries)


def _extract_nested_libinf(jar: Path, nested_dir: Path) -> list[str]:
    out = []
    try:
        with zipfile.ZipFile(jar) as zf:
            for name in zf.namelist():
                if name.startswith("LIB-INF/") and name.endswith(".jar"):
                    dest = nested_dir / jar.stem / Path(name).name
                    if not dest.is_file():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(name) as src, open(dest, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                    out.append(str(dest))
    except zipfile.BadZipFile:
        pass
    return out


# ---------------------------------------------------------------------------
# Module-level orchestration
# ---------------------------------------------------------------------------

def discover_top_level_classes(extracted_dir: Path) -> list[tuple[str, Path]]:
    """Return [(fqcn_with_slashes, class_file_path)] for every TOP-LEVEL class
    under extracted_dir (a class file whose basename has no '$').
    """
    out = []
    if not extracted_dir.is_dir():
        return out
    for class_file in sorted(extracted_dir.rglob("*.class")):
        if "$" in class_file.stem:
            continue
        if class_file.stem == "module-info":
            continue
        rel = class_file.relative_to(extracted_dir).with_suffix("")
        fqcn = str(rel).replace(os.sep, "/")
        out.append((fqcn, class_file))
    return out


def _decompile_one_class_with(
    java_bin: str,
    engine: str,
    tool_jar: Path,
    classfile: Path,
    out_dir: Path,
    timeout: float = DEFAULT_DECOMPILE_TIMEOUT_SECONDS,
) -> tuple[Optional[Path], Optional[str]]:
    """Decompile ONE .class with a specific engine jar. Each engine has its own
    CLI contract (verified against the actual jars in tools/decompilers/ / the
    scratch-provisioned JD-CLI — see docs/decompile-fidelity-report.md):
      CFR:      java -jar cfr.jar <class> --outputdir <dir> --silent true
      Procyon:  java -jar procyon.jar <class> -o <dir>
      JD-CLI:   java -jar jd-cli.jar -od <dir> <class>
    All three preserve (or, for JD-CLI's flat -od, simply don't need) the
    package path in their output; `rglob` finds the produced file either way.

    `engine` (one of "cfr", "procyon", "jd-cli") is supplied EXPLICITLY by the
    caller — never inferred from `tool_jar`'s filename. The previous
    filename-substring dispatch (`"cfr" in name` / `"jd-cli" in name` / else
    procyon) meant a renamed or differently-versioned jar silently picked the
    WRONG CLI contract, and anything unmatched silently fell through to
    Procyon's flags rather than failing. An unrecognized `engine` now raises
    instead of guessing.

    Returns (java_source_path_or_None, failure_reason_or_None): `failure_reason`
    is "timeout" when the subprocess itself timed out (see
    DEFAULT_DECOMPILE_TIMEOUT_SECONDS), None otherwise (including the ordinary
    "ran fine but produced no .java" case, which is not itself a timeout).
    """
    if engine not in ("cfr", "procyon", "jd-cli"):
        raise ValueError(f"_decompile_one_class_with: unrecognized engine {engine!r} (expected cfr/procyon/jd-cli)")
    if not tool_jar.is_file():
        return None, None
    out_dir.mkdir(parents=True, exist_ok=True)
    if engine == "cfr":
        cmd = [java_bin, "-jar", str(tool_jar), str(classfile), "--outputdir", str(out_dir), "--silent", "true"]
    elif engine == "jd-cli":
        cmd = [java_bin, "-jar", str(tool_jar), "-od", str(out_dir), str(classfile)]
    else:  # procyon
        cmd = [java_bin, "-jar", str(tool_jar), str(classfile), "-o", str(out_dir)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    candidates = list(Path(out_dir).rglob(f"{classfile.stem}.java"))
    return (candidates[0] if candidates else None), None


def _grade_one_class(
    fqcn: str,
    classfile: Path,
    *,
    vineflower_dir: Path,
    fallback_dir: Path,
    docsource_dir: Path,
    classpath: str,
    javac_bin: str,
    javap_bin: str,
    java_bin: str,
    cfr_jar: Path,
    procyon_jar: Path,
    jd_cli_jar: Optional[Path],
    primary_tree: str,
    tool_server: bool = False,
) -> tuple[str, dict]:
    """Grade one top-level class (the redundancy ladder) and return
    (fqcn, record). Self-contained: uses its own temp dirs, so it is safe to
    run concurrently for different classes (see grade_module's class_jobs)."""
    vf_java = vineflower_dir / f"{fqcn}.java"
    fb_java = fallback_dir / f"{fqcn}.java"
    source_java = vf_java if vf_java.is_file() else (fb_java if fb_java.is_file() else None)
    class_short = fqcn.rsplit("/", 1)[-1]

    docsource_java = docsource_dir / f"{fqcn}.java"
    docsource_available = docsource_java.is_file()
    docsource_roundtrip = None

    if source_java is None:
        # a missing decompiled source is a HARNESS problem (the corpus's
        # decompile pass never ran / never wrote this tree), never
        # "no-compile" (which claims the decompiled source itself failed
        # to compile — a decompiler-fidelity finding, not a setup bug).
        return fqcn, {
            "grade": "harness-error",
            "first_error": "no decompiled source found (vineflower/fallback both missing)",
            "best_decompiler": None,
            "attempted": [],
            "consensus": {"reaching_roundtrip": [], "count": 0},
            "docsource_available": docsource_available,
            "docsource_roundtrip": docsource_roundtrip,
        }

    with tempfile.TemporaryDirectory(prefix=f"n5fid-{class_short}-") as td:
        def _decompile_retry_thunk(engine, tool_jar, engine_label, classfile=classfile, class_short=class_short):
            with tempfile.TemporaryDirectory() as decompile_td, tempfile.TemporaryDirectory() as compile_td:
                java_src, reason = _decompile_one_class_with(java_bin, engine, tool_jar, classfile, Path(decompile_td))
                if java_src is None:
                    grade = "timeout" if reason == "timeout" else "no-compile"
                    suffix = " (timeout)" if reason == "timeout" else ""
                    return {"grade": grade, "first_error": f"{engine_label} retry decompile failed{suffix}", "mismatched_methods": [], "allowlist_matches": []}
                return recompile_and_grade(str(java_src), class_short, classpath, str(classfile), compile_td, javac_bin, javap_bin, tool_server=tool_server)

        def cfr_thunk():
            return _decompile_retry_thunk("cfr", cfr_jar, "CFR")

        def procyon_thunk():
            return _decompile_retry_thunk("procyon", procyon_jar, "Procyon")

        # first rung of the ladder is whatever tree grade_module was asked
        # to grade (`primary_tree`) -- labeling it the literal string
        # "vineflower" regardless of `--tree` misattributed a vineflower2
        # (or any other tree's) result to vineflower in `attempted`/
        # `per_engine_mismatched_methods`.
        first = recompile_and_grade(str(source_java), class_short, classpath, str(classfile), td, javac_bin, javap_bin, tool_server=tool_server)
        attempted = [(primary_tree, first)]
        if not _is_clean(first["grade"]):
            cfr_result = cfr_thunk()
            attempted.append(("cfr", cfr_result))
            if not _is_clean(cfr_result["grade"]):
                procyon_result = procyon_thunk()
                attempted.append(("procyon", procyon_result))
                if not _is_clean(procyon_result["grade"]) and jd_cli_jar is not None:

                    def jdcli_thunk():
                        return _decompile_retry_thunk("jd-cli", jd_cli_jar, "JD-CLI")

                    attempted.append(("jd-cli", jdcli_thunk()))

        best = select_best_decompiler(attempted)
        consensus = compute_consensus(attempted)

        if docsource_available:
            with tempfile.TemporaryDirectory() as ds_td:
                ds_result = recompile_and_grade(str(docsource_java), class_short, classpath, str(classfile), ds_td, javac_bin, javap_bin, tool_server=tool_server)
                docsource_roundtrip = _is_clean(ds_result["grade"])

        return fqcn, {
            "grade": best["grade"],
            "best_decompiler": best["best_decompiler"],
            "attempted": [(n, r["grade"]) for n, r in attempted],
            "first_error": next((r.get("first_error") for _, r in attempted if r["grade"] == "no-compile"), None),
            "mismatched_methods": [list(k) for k in (attempted[0][1].get("mismatched_methods") or [])],
            "allowlist_matches": attempted[0][1].get("allowlist_matches", []),
            # per-engine, per-method round-trip data — NOT a merge (an unsound
            # per-method Frankenstein class is never assembled here; see
            # docs/decompile-fidelity-report.md's Meta-decompilation section /
            # Harrand et al. arXiv:2005.11315), just the raw material a later,
            # separately-validated merge step would need.
            "per_engine_mismatched_methods": {
                n: [list(k) for k in (r.get("mismatched_methods") or [])] for n, r in attempted
            },
            "consensus": consensus,
            "docsource_available": docsource_available,
            "docsource_roundtrip": docsource_roundtrip,
        }


def grade_module(
    module: str,
    organized_dir: Path = DEFAULT_ORGANIZED_DIR,
    classpath: str = "",
    javac_bin: str = DEFAULT_JAVAC,
    javap_bin: str = DEFAULT_JAVAP,
    java_bin: str = DEFAULT_JAVA,
    cfr_jar: Path = DEFAULT_CFR_JAR,
    procyon_jar: Path = DEFAULT_PROCYON_JAR,
    jd_cli_jar: Optional[Path] = None,
    limit: Optional[int] = None,
    krak2_bin: str = "krak2",
    member_sample_size: int = 0,
    primary_tree: str = "vineflower",
    class_jobs: int = 1,
    tool_server: bool = False,
) -> dict:
    """`primary_tree` names the decompiled source tree to grade as the FIRST
    rung of the redundancy ladder — normally "vineflower" (tools/n5-decompile.sh's
    primary output), but any sibling tree under organized/<mod>/ with the same
    <package/Class>.java layout works (e.g. "vineflower2", a library-context-aware
    second decompile pass some other writer may produce), so two trees can be
    graded and compared on identical classes via two separate invocations.
    """
    mod_dir = organized_dir / module
    extracted_dir = mod_dir / "extracted"
    vineflower_dir = mod_dir / primary_tree
    fallback_dir = mod_dir / "fallback"
    docsource_dir = organized_dir / "docSource" / module

    classes = discover_top_level_classes(extracted_dir)
    if limit is not None:
        classes = classes[:limit]

    class_kwargs = dict(
        vineflower_dir=vineflower_dir, fallback_dir=fallback_dir, docsource_dir=docsource_dir,
        classpath=classpath, javac_bin=javac_bin, javap_bin=javap_bin, java_bin=java_bin,
        cfr_jar=cfr_jar, procyon_jar=procyon_jar, jd_cli_jar=jd_cli_jar, primary_tree=primary_tree,
        tool_server=tool_server,
    )
    per_class = {}
    if class_jobs > 1 and len(classes) > 1:
        # subprocess-bound (javac/javap/java): threads suffice. Results are
        # collected in submission (= sorted `classes`) order so per_class key
        # order is deterministic regardless of completion order; a per-class
        # exception propagates from .result() exactly as in the serial path.
        with concurrent.futures.ThreadPoolExecutor(max_workers=class_jobs) as pool:
            futures = [pool.submit(_grade_one_class, fqcn, classfile, **class_kwargs) for fqcn, classfile in classes]
            try:
                for fut in futures:
                    fqcn, record = fut.result()
                    per_class[fqcn] = record
            except BaseException:
                for fut in futures:
                    fut.cancel()
                raise
    else:
        for fqcn, classfile in classes:
            fqcn, record = _grade_one_class(fqcn, classfile, **class_kwargs)
            per_class[fqcn] = record

    grade_counts: dict[str, int] = {}
    for c in per_class.values():
        grade_counts[c["grade"]] = grade_counts.get(c["grade"], 0) + 1

    jar_path = None
    jar_sha256 = None
    recon_path = mod_dir / "recon.json"
    if recon_path.is_file():
        recon = json.loads(recon_path.read_text())
        jar_path = recon.get("jar_path")
        jar_sha256 = recon.get("jar_sha256")

    return {
        "module": module,
        "schema_version": SCHEMA_VERSION,
        "jar_sha256": jar_sha256,
        "primary_tree": primary_tree,
        "class_count": len(classes),
        "grade_counts": grade_counts,
        "classes": per_class,
        # a --limit-per-module run graded only a PREFIX of the module's real
        # classes -- is_module_up_to_date must never treat that partial run as
        # equivalent to (or an up-to-date cache for) a full run, or a later
        # unlimited invocation would silently skip the module and keep
        # reporting the truncated grade_counts as if they were complete
        # (R4-limited-run-cached-as-complete).
        "limit_per_module": limit,
    }


# ---------------------------------------------------------------------------
# Per-tree output files (fidelity.<tree>.json) + legacy fidelity.json migration
# ---------------------------------------------------------------------------

def fidelity_output_path(mod_dir: Path, tree: str) -> Path:
    """Where grading `tree` for this module is WRITTEN. Always tree-specific —
    two trees graded for the same module produce two distinct files, neither
    overwriting the other (see fidelity_read_path for the legacy-name fallback
    used only when READING).
    """
    return Path(mod_dir) / f"fidelity.{tree}.json"


def fidelity_read_path(mod_dir: Path, tree: str) -> Optional[Path]:
    """Where grading `tree` for this module is READ from, or None if no grade
    exists yet. Prefers the tree-specific name; for "vineflower" specifically,
    falls back to the pre-per-tree-files legacy name `fidelity.json` (every
    fidelity.json ever written by this tool, before --tree existed, graded the
    vineflower tree) so an already-graded corpus is never force-re-graded just
    because this migration landed. See migrate_legacy_fidelity_json for the
    one-time on-disk rename that retires the legacy name going forward.
    """
    mod_dir = Path(mod_dir)
    named = fidelity_output_path(mod_dir, tree)
    if named.is_file():
        return named
    if tree == "vineflower":
        legacy = mod_dir / "fidelity.json"
        if legacy.is_file():
            return legacy
    return None


def migrate_legacy_fidelity_json(mod_dir: Path) -> bool:
    """One-time migration: organized/<mod>/fidelity.json (the pre-per-tree-
    files name, always a vineflower grade) is renamed to
    organized/<mod>/fidelity.vineflower.json when the new name doesn't already
    exist. Returns True if a rename happened. Idempotent and safe to call
    unconditionally: a no-op once migrated, and never overwrites/discards
    either file when BOTH already exist (an ambiguous state this function
    refuses to silently resolve by deleting one).
    """
    mod_dir = Path(mod_dir)
    legacy = mod_dir / "fidelity.json"
    target = mod_dir / "fidelity.vineflower.json"
    if legacy.is_file() and not target.is_file():
        legacy.rename(target)
        return True
    return False


def is_module_up_to_date(
    mod_dir: Path, primary_tree: str = "vineflower", limit_per_module: Optional[int] = None
) -> bool:
    fidelity_path = fidelity_read_path(mod_dir, primary_tree)
    recon_path = Path(mod_dir) / "recon.json"
    if fidelity_path is None or not recon_path.is_file():
        return False
    try:
        fidelity = json.loads(fidelity_path.read_text())
        recon = json.loads(recon_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return (
        fidelity.get("schema_version") == SCHEMA_VERSION
        and fidelity.get("jar_sha256") == recon.get("jar_sha256")
        # a fidelity.json from grading a DIFFERENT tree (e.g. "vineflower2")
        # must never be mistaken for an up-to-date cache of THIS tree's grade —
        # default "vineflower" for pre-existing files written before this field existed
        and fidelity.get("primary_tree", "vineflower") == primary_tree
        # a limited run (--limit-per-module N) must never be mistaken for an
        # up-to-date cache of a run with a DIFFERENT (or no) limit — default
        # None for pre-existing files written before this field existed,
        # which were always full (unlimited) runs.
        and fidelity.get("limit_per_module") == limit_per_module
    )


# ---------------------------------------------------------------------------
# Sampled independent cross-checks (krak2 + niagara_help.py) — run once at
# report time over a capped, seeded-random sample of already-graded classes,
# not inline in the per-class grading loop (which only needs the recompile
# comparison to produce a grade).
# ---------------------------------------------------------------------------

def sample_independent_cross_checks(
    module_results: list[dict],
    organized_dir: Path = DEFAULT_ORGANIZED_DIR,
    sample_size: int = 30,
    seed: int = 20260928,
    javap_bin: str = DEFAULT_JAVAP,
    krak2_bin: str = "krak2",
) -> dict:
    all_classes = [(mr["module"], fqcn) for mr in module_results for fqcn in mr["classes"]]
    rng = random.Random(seed)
    rng.shuffle(all_classes)
    sampled = all_classes[:sample_size]

    member_checks = []
    krak2_checks = []
    for module, fqcn in sampled:
        classfile = organized_dir / module / "extracted" / f"{fqcn}.class"
        if not os.path.isfile(str(classfile)):
            continue
        parsed = parse_javap_verbose(run_javap_verbose(str(classfile), javap_bin=javap_bin))

        ours = slot_field_names(parsed)
        if ours:
            short = fqcn.rsplit("/", 1)[-1]
            docs_members = niagara_help_member_lookup(short.replace("/", "."))
            if docs_members is not None:
                agreement = member_set_agreement(ours, docs_members)
                member_checks.append({"class": f"{module}/{fqcn}", "agreement": agreement})

        if parsed["methods"]:
            (mname, mdesc), mdata = next(iter(parsed["methods"].items()))
            result = krak2_cross_check(str(classfile), mdata["code"], mname, mdesc, krak2_bin=krak2_bin)
            krak2_checks.append({"class": f"{module}/{fqcn}", "method": f"{mname}{mdesc}", "status": result["status"]})

    return {"sampled": sampled, "member_checks": member_checks, "krak2_checks": krak2_checks}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(module_results: list[dict], cross_checks: Optional[dict] = None) -> str:
    lines = ["# Decompile fidelity report", "", "Generated by `tools/n5-fidelity.py --report`.", ""]
    total_counts: dict[str, int] = {}
    total_classes = 0
    docsource_checked = 0
    docsource_roundtripped = 0
    no_engine_reaches_equivalence = []
    genuine_mismatch_classes = []
    compile_isolation_only_classes = []
    mixed_classes = []

    failed_modules = [mr for mr in module_results if mr.get("module_error")]

    lines.append("| Module | Classes | roundtrip-exact | roundtrip-equivalent | compiles-mismatch | no-compile | bytecode-only |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for mr in sorted(module_results, key=lambda r: r["module"]):
        if mr.get("module_error"):
            # a module that raised during grading must NEVER render as an
            # indistinguishable all-zero row (which reads as "0 classes, all
            # clean" — the OPPOSITE of what happened): it is excluded from
            # every count/total below and surfaced in its own row and its own
            # "Module failures" section instead (R4-module-failure-masked).
            lines.append(f"| {mr['module']} | **GRADING FAILED** — see failure details below | | | | | |")
            continue
        counts = mr["grade_counts"]
        for k, v in counts.items():
            total_counts[k] = total_counts.get(k, 0) + v
        total_classes += mr["class_count"]
        lines.append(
            f"| {mr['module']} | {mr['class_count']} | {counts.get('roundtrip-exact', 0)} | "
            f"{counts.get('roundtrip-equivalent', 0)} | {counts.get('compiles-mismatch', 0)} | "
            f"{counts.get('no-compile', 0)} | {counts.get('bytecode-only', 0)} |"
        )
        for fqcn, c in mr["classes"].items():
            if c.get("docsource_roundtrip") is not None:
                docsource_checked += 1
                if c["docsource_roundtrip"]:
                    docsource_roundtripped += 1
            if c["grade"] in ("no-compile", "compiles-mismatch", "bytecode-only"):
                no_engine_reaches_equivalence.append(f"{mr['module']}/{fqcn}")
            if c["grade"] == "bytecode-only":
                attempt_grades = {g for _, g in c.get("attempted", [])}
                has_mismatch = "compiles-mismatch" in attempt_grades
                has_nocompile = "no-compile" in attempt_grades
                entry = f"{mr['module']}/{fqcn}"
                if has_mismatch and not has_nocompile:
                    genuine_mismatch_classes.append(entry)
                elif has_nocompile and not has_mismatch:
                    compile_isolation_only_classes.append(entry)
                elif has_mismatch or has_nocompile:
                    mixed_classes.append(entry)

    lines.append("")
    lines.append(f"## Module failures ({len(failed_modules)})")
    lines.append("")
    if failed_modules:
        lines.append(
            "These modules raised an unexpected exception during grading (bad module name, corrupt "
            "recon.json, a decompiler crash, ...) and were graded ZERO classes — this is a harness/tooling "
            "failure, not a fidelity finding, and is excluded from every count and total below. `main()` "
            "exits non-zero when this list is non-empty."
        )
        for mr in sorted(failed_modules, key=lambda r: r["module"]):
            lines.append(f"- **{mr['module']}**: {mr.get('module_error', '(no error recorded)')}")
    else:
        lines.append("None.")

    lines.append("")
    lines.append("## Overall")
    lines.append("")
    for grade in ("roundtrip-exact", "roundtrip-equivalent", "compiles-mismatch", "no-compile", "bytecode-only"):
        n = total_counts.get(grade, 0)
        pct = (100.0 * n / total_classes) if total_classes else 0.0
        lines.append(f"- {grade}: {n}/{total_classes} ({pct:.1f}%)")

    lines.append("")
    lines.append("## Harness validation (docSource originals)")
    lines.append("")
    if docsource_checked:
        rate = 100.0 * docsource_roundtripped / docsource_checked
        lines.append(
            f"{docsource_roundtripped}/{docsource_checked} ({rate:.1f}%) of classes with a docSource original "
            "round-trip the ORIGINAL Tridium source through the same recompile+compare harness. A class where "
            "the original itself does not round-trip indicates a harness/normalizer gap or a stale docSource "
            "copy, not a decompiler fidelity problem."
        )
    else:
        lines.append("No classes with an available docSource original were graded in this run.")

    lines.append("")
    lines.append(f"## Classes where NO decompiler reached round-trip (\"use bytecode only\") — {len(no_engine_reaches_equivalence)}")
    lines.append("")
    for c in no_engine_reaches_equivalence[:200]:
        lines.append(f"- {c}")
    if len(no_engine_reaches_equivalence) > 200:
        lines.append(f"- ... and {len(no_engine_reaches_equivalence) - 200} more")

    lines.append("")
    lines.append("### Why these are bytecode-only: genuine mismatch vs. compile-isolation artifact")
    lines.append("")
    lines.append(
        "Every attempted engine's grade is kept per class (`attempted`, `per_engine_mismatched_methods` in "
        "`fidelity.json`), which splits the `bytecode-only` set into two very different failure modes: a class "
        "whose decompiled source COMPILED on every attempted engine but whose recompiled bytecode genuinely "
        "differs from the shipped class on at least one method (a real decompiler-fidelity gap — see "
        "`docs/decompiler-bakeoff.md`'s methodology note on isolated single-class compilation for why this "
        "reading still needs care), versus a class that never even compiled on any engine (most often the "
        "known single-class-isolation limitation — e.g. `SecurityUtil.doPrivileged` overload ambiguity that "
        "resolves fine when the whole module compiles together but not one class at a time; see "
        "docs/decompiler-bakeoff.md \"Other recompile-blocking issues found\")."
    )
    lines.append(
        f"- genuine semantic mismatch (compiled on every attempted engine, bytecode differs): "
        f"{len(genuine_mismatch_classes)}"
    )
    for c in genuine_mismatch_classes[:50]:
        lines.append(f"  - {c}")
    if len(genuine_mismatch_classes) > 50:
        lines.append(f"  - ... and {len(genuine_mismatch_classes) - 50} more")
    lines.append(
        f"- compile-isolation failure only (never compiled on any attempted engine): "
        f"{len(compile_isolation_only_classes)}"
    )
    lines.append(
        f"- mixed (some engines compile-mismatch, some no-compile): {len(mixed_classes)}"
    )

    lines.append("")
    lines.append("## Allowlist")
    lines.append("")
    if ALLOWLIST:
        for entry in ALLOWLIST:
            lines.append(f"- `{entry.name}`: {entry.justification}")
    else:
        lines.append("No allowlist entries are seeded. The mechanism exists (see `ALLOWLIST` in "
                      "`tools/n5-fidelity.py`) but no observed mismatch pattern has yet been confirmed "
                      "provably-semantics-preserving; every method-body mismatch currently grades "
                      "`compiles-mismatch`, never `roundtrip-equivalent`.")

    lines.append("")
    lines.append("## Redundancy: independent cross-checks (krak2, niagara_help.py)")
    lines.append("")
    lines.append(
        "Beyond the vineflower/CFR/Procyon(/JD-CLI) recompile ladder, two independent, "
        "non-decompiler sources validate the pipeline itself on a sampled subset of graded classes:"
    )
    lines.append("")
    if cross_checks is None or not cross_checks.get("sampled"):
        lines.append("- Not run in this invocation (pass `--report` after a grading run with "
                      "`--cross-check-sample N > 0`, or krak2 is not installed).")
    else:
        krak2_checks = cross_checks.get("krak2_checks", [])
        member_checks = cross_checks.get("member_checks", [])
        krak2_match = sum(1 for c in krak2_checks if c["status"] == "match")
        krak2_mismatch = [c for c in krak2_checks if c["status"] == "mismatch"]
        lines.append(
            f"- **krak2 (Krakatau2) normalizer cross-check**: {krak2_match}/{len(krak2_checks)} sampled "
            "methods' independently-disassembled opcode sequence (krak2, a Rust bytecode disassembler "
            "with no dependency on javap or the JDK's class reader) agrees with `normalize_method_instructions`'s "
            "own opcode sequence. This validates the *normalizer*, not decompiler fidelity — a mismatch here "
            "would mean the grader itself is untrustworthy, independent of what any decompiler produced."
        )
        for c in krak2_mismatch[:20]:
            lines.append(f"  - MISMATCH: {c['class']} {c['method']}")
        if member_checks:
            ratios = [c["agreement"]["ratio"] for c in member_checks]
            avg = sum(ratios) / len(ratios)
            lines.append(
                f"- **niagara_help.py (bajadoc/javadoc index) member-set cross-check**: {len(member_checks)} sampled "
                f"classes with Property/Action/Topic slot fields, average agreement ratio {avg:.2f} against the "
                "independently-indexed bajadoc PROPERTIES/ACTIONS listing (see `slot_field_names` / "
                "`niagara_help_member_lookup`)."
            )
            for c in member_checks:
                if c["agreement"]["ratio"] < 1.0:
                    lines.append(
                        f"  - {c['class']}: ratio {c['agreement']['ratio']:.2f}, "
                        f"missing from docs: {c['agreement']['missing_from_docs']}"
                    )
        else:
            lines.append("- **niagara_help.py member-set cross-check**: no sampled class had both a "
                          "Property/Action/Topic slot field and a resolvable niagara_help.py entry.")

    lines.append("")
    lines.append("## Toolbelt alignment (research-sdd kit) — for the T6 retro, not applied here")
    lines.append("")
    lines.append(
        "`~/investigacion/sdd-investigacion/research-sdd/toolbelt/corroborate-java.sh` "
        "(`java-corroboration.v1`) runs Vineflower + CFR + Procyon + `javap` + `jdeps` as sandboxed, "
        "hash-pinned adapters over a whole JAR and publishes class/member/dependency inventories and "
        "pairwise textual/hash agreement — the same three decompiler engines this grader uses, plus a "
        "trust/isolation model (Bubblewrap, digest pinning) this grader does not have. The two tools are "
        "complementary, not overlapping in what they measure: the kit's `java-corroboration.v1` compares "
        "decompiler OUTPUT to decompiler output (never recompiles, never touches ground-truth bytecode "
        "beyond `javap`/`jdeps` coverage), while this grader's recompile-and-compare-to-original-bytecode "
        "method is strictly stronger evidence of semantic fidelity but is per-class, N5-corpus-specific, "
        "and has no sandboxing. Gap for the retro (T6): `corroborate-java.sh` currently has no recompile "
        "step and no per-class grade; `tools/n5-fidelity.py`'s method could be proposed as an addition to "
        "`java-corroboration.v1`'s schema (or as a sibling wrapper) rather than staying niagara5-research-local — "
        "proposed, not applied, from this task's authorized scope."
    )
    lines.append("")
    lines.append("## JD-CLI (4th decompiler) provisioning")
    lines.append("")
    lines.append(
        "Provisioned from the official GitHub release `intoolswetrust/jd-cli` (the JD-Core CLI wrapper; "
        "`java-decompiler/jd-cli` is a dead redirect, `intoolswetrust/jd-cli` — formerly `kwart/jd-cmd` — "
        "is the maintained fork) tag `jd-cli-1.3.0-beta-1`, asset `jd-cli-1.3.0-beta-1-dist.zip`, "
        "sha256 `dfebe88fc906362e50049151ca8c764d1d4860d4e7d81ba657025a12ef406353`. Downloaded to this "
        "session's scratchpad (not committed — `tools/decompilers/` is out of this task's write scope and "
        "its `*.jar`/`*.zip` are gitignored anyway); used via `--jd-cli-jar <path>` as the 4th rung of the "
        "redundancy ladder when a path is passed, never by default. Fernflower (the other candidate) "
        "remains genuinely unavailable as a standalone jar — see `tools/decompilers/README.md`, unchanged "
        "from the original bake-off finding."
    )

    lines.append("")
    lines.append("## Methodology notes")
    lines.append("")
    lines.append(
        "- **No textual-similarity grade.** This grader never scores a `difflib`-style similarity ratio "
        "as (or as a substitute for) a fidelity grade — a single flipped comparison operator, or one wrong "
        "constant, keeps a method at roughly 0.99 textual similarity while being semantically wrong. Grades "
        "come only from javac recompilation + normalized-bytecode equality (this file's `grade_class_result`). "
        "A similarity score, if ever surfaced, would be for human triage ordering only, never the grade itself."
    )
    lines.append(
        "- **Attribute mirroring.** Tridium N5 classes are compiled with `-g` (LineNumberTable + "
        "LocalVariableTable present — confirmed T1, `control.jar` `BNumericWritable`: 62 LVT + 63 LNT entries) "
        "and WITHOUT `-parameters` (`javap -v` on that same class: 0 `MethodParameters` attributes). This "
        "grader compiles with `-g` and never passes `-parameters`, and separately records/compares "
        "`has_method_parameters` per method (see `parse_javap_verbose`) so a decompiler/recompile path that "
        "somehow acquired one would be caught rather than silently ignored."
    )
    lines.append(
        "- **Grade vocabulary vs. Harrand et al.** (\"Java Decompiler Diversity and its Application to "
        "Meta-decompilation\", arXiv:2005.11315 [CERT-web], who found their meta-decompiler Arlecchino "
        "recovered classes no single decompiler handled — 37.6% in their sample): their three-tier vocabulary "
        "(syntactically correct / semantically equivalent modulo inputs / strictly equivalent bytecode) maps "
        "onto this grader's grades roughly as: their \"strictly equivalent bytecode\" ~ `roundtrip-exact`; "
        "their \"semantically equivalent\" ~ `roundtrip-equivalent` (this grader's allowlist mechanism, "
        "currently empty — see Allowlist above); their \"syntactically correct\" has no direct equivalent here "
        "since this grader never accepts syntactic correctness alone as a passing grade (a `compiles-mismatch` "
        "is syntactically correct AND still fails). Per-engine, per-method round-trip data is recorded in "
        "`fidelity.json`'s `per_engine_mismatched_methods` as raw material for a possible future sound "
        "per-method merge step (in Arlecchino's spirit) — this tool does not itself assemble a merged class, "
        "since doing so soundly needs its own validation the corpus doesn't yet have."
    )
    lines.append(
        "- **Exception tables and switch tables are part of the compared representation**, not just straight-"
        "line bytecode: try/catch/finally ranges are compared with handler type preserved (canonicalized "
        "position, not raw byte offset) and `tableswitch`/`lookupswitch` case KEYS are kept literal while only "
        "their jump targets are relativized — two methods differing only in which exception type a handler "
        "catches, or in a swapped switch-case target, are never graded as matching."
    )

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# T20: v1-vs-v2 (or any tree-vs-tree) comparison — per-class grade transition
# ---------------------------------------------------------------------------

def load_tree_results(organized_dir: Path, modules: list[str], tree: str,
                      skipped: Optional[list] = None) -> list[dict]:
    """Read each module's ALREADY-GRADED fidelity.<tree>.json (or its legacy
    fidelity.json for "vineflower" — see fidelity_read_path). Never grades
    anything itself: --compare is a pure reporting mode over existing runs.

    A module whose file is missing or unreadable is never dropped silently: it is
    appended to ``skipped`` as ``(module, reason)`` so callers can report it.
    """
    out = []
    for module in modules:
        p = fidelity_read_path(Path(organized_dir) / module, tree)
        if p is None:
            if skipped is not None:
                skipped.append((module, f"missing fidelity.{tree}.json"))
            continue
        try:
            out.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError) as e:
            if skipped is not None:
                skipped.append((module, f"unreadable fidelity.{tree}.json: {e}"))
            continue
    return out


def compare_tree_grades(results_a: list[dict], results_b: list[dict], label_a: str, label_b: str) -> dict:
    """Per-class grade transition from tree `label_a` to tree `label_b`, over
    the classes present AND graded in BOTH module-results lists (a class or an
    entire module graded in only one tree contributes nothing — there is no
    transition to report for it). `results_a`/`results_b` are grade_module's
    own output shape: a list of {"module": ..., "classes": {fqcn: {"grade": ...}}}.

    Uses `_GRADE_RANK` (worst to best: no-compile/timeout/harness-error <
    compiles-mismatch/bytecode-only < roundtrip-equivalent < roundtrip-exact)
    to classify each transition as WORSE (rank went down), better (rank went
    up), or unchanged (same rank — including a same-rank grade RELABEL, e.g.
    compiles-mismatch->bytecode-only, which is not itself a regression).
    """
    a_by_module = {r["module"]: r["classes"] for r in results_a}
    b_by_module = {r["module"]: r["classes"] for r in results_b}

    transition_counts: dict[str, int] = {}
    per_module_transition_counts: dict[str, dict[str, int]] = {}
    worse: list[dict] = []
    better: list[dict] = []
    unchanged_count = 0
    common_class_count = 0

    modules_common = sorted(set(a_by_module) & set(b_by_module))
    for module in modules_common:
        a_classes = a_by_module[module]
        b_classes = b_by_module[module]
        common_fqcns = sorted(set(a_classes) & set(b_classes))
        for fqcn in common_fqcns:
            common_class_count += 1
            grade_a = a_classes[fqcn]["grade"]
            grade_b = b_classes[fqcn]["grade"]
            key = f"{grade_a}->{grade_b}"
            transition_counts[key] = transition_counts.get(key, 0) + 1
            per_module_transition_counts.setdefault(module, {})
            per_module_transition_counts[module][key] = per_module_transition_counts[module].get(key, 0) + 1

            rank_a = _GRADE_RANK.get(grade_a, -1)
            rank_b = _GRADE_RANK.get(grade_b, -1)
            entry = {"module": module, "class": fqcn, "from": grade_a, "to": grade_b}
            if rank_b < rank_a:
                worse.append(entry)
            elif rank_b > rank_a:
                better.append(entry)
            else:
                unchanged_count += 1

    return {
        "tree_a": label_a,
        "tree_b": label_b,
        "modules_common": modules_common,
        "common_class_count": common_class_count,
        "transition_counts": transition_counts,
        "per_module_transition_counts": per_module_transition_counts,
        "worse": worse,
        "better": better,
        "unchanged_count": unchanged_count,
    }


def _tree_clean_count(comparison: dict, side: str) -> int:
    """Count of classes graded roundtrip-exact/roundtrip-equivalent on one
    side (`side` is "from" for tree_a, "to" for tree_b) of every recorded
    transition -- the measured round-trip rate a primary-tree recommendation
    is based on (see generate_compare_report), never a textual/line-count diff.
    """
    idx = 0 if side == "from" else 1
    clean = 0
    for key, n in comparison["transition_counts"].items():
        grade = key.split("->")[idx]
        if grade in ("roundtrip-exact", "roundtrip-equivalent"):
            clean += n
    return clean


def generate_compare_report(
    comparison: dict,
    title: str = "tree comparison",
    include_heading: bool = True,
    notes: Optional[list[str]] = None,
) -> str:
    """`include_heading` is False when the caller (main()'s --compare branch)
    is about to hand this body to upsert_markdown_section, which is the sole
    owner of the `## {title}` heading it inserts -- emitting the heading here
    TOO produced a literal duplicated `## {title}` line (regression, see
    TestCompareCLIWritesReportSection.test_compare_report_never_duplicates_the_heading).
    Defaults True so a standalone/direct call (as in TestGenerateCompareReport)
    still gets a complete, self-contained markdown section.

    `notes` are free-text caveats the CALLER supplies (e.g. classpath/jar
    provenance for this specific run, or a fixed methodology caveat like
    "@Override is decompiler inference, not recovered information") -- this
    function never invents them, it only renders what it's given.
    """
    tree_a = comparison["tree_a"]
    tree_b = comparison["tree_b"]
    lines = [f"## {title}", ""] if include_heading else []
    lines.append(
        f"Per-class grade transition from `{tree_a}` to `{tree_b}` on the "
        f"{comparison['common_class_count']} classes present and graded in BOTH trees, "
        f"across {len(comparison['modules_common'])} common modules "
        f"({', '.join(comparison['modules_common'])})."
    )
    lines.append("")
    skipped_modules = comparison.get("skipped_modules") or {}
    skipped_rows = [(t, m, r) for t, items in skipped_modules.items() for m, r in items]
    if skipped_rows:
        lines.append(f"**{len(skipped_rows)} module result(s) could not be loaded and are NOT in this comparison:**")
        lines.append("")
        lines.extend(f"- `{t}/{m}`: {r}" for t, m, r in skipped_rows)
        lines.append("")
    else:
        lines.append("No module was skipped: every requested module had a readable result for both trees.")
        lines.append("")
    lines.append(f"| Transition (`{tree_a}` -> `{tree_b}`) | Count |")
    lines.append("|---|---:|")
    for key in sorted(comparison["transition_counts"]):
        lines.append(f"| `{key}` | {comparison['transition_counts'][key]} |")
    lines.append("")
    lines.append("### Per-module transition counts")
    lines.append("")
    any_module_line = False
    for module in comparison["modules_common"]:
        counts = comparison["per_module_transition_counts"].get(module, {})
        if not counts:
            continue
        any_module_line = True
        lines.append(f"- **{module}**: " + ", ".join(f"`{k}`: {v}" for k, v in sorted(counts.items())))
    if not any_module_line:
        lines.append("None.")
    lines.append("")

    worse = comparison["worse"]
    lines.append(f"### Classes that got WORSE in {tree_b} ({len(worse)})")
    lines.append("")
    lines.append(
        f"These matter most: a regression `{tree_b}` introduced relative to `{tree_a}`."
    )
    lines.append("")
    if worse:
        for w in sorted(worse, key=lambda w: (w["module"], w["class"])):
            lines.append(f"- {w['module']}/{w['class']}: `{w['from']}` -> `{w['to']}`")
    else:
        lines.append("None.")
    lines.append("")

    better = comparison["better"]
    lines.append(f"### Classes that got better in {tree_b} ({len(better)})")
    lines.append("")
    if better:
        for b in sorted(better, key=lambda b: (b["module"], b["class"])):
            lines.append(f"- {b['module']}/{b['class']}: `{b['from']}` -> `{b['to']}`")
    else:
        lines.append("None.")
    lines.append("")
    lines.append(f"Unchanged grade: {comparison['unchanged_count']}")
    lines.append("")

    total = comparison["common_class_count"]
    clean_a = _tree_clean_count(comparison, "from")
    clean_b = _tree_clean_count(comparison, "to")
    rate_a = (clean_a / total) if total else 0.0
    rate_b = (clean_b / total) if total else 0.0

    lines.append("### Recommendation")
    lines.append("")
    lines.append(
        f"- `{tree_a}` round-trip rate (roundtrip-exact + roundtrip-equivalent): "
        f"{clean_a}/{total} ({rate_a:.1%})"
    )
    lines.append(
        f"- `{tree_b}` round-trip rate (roundtrip-exact + roundtrip-equivalent): "
        f"{clean_b}/{total} ({rate_b:.1%})"
    )
    if worse:
        lines.append(
            f"- **Recommendation: keep `{tree_a}` as the primary tree.** `{tree_b}` introduced "
            f"{len(worse)} regression(s) (see 'got WORSE' above) — a non-empty worse-list disqualifies "
            f"a tree as primary regardless of its overall round-trip rate."
        )
    elif rate_b > rate_a:
        lines.append(
            f"- **Recommendation: adopt `{tree_b}` as the primary tree.** Strictly higher measured "
            f"round-trip rate ({rate_b:.1%} vs {rate_a:.1%}) and zero regressions."
        )
    elif rate_a > rate_b:
        lines.append(
            f"- **Recommendation: keep `{tree_a}` as the primary tree.** Higher (or equal) measured "
            f"round-trip rate ({rate_a:.1%} vs {rate_b:.1%})."
        )
    else:
        lines.append(
            f"- **Recommendation: no change.** `{tree_a}` and `{tree_b}` have identical measured "
            f"round-trip rates and zero regressions on this sample."
        )
    lines.append(
        "- This recommendation is based ONLY on the measured round-trip rate and the worse-list above — "
        "NEVER on textual similarity, line count, or any feature-adoption diff between the two trees' "
        "decompiled source (see 'No textual-similarity grade' in Methodology notes)."
    )
    lines.append("")

    if notes:
        lines.append("### Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines) + "\n"


def upsert_markdown_section(doc_text: str, heading_line: str, body: str) -> str:
    """Insert or replace ONE `## `-level section (identified by its exact
    heading line, e.g. "## v1 vs v2 (library context)") inside `doc_text`,
    leaving every other section byte-for-byte untouched (this is how --compare
    adds its section to an existing docs/decompile-fidelity-report.md without
    a full --report regenerate, which would need BOTH trees' complete grading
    data just to reproduce the unrelated single-tree tables). `body` replaces
    everything between the heading line and the next `## ` heading (or EOF).
    Appended at the end (with a preceding blank line) when the heading is not
    already present.
    """
    heading_line = heading_line.rstrip("\n")
    body = body.rstrip("\n")
    lines = doc_text.split("\n")

    heading_idx = None
    for i, line in enumerate(lines):
        if line.strip() == heading_line.strip():
            heading_idx = i
            break

    section_lines = [heading_line, "", body, ""]

    if heading_idx is None:
        new_lines = list(lines)
        while new_lines and new_lines[-1] == "":
            new_lines.pop()
        new_lines += [""] + section_lines
        return "\n".join(new_lines) + "\n"

    end_idx = len(lines)
    for j in range(heading_idx + 1, len(lines)):
        if lines[j].startswith("## "):
            end_idx = j
            break
    while end_idx > heading_idx + 1 and lines[end_idx - 1] == "":
        end_idx -= 1

    new_lines = lines[:heading_idx] + section_lines + lines[end_idx:]
    return "\n".join(new_lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _list_all_modules(organized_dir: Path) -> list[str]:
    out = []
    for p in sorted(organized_dir.iterdir()):
        if not p.is_dir() or p.name.startswith("_"):
            continue
        if p.name == "docSource":
            continue
        if (p / "recon.json").is_file():
            out.append(p.name)
    return out


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules", help="comma-separated module names")
    parser.add_argument("--all", action="store_true", help="grade every module with a recon.json")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--class-jobs", type=int, default=1,
                         help="grade this many classes concurrently within each module (default 1 = serial; results identical)")
    parser.add_argument("--tool-server", action="store_true",
                         help="run javac/javap in one persistent in-process JVM per worker thread instead of a fresh JVM per call "
                              "(identical grades, much faster; falls back to subprocesses if the server cannot run)")
    parser.add_argument("--limit-per-module", type=int, default=None)
    parser.add_argument("--report", action="store_true", help="(re)write docs/decompile-fidelity-report.md")
    parser.add_argument("--organized-dir", default=str(DEFAULT_ORGANIZED_DIR))
    parser.add_argument("--modules-dir", default=str(DEFAULT_MODULES_DIR))
    parser.add_argument("--bin-ext-dir", default=str(DEFAULT_BIN_EXT_DIR))
    parser.add_argument("--classpath-cache-dir", default=None,
                         help="default: a scratch dir under $TMPDIR (see task: 'extract once to a cache dir under the scratchpad')")
    parser.add_argument("--force", action="store_true", help="ignore fidelity.json's up-to-date cache")
    parser.add_argument("--jd-cli-jar", default=None)
    parser.add_argument("--cross-check-sample", type=int, default=0,
                         help="with --report: also run krak2/niagara_help.py cross-checks on N sampled graded classes")
    parser.add_argument("--tree", default="vineflower",
                         help="decompiled source tree to grade, e.g. vineflower (default) or vineflower2 — "
                              "see grade_module docstring. Output is organized/<mod>/fidelity.<tree>.json — "
                              "grading a second tree for the same module writes a SEPARATE file, never "
                              "overwriting the first tree's grade (see fidelity_output_path).")
    parser.add_argument("--compare", default=None, metavar="TREE_A,TREE_B",
                         help="report mode: read each already-graded module's fidelity.<tree>.json for BOTH "
                              "trees (no grading is performed) and report the per-class grade transition "
                              "between them over the --modules/--all selection. With --report, upserts a "
                              "comparison section into docs/decompile-fidelity-report.md instead of touching "
                              "the rest of the file (see --compare-title).")
    parser.add_argument("--compare-title", default=None,
                         help="heading text for the --compare --report section (default: '<TREE_A> vs "
                              "<TREE_B> (library context)')")
    parser.add_argument("--compare-note", action="append", default=None,
                         help="free-text caveat rendered under a 'Notes' subsection of the --compare --report "
                              "output (repeatable) — e.g. classpath/jar provenance for this run, or a fixed "
                              "methodology caveat. Never invented by this tool; the caller supplies the facts.")
    args = parser.parse_args(argv)

    organized_dir = Path(args.organized_dir)
    if args.all:
        modules = _list_all_modules(organized_dir)
    elif args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    else:
        parser.error("pass --modules a,b,c or --all")
        return 2

    if args.compare:
        parts = [p.strip() for p in args.compare.split(",") if p.strip()]
        if len(parts) != 2:
            parser.error("--compare requires exactly two comma-separated tree names, e.g. vineflower,vineflower2")
            return 2
        tree_a, tree_b = parts
        skipped_a: list = []
        skipped_b: list = []
        results_a = load_tree_results(organized_dir, modules, tree_a, skipped=skipped_a)
        results_b = load_tree_results(organized_dir, modules, tree_b, skipped=skipped_b)
        for label, skipped in ((tree_a, skipped_a), (tree_b, skipped_b)):
            for module, reason in skipped:
                print(f"[compare] SKIPPED {label}/{module}: {reason}", file=sys.stderr)
        comparison = compare_tree_grades(results_a, results_b, tree_a, tree_b)
        comparison["skipped_modules"] = {tree_a: skipped_a, tree_b: skipped_b}
        print(
            f"[compare {tree_a} -> {tree_b}] {comparison['common_class_count']} common classes across "
            f"{len(comparison['modules_common'])} common modules, {len(comparison['worse'])} worse, "
            f"{len(comparison['better'])} better, {comparison['unchanged_count']} unchanged",
            file=sys.stderr,
        )
        if args.report:
            title = args.compare_title or f"{tree_a} vs {tree_b} (library context)"
            report_path = REPO_ROOT / "docs" / "decompile-fidelity-report.md"
            existing = report_path.read_text() if report_path.is_file() else "# Decompile fidelity report\n"
            section_body = generate_compare_report(
                comparison, title=title, include_heading=False, notes=args.compare_note
            )
            updated = upsert_markdown_section(existing, f"## {title}", section_body)
            report_path.write_text(updated)
            print(f"wrote '{title}' section into {report_path}", file=sys.stderr)
        return 0

    cache_dir = Path(args.classpath_cache_dir) if args.classpath_cache_dir else Path(tempfile.gettempdir()) / "n5-fidelity-classpath-cache"
    classpath = build_classpath(cache_dir, Path(args.modules_dir), Path(args.bin_ext_dir))

    jd_cli_jar = Path(args.jd_cli_jar) if args.jd_cli_jar else None

    to_run = []
    for module in modules:
        mod_dir = organized_dir / module
        migrate_legacy_fidelity_json(mod_dir)
        if not args.force and is_module_up_to_date(
            mod_dir, primary_tree=args.tree, limit_per_module=args.limit_per_module
        ):
            print(f"[{module}] up to date, skipping", file=sys.stderr)
            continue
        to_run.append(module)

    results = []

    def _run_one(module: str) -> dict:
        # One module's unexpected failure (bad module name, corrupt recon.json,
        # decompiler crash, ...) must never silently drop every OTHER module's
        # already-computed grade or skip report generation entirely for the
        # whole batch — record the failure and keep going. It must also never
        # be rendered as an indistinguishable all-zero row in the report, or
        # silently exit 0 (R4-module-failure-masked) — see generate_report's
        # "Module failures" section and this function's caller.
        try:
            result = grade_module(
                module,
                organized_dir=organized_dir,
                classpath=classpath,
                limit=args.limit_per_module,
                jd_cli_jar=jd_cli_jar,
                primary_tree=args.tree,
                class_jobs=args.class_jobs,
                tool_server=args.tool_server,
            )
            fidelity_output_path(organized_dir / module, args.tree).write_text(
                json.dumps(result, indent=2, default=list) + "\n"
            )
            print(f"[{module}] {result['grade_counts']}", file=sys.stderr)
            return result
        except Exception as exc:  # noqa: BLE001 — deliberately broad: see comment above
            print(f"[{module}] FAILED: {exc!r}", file=sys.stderr)
            return {
                "module": module, "schema_version": SCHEMA_VERSION, "jar_sha256": None,
                "primary_tree": args.tree, "class_count": 0, "limit_per_module": args.limit_per_module,
                "grade_counts": {}, "classes": {}, "module_error": repr(exc),
            }

    if args.jobs > 1 and len(to_run) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(_run_one, to_run))
    else:
        results = [_run_one(m) for m in to_run]
    shutdown_tool_servers()

    # include already-up-to-date modules in the report too
    for module in modules:
        if module not in to_run:
            fp = fidelity_read_path(organized_dir / module, args.tree)
            if fp is not None:
                results.append(json.loads(fp.read_text()))

    failed_modules = [r["module"] for r in results if r.get("module_error")]

    if args.report:
        cross_checks = None
        if args.cross_check_sample > 0:
            cross_checks = sample_independent_cross_checks(
                results, organized_dir=organized_dir, sample_size=args.cross_check_sample
            )
        report_path = REPO_ROOT / "docs" / "decompile-fidelity-report.md"
        report_path.write_text(generate_report(results, cross_checks=cross_checks))
        print(f"wrote {report_path}", file=sys.stderr)

    if failed_modules:
        print(f"FAILED: {len(failed_modules)} module(s) raised during grading: {failed_modules}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
