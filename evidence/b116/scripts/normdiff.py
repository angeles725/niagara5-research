#!/usr/bin/env python3
"""B116 Part B text differential: docSource original vs corpus decompile (Vineflower / CFR fallback).

Members (fields, methods, ctors, initializers, nested types flattened with a path prefix) are aligned by
signature; each aligned member pair is compared at cumulative normalization stages. The FIRST stage at
which the pair becomes token-equal names the loss class that explains the whole difference; pairs that
never become equal are 'residual-structural' (and are then judged by the bytecode oracle, see semdiff.py).

Stages (cumulative):
  S0 lexical      comments, whitespace, package, imports stripped
  S1 annotations  all annotations removed (source-retention ones are unrecoverable; CLASS/RUNTIME ones are
                  rendered but with constant-folded element values)
  S2 qualification  'this.' / 'Outer.this.' removed; own-class / outer-class qualifiers removed;
                  package-qualified names reduced to simple names; explicit '<init>' super() dropped
  S3 modifiers/generics  'final' on locals/params removed; generic type arguments removed; diamond normalized;
                  redundant parentheses around simple operands removed
  S4 literals     numeric literals canonicalized by value (radix, underscores, suffix, exponent form);
                  char literals -> int code; string escapes canonicalized
  S5 constants    compile-time constant references (incl. static imports) substituted by value, then
                  constant expressions folded (javac JLS 15.29 semantics for + - * / % | & ^ << >> >>> ~)
  S6 local-names  local-variable / parameter / pattern / lambda-parameter identifiers alpha-renamed
  S7 braces/stmts  optional braces around single statements, 'else' after return, ++/--/+= spelling unified
"""
import os, sys, re, json
from collections import Counter, defaultdict

O = '/home/cristian/niagara5-research/organized'
S = os.path.dirname(os.path.abspath(__file__))
CONSTS = None

TOK = re.compile(r'''
 (?P<tb>"""(?:[^\\]|\\.)*?""")
|(?P<s>"(?:[^"\\\n]|\\.)*")
|(?P<c>'(?:[^'\\\n]|\\.)+')
|(?P<lc>//[^\n]*)
|(?P<bc>/\*.*?\*/)
|(?P<num>(?:0[xX][0-9a-fA-F_]+[lL]?)|(?:0[bB][01_]+[lL]?)|(?:(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?[fFdDlL]?))
|(?P<id>[A-Za-z_$][\w$]*)
|(?P<op>>>>=|<<=|>>=|\.\.\.|->|::|\+\+|--|&&|\|\||[=!<>+\-*/%&|^]=|[{}()\[\];,.@=<>!~?:+\-*/&|^%])
|(?P<ws>\s+)
''', re.S | re.X)

JAVA_KW = set('''abstract assert boolean break byte case catch char class const continue default do double else enum extends
final finally float for goto if implements import instanceof int interface long native new package private protected public
return short static strictfp super switch synchronized this throw throws transient try void volatile while var yield record
sealed permits non true false null when'''.split())
PRIMS = {'boolean', 'byte', 'char', 'short', 'int', 'long', 'float', 'double', 'void', 'var'}


def lex(src):
    out = []
    for m in TOK.finditer(src):
        k = m.lastgroup
        if k in ('ws', 'lc', 'bc'): continue
        out.append((k, m.group()))
    return out


def unesc(s):
    try: return bytes(s, 'utf-8', 'surrogatepass').decode('unicode_escape', 'surrogatepass') if '\\' in s else s
    except Exception: return s


def strip_header(toks):
    """drop package/import statements; return (toks, static_imports{name: Class}, imports{Simple: fqcn})"""
    out = []; i = 0; simp = {}; stat = {}
    while i < len(toks):
        if toks[i][1] in ('package', 'import') and (i == 0 or toks[i - 1][1] in (';', '}')):
            j = i
            while toks[j][1] != ';': j += 1
            body = [t[1] for t in toks[i + 1:j]]
            if toks[i][1] == 'import':
                if body and body[0] == 'static':
                    name = body[-1]; cls = ''.join(body[1:-2])
                    stat[name] = cls
                else:
                    fq = ''.join(body); simp[fq.split('.')[-1]] = fq
            i = j + 1; continue
        out.append(toks[i]); i += 1
    return out, stat, simp


def drop_annotations(toks):
    out = []; i = 0
    while i < len(toks):
        if toks[i][1] == '@' and i + 1 < len(toks) and toks[i + 1][1] != 'interface':
            j = i + 2
            while j + 1 < len(toks) and toks[j][1] == '.' : j += 2
            if j < len(toks) and toks[j][1] == '(':
                d = 0
                while True:
                    if toks[j][1] == '(': d += 1
                    elif toks[j][1] == ')': d -= 1
                    j += 1
                    if d == 0: break
            i = j; continue
        out.append(toks[i]); i += 1
    return out


def class_names(toks):
    s = set()
    for i, t in enumerate(toks):
        if t[1] in ('class', 'interface', 'enum', 'record') and i + 1 < len(toks) and toks[i + 1][0] == 'id' and (i == 0 or toks[i - 1][1] != '.'):
            s.add(toks[i + 1][1])
    return s


def qualify_norm(toks, own):
    out = []
    i = 0
    while i < len(toks):
        t = toks[i]
        # this. / Outer.this.
        if t[1] == 'this' and i + 1 < len(toks) and toks[i + 1][1] == '.' and (i == 0 or toks[i - 1][1] != '.'):
            i += 2; continue
        if t[0] == 'id' and t[1] in own and i + 3 < len(toks) and toks[i + 1][1] == '.' and toks[i + 2][1] == 'this' and toks[i + 3][1] == '.':
            i += 4; continue
        # package-qualified name a.b.C -> C  (lowercase segments followed by Capitalized)
        if t[0] == 'id' and t[1][:1].islower() and t[1] not in JAVA_KW and (i == 0 or toks[i - 1][1] not in ('.',)):
            j = i; segs = []
            while j + 2 < len(toks) and toks[j][0] == 'id' and toks[j][1][:1].islower() and toks[j + 1][1] == '.' and toks[j + 2][0] == 'id':
                segs.append(toks[j][1]); j += 2
            if segs and toks[j][1][:1].isupper() and len(segs) >= 1 and not (i > 0 and toks[i - 1][0] == 'id'):
                # only treat as package if the chain is followed by a Capitalized identifier
                i = j; continue
        # Type.Type (nested type reference) -> last segment; statically-imported member qualifier dropped
        if t[0] == 'id' and re.fullmatch(r'[A-Z]\w*[a-z]\w*', t[1]) and i + 2 < len(toks) and toks[i + 1][1] == '.' and toks[i + 2][0] == 'id' and re.fullmatch(r'[A-Z]\w*[a-z]\w*', toks[i + 2][1]) and (i == 0 or toks[i - 1][1] != '.'):
            i += 2; continue
        if t[0] == 'id' and t[1][:1].isupper() and i + 3 < len(toks) and toks[i + 1][1] == '.' and toks[i + 2][1] in STATICS and (i == 0 or toks[i - 1][1] != '.'):
            i += 2; continue
        # Own.X / Outer.Inner qualifiers: drop 'Own.' when Own is a class declared in this file
        if t[0] == 'id' and t[1] in own and i + 2 < len(toks) and toks[i + 1][1] == '.' and toks[i + 2][0] == 'id' and toks[i + 2][1] not in ('class', 'this', 'super', 'new') and (i == 0 or toks[i - 1][1] != '.'):
            i += 2; continue
        out.append(t); i += 1
    # drop explicit 'super();' at ctor start
    res = []; i = 0
    while i < len(out):
        if out[i][1] == 'super' and i + 3 < len(out) and out[i + 1][1] == '(' and out[i + 2][1] == ')' and out[i + 3][1] == ';' and (i == 0 or out[i - 1][1] in ('{', ';', '}')):
            i += 4; continue
        res.append(out[i]); i += 1
    return res


def generics_final_norm(toks):
    out = []; i = 0
    while i < len(toks):
        t = toks[i]
        if t[1] == 'final' and i + 1 < len(toks) and (toks[i + 1][0] == 'id'):
            # keep 'final' on fields/classes? we cannot tell reliably at token level; drop everywhere
            i += 1; continue
        if t[1] == '<' and i > 0 and (toks[i - 1][0] == 'id' and (toks[i - 1][1][:1].isupper() or toks[i - 1][1] in ('new',)) or toks[i - 1][1] in ('.',)):
            # try to match a generic argument list
            d = 0; j = i; ok = True
            while j < len(toks):
                v = toks[j][1]
                if v == '<': d += 1
                elif v == '>': d -= 1
                elif v == '>>': d -= 2
                elif v == '>>>': d -= 3
                elif v in ('?', ',', '.', '[', ']', 'extends', 'super', '&') or toks[j][0] == 'id': pass
                else: ok = False; break
                j += 1
                if d <= 0: break
            if ok and d == 0:
                i = j; continue
        # generic method type args before a call:  <T>foo(  or .<T>foo(
        out.append(t); i += 1
    # redundant parens around a single identifier/literal
    res = []; i = 0
    while i < len(out):
        if out[i][1] == '(' and i + 2 < len(out) and out[i + 2][1] == ')' and out[i + 1][0] in ('id', 'num', 's', 'c') and \
                not (i > 0 and (out[i - 1][0] == 'id' or out[i - 1][1] in (')', ']', '>'))) and not (i + 3 < len(out) and (out[i + 3][0] in ('id', 'num', 's', 'c') or out[i + 3][1] == '(')):
            res.append(out[i + 1]); i += 3; continue
        res.append(out[i]); i += 1
    return res


def numval(s):
    t = s.replace('_', '')
    low = t.lower()
    try:
        if low.startswith('0x') and not ('.' in low or 'p' in low):
            v = int(low.rstrip('l'), 16)
            if not low.endswith('l') and v >= 2 ** 31: v -= 2 ** 32
            if low.endswith('l') and v >= 2 ** 63: v -= 2 ** 64
            return ('I', v)
        if low.startswith('0b'):
            v = int(low[2:].rstrip('l'), 2); return ('I', v)
        if re.fullmatch(r'0[0-7]+l?', low):
            return ('I', int(low.rstrip('l'), 8))
        if low.endswith('l'): return ('I', int(low[:-1]))
        if low.endswith('f'): return ('F', float(low[:-1]))
        if low.endswith('d') or '.' in low or 'e' in low: return ('F', float(low.rstrip('d')))
        return ('I', int(low))
    except Exception:
        return ('?', s)


def literal_norm(toks):
    out = []
    for i, t in enumerate(toks):
        if t[0] == 'num':
            k, v = numval(t[1])
            if k == 'F':
                import struct
                if t[1].lower().replace('_', '').endswith('f'):
                    v = struct.unpack('f', struct.pack('f', v))[0]
                out.append(('num', 'F%r' % v))
            else:
                out.append(('num', 'I%d' % v))
        elif t[0] == 'c':
            ch = unesc(t[1][1:-1])
            out.append(('num', 'I%d' % ord(ch[0])) if len(ch) == 1 else t)
        elif t[0] in ('s', 'tb'):
            v = t[1]
            if t[0] == 'tb':
                out.append(('s', 'S' + repr(v))); continue
            out.append(('s', 'S' + repr(unesc(v[1:-1]))))
        else:
            out.append(t)
    # unary minus folding: - I5 -> I-5 when preceded by operator/start
    res = []
    for i, t in enumerate(out):
        if t[0] == 'num' and res and res[-1][1] == '-' and (len(res) == 1 or res[-2][0] == 'op' and res[-2][1] not in (')', ']')):
            res.pop(); res.append(('num', t[1][0] + ('-' + t[1][1:] if not t[1][1:].startswith('-') else t[1][2:])))
        else:
            res.append(t)
    return res


SIMPLE = None
def load_consts():
    global CONSTS, SIMPLE
    if CONSTS is None:
        CONSTS = json.load(open(f'{S}/consts.json'))
        SIMPLE = defaultdict(list)
        for cn, e in CONSTS.items():
            if e['consts']:
                SIMPLE[re.split(r'[/$]', cn)[-1]].append(e)
    return CONSTS


def const_lookup_simple(simple_cls, name, simp_imports, pkg_hint):
    C = load_consts()
    cands = []
    fq = simp_imports.get(simple_cls)
    if fq:
        e = C.get(fq.replace('.', '/'))
        if e and name in e['consts']: return e['consts'][name]
    for e in SIMPLE.get(simple_cls, []):
        if name in e['consts']:
            cands.append(e['consts'][name])
    vals = {json.dumps(x) for x in cands}
    if len(vals) == 1: return cands[0]
    return None


def hierarchy_consts(own_fq):
    """constants visible unqualified in class own_fq (itself, supers, interfaces, outers)"""
    C = load_consts(); seen = set(); out = {}
    todo = list(own_fq)
    while todo:
        c = todo.pop()
        if c in seen or c not in C: continue
        seen.add(c); e = C[c]
        for k, v in e['consts'].items(): out.setdefault(k, v)
        if e['super']: todo.append(e['super'])
        todo.extend(e['ifaces'])
    return out


def lit_of(v):
    kind, val = v
    if kind == 'string': return ('s', 'S' + repr(val))
    if kind == 'boolean': return ('id', 'true' if val else 'false')
    if kind in ('float', 'double'):
        if isinstance(val, str): return ('num', 'F' + val)
        return ('num', 'F%r' % float(val))
    if kind == 'char': return ('num', 'I%d' % val)
    return ('num', 'I%d' % int(val))


def const_subst(toks, locals_visible, stat_imports, simp_imports):
    out = []; i = 0
    while i < len(toks):
        t = toks[i]
        prev = toks[i - 1][1] if i else ''
        if t[0] == 'id' and prev != '.' and t[1] not in JAVA_KW:
            # Qualified X.NAME
            if i + 2 < len(toks) and toks[i + 1][1] == '.' and toks[i + 2][0] == 'id' and t[1][:1].isupper() and (i + 3 >= len(toks) or toks[i + 3][1] not in ('(', '.')):
                v = const_lookup_simple(t[1], toks[i + 2][1], simp_imports, None)
                if v is not None:
                    out.append(lit_of(v)); i += 3; continue
            if (i + 1 >= len(toks) or toks[i + 1][1] not in ('(', '.', '=')) or (i + 1 < len(toks) and toks[i + 1][1] == '.' and False):
                if t[1] in locals_visible and prev not in ('.',):
                    out.append(lit_of(locals_visible[t[1]])); i += 1; continue
                if t[1] in stat_imports:
                    v = const_lookup_simple(stat_imports[t[1]].split('.')[-1], t[1], simp_imports, None)
                    if v is not None: out.append(lit_of(v)); i += 1; continue
        out.append(t); i += 1
    return fold(out)


def jint(v): v &= 0xffffffff; return v - (1 << 32) if v >= 1 << 31 else v


def fold(toks):
    """fold binary ops between two numeric literals / two string literals when both neighbours bind looser"""
    PREC = {'*': 10, '/': 10, '%': 10, '+': 9, '-': 9, '<<': 8, '>>': 8, '>>>': 8, '&': 5, '^': 4, '|': 3}
    changed = True
    while changed:
        changed = False
        # parenthesized single literal
        for i in range(len(toks) - 2):
            if toks[i][1] == '(' and toks[i + 2][1] == ')' and toks[i + 1][0] in ('num', 's') and not (i > 0 and (toks[i - 1][0] == 'id' or toks[i - 1][1] in (')', ']'))):
                toks = toks[:i] + [toks[i + 1]] + toks[i + 3:]; changed = True; break
        if changed: continue
        for i in range(1, len(toks) - 1):
            op = toks[i][1]
            if op not in PREC: continue
            a, b = toks[i - 1], toks[i + 1]
            if a[0] not in ('num', 's') or b[0] not in ('num', 's'): continue
            lp = PREC.get(toks[i - 2][1], 0) if i >= 2 else 0
            rp = PREC.get(toks[i + 2][1], 0) if i + 2 < len(toks) else 0
            if i >= 2 and toks[i - 2][0] in ('num', 's', 'id'): continue
            if lp >= PREC[op] or rp > PREC[op]: continue
            if i >= 2 and toks[i - 2][1] in ('.', ')', ']'): continue
            r = None
            try:
                if a[0] == 's' or b[0] == 's':
                    if op == '+':
                        def sv(x):
                            if x[0] == 's': return eval(x[1][1:])
                            return str(int(x[1][1:])) if x[1][0] == 'I' else repr(float(x[1][1:]))
                        r = ('s', 'S' + repr(sv(a) + sv(b)))
                else:
                    ka, va = a[1][0], a[1][1:]; kb, vb = b[1][0], b[1][1:]
                    if ka == 'I' and kb == 'I':
                        x, y = int(va), int(vb)
                        r = {'*': x * y, '+': x + y, '-': x - y, '&': x & y, '|': x | y, '^': x ^ y, '<<': x << (y & 31),
                             '>>': x >> (y & 31), '/': int(x / y) if y else None, '%': (abs(x) % abs(y)) * (1 if x >= 0 else -1) if y else None,
                             '>>>': (x & 0xffffffff) >> (y & 31)}.get(op)
                        if r is not None: r = ('num', 'I%d' % jint(r))
                    elif op in ('*', '/', '+', '-'):
                        x, y = float(va), float(vb)
                        r = ('num', 'F%r' % {'*': x * y, '/': x / y if y else float('inf'), '+': x + y, '-': x - y}[op])
            except Exception:
                r = None
            if r is not None:
                toks = toks[:i - 1] + [r] + toks[i + 2:]; changed = True; break
    return toks


def local_rename(toks):
    """alpha-rename identifiers in declaration position (Type name [=;,:)]), lambda params, catch params"""
    decl = {}
    n = len(toks)
    for i in range(1, n - 1):
        t = toks[i]
        if t[0] != 'id' or t[1] in JAVA_KW: continue
        p = toks[i - 1]; q = toks[i + 1]
        if (p[0] == 'id' and (p[1][:1].isupper() or p[1] in PRIMS) or p[1] in (']', '>')) and q[1] in ('=', ';', ',', ':', ')', '&&', '||', '?') \
                and not (i >= 2 and toks[i - 2][1] in ('.', 'new')) and p[1] not in ('return', 'throw', 'case', 'new', 'instanceof', 'extends', 'implements', 'throws', 'class'):
            decl.setdefault(t[1], len(decl))
        if q[1] == '->' and p[1] in ('(', ',', '{', '=', 'return') or (q[1] == ',' and p[1] == '(' and False):
            decl.setdefault(t[1], len(decl))
    return [('id', 'L%d' % decl[t[1]]) if t[0] == 'id' and t[1] in decl and not (i and toks[i - 1][1] == '.') and not (i + 1 < n and toks[i + 1][1] == '(') else t for i, t in enumerate(toks)]


def stmt_norm(toks):
    out = []
    for i, t in enumerate(toks):
        v = t[1]
        if v in ('{', '}'): continue          # braces are structure only
        out.append(t)
    # unify i++ / ++i / i += 1 / i = i + 1 as 'INC i' ; i-- analogs
    res = []; i = 0
    while i < len(out):
        a = out[i]
        if a[0] == 'id' and i + 1 < len(out) and out[i + 1][1] in ('++', '--') and i + 2 < len(out) and out[i + 2][1] in (';', ')', ','):
            res += [('op', 'INC' if out[i + 1][1] == '++' else 'DEC'), a]; i += 2; continue
        if a[1] in ('++', '--') and i + 1 < len(out) and out[i + 1][0] == 'id' and (i == 0 or out[i - 1][1] in (';', '(', ',', ')')) and i + 2 < len(out) and out[i + 2][1] in (';', ')', ','):
            res += [('op', 'INC' if a[1] == '++' else 'DEC'), out[i + 1]]; i += 2; continue
        if a[0] == 'id' and i + 2 < len(out) and out[i + 1][1] in ('+=', '-=') and out[i + 2][1] == 'I1' and i + 3 < len(out) and out[i + 3][1] in (';', ')', ','):
            res += [('op', 'INC' if out[i + 1][1] == '+=' else 'DEC'), a]; i += 3; continue
        if a[0] == 'id' and i + 4 < len(out) and out[i + 1][1] == '=' and out[i + 2][1] == a[1] and out[i + 3][1] in ('+', '-') and out[i + 4][1] == 'I1' and i + 5 < len(out) and out[i + 5][1] in (';', ')', ','):
            res += [('op', 'INC' if out[i + 3][1] == '+' else 'DEC'), a]; i += 5; continue
        res.append(a); i += 1
    return res


# ------------------------------------------------------------------ member splitting

def split_members(toks, prefix=''):
    """return {key: tokens} for members of every class body found at top level (recursive for nested types)"""
    members = {}
    i = 0; n = len(toks)
    while i < n:
        if toks[i][1] in ('class', 'interface', 'enum', 'record') and i + 1 < n and toks[i + 1][0] == 'id' and (i == 0 or toks[i - 1][1] != '.'):
            name = toks[i + 1][1]
            j = i + 2
            while j < n and toks[j][1] != '{': j += 1
            k = match(toks, j)
            header = toks[i:j]
            members[prefix + name + '#header'] = header
            members.update(split_body(toks[j + 1:k], prefix + name + '.', toks[i][1] == 'enum'))
            i = k + 1; continue
        i += 1
    return members


def match(toks, j):
    d = 0
    for k in range(j, len(toks)):
        if toks[k][1] == '{': d += 1
        elif toks[k][1] == '}':
            d -= 1
            if d == 0: return k
    return len(toks) - 1


def split_body(body, prefix, is_enum):
    mem = {}; i = 0; n = len(body); anon_init = 0
    if is_enum:
        # enum constants up to first ';' at depth 0
        d = 0; j = 0
        while j < n:
            v = body[j][1]
            if v in ('(', '{', '['): d += 1
            elif v in (')', '}', ']'): d -= 1
            elif v == ';' and d == 0: break
            j += 1
        mem[prefix + '#enumconsts'] = body[:j]
        i = j + 1
    while i < n:
        # nested type
        j = i
        while j < n and body[j][1] in ('public', 'private', 'protected', 'static', 'final', 'abstract', 'sealed', 'non', '-', 'strictfp', 'synchronized', 'native', 'transient', 'volatile', 'default'):
            j += 1
        if j < n and body[j][1] in ('class', 'interface', 'enum', 'record') and j + 1 < n and body[j + 1][0] == 'id':
            k = j + 2
            while k < n and body[k][1] != '{': k += 1
            e = match(body, k)
            mem[prefix + body[j + 1][1] + '#header'] = body[i:k]
            mem.update(split_body(body[k + 1:e], prefix + body[j + 1][1] + '.', body[j][1] == 'enum'))
            i = e + 1; continue
        # initializer block
        if j < n and body[j][1] == '{':
            e = match(body, j)
            key = prefix + ('#static-init' if j > i and body[j - 1][1] == 'static' else '#init') + str(anon_init); anon_init += 1
            mem[key] = body[i:e + 1]; i = e + 1; continue
        # find end of member: ';' at depth 0 (field/abstract) or matching '}' of a body after ')'
        k = i; d = 0; paren_seen = False; is_method = False
        while k < n:
            v = body[k][1]
            if v == '(':
                if d == 0 and not paren_seen and k > i and body[k - 1][0] == 'id':
                    # method if no '=' before
                    if not any(t[1] == '=' for t in body[i:k]): is_method = True
                    paren_seen = True
                d += 1
            elif v == ')': d -= 1
            elif v == '{' and d == 0:
                if is_method:
                    e = match(body, k); k = e; break
                d2 = 0  # field initializer with anonymous class / array init
                e = match(body, k); k = e + 1; continue
            elif v == ';' and d == 0: break
            k += 1
        seg = body[i:k + 1]
        if is_method:
            # key: name + param simple types
            p = next(x for x in range(i, k) if body[x][1] == '(' and body[x - 1][0] == 'id')
            name = body[p - 1][1]
            q = p; dd = 0
            while True:
                if body[q][1] == '(': dd += 1
                elif body[q][1] == ')':
                    dd -= 1
                    if dd == 0: break
                q += 1
            params = split_params(body[p + 1:q])
            mem[prefix + name + '(' + ','.join(params) + ')'] = seg
        else:
            # field(s): key by declared names
            names = []
            dd = 0
            for x in range(i, k):
                v = body[x][1]
                if v in ('(', '{', '['): dd += 1
                elif v in (')', '}', ']'): dd -= 1
                if dd == 0 and body[x][0] == 'id' and x + 1 <= k and body[x + 1][1] in ('=', ';', ',') and x > i and body[x - 1][1] not in ('.',):
                    names.append(v)
            if names:
                mem[prefix + 'F:' + ','.join(names)] = seg
        i = k + 1
    return mem


def split_params(ptoks):
    out = []; cur = []; d = 0
    for t in ptoks + [('op', ',')]:
        v = t[1]
        if v in ('<', '(', '['): d += 1
        elif v in ('>', ')', ']'): d -= 1
        elif v == '>>': d -= 2
        if v == ',' and d == 0:
            if cur: out.append(ptype(cur))
            cur = []
        else: cur.append(t)
    return out


def ptype(toks):
    toks = drop_annotations(toks)
    toks = [t for t in toks if t[1] != 'final']
    # remove generics
    res = []; d = 0
    for t in toks:
        if t[1] == '<': d += 1; continue
        if t[1] == '>': d -= 1; continue
        if t[1] == '>>': d -= 2; continue
        if d == 0: res.append(t[1])
    if len(res) >= 2: res = res[:-1]  # drop name
    s = ''.join(res).replace('...', '[]')
    base = s.rstrip('[]'); dims = s[len(base):]
    return base.split('.')[-1] + dims


STATICS = set()
STAGES = ['S0-lexical', 'S1-annotations', 'S2-qualification', 'S3-modifiers/generics/parens', 'S4-literal-form', 'S5-constant-inlining/folding', 'S6-local-names', 'S7-braces/increments']


def compare_pair(orig_src, dec_src, own_fq_classes):
    ta, stat_a, simp_a = strip_header(lex(orig_src))
    tb, stat_b, simp_b = strip_header(lex(dec_src))
    own = class_names(ta) | class_names(tb)
    STATICS.clear(); STATICS.update(stat_a); STATICS.update(stat_b)
    visible = hierarchy_consts(own_fq_classes)
    ma = split_members(ta); mb = split_members(tb)
    res = {'members_orig': len(ma), 'members_dec': len(mb), 'only_orig': [], 'only_dec': [], 'pairs': {}}
    for k in ma:
        if k not in mb: res['only_orig'].append(k)
    for k in mb:
        if k not in ma: res['only_dec'].append(k)
    gen = {}
    for k in ma:
        if k not in mb: continue
        a, b = ma[k], mb[k]
        is_gen = any(a[x][1] == '@' and x + 1 < len(a) and a[x + 1][1] == 'Generated' for x in range(len(a) - 1))
        stage = None
        fa, fb = a, b
        pipeline = [lambda x, s=None: x,
                    lambda x, s=None: drop_annotations(x),
                    lambda x, s=None: qualify_norm(x, own),
                    lambda x, s=None: generics_final_norm(x),
                    lambda x, s=None: literal_norm(x),
                    None,
                    lambda x, s=None: local_rename(x),
                    lambda x, s=None: stmt_norm(x)]
        for si, f in enumerate(pipeline):
            if f is None:
                fa = const_subst(fa, visible, stat_a, simp_a); fb = const_subst(fb, visible, stat_b, simp_b)
            else:
                fa, fb = f(fa), f(fb)
            if [t[1] for t in fa] == [t[1] for t in fb]:
                stage = STAGES[si]; break
        sub = None
        if stage is None:
            import difflib
            xa = [t[1] for t in fa]; xb = [t[1] for t in fb]
            dt = set()
            for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, xa, xb, autojunk=False).get_opcodes():
                if op != 'equal': dt.update(xa[i1:i2]); dt.update(xb[j1:j2])
            CF_ = {'if', 'else', 'return', '!', 'break', 'continue', 'while', 'for', 'switch', 'case', 'default', 'do', '?', ':', '&&', '||', '==', '!=', '<', '>', '<=', '>=', 'yield', '->', 'try', 'catch', 'finally', 'throw'}
            tags = []
            if dt & CF_: tags.append('control-flow/expression-restructure')
            if any(re.fullmatch(r'L\d+', x) for x in dt) or '=' in dt: tags.append('local-variable-inlining/split')
            LIT = re.compile(r"(S['\"].*|I-?\d+|F.*\d.*|Fnan|Finf|F-inf|L\d+)$")
            if dt <= {'(', ')'} | {x for x in dt if (re.fullmatch(r'[A-Z]\w*', x) and not LIT.match(x)) or x in PRIMS}: tags = ['cast-insert/remove']
            if 'instanceof' in dt: tags.append('instanceof-pattern')
            if 'new' in dt or '[' in dt: tags.append('array/varargs-or-alloc-shape')
            if any(x.startswith(('S', 'I', 'F')) and x[1:2] in "'\"-0123456789" for x in dt): tags.append('literal/constant-residual')
            if 'class' in dt or 'Override' in dt: tags.append('nested/anonymous-class-shape')
            MODS = {'public', 'private', 'protected', 'static', 'final', 'abstract', 'default', 'synchronized', 'transient', 'volatile', 'native', 'strictfp'}
            if not tags and dt <= MODS: tags = ['modifier-spelling(implicit-interface/order)']
            elif not tags and '.' in dt and len(dt - MODS - {'.'}) <= 2: tags = ['qualification-residual(inherited-constant/nested-type)']
            sub = '+'.join(tags) or 'other'
        res['pairs'][k] = {'stage': stage or 'residual-structural', 'sub': sub, 'generated': is_gen, 'len': len(a)}
    return res


def fq_for(mod, rel):
    top = rel[:-5]
    return [top] + [top + '$' + x for x in ()]


def main():
    pairs = [l.rstrip('\n').split('\t') for l in open(f'{S}/pairs.tsv')]
    only = sys.argv[1] if len(sys.argv) > 1 else None
    out = open(f'{S}/normdiff.jsonl', 'w')
    for mod, rel, hasv, hasc in pairs:
        if rel.endswith('package-info.java'): continue
        if only and mod != only: continue
        base = f'{O}/_bin-ext/nre' if mod == 'nre' else f'{O}/{mod}'
        dec = None; tool = None
        for sub, tl in (('vineflower', 'vineflower'), ('fallback', 'cfr')):
            p = f'{base}/{sub}/{rel}'
            if os.path.exists(p): dec = p; tool = tl; break
        if not dec: continue
        orig = open(f'{O}/docSource/{mod}/{rel}', encoding='utf-8', errors='replace').read()
        d = open(dec, encoding='utf-8', errors='replace').read()
        top = rel[:-5]
        # include nested classes present in extracted dir for constant visibility
        fqs = [top]
        exdir = os.path.dirname(f'{base}/extracted/{rel}')
        if os.path.isdir(exdir):
            stem = os.path.basename(top)
            fqs += [os.path.dirname(top) + '/' + f[:-6] for f in os.listdir(exdir) if f.startswith(stem + '$') and f.endswith('.class')]
        try:
            r = compare_pair(orig, d, fqs)
        except Exception as e:
            r = {'error': repr(e)}
        r.update({'mod': mod, 'rel': rel, 'tool': tool, 'vf_marker': '$VF:' in d or "Couldn't be decompiled" in d})
        out.write(json.dumps(r) + '\n')
    out.close()


if __name__ == '__main__':
    main()
