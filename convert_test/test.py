import nysol.mcmd as nm

dat=[
["顧客","日付","量"],
["Aさん","20180101",5200],
["Bさん","20180101",800],
["Bさん","20180112",3500],
["Aさん","20180105",2000],
["Bさん","20180107",4000]
]

# f = None
# f <<= nm.mcut(f='0', x=True, i='/Users/ygt1qa/Downloads/807a5ccd-08dd-47be-a71c-dd32201ce2ee.csv')
# f <<= nm.mcut(f='0', x=True)
# # f <<= nm.cmd('nkf -w -Lu /Users/ygt1qa/Downloads/807a5ccd-08dd-47be-a71c-dd32201ce2ee.csv')
# f <<= nm.m2tee(o='result.csv')
#
# f.run()

def Cp932_to_utf8():
    """
    ストリームでcp932→utf8に変換するコマンド
    """
    import sys
    import traceback
    import io

    try:
        # stdinのencodingがデフォルトでutf-8なので、設定し直す。
        input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='cp932')
        with open('result.csv', 'w') as f:
            for line in input_stream:
                # 標準出力するときも自動でutf-8に変換されるので、printだけでいい
                print(line, end='')
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)

def utf8_to_Cp932():
    """
    ストリームでutf-8→cp932に変換するコマンド
    """
    import sys
    import traceback
    import io

    try:
        sys.stdout.flush()
        sys.stdout = open(sys.stdout.fileno(), 'w', encoding='cp932', closefd=False)
        for line in sys.stdin:
            # 改行コードは変えてくれなさそうなのでここで変える
            print(line.strip() + '\r\n', end='')
    except Exception as e:
        with open('/dev/stderr', 'w') as fpe:
            traceback.print_exc(file=fpe)

import time

f = None

start = time.time()
f <<= nm.mread(i='convert_test/test2.csv')
# f <<= nm.runfunc(Cp932_to_utf8)
f <<= nm.runfunc(utf8_to_Cp932)
f <<= nm.m2tee(o='convert_test/result.csv')

f.run()

elapsed_time = time.time() - start
print ("elapsed_time:{0}".format(elapsed_time) + "[sec]")
