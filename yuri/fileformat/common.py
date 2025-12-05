from sys import stdout
from enum import IntEnum
from struct import Struct as St
from dataclasses import dataclass
from typing import cast, BinaryIO as BinIO, TextIO
from typing import Literal as Lit, Sequence as Seq, Callable
VerRange = range(200, 501)
LE = 'little'
CP932 = 'cp932'
F64 = St('<d')
Ints = tuple[int, ...]


class Rdr:
    __slots__ = ['idx', 'enc', 'b', 'v']
    idx: int
    enc: str
    b: bytes
    v: memoryview

    @classmethod
    def from_bio(cls, bio: BinIO, enc: str = CP932):
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
VMinUsr = 1000


class YTyp(IntEnum):
    UNK = 0
    INT = 1
    FLT = 2
    STR = 3


class VScope(IntEnum):
    G = 1
    S = 2
    F = 3


class VScoEx(IntEnum):
    SYS = 0
    DEF = 1
    G2 = 2
    G3 = 3
