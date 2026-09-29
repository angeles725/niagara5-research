#!/usr/bin/env python3
"""B120: mechanical reconstructions of pattern-switch methods, verified by javac-25 recompile + bytecode compare.

Each CASE starts from a Vineflower tree file (v2 unless noted) and applies a small, explicit patch list:
  * `sub`   regex substitutions (rename an unused binding to the unnamed pattern `_`, etc.),
  * `lines` replace an inclusive 1-based line range (used to turn the pseudo-Java restart loop into a
            guarded pattern switch, or to neutralise an UNRELATED method that blocks javac),
  * `shim`  pin SecurityUtil.doPrivileged overloads (see grade_sites.SHIM_SRC; B116 defect family).
The patched file is compiled with javac 25; the target method's NORMALIZED bytecode (tools/n5-fidelity.py
functions via grade_sites) is compared with the shipped class, bootstrap-method label lists injected.
Result per case: exact / mismatch(+effect diff).  The reconstructed METHOD text and the multi-line patch
blocks (patch-blocks.json) live OUTSIDE git in organized/_evidence/b120/ (sha256 in artifacts.sha256).
Usage: reconstruct.py --scratch DIR [--out recon-results.json]
"""
import argparse, json, re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import grade_sites as g


CASES = [
    {"name": "PlatformStationManager.createStation", "mod": "platform", "tree": "vineflower2",
     "top": "com/tridium/platform/daemon/PlatformStationManager", "targets": ["com/tridium/platform/daemon/PlatformStationManager"],
     "method": "createStation",
     # v2 file: 65-66 = `Version pwChars = bogVersion; byte var14 = 0;`, 68 = `while (true) {`, 69-106 = pseudo switch,
     # 138 = the loop's closing brace.  The switch replaces 65-106; the while-wrapper braces go.
     # 108-135 is `if (isMinNiagaraVersion(N4)) {...return result;}` + `throw AX host`; the shipped code is
     # `if (min N4) {keyring/passphrase checks} else { throw AX host }` followed by the transfer (bytecode: goto over the throw).
     "patches": [{"lines": [135, 138, ""]},
                 {"lines": [123, 123, "@PSM_ELSE"]},
                 {"lines": [65, 106, "@PSM_SWITCH"]}]},
    {"name": "EntitlementApi.sendRequestMessageAndHandleResponse", "mod": "_bin-ext/nre", "tree": "vineflower2",
     "top": "com/tridium/nre/subscription/EntitlementApi", "targets": ["com/tridium/nre/subscription/EntitlementApi"],
     "method": "sendRequestMessageAndHandleResponse",
     "patches": [{"sub": [r"case (SocketTimeoutException|NoRouteToHostException|UnknownHostException) var\d+:", r"case \1 _:"]}]},
    {"name": "Introspector.getModule", "mod": "baja", "tree": "vineflower2",
     "top": "com/tridium/sys/schema/Introspector", "targets": ["com/tridium/sys/schema/Introspector"], "method": "getModule",
     "patches": [{"sub": [r"case BootstrapClassLoader var\d+ ->", r"case BootstrapClassLoader _ ->"]}]},
    {"name": "BWbProfile.dumpMenu", "mod": "workbench", "tree": "vineflower2",
     "top": "niagara/workbench/BWbProfile", "targets": ["niagara/workbench/BWbProfile"], "method": "dumpMenu", "system": True,
     # the BMenuItem arm: bytecode is `if (x instanceof Tool) continue; if (x instanceof SideBar) continue; println` (ifeq/goto pairs);
     # Vineflower folds them into one `!a && !b` condition (same effects, different branch layout).
     "patches": [{"sub": [r"case BSeparator var\d+:", r"case BSeparator _:"]},
                 {"sub": [r"if \(!\(menuItem\.getCommand\(\) instanceof WbCommands\.ToolCommand\) && !\(menuItem\.getCommand\(\) instanceof WbCommands\.SideBarCommand\)\) \{\s*System\.out\.println\(itemIndent \+ item\.getName\(\)\);\s*\}",
                          "@MENU_ITEM"]}]},
    # B116-family blockers that sit in OTHER members of the same file; the switch method is not touched except
    # the duplicate-local rename in loadType's inner string switch (colon-form arms share one scope).
    {"name": "BBrokerChannel.loadType(type switch)", "mod": "fox", "tree": "vineflower2",
     "top": "com/tridium/fox/sys/broker/BBrokerChannel", "targets": ["com/tridium/fox/sys/broker/BBrokerChannel"],
     "method": "loadType", "match_desc": "Lniagara/io/ValueDocDecoder;", "shim": "psea",
     "patches": [{"sub": [r"^import com\.tridium\.sys\.module\.ModuleSetClassLoader\.LoadedModule;", "", 1]},
                 {"sub": [r"\bLoadedModule candidateLoadedModule", "var candidateLoadedModule", 1]},
                 {"sub_after": ["case \"a\":", r"\bdefaultValue\b", "defaultValueA"]},
                 {"sub_after": ["case \"a\":", r"\bdefaultValueDecoder\b", "defaultValueDecoderA"]},
                 {"sub": [r"case SimpleType var\d+:", r"case SimpleType _:"]}]},
    {"name": "BJettyWebServer.walkContextHandler", "mod": "jetty", "tree": "vineflower2",
     "top": "com/tridium/jetty/BJettyWebServer", "targets": ["com/tridium/jetty/BJettyWebServer"], "method": "walkContextHandler",
     "patches": [{"sub": [r"^import niagara\.web\.BWebServer\.ServerState;", "", 1]},
                 {"sub": [r"^import org\.eclipse\.jetty\.server\.ServerConnector\.ServerConnectorManager;", "", 1]},
                 {"sub": [r"ServerState\.started\.name\(\)", '"started"']},
                 {"neutralise_method": "newSelectorManager"}]},
]


OUT = Path("/home/cristian/niagara5-research/organized/_evidence/b120")   # gitignored: reconstructed Tridium source stays out of git
BLOCKS = json.loads((OUT / "patch-blocks.json").read_text()) if (OUT / "patch-blocks.json").exists() else {}


def blk(x):
    return BLOCKS[x[1:]] if isinstance(x, str) and x.startswith("@") else x


def find_multiline_method(text, name):
    """Fallback for signatures spanning several lines: first line with `name(` then brace-match from the first `{`."""
    ls = text.split("\n")
    for i, l in enumerate(ls):
        if re.search(r"\b" + re.escape(name) + r"\s*\(", l) and not l.strip().startswith(("return", "if", "for", "while", "switch", "throw", "this.", "super.")):
            depth, started = 0, False
            for j in range(i, len(ls)):
                for ch in ls[j]:
                    if ch == "{":
                        depth, started = depth + 1, True
                    elif ch == "}":
                        depth -= 1
                if started and depth <= 0:
                    return [(i + 1, j + 1)]
    return []


def method_span(lines, name, nth=0):
    txt = "\n".join(lines)
    spans = g.method_line_spans(txt, name)
    return spans[nth] if spans else None


def apply_patches(text, patches, method):
    lines = text.split("\n")
    # bottom-up line-range replacements first (line numbers refer to the ORIGINAL tree file)
    for p in sorted([p for p in patches if "lines" in p], key=lambda p: -p["lines"][0]):
        a, b, new = p["lines"]
        new = blk(new)
        lines[a - 1:b] = new.rstrip("\n").split("\n") if new else []
    text = "\n".join(lines)
    for p in patches:
        if "sub" in p:
            pat, rep, *cnt = p["sub"]
            rep = blk(rep)
            text = re.sub(pat, rep, text, count=cnt[0] if cnt else 0, flags=re.M)
        elif "sub_after" in p:
            marker, pat, rep = p["sub_after"]
            i = text.index(marker)
            j = text.index("case \"t\":", i)
            text = text[:i] + re.sub(pat, rep, text[i:j]) + text[j:]
        elif "neutralise_method" in p:
            spans = g.method_line_spans(text, p["neutralise_method"])
            ls = text.split("\n")
            a, b = spans[0]
            ls[a:b - 1] = ["      throw new Error();"]
            text = "\n".join(ls)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "recon-results.json"))
    a = ap.parse_args()
    cp = g.classpath(Path(a.scratch) / "cp")
    g.SHIM[0] = g.build_shim(a.scratch, cp)
    results = []
    for c in CASES:
        src = g.ORG / c["mod"] / c["tree"] / (c["top"] + ".java")
        text = apply_patches(src.read_text(), c["patches"], c["method"])
        d = Path(a.scratch) / "recon" / c["name"].replace("(", "_").replace(")", "_").replace(" ", "_")
        shutil.rmtree(d, ignore_errors=True)
        pf = d / "src" / (c["top"] + ".java")
        pf.parent.mkdir(parents=True, exist_ok=True)
        res = {"name": c["name"], "tree": c["tree"], "top": c["top"], "variant": None}
        outc = d / "out"
        ok, errs, used = False, [], None
        for variant in ([None] + (["pea", "pa", "psea"] if "doPrivileged" in text else [])):
            body = text if variant is None else text.replace("SecurityUtil.doPrivileged(", f"b120shim.B120Shim.{variant}(")
            if c.get("shim") and variant is None and "doPrivileged" in text:
                continue
            pf.write_text(body)
            shutil.rmtree(outc, ignore_errors=True)
            ok, errs = g.compile_tree(pf, (g.SHIM[0] + ":" if variant else "") + cp, outc, system=g.SYSTEM_JRE if c.get("system") else None)
            if ok:
                used = variant
                break
        res["compiled"], res["shim"] = ok, used
        if not ok:
            res["errors"] = [re.sub(r".*/scratchpad/", "", e) for e in errs]
            results.append(res)
            continue
        res["methods"] = {}
        for t in c["targets"]:
            sp, _ = g.parsed(g.ORG / c["mod"] / "extracted" / (t + ".class"))
            rp, _ = g.parsed(outc / (t + ".class"))
            for k in g.switch_methods(sp):
                if k[0] != c["method"] or c.get("match_desc") and c["match_desc"] not in k[1]:
                    continue
                A, B = sp["methods"][k], rp["methods"].get(k)
                if B is None:
                    res["methods"][k[0] + k[1]] = {"verdict": "missing"}
                    continue
                bcode = [re.sub(r"b120shim/B120Shim\.(pea|pa|psea):", "niagara/nre/util/SecurityUtil.doPrivileged:", l) for l in B["code"]]
                exact = A["code"] == bcode and A["flags"] == B["flags"] and A.get("exception_table", []) == B.get("exception_table", [])
                if exact:
                    res["methods"][k[0] + k[1]] = {"verdict": "exact"}
                else:
                    kind, first, ed = g.classify_diff(A["code"], bcode)
                    res["methods"][k[0] + k[1]] = {"verdict": "mismatch", "kind": kind, "first_diff": first, "effect_diff": ed}
        # method text
        sp_ = g.method_line_spans(pf.read_text(), c["method"]) or find_multiline_method(pf.read_text(), c["method"])
        if sp_:
            ls = pf.read_text().split("\n")
            OUT.mkdir(parents=True, exist_ok=True)
            snippet = "\n".join(ls[sp_[0][0] - 1:sp_[0][1]])
            (OUT / (c["name"].replace("(", "_").replace(")", "_").replace(" ", "_") + ".java.txt")).write_text(
                f"// B120 reconstruction (patched {c['tree']} tree, verified by javac-25 recompile + bytecode compare; see recon-results.json)\n" + snippet + "\n")
        results.append(res)
    json.dump(results, open(a.out, "w"), indent=1)
    for r in results:
        print(r["name"], "compiled" if r["compiled"] else "NO-COMPILE", r.get("shim") or "", {k: v["verdict"] for k, v in r.get("methods", {}).items()}, r.get("errors", [])[:3])


if __name__ == "__main__":
    main()
