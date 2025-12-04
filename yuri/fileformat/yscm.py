from .common import *
YscMagic = b'YSCM'
SYscHead = St('<4sIII')
TYscHead = tuple[bytes, int, int, int]


@dataclass(slots=True)
class MArg:
    name: str
    typ: YTyp
    unk: int

    @classmethod
    def read(cls, r: Rdr):
        name = r.sz()
        typ, unk = r.read(2)
        return cls(name, YTyp(typ), unk)


@dataclass(slots=True)
class MCmd:
    name: str
    args: list[MArg]

    @classmethod
    def read(cls, r: Rdr):
        name = r.sz()
        narg = r.byte()
        return cls(name, [MArg.read(r) for _ in range(narg)])


@dataclass(slots=True)
class YSCM:
    ver: int
    cmds: list[MCmd]
    errs: list[str]
    b256: memoryview

    @classmethod
    def read(cls, r: Rdr, *, v: int | None = None):
        mag, v_, ncmd, pad = cast(TYscHead, r.unpack(SYscHead))
        assert mag == YscMagic, f'not YSC magic: {mag}'
        assert (v := v or v_) in VerRange, f'unsupported version: {v}'
        assert pad == 0, f'nonzero padding: {pad:0>8x}'
        cmds = [MCmd.read(r) for _ in range(ncmd)]
        errs = [r.sz() for _ in range(NErrStr)]
        b256 = r.read(256)
        r.assert_eof(v)
        return cls(v, cmds, errs, b256)
