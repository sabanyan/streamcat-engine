# データ作成用

import nysol.mcmd as nm
# nm.mread(i=dat,o='test.csv').run()
# dat=[
# ["customer","date","amount"],
# ["A","20180101",5200],
# ["B","20180101",800],
# ["B","20180112",3500],
# ["A","20180105",2000],
# ["B","20180107",4000]
# ]

import os
import errno
import sys

def Mod(FIFOs):
    header = True

    with open(FIFOs[0], "w") as fifo, open(FIFOs[1], "w") as fifo2:
        for line in sys.stdin:
            datum = line.split(',')

            # header
            if header:
                header = False
                # headerは標準入力、名前付きパイプ両方に出力する
                print(datum[0] + ',' + datum[1] + ',' + datum[2])
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + '\n')
                fifo2.write(datum[0] + ',' + datum[1] + ',' + datum[2] + '\n')
                continue

            if datum[0] == '275399':
                print(datum[0] + ',' + datum[1] + ',' + datum[2])
            elif datum[0] == '275420':
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + '\n')
            else:
                fifo2.write(datum[0] + ',' + datum[1] + ',' + datum[2] + '\n')

def Redirect(FIFO):
    with open(FIFO, "r") as f:
        for line in f:
            datum = line.split(',')
            print(datum[0] + ',' + datum[1] + ',' + datum[2], end="")

f=None
f2=None
f3=None

import uuid
# 毎回違うファイル名にするためにuuidを使用　
FIFO = 'tmp/' + str(uuid.uuid4())
FIFO2 = 'tmp/' + str(uuid.uuid4())

try:
    os.mkfifo(FIFO)
    os.mkfifo(FIFO2)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

f <<= nm.m2tee(i='../kskp/data/ryudo_demo.csv')

# OK部分
f <<= nm.runfunc(Mod, [FIFO, FIFO2])
f <<= nm.mcut(f=0,x=True,o='result/result.csv')
# f <<= nm.m2tee(o='result.csv')
# NG部分
f2 <<= nm.runfunc(Redirect, FIFO)
f2 <<= nm.m2tee(o='result/fifo_result.csv')

f3 <<= nm.runfunc(Redirect, FIFO2)
f3 <<= nm.m2tee(o='result/fifo_result2.csv')

# f.run()
# 実行
nm.runs([f,f2,f3],msg='on')

os.unlink(FIFO)
os.unlink(FIFO2)

# ↓は駄目
# f.run()
# f2.run()
