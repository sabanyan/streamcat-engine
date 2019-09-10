# データ作成用

import nysol.mcmd as nm

dat=[
["customer","date","amount"],
["A","20180101",5200],
["B","20180101",800],
["B","20180112",3500],
["A","20180105",2000],
["B","20180107",4000],
["C","20190211",5000]
]

import os
import errno
import sys
import traceback

def Mod(input, FIFO):
    header = True
    try:
        with open(FIFO, "w") as fifo:
            for line in input.getline(header=True):
                datum_str = ','.join(line)

                # header
                if header:
                    header = False
                    # headerは標準入力、名前付きパイプ両方に出力する
                    print(datum_str, end='\n')
                    fifo.write(datum_str + '\n')
                    continue

                if line[0] == 'B':
                    print(datum_str, end='\n')
                else:
                    fifo.write(datum_str + '\n')
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
          traceback.print_exc(file=fpe)

def Mod2(input, FIFO):

    header = True
    try:
        with open(FIFO, "w") as fifo:
            for line in input.getline(header=True):
                datum_str = ','.join(line)

                # header
                if header:
                    header = False
                    # headerは標準入力、名前付きパイプ両方に出力する
                    print(datum_str, end='\n')
                    fifo.write(datum_str + '\n')
                    continue

                if line[0] == 'A':
                    print(datum_str, end='\n')
                else:
                    fifo.write(datum_str + '\n')
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
          traceback.print_exc(file=fpe)

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
input = None
input <<= nm.m2tee(i=dat)

# result1
f <<= nm.runfunc(Mod, input, FIFO)
f <<= nm.m2tee(o='result/result1.csv')

# redirect
input2 = None
input2 <<= nm.m2tee(i=FIFO)

# result2
f2 <<= nm.runfunc(Mod2, input2, FIFO2)
f2 <<= nm.m2tee(o='result/result2.csv')

# result3
f3 <<= nm.m2tee(i=FIFO2)
f3 <<= nm.m2tee(o='result/result3.csv')

# 実行
nm.runs([f,f2,f3],msg='on')

os.unlink(FIFO)
os.unlink(FIFO2)
