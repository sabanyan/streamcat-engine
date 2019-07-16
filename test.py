import nysol.mcmd as nm
import subprocess

# できるやつ
f = None
# f <<= nm.cmd('cat kskp/data/2500.csv')
# f <<= nm.cmd('mcut i=kskp/data/2500.csv f=0,1,2,3,4 -x')
# args = {}
# 駄目
# args['o'] = ['kskp/data/result/result.csv','kskp/data/cache_frames/cache.csv','kskp/data/cache.csv','kskp/data/cache2.csv']
# いける
# args['o'] = 'kskp/data/cache_frames/cache.csv'
# f <<= nm.m2tee(args)
f <<= nm.mcut(f='0,1,2,3,4,5,6,7,8,9,10',x=True,i='kskp/data/2500.csv')
f <<= nm.mcut(f='0,1,2,3,4,5',x=True)
f.run()

# できない（片方だけ出力される）
# f = None
# f <<= nm.cmd('cat kskp/data/2500.csv')
# f.m2tee(o='kskp/data/result/result.csv').m2tee(o='kskp/data/cache_frames/cache.csv').run()

# これはできる（重複列がない場合）
# f = None
# f <<= nm.mcut(i='kskp/data/2500.csv', f='0,1,2,3,4,5', x=True)
# f <<= nm.m2tee(o='kskp/data/result/result.csv')
# f <<= nm.m2tee(o='kskp/data/cache_frames/cache.csv')
# f.run()

# def msubprocess():
#     process = subprocess.Popen(['mchkcsv', 'i=kskp/data/2500.csv'], stdout=subprocess.PIPE)
#     stdout, stderr = process.communicate()
#     print(stdout.decode("utf8"))
#
# f = None
# f <<= nm.runfunc(msubprocess)
# f <<= nm.m2tee(o='kskp/data/result/result.csv')
# f <<= nm.m2tee(o='kskp/data/cache_frames/cache.csv')
# f.run()
