import yuri.yuridec as yuridec
import yuri.yuricom as yuricom

# decompile into official YST syntax, compile with official tools
yuridec.run('files/v494', 'example/v494', dcls=yuridec.YDecYuris)

# decompile into my own YURI syntax (based on python ast module)
yuridec.run('files/v494', 'example/v494', dcls=yuridec.YDecYuri)

# compile YURI syntax into YBN then YPF, enable parallelism (default ON)
yuricom.run(yuricom.KEY_290, 'example/v494', 494,
            'example/v494-work',  # folder to store intermediate results
            'files/v494',  # where original ysv.ybn, yse.ybn, yscfg.ybn go
            'example/v494.ypf',  # output file
            mp_parallel=True)
