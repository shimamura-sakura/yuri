from .common import *
VInit = tuple[Lit[YTyp.INT], int]\
    | tuple[Lit[YTyp.FLT], float]\
    | tuple[Lit[YTyp.STR], bytes]
SVarV000 = St('<B HHBB')
SVarV481 = St('<BBHHBB')
YsvMagic = b'YSVR'
SYsvHead = St('<4sIH')
TYsvHead = tuple[bytes, int, int]


@dataclass(slots=True)
class Var:
    scope: VScope
    scoex: VScoEx
    iscr: int
    ivar: int
    dims: Seq[int]
    init: VInit | None

    @classmethod
    def readV000(cls, r: Rdr):
        sc, iscr, ivar, typ, ndim = cast(Ints, r.unpack(SVarV000))
        scex = VScoEx.SYS if ivar < VMinUsr else VScoEx.DEF
        return cls(VScope(sc), scex, iscr, ivar, *cls._dims_init(r, typ, ndim))

    @classmethod
    def readV481(cls, r: Rdr):
        sc, scex, iscr, ivar, typ, ndim = cast(Ints, r.unpack(SVarV481))
        return cls(VScope(sc), VScoEx(scex), iscr, ivar, *cls._dims_init(r, typ, ndim))

    @classmethod
    def _dims_init(cls, r: Rdr, typ: int, ndim: int):
        dims = [r.ui(4) for _ in range(ndim)]
        match (typ := YTyp(typ)):
            case YTyp.UNK: init = None
            case YTyp.INT: init = (typ, r.si(8))
            case YTyp.FLT: init = (typ, r.f64())
            case YTyp.STR: init = (typ, r.read(r.ui(2)).tobytes())  # TODO: parse expr
        return dims, init

    def writeV000(self, f: BinIO, enc: str):
        typ = 0 if self.init is None else self.init[0]
        f.write(SVarV000.pack(self.scope, self.iscr, self.ivar, typ, len(self.dims)))
        self._write_dims_init(f, enc)

    def writeV481(self, f: BinIO, enc: str):
        typ = 0 if self.init is None else self.init[0]
        f.write(SVarV481.pack(self.scope, self.scoex, self.iscr, self.ivar, typ, len(self.dims)))
        self._write_dims_init(f, enc)

    def _write_dims_init(self, f: BinIO, enc: str):
        f.writelines(d.to_bytes(4, LE) for d in self.dims)
        match self.init:
            case None: pass
            case (YTyp.INT, i): f.write(i.to_bytes(8, LE, signed=True))
            case (YTyp.FLT, v): f.write(F64.pack(v))
            case (YTyp.STR, v):
                f.write(len(v).to_bytes(2, LE))
                f.write(v)  # TODO: assemble


@dataclass(slots=True)
class YSVR:
    ver: int
    vars: list[Var]

    @classmethod
    def read(cls, r: Rdr, *, v: int | None = None):
        mag, v_, nvar = cast(TYsvHead, r.unpack(SYsvHead))
        assert mag == YsvMagic, f'not YSV magic: {mag}'
        assert (v := v or v_) in VerRange, f'unsupported version: {v}'
        fun = Var.readV481 if v >= 481 else Var.readV000
        vars = [fun(r) for _ in range(nvar)]
        r.assert_eof(v)
        return cls(v, vars)

    def write(self, f: BinIO, enc: str = CP932, *, v: int | None = None):
        assert (v := v or self.ver) in VerRange, f'unsupported version: {v}'
        f.write(SYsvHead.pack(YsvMagic, v, len(self.vars)))
        fun = Var.writeV481 if v >= 481 else Var.writeV000
        for var in self.vars:
            fun(var, f, enc)
