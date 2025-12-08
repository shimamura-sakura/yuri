import yuri.yuridec as yuridec
import yuri.yuricom as yuricom
yuridec.run('files/v494', 'example/v494', dcls=yuridec.YDecYuri)
yuricom.run(yuricom.KEY_290, 'example/v494', 494,
            'example/v494-work', 'files/v494', 'example/v494.ypf')
