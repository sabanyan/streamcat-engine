import nysol.mcmd as nm
import traceback

dat=[
["customer","date","amount"],
["A","20180101",5200],
["B","20180101",800],
["B","20180112",3500],
["A","20180105",2000],
["B","20180107",4000]
]

def Mod(i):
    try:
        for line in i.getline(header=True):
            print(line)
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)
f = None
m = None
f <<= nm.mcut(f="customer,date", i=dat)
m <<= nm.mcut(f='amount', i=dat)

f2 = None
f2 <<= nm.runfunc(Mod, f)
f2 <<= nm.m2tee(o='result/result.csv')
f2.run()
