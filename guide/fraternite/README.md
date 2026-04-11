# An example - Fraternite and Fraternite HD

_Don't just copy paste code from this page, only run them after you understand._

Game used:

- "\[140725\]\[CLOCKUP\] フラテルニテ パッケージ版"
- "\[190927\]\[CLOCKUP\] フラテルニテ HDリマスター"

## Requirements

- Python 3.13 (not 3.12 nor 3.14)
- `pip install murmurhash2 xor_cipher deflate`
- Copy the `yuri` folder into your `site_packages` or to beside your script, so we can import it
- You being able to understand and write python code

## Fraternite

Full script: [fraternite.py](fraternite.py)

### 1. Extract YPF

First, we find the ypf file containing the game's scripts.  
For this game, it's at `pac/bn.ypf`.  
For other games, it may or may not in the `pac` folder, and it may be named `ysbin.ypf`.  
Anyway, it should contain many `.ybn` files.

```python
from os import makedirs, path
from yuri.fileformat import *
import yuri.yuridec as yuridec
import yuri.yuricom as yuricom
from multiprocessing import freeze_support

# Windows need this for multiprocessing
if __name__ == '__main__':
    freeze_support()


# change to your own path
YPF_IN  = '/tmp/fraternite/game/pac/bn.ypf'
YPF_EX  = '/tmp/fraternite/extract_ypf'
YPF_VER = 490  # see below, change to your value

if 1:
    # YPF_IN: input ypf file
    # YPF_EX: folder to extract into
    with open(YPF_IN, 'rb') as fp:
        # ents: entries in ypf
        # ver: ypf version
        ents, ver = ypf_read(fp)
        print('ypf ver', ver)
    # name: file name (e.g. "ysbin\yst00001.ybn")
    # k: file kind
    # c: compression (0 - none, 1 - deflate)
    # data: file data, decompressed
    # ul: uncompressed length
    for name, k, c, data, ul in ents:
        print('file', name, k, c, ul)
        out_name = path.join(YPF_EX, *name.split('\\'))
        makedirs(path.dirname(out_name), exist_ok=True)
        with open(out_name, 'wb') as fp:
            fp.write(data)
```

Run with: `python your_script_name.py`

```
ypf ver 490
file ysbin\yst00034.ybn 0 1 92080
file ysbin\yst00145.ybn 0 1 628
file ysbin\yscfg.ybn 0 1 90
file ysbin\yst00236.ybn 0 1 5414
file ysbin\yst00292.ybn 0 1 33116
file ysbin\yst00226.ybn 0 1 89696
...
```

After successing, change the `1` after `if` to `0` to disable this code.  
Also, change `YPF_VER` to the value printed after `ypf ver`, here `490`.

### 2. Decompile

First we write basic decompiling code, append this to your script:

```python

# Because the YBN files are in a folder, we enter it
YBN_IN = path.join(YPF_EX, 'ysbin')
DEC_OUT = '/tmp/fraternite/decompile_yst'

if 1:
    # parameter 0: input folder, it should contain your ybn files directly
    # parameter 1: output folder, to which the decompiler will create files
    yuridec.run(YBN_IN, DEC_OUT)
```

#### `X is not a valid VScope` - maybe a custom version number

If YURI doesn't report this error for your game, you can skip this section.

If you run this code, you will encounter an error saying this.  
It's because Yu-ris added a field to `ysv.ybn` (YSVR) in version 481.  
This game has a version number of 490, but it actually has something earlier than that.  
We need to force YURI to process it as that version, for now we just use 480.

```python
YBN_IN = path.join(YPF_EX, 'ysbin')
DEC_OUT = '/tmp/fraternite/decompile_yst'
FORCE_VER = 480  # force version 480

if 1:
    # keyword argument "ver", force version
    yuridec.run(YBN_IN, DEC_OUT, ver=FORCE_VER)
```

#### `AssertionError; lineno guess key` - custom YSTB encryption key

If YURI doesn't report this error for your game, you can skip this section.

```
AssertionError
lineno guess key: 0x7f,0x3,0x3b,0x26,0x7c,0x3,0x3b,0x26,0x7d,0x3,0x3b,0x26,0x7a,0x3,0x3b,0x26
data\script\eris\es_button.yst
```

This means YURI used a wrong key for YSTB decryption.  
YURI has two key in it for public versions of the Yu-ris engine and will use them automatically by game version.
However, some games use custom keys for YSTB encryption, and we can guess it using that `lineno` line.  
(This only works for versions above 300)

YSTB encryption is simple XOR-ing every 4 bytes with the key.  
In YSTB files, there are 4 sections, each encrypted independently:

- Instructions (commands)
- Attributes (commands' parameters)
- Attribute Values
- Line Numbers

Let's take the first 4 bytes of the lineno line: `0x7f, 0x03, 0x3b, 0x26`  
It's the first line number in original script `data\script\eris\es_button.yst`  
Empirically, the first code line in this file is usually line number 9, in little endian: `0x09, 0x00, 0x00, 0x00`.  
We XOR it with the lineno to get the key: `0x76, 0x03, 0x3b, 0x26`.  
Then we pass `key=0x76033b26` to `yuridec`.

```python
YBN_IN = path.join(YPF_EX, 'ysbin')
DEC_OUT = '/tmp/fraternite/decompile_yst'
FORCE_VER = 480  # force version 480
YSTB_KEY = 0x76033b26

if 1:
    # keyword argument "key", YSTB decryption key
    yuridec.run(YBN_IN, DEC_OUT, ver=FORCE_VER, key=YSTB_KEY)
```

If you are using other tools to extract YPF files, then it's also possible that they have already done the decryption.  
Then you'll need to pass `key=0` here.

#### Passing YSCD for public versions with official SDK available

You can download official SDKs at [the official site](https://yu-ris.net/).  
If you are sure that your game is using a public version and you have its SDK,  
you can give YURI its `YSCom.ycd` file to restore system variable names.  
So the generated source code can be compiled by the official compiler.

```python
if 1:
    with open('YSCom.ycd', 'rb') as fp:
        yscd = YSCD.read(Rdr.from_bio(fp))
    yuridec.run(YBN_IN, DEC_OUT, ver=FORCE_VER, key=YSTB_KEY, yscd=yscd)
```

#### Other options

- `ienc`: input encoding, encoding of strings in YSTB, default `cp932`
  - there are some custom versions using UTF-8
- `oenc`: output encoding, encoding of output source files; default value depending on output syntax
  - YST (official) syntax: `cp932`
  - YURI compiler syntax: `utf-8`
- `dcls`: output syntax
  - `yuridec.YDecYuris`: default, YST (official) syntax
  - `yuridec.YDecYuri`: YURI compiler syntax, based on python ast module
- `mp_parallel`: enable or disable multiprocessing, default `True`
- `also_dump`: also output some raw data in `.dump` files, default `False`
- `word_enc`: encoding for WORD (dialog line) command  
  Some Chinese translation group modify the game to use GBK encoding

#### Done decompiling

Now we have the decompiled source code in `DEC_OUT` (here `decompile_yst`).  
Let's look into it:

For example, `data/script/userscript/00_オープニング/s001：オープニング.txt`

```
#=fla_101
GOSUB[#="MAC.EV" PSTR="ev_yuk_t01_01" PFLT2=200 PINT3=500 PSTR4='' PINT5=-1 PINT6=-2 PINT7=-2 PINT8=0 PINT9=1]

GOSUB[#="es.SND" PINT=21 PSTR2="MB1_M04_0001" PINT3=-1 PINT4=-1 PINT5=-1 PINT6=0]
クラブ女性Ａ「ふふふ…」

PREP[TEXTVAL=1];GOSUB[#="es.SND" PINT=21 PSTR2="MB2_M07_0001" PINT3=-1 PINT4=-1 PINT5=-1 PINT6=0]
クラブ女性２「ふふ…」

PREP[TEXTVAL=1];GOSUB[#="es.SND" PINT=21 PSTR2="MB4_M07_0001" PINT3=-1 PINT4=-1 PINT5=-1 PINT6=0]
クラブ女性４「ふふふっ」

PREP[TEXTVAL=1];GOSUB[#="es.SND" PINT=21 PSTR2="MB1_M04_0002" PINT3=-1 PINT4=-1 PINT5=-1 PINT6=0]
クラブ女性Ａ「見て、とっても幸せそう…」

PREP[TEXTVAL=1];GOSUB[#="es.SND" PINT=21 PSTR2="MB2_M07_0001" PINT3=-1 PINT4=-1 PINT5=-1 PINT6=0]
クラブ女性３「よかったね…本当によかった…」
```

You can use these source codes for your purposes.

However, if you are using a custom version or without official SDK, you cannot compile them with the official compiler.  
Then you'll need to use the YURI compiler. For that, go to next section.

### 3. Compile

(Remember to disable decompiling code by changing the `if 1` to `if 0`)

Before we start, we change the decompiler output syntax to YURI (`dcls=yuridec.YDecYuri`) and decompile once.
Also, enable `also_dump` to create dump files for later use (to determine an option).  
Lastly, we assume that you didn't use the `yscd` file.

First, we write basic compiling code.

```python
COM_TEMP = '/tmp/fraternite/com_work'
COM_OUT = '/tmp/fraternite/output.ypf'
DEC_YURI = '/tmp/fraternite/decompile_yuri'
WRITE_VER = 490

if 1:
    yuricom.run(
        YSTB_KEY,  # [0]: YSTB key
        DEC_YURI,  # [1]: input source files
        FORCE_VER,  # [2]: (real) version of files
        COM_TEMP,  # [3]: temporary directory for the compiler
        YBN_IN,  # [4]: for some original ybn files from the game
        COM_OUT,  # [5]: output ysbin.ypf
        t_ver=FORCE_VER,  # keyword: if you forced version, also pass this for game original files
        w_ver=WRITE_VER,  # keyword: the version number the game used
        ypf_ver=YPF_VER,  # keyword, the version number the game used for YPF
    )
```

Note the three keyword arguments, you might need them if you forced version.

#### `ValueError: malformed node or string`

This is because the game used a non-constant expression in an initial value for some variables.  
Currently YURI can't handle that, but it's usually trivially fixable by changing the code.

The error is often on `es_button.yst.yuri`.

```
S_STR[sStr1391.S] = gStr1141.S(38, 21)
S_STR[sStr1392.S] = gStr1141.S(38, 6)
```

Search for them in the source code:

```
$ grep -R 'gStr1141.S(38, 21)' decompile_yuri
decompile_yuri/data/script/puserdefine/フォルダ定義.txt.yuri:LET[gStr1141.S(38, 21)] = 'se/'
...
$ grep -R 'gStr1141.S(38, 6)' decompile_yuri
decompile_yuri/data/script/puserdefine/フォルダ定義.txt.yuri:LET[gStr1141.S(38, 6)] = 'cg/'
...
```

And replace them in `es_button.yst.yuri`:

```
S_STR[sStr1391.S] = 'se/'
S_STR[sStr1392.S] = 'cg/'
```

Then the compile should success and you get an `output.ypf`

```
$ python fraternite.py
/tmp/fraternite/decompile_yuri/data/script/eris/global.yst.yuri
/tmp/fraternite/decompile_yuri/data/script/puserdefine/productlib/global.txt.yuri
/tmp/fraternite/decompile_yuri/data/script/eris/scene/extra/vomode/global_f.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/menu/es_menu.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/saveload/es_aload.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/saveload/es_load.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/saveload/es_qload.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/saveload/es_qsave.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/saveload/es_save.yst.yuri
compile /tmp/fraternite/decompile_yuri/data/script/eris/scene/status/es_status.yst.yuri
...
```

Replace the game's `bn.ypf` (backup!) with it and run the game.
For me, the game starts normally.

#### Do some small editing

Let's test that YURI indeed is working by changing the window title in `system_start.yst.yuri`

```python
LBL = 'SYSTEM_START'
WINDOW(NO=0, CAPTION='Hello World from YURI compiler')
GO(LBL='es.ERIS')
END()
```

Compile, replace `bn.ypf`, run.

![](ss-2026-04-11_21-20-36_1775913636.png)

Also, I skipped through it for a while and it didn't crash.

## Fraternite HD

(TODO)
