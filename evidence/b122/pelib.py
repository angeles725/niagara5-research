#!/usr/bin/env python3
"""Stdlib-only PE / CLR-metadata reader used as the independent instrument in B122.

No third-party parser (pefile/lief are not installed); everything follows ECMA-335 II.22
and the Microsoft PE/COFF spec. Read-only: never executes or loads the binary.
"""
import hashlib
import struct


class PE:
    def __init__(self, data):
        self.d = data
        if data[:2] != b"MZ":
            raise ValueError("no MZ")
        self.pe = struct.unpack_from("<I", data, 0x3C)[0]
        if data[self.pe:self.pe + 4] != b"PE\0\0":
            raise ValueError("no PE sig")
        (self.machine, self.nsec, self.timestamp, _, _, self.optsize, self.chars) = struct.unpack_from(
            "<HHIIIHH", data, self.pe + 4)
        self.opt = self.pe + 24
        self.magic = struct.unpack_from("<H", data, self.opt)[0]
        self.is64 = self.magic == 0x20B
        dd = self.opt + (112 if self.is64 else 96)
        self.checksum_off = self.opt + 64
        self.ddoff = dd
        self.dirs = [struct.unpack_from("<II", data, dd + 8 * i) for i in range(16)]
        so = self.opt + self.optsize
        self.sections = []
        for i in range(self.nsec):
            n, vs, va, rs, ro = struct.unpack_from("<8sIIII", data, so + 40 * i)
            self.sections.append((n.rstrip(b"\0").decode("latin1"), va, vs, ro, rs))

    def off(self, rva):
        for _, va, vs, ro, rs in self.sections:
            if va <= rva < va + max(vs, rs):
                return rva - va + ro
        if rva < 0x1000:
            return rva
        raise ValueError("rva %#x unmapped" % rva)

    def cstr(self, off):
        return self.d[off:self.d.index(b"\0", off)].decode("latin1")

    def exports(self):
        rva, size = self.dirs[0]
        if not rva:
            return []
        o = self.off(rva)
        (_, _, _, _, _, base, nfunc, nnames, aof, aon, aoo) = struct.unpack_from("<IIHHIIIIIII", self.d, o)
        out = []
        for i in range(nnames):
            nrva = struct.unpack_from("<I", self.d, self.off(aon) + 4 * i)[0]
            ordi = struct.unpack_from("<H", self.d, self.off(aoo) + 2 * i)[0]
            frva = struct.unpack_from("<I", self.d, self.off(aof) + 4 * ordi)[0]
            out.append((self.cstr(self.off(nrva)), ordi + base, frva))
        self.nfunc_total = nfunc
        return out

    def imports(self):
        """{dll: [function names or '#ordinal']} from the import directory."""
        rva, _ = self.dirs[1]
        out = {}
        if not rva:
            return out
        o, w = self.off(rva), (8 if self.is64 else 4)
        while True:
            oft, _, _, name, ft = struct.unpack_from("<IIIII", self.d, o)
            if not name:
                break
            fns, t = [], self.off(oft or ft)
            while True:
                v = int.from_bytes(self.d[t:t + w], "little")
                if not v:
                    break
                fns.append("#%d" % (v & 0xFFFF) if v >> (w * 8 - 1) else self.cstr(self.off(v & 0x7FFFFFFF) + 2))
                t += w
            out[self.cstr(self.off(name))] = fns
            o += 20
        return out

    def authenticode(self):
        off, size = self.dirs[4]
        if not off:
            return None
        return self.d[off + 8:off + size]

    def authenticode_hash(self, alg="sha256"):
        off, size = self.dirs[4]
        end = off if off else len(self.d)
        h = hashlib.new(alg)
        h.update(self.d[:self.checksum_off])
        h.update(self.d[self.checksum_off + 4:self.ddoff + 32])
        h.update(self.d[self.ddoff + 40:end])
        return h.hexdigest()
