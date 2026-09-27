"""
Thread Safety Scan for Module Navigator (Phase 28).

Commands:
  thread-safety <class>              Thread safety analysis for a class
  thread-scan [--module mod] [-n N]  Module-wide thread safety summary

Detects: synchronized blocks/methods, volatile fields, AtomicX types,
ReentrantLock usage, ConcurrentX collections, ThreadLocal, CountDownLatch,
Semaphore, ReadWriteLock, Executor usage.

Critical for understanding concurrency in Niagara services — the engine
is multi-threaded and services run on shared threads.

No builder needed — uses field-index + method-index + class-index on-demand.
Global scan uses indexes only (fast). Per-class scan adds source analysis.
"""

import os
import re
from collections import defaultdict


# ---------------------------------------------------------------------------
# Index loading (reuse existing loaders, on-demand cached)
# ---------------------------------------------------------------------------

def _load_field_index(base_dir):
    from module_nav_lib.fields import load_field_index
    return load_field_index(base_dir)


def _load_method_index(base_dir):
    from module_nav_lib.methods import load_method_index
    return load_method_index(base_dir)


def _load_class_index(base_dir):
    from module_nav_lib.class_search import load_class_index
    return load_class_index(base_dir)


def _load_inheritance(base_dir):
    from module_nav_lib.hierarchy import load_inheritance
    return load_inheritance(base_dir)


# ---------------------------------------------------------------------------
# Concurrency pattern definitions
# ---------------------------------------------------------------------------

ATOMIC_TYPES = frozenset([
    "AtomicInteger", "AtomicLong", "AtomicBoolean", "AtomicReference",
    "AtomicIntegerArray", "AtomicLongArray", "AtomicReferenceArray",
    "AtomicIntegerFieldUpdater", "AtomicLongFieldUpdater",
    "AtomicReferenceFieldUpdater", "AtomicStampedReference",
    "AtomicMarkableReference",
])

CONCURRENT_TYPES = frozenset([
    "ConcurrentHashMap", "ConcurrentLinkedQueue", "ConcurrentLinkedDeque",
    "ConcurrentSkipListMap", "ConcurrentSkipListSet",
    "CopyOnWriteArrayList", "CopyOnWriteArraySet",
    "BlockingQueue", "LinkedBlockingQueue", "ArrayBlockingQueue",
    "PriorityBlockingQueue", "SynchronousQueue", "DelayQueue",
    "LinkedTransferQueue", "BlockingDeque", "LinkedBlockingDeque",
])

LOCK_TYPES = frozenset([
    "ReentrantLock", "ReentrantReadWriteLock", "StampedLock",
    "ReadWriteLock", "Lock", "Condition",
])

SYNC_PRIMITIVES = frozenset([
    "CountDownLatch", "CyclicBarrier", "Semaphore", "Phaser",
    "Exchanger", "CompletableFuture", "FutureTask", "Future",
])

EXECUTOR_TYPES = frozenset([
    "ExecutorService", "ThreadPoolExecutor", "ScheduledExecutorService",
    "ScheduledThreadPoolExecutor", "ForkJoinPool", "Executors",
    "Executor",
])

THREAD_LOCAL_TYPES = frozenset([
    "ThreadLocal", "InheritableThreadLocal",
])

# Source-level regex patterns (used only in per-class analysis)
SOURCE_PATTERNS = {
    "synchronized_block": re.compile(r'\bsynchronized\s*\('),
    "synchronized_method": re.compile(
        r'\b(?:public|protected|private)?\s*synchronized\s+'
        r'(?:static\s+)?(?:\w+(?:<[^>]*>)?)\s+(\w+)\s*\('),
    "volatile_field": re.compile(r'\bvolatile\b'),
    "wait_notify": re.compile(r'\b(?:wait|notify|notifyAll)\s*\('),
    "thread_sleep": re.compile(r'Thread\.sleep\s*\('),
    "thread_interrupt": re.compile(r'\b(?:interrupt|isInterrupted|interrupted)\s*\('),
}

ALL_CONCURRENCY_TYPES = (
    ATOMIC_TYPES | CONCURRENT_TYPES | LOCK_TYPES |
    SYNC_PRIMITIVES | EXECUTOR_TYPES | THREAD_LOCAL_TYPES
)


# ---------------------------------------------------------------------------
# Fast index-only scan (for global/module-wide thread-scan)
# ---------------------------------------------------------------------------

_scan_cache = {}


def _scan_fields_for_concurrency(base_dir, module_filter=None):
    """Scan field-index for concurrency patterns (index-only, fast).

    Returns dict: class_name -> {
        module, volatile_fields, atomic_fields, concurrent_fields,
        lock_fields, sync_primitive_fields, executor_fields,
        threadlocal_fields, risk_score, risk_level
    }
    """
    cache_key = "fields_" + (module_filter or "__all__")
    if cache_key in _scan_cache:
        return _scan_cache[cache_key]

    fi = _load_field_index(base_dir)
    ci_data = _load_class_index(base_dir)

    if not fi or not ci_data:
        return {}

    fields_idx = fi.get("fields", {})
    class_fields = fi.get("class_fields", {})
    ci_classes = ci_data.get("classes", {})

    # Build module lookup
    class_module = {}
    for cname, entries in ci_classes.items():
        top = [e for e in entries if not e.get("outer_class")]
        if top:
            class_module[cname] = top[0].get("module", "?")
        elif entries:
            class_module[cname] = entries[0].get("module", "?")

    result = {}

    for cname in ci_classes:
        mod = class_module.get(cname, "?")
        if module_filter and mod != module_filter:
            continue

        volatile_fields = []
        atomic_fields = []
        concurrent_fields = []
        lock_fields = []
        sync_primitive_fields = []
        executor_fields = []
        threadlocal_fields = []

        field_names = class_fields.get(cname, [])
        for fname in field_names:
            if fname not in fields_idx:
                continue
            for entry in fields_idx[fname]:
                if entry.get("class") != cname:
                    continue
                ftype = entry.get("type", "")
                mods = entry.get("modifiers", [])

                if "volatile" in mods:
                    volatile_fields.append(fname)
                if ftype in ATOMIC_TYPES:
                    atomic_fields.append({"name": fname, "type": ftype})
                if ftype in CONCURRENT_TYPES:
                    concurrent_fields.append({"name": fname, "type": ftype})
                if ftype in LOCK_TYPES:
                    lock_fields.append({"name": fname, "type": ftype})
                if ftype in SYNC_PRIMITIVES:
                    sync_primitive_fields.append({"name": fname, "type": ftype})
                if ftype in EXECUTOR_TYPES:
                    executor_fields.append({"name": fname, "type": ftype})
                if ftype in THREAD_LOCAL_TYPES:
                    threadlocal_fields.append({"name": fname, "type": ftype})
                break

        has_any = (
            volatile_fields or atomic_fields or concurrent_fields or
            lock_fields or sync_primitive_fields or executor_fields or
            threadlocal_fields
        )
        if not has_any:
            continue

        risk_score = (
            len(volatile_fields) * 1 +
            len(atomic_fields) * 1 +
            len(concurrent_fields) * 1 +
            len(lock_fields) * 2 +
            len(sync_primitive_fields) * 2 +
            len(executor_fields) * 3 +
            len(threadlocal_fields) * 2
        )

        if risk_score >= 10:
            risk_level = "HIGH"
        elif risk_score >= 5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        result[cname] = {
            "module": mod,
            "volatile_fields": volatile_fields,
            "atomic_fields": atomic_fields,
            "concurrent_fields": concurrent_fields,
            "lock_fields": lock_fields,
            "sync_primitive_fields": sync_primitive_fields,
            "executor_fields": executor_fields,
            "threadlocal_fields": threadlocal_fields,
            "synchronized_methods": [],  # not scanned at index level
            "source_patterns": {},       # not scanned at index level
            "risk_score": risk_score,
            "risk_level": risk_level,
        }

    _scan_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# Deep per-class analysis (includes source scanning)
# ---------------------------------------------------------------------------

def _analyze_class_source(source_path):
    """Analyze a single source file for concurrency patterns.

    Returns dict of source_pattern_name -> count, plus synchronized_methods list.
    """
    source_hits = {}
    sync_methods = []

    if not source_path or not os.path.isfile(source_path):
        return source_hits, sync_methods

    try:
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception:
        return source_hits, sync_methods

    # Count synchronized blocks
    sb = SOURCE_PATTERNS["synchronized_block"].findall(source)
    if sb:
        source_hits["synchronized_block"] = len(sb)

    # Find synchronized methods
    for m in SOURCE_PATTERNS["synchronized_method"].finditer(source):
        sync_methods.append(m.group(1))

    # wait/notify
    wn = SOURCE_PATTERNS["wait_notify"].findall(source)
    if wn:
        source_hits["wait_notify"] = len(wn)

    # Thread.sleep
    ts = SOURCE_PATTERNS["thread_sleep"].findall(source)
    if ts:
        source_hits["thread_sleep"] = len(ts)

    # interrupt
    ti = SOURCE_PATTERNS["thread_interrupt"].findall(source)
    if ti:
        source_hits["thread_interrupt"] = len(ti)

    return source_hits, sync_methods


def _get_class_source_path(base_dir, class_name):
    """Get source file path for a class."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        return ""
    ci_classes = ci_data.get("classes", {})
    source_root = ci_data.get("_meta", {}).get("source", "")

    entries = ci_classes.get(class_name, [])
    top = [e for e in entries if not e.get("outer_class")]
    if top and source_root:
        rel_path = top[0].get("path", "")
        if rel_path:
            return os.path.join(source_root, rel_path)
    return ""


# ---------------------------------------------------------------------------
# thread-safety <class>
# ---------------------------------------------------------------------------

def cmd_thread_safety(base_dir, class_name):
    """Show thread safety details for a specific class."""
    ci_data = _load_class_index(base_dir)
    if not ci_data:
        print("  ERROR: class-index.json not found.")
        return

    ci_classes = ci_data.get("classes", {})

    # Case-insensitive lookup
    actual_name = class_name
    if class_name not in ci_classes:
        lower = class_name.lower()
        for k in ci_classes:
            if k.lower() == lower:
                actual_name = k
                break
        else:
            print("  Class '{}' not found.".format(class_name))
            return

    entries = ci_classes[actual_name]
    top = [e for e in entries if not e.get("outer_class")]
    if top:
        module = top[0].get("module", "?")
    elif entries:
        module = entries[0].get("module", "?")
    else:
        module = "?"

    # Field-based analysis (from indexes)
    field_info = _scan_fields_for_concurrency(base_dir).get(actual_name)

    # Source-based analysis (per-class, fast)
    src_path = _get_class_source_path(base_dir, actual_name)
    source_hits, sync_methods = _analyze_class_source(src_path)

    # Merge results
    has_field_info = field_info is not None
    has_source_info = bool(source_hits or sync_methods)

    print("")
    print("  THREAD SAFETY: {}".format(actual_name))
    print("  " + "=" * 55)
    print("  Module: {}".format(module))

    if not has_field_info and not has_source_info:
        print("")
        print("  No concurrency patterns detected.")
        print("  (No synchronized, volatile, Atomic, Lock, or Concurrent usage found)")
        print("")
        return

    # Calculate combined risk
    risk_score = 0
    if field_info:
        risk_score = field_info["risk_score"]
    risk_score += len(sync_methods) * 1
    risk_score += source_hits.get("synchronized_block", 0) * 1
    risk_score += source_hits.get("wait_notify", 0) * 3

    if risk_score >= 10:
        risk_level = "HIGH"
    elif risk_score >= 5:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    print("  Risk: {}  (score: {})".format(risk_level, risk_score))
    print("")

    # Synchronized methods
    if sync_methods:
        print("  SYNCHRONIZED METHODS ({}):" .format(len(sync_methods)))
        for m in sync_methods:
            print("    synchronized {}()".format(m))
        print("")

    # Synchronized blocks
    sync_blocks = source_hits.get("synchronized_block", 0)
    if sync_blocks:
        print("  SYNCHRONIZED BLOCKS: {}".format(sync_blocks))
        print("")

    if field_info:
        if field_info["volatile_fields"]:
            print("  VOLATILE FIELDS ({}):" .format(len(field_info["volatile_fields"])))
            for f in field_info["volatile_fields"]:
                print("    volatile {}".format(f))
            print("")

        if field_info["atomic_fields"]:
            print("  ATOMIC FIELDS ({}):" .format(len(field_info["atomic_fields"])))
            for f in field_info["atomic_fields"]:
                print("    {} {}".format(f["type"], f["name"]))
            print("")

        if field_info["concurrent_fields"]:
            print("  CONCURRENT COLLECTIONS ({}):" .format(len(field_info["concurrent_fields"])))
            for f in field_info["concurrent_fields"]:
                print("    {} {}".format(f["type"], f["name"]))
            print("")

        if field_info["lock_fields"]:
            print("  LOCK FIELDS ({}):" .format(len(field_info["lock_fields"])))
            for f in field_info["lock_fields"]:
                print("    {} {}".format(f["type"], f["name"]))
            print("")

        if field_info["sync_primitive_fields"]:
            print("  SYNC PRIMITIVES ({}):" .format(len(field_info["sync_primitive_fields"])))
            for f in field_info["sync_primitive_fields"]:
                print("    {} {}".format(f["type"], f["name"]))
            print("")

        if field_info["executor_fields"]:
            print("  EXECUTOR FIELDS ({}):" .format(len(field_info["executor_fields"])))
            for f in field_info["executor_fields"]:
                print("    {} {}".format(f["type"], f["name"]))
            print("")

        if field_info["threadlocal_fields"]:
            print("  THREADLOCAL FIELDS ({}):" .format(len(field_info["threadlocal_fields"])))
            for f in field_info["threadlocal_fields"]:
                print("    {} {}".format(f["type"], f["name"]))
            print("")

    # wait/notify
    wn = source_hits.get("wait_notify", 0)
    if wn:
        print("  WAIT/NOTIFY CALLS: {}".format(wn))
        print("")

    # Thread patterns
    thread_sleep = source_hits.get("thread_sleep", 0)
    thread_int = source_hits.get("thread_interrupt", 0)
    if thread_sleep or thread_int:
        print("  THREAD USAGE:")
        if thread_sleep:
            print("    Thread.sleep() calls: {}".format(thread_sleep))
        if thread_int:
            print("    interrupt calls: {}".format(thread_int))
        print("")

    if src_path:
        print("  Source: {}".format(src_path))
        print("")


# ---------------------------------------------------------------------------
# thread-scan [--module mod] [-n N]
# ---------------------------------------------------------------------------

def cmd_thread_scan(base_dir, module_filter=None, limit=50):
    """Scan for thread safety patterns across classes (index-only, fast)."""
    thread_map = _scan_fields_for_concurrency(base_dir, module_filter=module_filter)
    if not thread_map:
        if module_filter:
            print("  No concurrency patterns found in module '{}'.".format(module_filter))
        else:
            print("  No concurrency patterns found.")
        return

    total = len(thread_map)
    by_risk = defaultdict(list)
    by_module = defaultdict(int)
    total_volatile = 0
    total_atomic = 0
    total_concurrent = 0
    total_locks = 0
    total_executors = 0
    total_threadlocal = 0
    total_sync_primitives = 0

    for cname, info in thread_map.items():
        by_risk[info["risk_level"]].append(cname)
        by_module[info["module"]] += 1
        total_volatile += len(info["volatile_fields"])
        total_atomic += len(info["atomic_fields"])
        total_concurrent += len(info["concurrent_fields"])
        total_locks += len(info["lock_fields"])
        total_executors += len(info["executor_fields"])
        total_threadlocal += len(info["threadlocal_fields"])
        total_sync_primitives += len(info["sync_primitive_fields"])

    scope = module_filter if module_filter else "ALL modules"
    print("")
    print("  THREAD SAFETY SCAN: {}".format(scope))
    print("  " + "=" * 55)
    print("")
    print("  Classes with concurrency: {:>6,}".format(total))
    print("  Modules with concurrency: {:>6,}".format(len(by_module)))
    print("")
    print("  FIELD-LEVEL PATTERNS:")
    print("    Volatile fields:       {:>6,}".format(total_volatile))
    print("    Atomic fields:         {:>6,}".format(total_atomic))
    print("    Concurrent colls:      {:>6,}".format(total_concurrent))
    print("    Lock fields:           {:>6,}".format(total_locks))
    print("    Sync primitives:       {:>6,}".format(total_sync_primitives))
    print("    Executor fields:       {:>6,}".format(total_executors))
    print("    ThreadLocal fields:    {:>6,}".format(total_threadlocal))
    print("")
    print("  (Use 'thread-safety <class>' for synchronized block/method analysis)")
    print("")

    # Risk breakdown
    print("  RISK BREAKDOWN:")
    for level in ["HIGH", "MEDIUM", "LOW"]:
        count = len(by_risk.get(level, []))
        print("    {:8s} {:>6,}".format(level, count))
    print("")

    # Top modules
    top_modules = sorted(by_module.items(), key=lambda x: x[1], reverse=True)
    print("  TOP MODULES ({} with concurrency):" .format(len(top_modules)))
    for mod, count in top_modules[:15]:
        print("    {:40s} {:>4,} classes".format(mod, count))
    if len(top_modules) > 15:
        print("    ... and {} more modules".format(len(top_modules) - 15))
    print("")

    # Top HIGH-risk classes
    high_risk = by_risk.get("HIGH", [])
    if high_risk:
        high_sorted = sorted(high_risk,
                             key=lambda c: thread_map[c]["risk_score"],
                             reverse=True)
        show = high_sorted[:limit]
        print("  HIGH RISK CLASSES ({} total, showing {}):".format(
            len(high_risk), len(show)))
        for cname in show:
            info = thread_map[cname]
            parts = []
            vf = len(info["volatile_fields"])
            af = len(info["atomic_fields"])
            cf = len(info["concurrent_fields"])
            lk = len(info["lock_fields"])
            ex = len(info["executor_fields"])
            tl = len(info["threadlocal_fields"])
            sp = len(info["sync_primitive_fields"])

            if vf:
                parts.append("{}vol".format(vf))
            if af:
                parts.append("{}atomic".format(af))
            if cf:
                parts.append("{}conc".format(cf))
            if lk:
                parts.append("{}lock".format(lk))
            if sp:
                parts.append("{}sync".format(sp))
            if ex:
                parts.append("{}exec".format(ex))
            if tl:
                parts.append("{}tl".format(tl))

            detail = ", ".join(parts) if parts else "patterns"
            print("    {:40s} {:12s} score:{:>3} ({})".format(
                cname, info["module"], info["risk_score"], detail))
        print("")
    else:
        print("  No HIGH risk classes found.")
        print("")
