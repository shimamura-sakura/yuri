from struct import Struct
from os import walk, path
from collections.abc import Buffer
from encodings import search_function
from codecs import CodecInfo, register as register_codec
from typing import Sequence as Seq, NamedTuple, Any, BinaryIO
__all__ = ['CustomEncoder']


def create_mapping(idir: str, oenc: str, ienc: str, ends: Seq[str]):
    # map: fail -> good
    chars: set[str] = set()
    for dirpath, _, filenames in walk(idir):
        for filename in filenames:
            for end in ends:
                if filename.endswith(end):
                    break
            else:
                continue
            with open(path.join(dirpath, filename), 'r', encoding=ienc) as fp:
                chars.update(fp.read())
    # categorize good and bad characters in target encoding
    goods: list[str] = []
    fails: list[int] = []
    for ch in sorted(chars):
        try:
            ch.encode(oenc)
            goods.append(ch)
        except UnicodeEncodeError:
            fails.append(ord(ch))
    # map bad characters to good characters, keeping known good characters
    goodset = set(map(ord, goods))
    failmap: list[tuple[int, int]] = []
    for ich in range(256, 65536):
        try:
            if ich in goodset:
                continue
            if len(fails) == 0:
                break
            chr(ich).encode(oenc)
            failmap.append((fails.pop(), ich))
        except UnicodeEncodeError:
            pass
    assert len(fails) == 0, 'unable to map all failed characters'
    return failmap


def notimpelemented(input: Buffer, errors: str = 'strict'):
    raise NotImplemented


class CustomEncodeFunc(NamedTuple):
    ofunc: Any
    c_map: dict[int, int]

    def __call__(self, input: str, errors: str = 'strict') -> tuple[bytes, int]:
        return self.ofunc(input.translate(self.c_map), errors)


SGoodFail = Struct('<HH')


class CustomEncoder(NamedTuple):
    name: str
    info: CodecInfo
    fmap: list[tuple[int, int]]

    @classmethod
    def create(cls, iroot: str, o_enc: str, name: str,
               i_enc: str = 'utf-8', ends: Seq[str] = ('.yuri',)):
        assert (oinfo := search_function(o_enc)) is not None
        flst = create_mapping(iroot, o_enc, i_enc, ends)
        func = CustomEncodeFunc(oinfo.encode, dict(flst))
        info = CodecInfo(func, notimpelemented, name=name)
        return cls(name, info, flst)

    def register(self):
        return register_codec(self)

    def write_mapbin(self, f: BinaryIO):
        for fail, good in self.fmap:
            f.write(SGoodFail.pack(good, fail))

    def __call__(self, name: str):
        if name == self.name:
            return self.info
        return None
