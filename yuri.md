# The Yu-ris Engine and its file formats, and the usage of Yuri

[toc]

## The Yu-ris Engine

Yu-ris is a game engine, running compiled scripts on a virtual machine.  
The script can use many commands to manipulate picture layers, sound and others.  
There are also conventional programming language features, like variables and control flow.  
Let's see these by a sample code (in official YST syntax):

```
S_STR[$cgFile="hello.png"] // Note for YSVR: this will go into YSVR
#SomeLbl
INT[$windId=1] // Note for YSVR: this will not
STR[$cgName="HelloCG"]
IF[$cgName!="ByeCG"]
  こんにちは // This line will become a WORD command, and will be handled by the E-ris library.
  GO[#=AnotherLbl]
  #AnotherLbl
  CG[ID=$cgName FILE=$cgFile E=1 X=0 Y=0 Z=3]
ELSE[$cgName=="WtfCG"]
  WINDOW[NO=$windId CAPTION="Hello"]
  GOSUB[#=SomeSub PINT=1 PSTR2="HAHA"]
ELSE[]
  GO[#=SomeLbl]
IFEND[]
#SomeSub
INT[@a=@_PINT(1)]
STR[$b=$_PSTR(2)]
LOOP[SET=@a]
  #YetAnother
  LOOPBREAK[]
LOOPEND[]
RETURN[RINT=@a+1 RSTR=$b+"NONO"]
```

There are also macros, but they will be expanded at compile time.

For the meaning of these commands, please read the official document at:
https://yu-ris.net/manual/yu-ris/index.html

### The E-ris library

However, people generally don't write Yu-ris code directly.
They often use macros offered by E-ris to make visual novels.
People generally only write dialog lines and call E-ris macros.
E-ris will handle the displaying part and do all other visual novel things.

The code of E-ris is very messy, and sometimes it even use undocumented parameters.
And there are special commands for E-ris use.

For example, each time you have a dialog line, the engine stores it in a system variable called `$_TEXT` and suspend the visual novel script thread. Then E-ris wakes up, reads `$_TEXT` and draws it to a CG layer, finally displays it.

### Custom versions

The author of Yu-ris and E-ris made many customized versions for commercial titles.
Sometimes there are new commands special to one title.
Sometimes there are custom encryption keys for YSTB.
Sometimes there are new features in E-ris (e.g. image font).

Sometimes they use original version numbers.
Sometimes they use a custom version number, not reflecting the real version they derive from.
Then we need to guess them by file format, release date etc.

Fortunately there are no breaking changes to file formats.

### Extremely old versions

By this, I mean very very old, like 1xx from around 2004.
These versions are not in the topic of this article.
We only talk about 2xx to 4xx here.

### Let's Go

Now let's see how these commands become those YBN files.

## File Formats

There are many types of YBN files, differentiated by their first four bytes.
Codes for them are in `yuri/fileformat`

- YSCM(ysc.ybn): command definitions (command and argument names)
- YSER(yse.ybn): error definitions (error messages)
- YSCF(yscfg.ybn): game configurations like window size, enable sound and others. generated from game project's `config/projectconfig.txt`
- YSTD(yst.ybn): general informations about all scripts (variable count and text count)
- YSTL(yst_list.ybn): list of script files, including their original names, count of variables, labels and texts
- YSLB(ysl.ybn): labels (name, code position)
- YSVR(ysv.yvn): variables (type, array dimensions, initial value)
- YSTB(yst%05d.ybn): script file, commands and their arguments

For informations about YSCM, YSER, YSCF, YSTD, please read [Notes.txt](https://github.com/arcusmaximus/VNTranslationTools/blob/main/VNTextPatch.Shared/Scripts/Yuris/Notes.txt). I don't have anything to add about them.

For the rest YSTL, YSLB, YSVR and YSTB, here we go.

### YSTL (Script List)

This file is a list of all script files. It contains their original names and some counts about their code (variable, label, text count).

```
int magic = 'YSTL'
int version
int numScripts
Script[numScripts]
    int index
    int pathLength
    byte path[pathLength]
    FILETIME modificationTime // a Windows C data type
    int numVariables // count of variables, local (INT, STR, FLT) and static (S_INT, ...)
    int numLabels    // count of labels (#SomeLbl, #AnotherLbl)
    int numTexts     // count of WORD command, present only since version 474
```

For an entry, `"yst%05d.ybn" % index` is the YBN file for it.

Sometimes an entry doesn't have a YBN file corresponding to it.
Then it's numVariables will be negative.

Yuri uses the `path` to restore the original file tree structure of the game.

### YSLB (Labels)

This file lists all labels from all script files.

```
int magic = 'YSLB'
int version
int numLabels
int labelHashRanges[256] // See note

Label[numLabels]
    byte nameLength
    byte name[nameLength]
    int nameHash
    int codePos
    int scriptIndex
    byte if_level   // different from Notes.txt
    byte loop_level // different from Notes.txt
```

Labels are sorted by their `nameHash`.
And the index of the first label with a nameHash whose MSB is B is stored at labelHashRanges[B]
When looking up a label, the game does something like this:

```python
def find_label(name: str):
  h = hash_name(name)
  i = labelHashRanges[h >> 24] # The highest byte

  while i < len(labels): # Linear search
    if labels[i].name == name:
      # script and code position
      return (scripts[labels[i].scriptIndex], labels[i].codePos)

  raise IndexError('label not found')
```

In 2xx versions, `codePos` is a byte offset into the instruction section of YSTB.  
In 3xx and newer versions, `codePos` is an index into the instruction array of YSTB.

Sometimes, a jump or call will go out or into an IF or LOOP block.
`if_level` and `loop_level` is for these occasions.  
`#AnotherLbl` has `if_level=1, loop_level=0`.
`#YetAnother` has `if_level=0, loop_level=1`.
Some labels might have both non-zero.

### YSVR (Variables)

This file lists all variables from the game and script.

```
int magic = 'YSVR'
int version
short numVariables // just the entry count, not total variable count, that's in YSTD
Variable[numVariables]
    byte scope (1 = global, 2 = static, 3 = folder)
    byte scope_ex (0 = system, 1 = default, 2 = G_XXX2, 3 = G_XXX3) // only present since v481
    short scriptId
    short variableIndex
    byte type (1 = long (INT), 2 = double (FLT), 3 = string (STR))
    byte numDimensions
    int dimensionSize[numDimensions]
    if type == 0
        // none
    elseif type == 1
        long value
    elseif type == 2
        double value
    elseif type == 3 // STR
        short exprLength
        byte expr[exprLength] // expression vm code for one string value, see YSTB
```

**Note on variables**

- Each variable has an index, system variables are 0-999, user variables are 1000-above
- Each variable has a type (INT, STR, FLT) and can be an array
- Each variable has a scope (G\_ global, S\_ static, F\_ folder, and local)
- Since 481, global scope is further divided into G_xxx, G_xxx2, G_xxx3

This file doesn't contain local variables, they only takes an index and is defined using a command.
Indices for local variables are skipped, so variableIndex's are not continuous.

Other variable commands of nonlocal scope (G\_, S\_, F\_) will not go
into YSTB files in newer versions (4xx), and Yu-ris author recommends not to put
them in execution paths (in older versions).

The first 1000 entries will always present and are for system variables.
Non-existent system variables will still have an entry, but with type == 0.

STR uses an expression for initial value. They are not always a constant expression.
This is the case for a few variables in a few games. But they mostly are.

There are no names, so system variable names are recovererd from official YSCom.ycd
and user variable names are lost in compilation.

### YSTB (Script)

#### V300 and above (new format)

```
int magic = 'YSTB'
int version
// V300
int numInstructions
int instructionsSize (= numInstructions * 4)
int attributeDescriptorsSize
int attributeValuesSize
int lineNumbersSize (should = instructionsSize)
int padding == 0
// Here 32 Bytes

Instruction[numInstructions]
    byte opcode
    byte numAttributes
    short paramCount // See note

AttributeDescriptor[attributeDescriptorsSize / 12]
    short id
    byte type (1 = INT, 2 = FLT, 3 = STR, 0 for a few special attributes)
    byte assign_op (0-8: =, +, -, *, /, %, &, |, ^)
    int size
    int offsetInAttributeValues

byte attributeValues[attributeValuesSize]

int lineNumbers[lineNumbersSize / 4] // count = numInstructions
```

There are three big parts: Instruction, Attributes, AttributeValues.
Read them as two arrays and a bytearray.
For each instruction, take numAttributes from Attributes as its arguments.
One lineNumber for each instruction.

Each of the three is XOR encrypted independently.  
There are two keys for public versions: (200+: 0x07B4024A, 290+: 0xD36FAC96).  
Commercial titles often use different keys, you can guess them using the lineNumbers array.

**Guessing the key on V300+**

The first file is often "es_button.yst" and the first command line is often line 9.
Then 9 ^ (the first line number) is the encryption key.

Alternatively, as the first line number is usually very small (< 16),
you can try changing only the lower half of the first byte of the first line number.  
Like: 0x3\[E\]\_DFA895 -> 0x3\[0\-F\]\_DFA895

**Note on commands**

Consider this command:

`VARACT[SET=@SomeVar() SIZE+=1]`

Each command can has some arguments (Notes.txt call it Attribute).  
And special to Yu-ris is that an argument can has an assignment operator (e.g. +=, increase).  
Here for `SIZE` it's the case, it means increase the size of array `SomeVar` by 1.

(below "Instruction" means command)

**Attributes**

opcode is an index into YSCM/YSCD's command array.  
Attr.id is an index into YSCM/YSCD's command's attribute array.  
Yuri uses these two to restore commands

For some special commands and attributes, Attr.id doesn't have a meaning and is not an index.
And even the size and offset is not a range into attributeValues.
For `WORD`, it is a data range, but the data is a plain string.

For most attributes, attributeValues\[offsetInAttributeValues:\]\[:size\] is an expression using
the [Expression VM](https://github.com/arcusmaximus/VNTranslationTools/blob/main/VNTextPatch.Shared/Scripts/Yuris/Notes.txt#L181) format. Decompiling them is like converting from RPN back to middle fixed.

Special cases:

- AND as a unary operator meaning take variable address (when only one value on stack).
- Those referencing a variable, but type is not 0x24 or 0x40: taking address or converting type (in old versions).
- ...

Special commands:

- IF, ELSE(with arguments, as an "else if"):
  - attr\[0\]: condition expression
  - attr\[1\]: else: size = code position, offset = the first data offset of the target command
  - attr\[2\]: ifend: size / offset, same as above
- LOOP
  - attr\[0\] (SET=): loop count, -1 = infinity
  - attr\[1\]: loopend: size / offset, same as IF
- WORD
  - attr\[0\]: size / offset is a plain string, not an expression, type = 0
- "\_" (a variable as a WORD)
  - attr\[0\]: no name; size / offset is an expression (regular)
- those defining variables (G\_, S\_, F\_, INT...) and LET (assign)
  - attributes have no name
  - attr\[0\]: for LET, might have assign operator; variable to be assigned
  - attr\[1\]: value to be assigned
- RETURNCODE (after each line of dialog, to suspend the thread ?)
  - attr\[0\]: size as the code
- ...

`paramCount` field:

For GOSUB and RETURN commands, it means the count of PINT, PSTR, RINT, RSTR attributes.
These are the parameters count to the "function call" and "function return".
In some versions, this field is not straightforwardly a total count, but a mix of count for each type.
This is `opt_v555_npar`, as I first discovered it in an v555 game.

There are too many special cases, please read `fileformat/ystb.py` and `decompiler/base.py` for detail.

#### V200 (old format)

```
int magic = 'YSTB'
int version < 300
// V200
int commandsLength
int expressionsLength
int expressionsOffset
... paddings ...
// Here 32 Bytes

Instruction:
  byte opcode
  byte attrCount
  int  lineNumber

  Attribute[attrCount]
    // Same as V300

Expression:
  // Same as V300
```

In V200+, Instruction and Attributes is a combined section.
Each instruction's attributes follows it.

In V290, RETURNCODE's attribute doesn't have `offset` field, so it's only 8 byte.

The two sections is XOR encrypted.

## The usage of Yuri

Currently, you should use exactly Python 3.13, as there are issues with 3.12 or 3.14.
Revision number should not matter.

### YPF

```python
from os import makedirs
from os.path import dirname
from yuri.fileformat import ypf

with open('YPF_FILE', 'rb') as fp:
  ents, ver = ypf.read(
    fp, # python file (BinaryIO) to be read
    # - below, keyword arguments, all optional -
    v: int = 494,       # force version
    enc: str = 'cp932', # filename encoding
    # - usually inferred from version number -
    nl_map: bytes, # map name size: f.read(nl_map[original_value])
    nb_xor: bytes, # xor name bytes, as a map: name = name.translate(nb_xor)
    # check hash (data, expected), return None when ok, return actual hash when actual != expected
    h_name: Callable[[bytes, int], int | None], # hash name
    h_file: Callable[[bytes, int], int | None], # hash file data
    log: TextIO, # log file, (open 'w')
    do_decompress: bool = True, # is ents.data decompressed ?
  )
  print(ver) # ypf version

for name, k, c, data, ul in ents:
  # name: pathname, e.g. "ysbin\ysv.ybn"
  # k: kind of file, maybe related to file extension ? idk
  # c: compression, 0 - none, 1 - deflate
  # data: decompressed data
  # ul: decompressed size
  with open(name, 'wb') as fp:
    fp.write(data)


with open('YPF_REMAKE', 'wb') as fp:
  # ents.c
  #  0: don't compress
  #  1: do compress, data is uncompressed
  # -1: don't compress, data is already compressed (as deflate)
  ypf.make(
    ents, # same as ypf.read
    ver,  # version, you can copy this from ypf.read return value
    fp,   # python file (BinaryIO) to be written
    # - below, keyword arguments, all optional -
    enc: str = 'cp932', # filename encoding
    # - same as ypf.read -
    nl_map, nb_xor,
    h_name, h_file, # we use it to generate a hash
    comp: Callable[[Buffer], bytes], # deflate compressor
    force_comp: bool, # use compression even for those which c=0
    log: TextIO, # log file, (open 'w')
  )
```

### Decompiler

```python
from yuri.fileformat import *
from multiprocessing import freeze_support
import yuri.yuridec as yuridec
import yuri.yuricom as yuricom

if __name__ == '__main__':
  freeze_support() # for multiprocessing, especially on Windows

  # Do this if you have the official Yu-ris SDK, or skip this and don't pass yscd and cdict
  with open('YSCom.ycd', 'rb') as fp:
    yscd = YSCD.read(Rdr.from_bio(fp))
    cdict = {v.name: (v.typ, i) for i, v in enumerate(yscd.vars)} # for passing to yuricom.run

  yuridec.run(
    'input_ysbin_folder', # input ybn files in this folder
    'output_src_folder' , # output source files into this folder
    key=0xDEADBEEF,       # YSTB encryption key, pass 0 if already decrypted by other tools, pass None to use the public version key
    ienc: str = 'cp932' , # text encoding in ybn files, often cp932, some game use utf-8 or others
    oenc: str | None    , # output source encoding, default depending on output syntax (yst - cp932, yuri - utf8)
    yscd: YSCD | None = yscd, # YSCom.ycd, for system variable names, should use this for yst syntax
    dcls, # pass yuridec.YDecYuris or yuridec.YDecYuri for official YST or my YURI syntax
    mp_parallel: bool, # enable or disable multiprocessing, default ON
    also_dump: bool, # also dump raw informations in YSTB, YSVR, YSLB etc.
    ver: int, # force parse as version, when working with custom version numbers
    word_enc: str | None, # some Chinese groups change WORD command to GBK, but other strings are still CP932, then pass 'gbk' to this
  )
```

Common Errors:

- "lineno guess key": maybe wrong YSTB key
  - see above YSTB format, try to guess a key
  - already decrypted, pass key=0
- error about YSVR (see Python traceback): Maybe wrong real version due to a custom version number, try passing ver=481 / ver=480
- string decoding error: maybe the game is utf-8, try ienc='utf-8'; maybe the game is Chinese translated, try word_enc='gbk'

### Compiler

```python
from yuri.fileformat import *
from multiprocessing import freeze_support
import yuri.yuridec as yuridec
import yuri.yuricom as yuricom

if __name__ == '__main__':
  freeze_support() # for multiprocessing, especially on Windows

  # Do this if you have the official Yu-ris SDK, or skip this and don't pass yscd and cdict
  with open('YSCom.ycd', 'rb') as fp:
    yscd = YSCD.read(Rdr.from_bio(fp))
    cdict = {v.name: (v.typ, i) for i, v in enumerate(yscd.vars)} # for passing to yuricom.run

  yuricom.run(
    0xDEADBEEF, # YSTB key
    'input_src_folder', # source file (YURI syntax, .yuri) directory
    495, # game version (real version, not custom version number)
    # working directory to store some intermediate file, you can delete it
    'temp_directory', # wroot: str
    # we need original ysv, ysc, yse, yscfg from your game, place them in this folder
    'original_ysbin_folder', # troot: str
    # output YPF file
    'ysbin.ypf', # o_ypf: str
    # - below optional -
    i_enc = 'utf-8', # encoding of input source files, default utf-8
    t_enc = 'cp932', # encoding of original ysbin files, default cp932
    t_ver: int|None, # force version of original ysbin files, like in yuridec.run
    w_ver: int|None, # version number in output ybns, pass your game's custom version number here, e.g. ver=480 but w_ver=554
    o_enc = 'cp932', # encoding in output ybn files, default cp932, see above yuridec, you may need to pass utf8 or gbk
    cdict = cdict,   # if you passed yscd to yuridec, then you need this (for recognizing system variable names)
    mp_parallel: bool, # enable or disable multiprocessing, default ON
    ypf_ver: int,    # YPF version, some custom game use 500, default equal to game version
    # turn on also_dump in yuridec and find some GOSUBs in .dump files
    # if their `npar` is very strange, then pass True to this
    opts = ComOpts(opt_v555_npar=False)
  )
```
