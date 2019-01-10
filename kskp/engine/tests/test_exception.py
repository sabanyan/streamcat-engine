"""
例外処理が正しく行われるかどうかのテスト
"""

import unittest

def do_something(first_pow):
    i = 0
    for n in range(2 ** first_pow):
        i += n
    # try:
    #     i = i / 0
    # except Exception as e:
    #     ex =  ValueError(f'first_pow: {first_pow}')
    #     ex.__cause__ = e
    #     return ex
    return i

class ErrorHandlingTestCase(unittest.TestCase):
    @unittest.skip
    def test_concurrent_errors(self):
        """
        エラーを並列で発生させられるかどうかのテスト
        (multiprocess)
        """
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor() as executor:
            # 並行処理する対象とそれに対応する値 (処理の引数) を辞書で用意する
            mappings = {executor.submit(do_something, n): n for n in [28, 26, 24, 22]}

            # futures.as_completed() は処理がおわったものから結果を返していくジェネレータ
            for future in as_completed(mappings):
                # 完了した処理に対応する引数を辞書から取得する
                target = mappings[future]
                # 処理結果を取得する
                result = future.result()
                # 結果を表示する
                msg = '{n}: {prime}'.format(n=target, prime=result)
                print(msg)

    def test_websocket(self):
        """
        websocketの動作確認
        """

    def test_mcmd_error(self):
        """
        mcmdは直接excepionを吐かないが、それを起点にした返し

        大切なのは、仕様。mcmd実行中にエラーが起きた際は、その文字列をなんとかして取得、
        そのあと独自の例外を作成するところまではいいのだが、その後がまだあやふやではないだろうか。
        他の方法も思いつかないので、普通にExceptionに包んで返せばいいか。
        """

        m = McutTest()
        with self.assertRaises(MCMDError):
            m.run()
        

import sys

class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        self._stderr.close() # for ResoucredWarning: unclosed file
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

class ErrorInfo():
    def __init__(self, description, input_n, output_n, called_at):
        self.description = description
        self.number_of_input = input_n
        self.number_of_output = output_n
        self.called_at = called_at

    @classmethod
    def parse_stderr(cls, s):
        """
        以下のようなMCMDの実行時のエラー文字列をparseしてオブジェクトに起こす
        '#ERROR# field name not found: `c' in a.csv (kgcut); kgcut f=c i=a.csv; IN=0 OUT=0; 2018/06/14 20:57:21'
        """
        # s = "#ERROR# field name not found: `c' in a.csv (kgcut); kgcut f=c i=a.csv; IN=1253 OUT=5624; 2018/06/14 20:57:21"
        # まず、セミコロンで区切る
        ss = s.split(';')

        # 入力と出力の件数をパースする
        import re
        io = re.search(r'IN=(\d+) OUT=(\d+)', ss[2]).groups()

        return cls(ss[0].replace('#ERROR# ', ''), int(io[0]), int(io[1]), ss[3])

class MCMDError(Exception):
    def __init__(self, errors):
        self.errors = errors

class McutTest():
    def run(self):
        import nysol.mcmd as nm
        dat=[
            ["customer","date","amount"],
            ["A","20180101",5200],
            ["B","20180101",800],
            ["B","20180112",3500],
            ["A","20180105",2000],
            ["B","20180107",4000]
        ]
        message_f = 'kskp/messages/test_mcmd_error.txt'
        with RedirectStdStreams(stderr=open(message_f, 'w')):
            nm.mcut(f="customer,amuont",i=dat).run(msg='on') # amountをtypoしている
        
        with open(message_f, 'r') as f:
            content = [lin for lin in f.readlines() if lin.startswith('#ERROR#') and 'kgcut' in lin][0]
            err = MCMDError([ErrorInfo.parse_stderr(content)])
            print('description:', err.errors[0].description)
            print('number_of_input:', err.errors[0].number_of_input)
            print('number_of_output:', err.errors[0].number_of_output)
            print('called_at:', err.errors[0].called_at)
            raise err
    
    def execute(self):
        """
        未使用、他のファイルからサンプルとして引っ張ってきただけのコード
        """
        import io
        import nysol.mcmd as nm
        dat=[
            ["customer","date","amount"],
            ["A","20180101",5200],
            ["B","20180101",800],
            ["B","20180112",3500],
            ["A","20180105",2000],
            ["B","20180107",4000]
        ]
        with io.StringIO() as output:
            oldstderr = sys.stderr
            sys.stderr = output        
            r = nm.mselstr(i=dat, f='date', v='20180101').run()
            contents = output.getvalue()
            sys.stderr = oldstderr

            if len(contents) > 0:                
                errors = []
                for content in contents.split('\n'):
                    print('mselstr error:', content)
                    if '#ERROR#' in content and '#ERROR# ; kgshell' not in content:
                        errors.append(ErrorInfo.parse_stderr(content))
                
                if len(errors) > 0:
                    raise MCMDError(errors)
            else:
                return r
