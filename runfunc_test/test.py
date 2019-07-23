import nysol.mcmd as nm
import os

with open('dat1.csv','w') as f:
  f.write(
'''item,amount
apple,100
milk,350
orange,100
pineapplejuice,500
wine,1000
''')

f = None
f2 = None
f <<= nm.mselstr(f="item", v="apple,orange", i="dat1.csv")
f2 <<= f.redirect('u')

f <<= nm.m2tee(o='result1.csv')
f2 <<= nm.m2tee(o='result2.csv')

nm.runs([f,f2])

os.unlink('dat1.csv')
