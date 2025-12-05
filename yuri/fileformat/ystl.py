from .common import *
YstlMagic = b'YSTL'
SYstlHead = St('<4sII')
TYstlHead = tuple[bytes, int, int]
SScrHead = St('<II')
SScrV200 = St('<Q2i')
SScrV470 = St('<Q3i')
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
    def read(cls, r: Rdr, st: St):
        iscr, plen = cast(TScrHead, r.unpack(SScrHead))
        return cls(iscr, r.str(plen), *r.unpack(st))

    def writeV200(self, f: BinIO, enc: str):
        nb = bytes(self.path, enc)
        f.writelines((SScrHead.pack(self.iscr, len(nb)), nb))
        f.write(SScrV200.pack(self.time, self.nvar, self.nlbl))

    def writeV470(self, f: BinIO, enc: str):
        nb = bytes(self.path, enc)
        f.writelines((SScrHead.pack(self.iscr, len(nb)), nb))
        f.write(SScrV470.pack(self.time, self.nvar, self.nlbl, self.ntext))


@dataclass(slots=True)
class YSTL:
    ver: int
    scrs: list[Scr]

    @classmethod
    def read(cls, r: Rdr, *, v: int | None = None):
        mag, v_, nscr = cast(TYstlHead, r.unpack(SYstlHead))
        assert mag == YstlMagic, f'not yst_list.ybn magic: {mag}'
        assert (v := v or v_) in VerRange, f'unsupported version: {v}'
        st = SScrV470 if v >= 470 else SScrV200
        scrs = [Scr.read(r, st) for _ in range(nscr)]
        r.assert_eof(v)
        return cls(v, scrs)

    def write(self, f: BinIO, enc: str = CP932, *, v: int | None = None):
        assert (v := v or self.ver) in VerRange, f'unsupported version: {v}'
        f.write(SYstlHead.pack(YstlMagic, v, len(self.scrs)))
        wfn = Scr.writeV470 if v >= 470 else Scr.writeV200
        for s in self.scrs:
            wfn(s, f, enc)
