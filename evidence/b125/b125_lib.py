"""Shared paths and helpers for the B125 scripts (Kotlin-plugin wall sites)."""
import importlib.util, hashlib, os, re, sys

CORPUS = os.environ.get("N5_CORPUS", "/home/cristian/niagara5-research")
ORG = f"{CORPUS}/organized"
EV = f"{ORG}/_evidence/b125"
B121 = f"{ORG}/_evidence/b121"
SNAP = f"{EV}/tools-snapshot"          # frozen copies of tools/n5-fidelity.py + tools/n5_canon.py (sha256 in tools-snapshot.sha256)
JAVA_BIN = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin"
JARS = {"n-plugin": "n-plugin-5.0.54.9.2", "n-conv-plugin": "n-conv-plugin-5.0.54.9.2",
        "settings": "settings-5.0.9.8.14", "utils": "utils-5.0.7.8.14"}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def load_fidelity():
    """Import the snapshot of tools/n5-fidelity.py (imports n5_canon from the same dir); nothing is modified."""
    sys.path.insert(0, SNAP)
    spec = importlib.util.spec_from_file_location("n5fid", f"{SNAP}/n5-fidelity.py")
    m = importlib.util.module_from_spec(spec); sys.modules["n5fid"] = m
    spec.loader.exec_module(m)
    return m

def extracted(jar):  # shipped class files of a jar
    return f"{ORG}/_etc-m2/{JARS[jar]}/extracted"
