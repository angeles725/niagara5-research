#!/usr/bin/env python3
"""B121 step 3b: compare Vineflower 1.12.0 output WITH the bundled Kotlin plugin (--kt-enable=true, .kt files)
against the same run WITHOUT it (--kt-enable=false, .java files), and against the corpus's existing
organized/_etc-m2/<jar>/vineflower2 tree. Prints one TSV: metric x jar x tree."""
import os, re, sys, hashlib, glob, collections
ROOT = "/home/cristian/niagara5-research/organized"
EV = ROOT + "/_evidence/b121"
JARS = {"n-plugin": "n-plugin-5.0.54.9.2", "n-conv-plugin": "n-conv-plugin-5.0.54.9.2",
        "settings": "settings-5.0.9.8.14", "utils": "utils-5.0.7.8.14"}
TREES = {"vf-kt(fresh)": lambda j: f"{EV}/vf-kt/{j}", "vf-java(fresh,--kt-enable=false)": lambda j: f"{EV}/vf-java/{j}",
         "corpus-v2": lambda j: f"{ROOT}/_etc-m2/{JARS[j]}/vineflower2"}
PATS = collections.OrderedDict([
    ("couldnt_be_decompiled", re.compile(r"Couldn't be decompiled")),
    ("unable_to_decompile_class", re.compile(r"Unable to decompile class")),
    ("unrepresentable", re.compile(r"<unrepresentable>")),
    ("Intrinsics_lines", re.compile(r"\bIntrinsics\.")),
    ("dollar_default_calls", re.compile(r"\$default\b")),
    ("dollar_this_names", re.compile(r"\$this\$")),
    ("dollar_i_f_dollar_names", re.compile(r"\$i\$f\$")),
    ("dollar_i_a_dollar_names", re.compile(r"\$i\$a\$")),
    ("synthetic_varN_names", re.compile(r"\bvar\d+\b")),
    ("i_f_marker_name_bound_to_NON_int_local", re.compile(r"^\s*(?!int\b|long\b)[A-Za-z_][\w<>\[\], ?]*\s\$i\$[fa]\$[\w$-]+\s*=", re.M)),
    ("i_f_marker_name_bound_to_int_local", re.compile(r"^\s*int\s\$i\$[fa]\$[\w$-]+\s*=", re.M)),
    ("unrepresentable_INSTANCE_lambda", re.compile(r"<unrepresentable>(\.INSTANCE|::)")),
    ("kt_fun_named_like_class_constructor", re.compile(r"^\s*open fun ([A-Z]\w*)\(", re.M)),
    ("Companion_refs", re.compile(r"\bCompanion\b")),
    ("INSTANCE_refs", re.compile(r"\bINSTANCE\b")),
    ("jetbrains_NotNull_Nullable", re.compile(r"@(NotNull|Nullable)\b")),
    ("kotlin_nullable_types_'?'", re.compile(r"[A-Za-z>\]]\?[ ,)=\n{]")),
    ("kotlin_default_param_'= '_in_fun", re.compile(r"\bfun\b[^\n{]*\([^)\n]*=[^)\n]*\)")),
    ("kotlin_fun_keyword", re.compile(r"\bfun\b")),
    ("java_static_final_field_lines", re.compile(r"\bstatic final\b")),
])

def files(d):
    out = []
    for r, _d, fs in os.walk(d):
        for f in fs:
            if f.endswith((".kt", ".java")):
                out.append(os.path.join(r, f))
    return out

def main():
    w = sys.stdout.write
    w("jar\ttree\tmetric\tvalue\n")
    for j in JARS:
        base = {}
        for t, fn in TREES.items():
            d = fn(j)
            fs = files(d)
            txt = {}
            for f in fs:
                txt[os.path.relpath(f, d)] = open(f, encoding="utf8", errors="replace").read()
            base[t] = txt
            w(f"{j}\t{t}\tfiles\t{len(fs)}\n")
            w(f"{j}\t{t}\tfiles_kt\t{sum(1 for f in fs if f.endswith('.kt'))}\n")
            w(f"{j}\t{t}\tfiles_java\t{sum(1 for f in fs if f.endswith('.java'))}\n")
            w(f"{j}\t{t}\tlines\t{sum(v.count(chr(10)) for v in txt.values())}\n")
            for m, p in PATS.items():
                w(f"{j}\t{t}\t{m}\t{sum(len(p.findall(v)) for v in txt.values())}\n")
        # byte-equality: fresh kt vs corpus v2 (same flags subset?)
        a, b = base["vf-kt(fresh)"], base["corpus-v2"]
        common = set(a) & set(b)
        same = sum(1 for k in common if a[k] == b[k])
        w(f"{j}\tfresh-kt vs corpus-v2\tfiles_in_both\t{len(common)}\n")
        w(f"{j}\tfresh-kt vs corpus-v2\tbyte_identical_files\t{same}\n")
        w(f"{j}\tfresh-kt vs corpus-v2\tfiles_only_fresh\t{len(set(a) - set(b))}\n")
        w(f"{j}\tfresh-kt vs corpus-v2\tfiles_only_corpus\t{len(set(b) - set(a))}\n")

main()
