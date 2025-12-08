# Yuri

A decompiler and compiler for the Yu-Ris engine, with parallelism.

Tested on v488 [Natsuzora Asterism](https://www.dlsite.com/maniax/work/=/product_id/RJ367965.html) and v494 official example

## Dependencies

> pip install murmurhash2 xor-cipher deflate

## Usage and Example

See [v494.py](v494.py)

### Running

Download 0.494 official sdk, use YSPac to pack all folders under `システム/data/`

![](pics/xfce4_screenshot.png)

Then copy `data.ypf` into `example`.

Also copy `yscfg.dat`, `yu-ris.exe`, `エンジン設定.exe`.

```
example
├── data.ypf
├── v494
├── v494-work
├── v494.ypf
├── yscfg.dat
├── yu-ris.exe
└── エンジン設定.exe
```

Run `yu-ris.exe`.

## Advantages over the official compiler

1. Parallel  
   Actually, after parsing `global.yst` and `global_f.yst`s, all other `.yst`s
   can be compiled individually thus in parallel. After which, the compiler
   assign indices to variables and fill them into YSTB's
   code section, then compress YBN files and create YPF archive. The filling-in
   and compress step is also run in parallel.  
   To compare, Natsuzora Asterism's scripts takes around 50 seconds on the official
   YSCom (also 48 seconds when disabled parallelism on Yuri) on my machine.
   It only takes 10 seconds with parallelism enabled (12 core).

```
- read global.yst.yuri and global_f.yst.yuri(s)
- [parallel]: compile .yst.yuri files
- assign indices to variables
- [parallel]: fill indices into YBN and compress YBN
```

2. Fast  
   Actually, the 48 seconds above also include compressing YBN files, while
   YSCom's 50 seconds only include compiling YBN.

3. Incremental  
   As long as related `global` and `global_f` do not change, a YST does not need
   to be recompiled if its source doesn't change.  
   Also, as long as the code does not change (only add/del empty lines, comments),
   a YBN does not need to be re-compressed.  
   After an initial full compilation, subsequent compilations usually only takes
   a few seconds.
