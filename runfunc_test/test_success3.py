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
            data_str = ','.join(datum)

            # header
            if header:
                header = False
                # headerは標準入力、名前付きパイプ両方に出力する
                print(data_str)
                fifo.write(data_str + '\n')
                continue

            if datum[0] == '275399':
                print(data_str)
            else:
                fifo.write(data_str + '\n')

def Mod2(FIFO):
    header = True

    with open(FIFO, "w") as fifo:
        for line in sys.stdin:
            datum = line.split(',')

            # header
            if header:
                header = False
                # headerは標準入力、名前付きパイプ両方に出力する
                print(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3], end='')
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3])
                continue

            if datum[0] == '275439':
                print(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3], end='')
            else:
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3])

def Mod3(FIFO):
    header = True

    with open(FIFO, "w") as fifo:
        for line in sys.stdin:
            datum = line.split(',')

            # header
            if header:
                header = False
                # headerは標準入力、名前付きパイプ両方に出力する
                print(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3], end='')
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3])

                continue

            if datum[3] == '66873828\n':
                print(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3], end='')
            else:
                fifo.write(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3])

def Redirect(FIFO):
    """
    指定したFIFOに流れているデータを取得する
    """
    with open(FIFO, "r") as f:
        for line in f:
            datum = line.split(',')
            print(datum[0] + ',' + datum[1] + ',' + datum[2] + ',' + datum[3], end="")

f=None
f2=None
f3=None
f4=None

import uuid

FIFO = 'tmp/' + str(uuid.uuid4())
FIFO2 = 'tmp/' + str(uuid.uuid4())
FIFO3 = 'tmp/' + str(uuid.uuid4())

try:
    os.mkfifo(FIFO)
    os.mkfifo(FIFO2)
    os.mkfifo(FIFO3)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

# 　　　***【処理イメージ】***
#  ()がframe、<>が関数
#
#           (ryudo_demo)
#                ↓
#          <Mod_Command>
#   OK ↓　　　　  　        NG ↓
#      ↓                 <Redirect>
#      ↓                      ↓
# <Mod3_Command>       <Mod2_Command>
#  NG ↓　     OK ↓         OK ↓　   NG ↓
# <Redirect> (result2)  (result3)  <Redirect>
#     ↓                               ↓
# (result1)                        (result4)

# 最初の分岐
f <<= nm.m2tee(i='../kskp/data/ryudo_demo.csv')
f <<= nm.runfunc(Mod, FIFO)
# redirect
f3 <<= nm.runfunc(Redirect, FIFO)

# 左
# result1
f <<= nm.runfunc(Mod3, FIFO3)
# result4
f2 <<= nm.runfunc(Redirect, FIFO3)

# 右
# result2
f3 <<= nm.runfunc(Mod2, FIFO2)
# result3
f4 <<= nm.runfunc(Redirect, FIFO2)

f <<= nm.m2tee(o='result/result2.csv')
f2 <<= nm.m2tee(o='result/result1.csv')
f3 <<= nm.m2tee(o='result/result3.csv')
f4 <<= nm.m2tee(o='result/result4.csv')

# 実行
nm.runs([f,f2,f3,f4],msg='on')

os.unlink(FIFO)
os.unlink(FIFO2)
os.unlink(FIFO3)
