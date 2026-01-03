from .common import *
YstlMagic = b'YSTL'
SYstlHead = St('<4sII')
TYstlHead = tuple[bytes, int, int]
SScrHead = St('<II')
SScrV200 = St('<Q2i')
SScrV473 = St('<Q3i')
TScrHead = tuple[int, int]


@dataclass(slots=True)
class Scr:
    iscr: int
    path: str
    time: int
    nvar: int
    nlbl: int
    ntext: int = 0

    @classmethod
    def read(cls, r: Rdr, st: St, i: int):
        iscr, plen = cast(TScrHead, r.unpack(SScrHead))
        assert iscr == i, f'iscr({iscr}) != i{i}'
        return cls(iscr, r.str(plen), *r.unpack(st))

    def writeV200(self, f: BinIO, enc: str):
        nb = bytes(self.path, enc)
        f.writelines((SScrHead.pack(self.iscr, len(nb)), nb))
        f.write(SScrV200.pack(self.time, self.nvar, self.nlbl))

    def writeV477(self, f: BinIO, enc: str):
        nb = bytes(self.path, enc)
        f.writelines((SScrHead.pack(self.iscr, len(nb)), nb))
        f.write(SScrV473.pack(self.time, self.nvar, self.nlbl, self.ntext))


@dataclass(slots=True)
class YSTL:
    ver: int
    scrs: list[Scr]

    @classmethod
    def read(cls, r: Rdr, *, v: int | None = None):
        mag, v_, nscr = cast(TYstlHead, r.unpack(SYstlHead))
        assert mag == YstlMagic, f'not yst_list.ybn magic: {mag}'
        assert (v := v or v_) in VerRange, f'unsupported version: {v}'
        st = SScrV473 if v >= 473 else SScrV200
        scrs = [Scr.read(r, st, i) for i in range(nscr)]
        r.assert_eof(v)
        return cls(v, scrs)

    def write(self, f: BinIO, enc: str = CP932, *, v: int | None = None):
        assert (v := v or self.ver) in VerRange, f'unsupported version: {v}'
        f.write(SYstlHead.pack(YstlMagic, v, len(self.scrs)))
        wfn = Scr.writeV477 if v >= 473 else Scr.writeV200
        for s in self.scrs:
            wfn(s, f, enc)

    def print(self, f: TextIO = stdout):
        f.write(f'YSTL ver={self.ver} nscr={len(self.scrs)}\n')
        f.writelines(f'[{i}] {l}\n' for i, l in enumerate(self.scrs))
