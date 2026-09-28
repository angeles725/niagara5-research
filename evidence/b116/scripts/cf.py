#!/usr/bin/env python3
"""Minimal class-file parser + normalized per-method bytecode fingerprint (B116 scratch).

normalize(): constant-pool indices resolved to symbolic values; branch targets expressed
as instruction ordinals (not byte pcs); LVT/LNT/StackMapTable excluded from the code
fingerprint but returned separately.
"""
import struct, sys, zipfile, hashlib

OPLEN = {}
def _set(ops, n):
    for o in ops: OPLEN[o] = n
_set(range(0x00, 0x10), 0); _set([0x10], 1); _set([0x11], 2); _set([0x12], 1); _set([0x13, 0x14], 2)
_set(range(0x15, 0x1a), 1); _set(range(0x1a, 0x36), 0); _set(range(0x36, 0x3b), 1); _set(range(0x3b, 0x84), 0)
_set([0x84], 2); _set(range(0x85, 0x99), 0); _set(range(0x99, 0xa9), 2); _set([0xa9], 1); _set(range(0xac, 0xb2), 0)
_set(range(0xb2, 0xb9), 2); _set([0xb9], 4); _set([0xba], 4); _set([0xbb], 2); _set([0xbc], 1); _set([0xbd], 2)
_set([0xbe, 0xbf], 0); _set([0xc0, 0xc1], 2); _set([0xc2, 0xc3], 0); _set([0xc5], 3); _set([0xc6, 0xc7], 2)
_set([0xc8, 0xc9], 4)
BRANCH2 = set(range(0x99, 0xa9)) | {0xc6, 0xc7}
BRANCH4 = {0xc8, 0xc9}
CPREF2 = {0x13, 0x14, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6, 0xb7, 0xb8, 0xbb, 0xbd, 0xc0, 0xc1, 0xc5, 0xb9, 0xba}


class CF:
    def __init__(self, data):
        self.d = data; self.p = 0
        magic, self.minor, self.major = struct.unpack('>IHH', self.r(8))
        n = self.u2(); self.cp = [None] * n; i = 1
        while i < n:
            t = self.u1()
            if t == 1: ln = self.u2(); self.cp[i] = ('utf8', self.r(ln).replace(b'\xc0\x80', b'\x00').decode('utf-8', 'surrogatepass'))
            elif t == 3: self.cp[i] = ('int', struct.unpack('>i', self.r(4))[0])
            elif t == 4: self.cp[i] = ('float', struct.unpack('>f', self.r(4))[0])
            elif t == 5: self.cp[i] = ('long', struct.unpack('>q', self.r(8))[0]); i += 1
            elif t == 6: self.cp[i] = ('double', struct.unpack('>d', self.r(8))[0]); i += 1
            elif t in (7, 8, 16, 19, 20): self.cp[i] = ({7: 'class', 8: 'string', 16: 'mtype', 19: 'module', 20: 'package'}[t], self.u2())
            elif t in (9, 10, 11, 12, 17, 18): self.cp[i] = ({9: 'fref', 10: 'mref', 11: 'imref', 12: 'nat', 17: 'dyn', 18: 'indy'}[t], self.u2(), self.u2())
            elif t == 15: self.cp[i] = ('mh', self.u1(), self.u2())
            else: raise ValueError('bad cp tag %d' % t)
            i += 1
        self.access, self.this, self.sup = self.u2(), self.u2(), self.u2()
        self.ifaces = [self.cls(self.u2()) for _ in range(self.u2())]
        self.fields = [self.member() for _ in range(self.u2())]
        self.methods = [self.member() for _ in range(self.u2())]
        self.attrs = self.attributes()
        self.name = self.cls(self.this)
        self.bootstraps = []
        if 'BootstrapMethods' in self.attrs:
            b = self.attrs['BootstrapMethods']; q = 2
            for _ in range(struct.unpack('>H', b[:2])[0]):
                mh, na = struct.unpack('>HH', b[q:q + 4]); q += 4
                args = [struct.unpack('>H', b[q + 2 * k:q + 2 * k + 2])[0] for k in range(na)]; q += 2 * na
                self.bootstraps.append((mh, args))

    def r(self, n): v = self.d[self.p:self.p + n]; self.p += n; return v
    def u1(self): return self.r(1)[0]
    def u2(self): return struct.unpack('>H', self.r(2))[0]
    def u4(self): return struct.unpack('>I', self.r(4))[0]
    def utf(self, i): return self.cp[i][1]
    def cls(self, i): return self.utf(self.cp[i][1]) if i else None

    def member(self):
        acc, ni, di = self.u2(), self.u2(), self.u2()
        return {'access': acc, 'name': self.utf(ni), 'desc': self.utf(di), 'attrs': self.attributes()}

    def attributes(self):
        out = {}
        for _ in range(self.u2()):
            n = self.utf(self.u2()); ln = self.u4(); out[n] = self.r(ln)
        return out

    def sym(self, i, depth=0):
        e = self.cp[i]; t = e[0]
        if t == 'utf8': return e[1]
        if t in ('int', 'float', 'long', 'double'): return '%s:%r' % (t, e[1])
        if t == 'class': return 'C:' + self.utf(e[1])
        if t == 'string': return 'S:' + repr(self.utf(e[1]))
        if t == 'mtype': return 'MT:' + self.utf(e[1])
        if t in ('fref', 'mref', 'imref'):
            nat = self.cp[e[2]]
            return '%s:%s.%s:%s' % (t, self.cls(e[1]), self.utf(nat[1]), self.utf(nat[2]))
        if t == 'nat': return self.utf(e[1]) + ':' + self.utf(e[2])
        if t == 'mh': return 'MH%d:%s' % (e[1], self.sym(e[2]))
        if t in ('indy', 'dyn'):
            nat = self.cp[e[2]]
            bm = self.bootstraps[e[1]] if e[1] < len(self.bootstraps) else (0, [])
            args = ','.join(self.sym(a) for a in bm[1]) if depth < 2 else '...'
            return '%s:%s:%s@%s[%s]' % (t, self.utf(nat[1]), self.utf(nat[2]), self.sym(bm[0]) if bm[0] else '?', args)
        return str(e)

    def code(self, m):
        a = m['attrs'].get('Code')
        if a is None: return None
        max_stack, max_locals, clen = struct.unpack('>HHI', a[:8])
        code = a[8:8 + clen]; q = 8 + clen
        nexc = struct.unpack('>H', a[q:q + 2])[0]; q += 2
        exc = []
        for _ in range(nexc):
            s, e, h, ct = struct.unpack('>HHHH', a[q:q + 8]); q += 8
            exc.append((s, e, h, self.cls(ct) if ct else 'any'))
        # sub-attributes
        sub = {}; nat = struct.unpack('>H', a[q:q + 2])[0]; q += 2
        for _ in range(nat):
            ni, ln = struct.unpack('>HI', a[q:q + 6]); q += 6
            sub[self.utf(ni)] = a[q:q + ln]; q += ln
        # decode
        ins = []; pc = 0; pcs = []
        while pc < len(code):
            op = code[pc]; start = pc; pcs.append(pc)
            if op == 0xaa:  # tableswitch
                pc += 1; pc += (4 - pc % 4) % 4
                dflt, lo, hi = struct.unpack('>iii', code[pc:pc + 12]); pc += 12
                offs = struct.unpack('>%di' % (hi - lo + 1), code[pc:pc + 4 * (hi - lo + 1)]); pc += 4 * (hi - lo + 1)
                ins.append((start, 'tableswitch', (lo, hi, start + dflt, tuple(start + o for o in offs))))
            elif op == 0xab:
                pc += 1; pc += (4 - pc % 4) % 4
                dflt, np_ = struct.unpack('>ii', code[pc:pc + 8]); pc += 8
                pairs = []
                for _ in range(np_):
                    k, o = struct.unpack('>ii', code[pc:pc + 8]); pc += 8; pairs.append((k, start + o))
                ins.append((start, 'lookupswitch', (start + dflt, tuple(pairs))))
            elif op == 0xc4:  # wide
                op2 = code[pc + 1]
                if op2 == 0x84:
                    idx, c = struct.unpack('>Hh', code[pc + 2:pc + 6]); pc += 6; ins.append((start, 'iinc', (idx, c)))
                else:
                    idx = struct.unpack('>H', code[pc + 2:pc + 4])[0]; pc += 4; ins.append((start, op2, (idx,)))
            else:
                n = OPLEN[op]; raw = code[pc + 1:pc + 1 + n]; pc += 1 + n
                if op in BRANCH2: arg = ('T', start + struct.unpack('>h', raw)[0])
                elif op in BRANCH4: arg = ('T', start + struct.unpack('>i', raw)[0])
                elif op == 0x12: arg = self.sym(raw[0])
                elif op in CPREF2: arg = self.sym(struct.unpack('>H', raw[:2])[0])
                elif op == 0x10: arg = struct.unpack('>b', raw)[0]
                elif op == 0x11: arg = struct.unpack('>h', raw)[0]
                elif op == 0x84: arg = (raw[0], struct.unpack('>b', raw[1:2])[0])
                elif op == 0xbc: arg = raw[0]
                else: arg = tuple(raw)
                ins.append((start, op, arg))
        ordinal = {p: k for k, p in enumerate(pcs)}; ordinal[len(code)] = len(pcs)
        def T(p): return ordinal.get(p, 'pc%d' % p)
        norm = []
        for (s, op, arg) in ins:
            if op == 'tableswitch': norm.append(('tableswitch', arg[0], arg[1], T(arg[2]), tuple(T(x) for x in arg[3])))
            elif op == 'lookupswitch': norm.append(('lookupswitch', T(arg[0]), tuple((k, T(x)) for k, x in arg[1])))
            elif isinstance(arg, tuple) and len(arg) == 2 and arg[0] == 'T': norm.append((op, 'T', T(arg[1])))
            else: norm.append((op, arg))
        excn = [(T(s), T(e), T(h), c) for (s, e, h, c) in exc]
        lnt = []
        if 'LineNumberTable' in sub:
            b = sub['LineNumberTable']; k = struct.unpack('>H', b[:2])[0]
            lnt = sorted(struct.unpack('>HH', b[2 + 4 * j:6 + 4 * j]) for j in range(k))
            lnt = [(T(p), l) for p, l in lnt]
        lvt = []
        if 'LocalVariableTable' in sub:
            b = sub['LocalVariableTable']; k = struct.unpack('>H', b[:2])[0]
            for j in range(k):
                sp, ln, ni, di, ix = struct.unpack('>HHHHH', b[2 + 10 * j:12 + 10 * j])
                lvt.append((ix, self.utf(ni), self.utf(di)))
        return {'ins': norm, 'exc': excn, 'lnt': lnt, 'lvt': sorted(lvt), 'max_stack': max_stack,
                'max_locals': max_locals, 'subattrs': sorted(sub)}


def mkey(m): return m['name'] + m['desc']


def fingerprint(cf, m, with_locals_index=True):
    c = cf.code(m)
    if c is None: return None
    return hashlib.sha1(repr((c['ins'], c['exc'])).encode()).hexdigest()


if __name__ == '__main__':
    cf = CF(open(sys.argv[1], 'rb').read())
    print(cf.name, cf.major, 'fields', len(cf.fields), 'methods', len(cf.methods), sorted(cf.attrs))
    for m in cf.methods:
        c = cf.code(m)
        print(' ', mkey(m), 'lvt' if c and c['lvt'] else '-', len(c['ins']) if c else 'abstract')
