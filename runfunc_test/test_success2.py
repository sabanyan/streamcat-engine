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

def Mod(FIFO):
    header = True
    with open(FIFO, "w") as fifo:
        for line in sys.stdin:
            datum = line.split(',')

            # header
            if header:
                header = False
                # headerは標準入力、名前付きパイプ両方に出力する
                print(datum[0] + ',' + datum[1] + ',' + datum[2])
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + '\n')
                continue

            if datum[0] == '275399':
                print(datum[0] + ',' + datum[1] + ',' + datum[2])
            else:
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + '\n')

def Mod2(FIFO):

    header = True

    with open(FIFO, "w") as fifo:
        for line in sys.stdin:
            datum = line.split(',')

            # header
            if header:
                header = False
                # headerは標準入力、名前付きパイプ両方に出力する
                print(datum[0] + ',' + datum[1] + ',' + datum[2], end='')
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2])
                continue

            if datum[0] == '275439':
                print(datum[0] + ',' + datum[1] + ',' + datum[2], end='')
            else:
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2])

def Redirect(FIFO):
    """
    指定したFIFOに流れているデータを取得する
    """
    with open(FIFO, "r") as f:
        for line in f:
            datum = line.split(',')
            print(datum[0] + ',' + datum[1] + ',' + datum[2], end="")

f=None
f2=None
f3=None

import uuid

FIFO = 'tmp/' + str(uuid.uuid4())
FIFO2 = 'tmp/' + str(uuid.uuid4())

try:
    os.mkfifo(FIFO)
    os.mkfifo(FIFO2)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

# 　　　***【処理イメージ】***
#  ()がframe、<>が関数
#
#        (ryudo_demo)
#             ↓
#       <Mod_Command>
#    OK ↓　　　　 　NG ↓
#   (result1)   <Redirect>
#                    ↓
#              <Mod2_Command>
#            OK ↓　　　　　NG ↓
#          (result2)    <Redirect>
#                           ↓
#                       (result3)

f <<= nm.m2tee(i='../kskp/data/ryudo_demo.csv')

# result1
f <<= nm.runfunc(Mod, FIFO)
f <<= nm.m2tee(o='result/result1.csv')

# redirect
f2 <<= nm.runfunc(Redirect, FIFO)

# result2
f2 <<= nm.runfunc(Mod2, FIFO2)
f2 <<= nm.m2tee(o='result/result2.csv')

# result3
f3 <<= nm.runfunc(Redirect, FIFO2)
f3 <<= nm.m2tee(o='result/result3.csv')

# 実行
nm.runs([f,f2,f3],msg='on')

os.unlink(FIFO)
os.unlink(FIFO2)

# <気づき>
# 1. runfuncのargsにFileオブジェクトは渡せない
# runfuncの引数は、nm.runfunc(function, args)となっているが、
# argsにopen(FIFO, 'w')のようなFileオブジェクトは渡せない
# runfuncの内部でargsをdeepcopyしてからそれをfunctionに渡しているらしく、それは基本的にはできないので
# 関数内部でopenするしかなさそう
# https://stackoverflow.com/questions/32593035/why-does-deepcopy-fail-when-copying-a-complex-object
