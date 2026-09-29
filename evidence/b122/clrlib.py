"""CLR (ECMA-335 II.22) metadata reader on top of pelib.PE - the independent second instrument for B122."""
import hashlib
import struct

S, G, B = "S", "G", "B"
CODED = {  # name -> (tag bits, [table ids or None])
    "TypeDefOrRef": (2, [2, 1, 27]),
    "HasConstant": (2, [4, 8, 23]),
    "HasCustomAttribute": (5, [6, 4, 1, 2, 8, 9, 10, 0, 14, 23, 20, 17, 26, 27, 32, 35, 38, 39, 40, 42, 44, 43]),
    "HasFieldMarshal": (1, [4, 8]),
    "HasDeclSecurity": (2, [2, 6, 32]),
    "MemberRefParent": (3, [2, 1, 26, 6, 27]),
    "HasSemantics": (1, [20, 23]),
    "MethodDefOrRef": (1, [6, 10]),
    "MemberForwarded": (1, [4, 6]),
    "Implementation": (2, [38, 35, 39]),
    "CustomAttributeType": (3, [None, None, 6, 10, None]),
    "ResolutionScope": (2, [0, 26, 35, 1]),
    "TypeOrMethodDef": (1, [2, 6]),
}
# column kinds: int = fixed bytes, S/G/B = heap index, ("T", id) = table index, ("C", name)
SCHEMA = {
    0: [2, S, G, G, G], 1: [("C", "ResolutionScope"), S, S],
    2: [4, S, S, ("C", "TypeDefOrRef"), ("T", 4), ("T", 6)], 3: [("T", 4)],
    4: [2, S, B], 5: [("T", 6)], 6: [4, 2, 2, S, B, ("T", 8)], 7: [("T", 8)],
    8: [2, 2, S], 9: [("T", 2), ("C", "TypeDefOrRef")], 10: [("C", "MemberRefParent"), S, B],
    11: [2, ("C", "HasConstant"), B], 12: [("C", "HasCustomAttribute"), ("C", "CustomAttributeType"), B],
    13: [("C", "HasFieldMarshal"), B], 14: [2, ("C", "HasDeclSecurity"), B],
    15: [2, 4, ("T", 2)], 16: [4, ("T", 4)], 17: [B], 18: [("T", 2), ("T", 20)], 19: [("T", 20)],
    20: [2, S, ("C", "TypeDefOrRef")], 21: [("T", 2), ("T", 23)], 22: [("T", 23)], 23: [2, S, B],
    24: [2, ("T", 6), ("C", "HasSemantics")], 25: [("T", 2), ("C", "MethodDefOrRef"), ("C", "MethodDefOrRef")],
    26: [S], 27: [B], 28: [2, ("C", "MemberForwarded"), S, ("T", 26)], 29: [4, ("T", 4)],
    30: [4, 4], 31: [4], 32: [4, 2, 2, 2, 2, 4, B, S, S], 33: [4], 34: [4, 4, 4],
    35: [2, 2, 2, 2, 4, B, S, S, B], 36: [4, ("T", 35)], 37: [4, 4, 4, ("T", 35)],
    38: [4, S, B], 39: [4, 4, S, S, ("C", "Implementation")], 40: [4, 4, S, ("C", "Implementation")],
    41: [("T", 2), ("T", 2)], 42: [2, 2, ("C", "TypeOrMethodDef"), S], 43: [("C", "MethodDefOrRef"), B],
    44: [("T", 42), ("C", "TypeDefOrRef")],
}


class Clr:
    def __init__(self, pe):
        self.pe = pe
        rva, _ = pe.dirs[14]
        self.ok = bool(rva)
        if not rva:
            return
        d = pe.d
        o = pe.off(rva)
        (self.cb, self.maj, self.min, mdrva, mdsize, self.flags, self.entry) = struct.unpack_from(
            "<IHHIIII", d, o)
        self.sn_rva, self.sn_size = struct.unpack_from("<II", d, o + 32)
        self.md = pe.off(mdrva)
        m = self.md
        if d[m:m + 4] != b"BSJB":
            raise ValueError("no BSJB")
        vlen = struct.unpack_from("<I", d, m + 12)[0]
        self.version = d[m + 16:m + 16 + vlen].rstrip(b"\0").decode("latin1")
        p = m + 16 + vlen + 2
        ns = struct.unpack_from("<H", d, p)[0]
        p += 2
        self.streams = {}
        for _ in range(ns):
            so, ss = struct.unpack_from("<II", d, p)
            p += 8
            e = d.index(b"\0", p)
            name = d[p:e].decode()
            p = (e + 4) & ~3
            self.streams[name] = (m + so, ss)
        self._tables()

    def heap_str(self, i):
        o = self.streams["#Strings"][0] + i
        return self.pe.cstr(o)

    def heap_blob(self, i):
        o = self.streams["#Blob"][0] + i
        b0 = self.pe.d[o]
        if b0 < 0x80:
            n, o = b0, o + 1
        elif b0 < 0xC0:
            n, o = ((b0 & 0x3F) << 8) | self.pe.d[o + 1], o + 2
        else:
            n, o = struct.unpack_from(">I", self.pe.d, o)[0] & 0x1FFFFFFF, o + 4
        return self.pe.d[o:o + n]

    def _tables(self):
        d = self.pe.d
        t = self.streams["#~"][0]
        (_, maj, mnr, hs, _, valid, _) = struct.unpack_from("<IBBBBQQ", d, t)
        self.hs = hs
        p = t + 24
        self.rows = {}
        for i in range(64):
            if valid >> i & 1:
                self.rows[i] = struct.unpack_from("<I", d, p)[0]
                p += 4
        big = lambda i: self.rows.get(i, 0) >= 65536
        self.sz = {}

        def col(k):
            if isinstance(k, int):
                return k
            if k == S:
                return 4 if hs & 1 else 2
            if k == G:
                return 4 if hs & 2 else 2
            if k == B:
                return 4 if hs & 4 else 2
            if k[0] == "T":
                return 4 if big(k[1]) else 2
            bits, tabs = CODED[k[1]]
            mx = max(self.rows.get(x, 0) for x in tabs if x is not None)
            return 4 if mx >= (1 << (16 - bits)) else 2

        self.layout = {i: [col(k) for k in SCHEMA[i]] for i in self.rows}
        self.tab = {}
        for i in sorted(self.rows):
            rs = sum(self.layout[i])
            rowsl = []
            for r in range(self.rows[i]):
                vals, q = [], p + r * rs
                for w in self.layout[i]:
                    vals.append(int.from_bytes(d[q:q + w], "little"))
                    q += w
                rowsl.append(vals)
            self.tab[i] = rowsl
            p += rs * self.rows[i]

    def assembly(self):
        r = self.tab.get(32)
        if not r:
            return None
        h, ma, mi, bu, rv, fl, pk, nm, cu = r[0]
        return dict(name=self.heap_str(nm), version="%d.%d.%d.%d" % (ma, mi, bu, rv),
                    pubkey=self.heap_blob(pk), flags=fl)

    def asm_refs(self):
        return [(self.heap_str(r[6]), "%d.%d.%d.%d" % tuple(r[0:4])) for r in self.tab.get(35, [])]

    def pinvokes(self):
        out = []
        for fl, mf, nm, sc in self.tab.get(28, []):
            mod = self.heap_str(self.tab[26][sc - 1][0]) if sc else ""
            meth = mf >> 1
            out.append((mod, self.heap_str(nm), self.heap_str(self.tab[6][meth - 1][3]) if mf & 1 else "?"))
        return out

    def typedefs(self):
        return [(self.heap_str(r[2]), self.heap_str(r[1])) for r in self.tab.get(2, [])]

    def target_framework(self):
        """Value of [assembly: TargetFramework(...)] from the CustomAttribute table."""
        for parent, typ, val in self.tab.get(12, []):
            if parent & 31 != 14:  # Assembly
                continue
            tag, idx = typ & 7, typ >> 3
            if tag != 3:
                continue
            cls = self.tab[10][idx - 1][0]
            if cls & 7 != 1:
                continue
            tr = self.tab[1][(cls >> 3) - 1]
            if self.heap_str(tr[1]) == "TargetFrameworkAttribute":
                b = self.heap_blob(val)
                n = b[2]
                return b[3:3 + n].decode("utf8", "replace")
        return None

    def token_of_pubkey(self):
        pk = self.assembly()["pubkey"]
        return hashlib.sha1(pk).digest()[-8:][::-1].hex() if pk else None
