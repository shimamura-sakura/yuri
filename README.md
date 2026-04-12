# Yuri

A decompiler and compiler for the Yu-Ris engine, with parallelism.

Tested on many versions, including public and commercial.

## Requirements

1. Python 3.13.x (not 3.12 nor 3.14)
2. `pip install murmurhash2 xor_cipher deflate`

## Usage

- [main.py](main.py)
- [A more detailed readme](yuri.md)
- [Example - Fraternite and Fraternite HD](guide/fraternite/README.md)
- [Example - Unionism Quartet](guide/unionism/README.md)

## Other

patch_text.py in the root folder has two functions: ext_text, pat_text.
They are used to extract(ext) and edit(pat) text in .yuri files (dialog line only).
Both their arguments are (.yuri directory, text directory).
As usual, freeze_support is needed.

gbk.py has a patch_exe(infile, outfile) function, it makes the Yu-Ris exe uses gbk instead of shiftjis.
modified from https://github.com/jyxjyx1234/YURIS_TOOLS/blob/main/GBK.py
