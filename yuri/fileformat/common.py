from enum import IntEnum
from struct import Struct as St
from dataclasses import dataclass
from typing import cast, BinaryIO
VerRange = range(200, 501)
LE = 'little'
CP932 = 'cp932'
F64 = St('<d')


class Rdr:
    __slots__ = ['idx', 'enc', 'b', 'v']
    idx: int
    enc: str
    b: bytes
    v: memoryview

    @classmethod
    def from_bio(cls, bio: BinaryIO, enc: str = CP932):
        return cls(bio.read(), enc)

    def __init__(self, data: bytes, enc: str = CP932):
        self.idx = 0
        self.enc = enc
        self.b = data
        self.v = memoryview(data)

    def read(self, n: int):
        beg = self.idx
        end = beg+n
        ret = self.v[beg:end]
        assert (got := len(ret)) == n, f'read: want={n}, got={got}, at={beg}'
        self.idx = end
        return ret

    def byte(self):
        b = self.v[self.idx]
        self.idx += 1
        return b

    def si(self, n: int):
        return int.from_bytes(self.read(n), LE, signed=True)

    def ui(self, n: int):
        return int.from_bytes(self.read(n), LE, signed=False)

    def bz(self):
        beg = self.idx
        end = self.b.index(0, beg)
        self.idx = end+1
        return self.v[beg:end]

    def sz(self, *, enc: str | None = None):
        return str(self.bz(), enc or self.enc)

    def str(self, n: int, *, enc: str | None = None):
        return str(self.read(n), enc or self.enc)

    def unpack(self, t: St):
        return t.unpack(self.read(t.size))

    def f64(self) -> float:
        return F64.unpack(self.read(8))[0]

    def assert_eof(self, ver: int):
        i = self.idx
        l = len(self.v)
        assert i == l, f'incomplete read, idx={i}, len={l}, ver={ver}'


NErrStr = 37  # for YSCM and YSCD


class YTyp(IntEnum):
    ANY = 0
    INT = 1
    FLT = 2
    STR = 3
