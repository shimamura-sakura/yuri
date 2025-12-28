from yuri.fileformat import *
from multiprocessing import freeze_support
import yuri.yuridec as yuridec
import yuri.yuricom as yuricom

if __name__ == '__main__':
    freeze_support()
    # decompile into official YST syntax, compile with official tools
    # use ycd file to recover system variable names
    with open('example/v494.ycd', 'rb') as fp:
        yscd = YSCD.read(Rdr.from_bio(fp))
        cdict = {v.name: (v.typ, i) for i, v in enumerate(yscd.vars)}
    yuridec.run('files/v494', 'example/v494', dcls=yuridec.YDecYuris, yscd=yscd)

    # decompile into my own YURI syntax (based on python ast module)
    yuridec.run('files/v494', 'example/v494', dcls=yuridec.YDecYuri, yscd=yscd)

    # compile YURI syntax into YBN then YPF, enable parallelism (default ON)
    # use ycd to enable using original names for system variables
    yuricom.run(yuricom.KEY_290, 'example/v494', 494,
                'example/v494-work',  # folder to store intermediate results
                'files/v494',  # where original ysv.ybn, yse.ybn, yscfg.ybn go
                'example/v494.ypf',  # output file
                cdict=cdict, mp_parallel=True)
