"""
例外処理が正しく行われるかどうかのテスト
"""

import unittest
from streamcat.engine import FlowCommand, aexecute
from streamcat.store import FlowData, CommandException
from streamcat.store.tests.test_case_base import TestCaseBase
from .test_main import convert_from_job_exs

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

class ErrorHandlingTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

    @unittest.skip('例外処理の実装待ち?')
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

    @unittest.skip('例外処理の実装待ち?')
    def test_websocket(self):
        """
        websocketの動作確認
        """
        # a = 1 / 0

    @unittest.skip('例外処理の実装待ち?')
    def test_mcmd_error(self):
        """
        mcmdは直接excepionを吐かないが、それを起点にした返し

        大切なのは、仕様。mcmd実行中にエラーが起きた際は、その文字列をなんとかして取得、
        そのあと独自の例外を作成するところまではいいのだが、その後がまだあやふやではないだろうか。
        他の方法も思いつかないので、普通にExceptionに包んで返せばいいか。
        """

        from kskp.mcmd import McutTest, MCMDError

        dat=[
            ["customer","date","amount"],
            ["A","20180101",5200],
            ["B","20180101",800],
            ["B","20180112",3500],
            ["A","20180105",2000],
            ["B","20180107",4000]
        ]

        m = McutTest()
        with self.assertRaises(MCMDError):
            m.run({'f': 'customer,amuont'}, {'i': dat})

    async def test_runs_error(self):
        """
        Runsコマンドのrun()から例外が送出された場合でもエラーが取得できること
        """
        # selectコマンドの引数(args)に不正な値を設定する
        flow_json = {
            'label': 'MSYOLコマンドによるフロー',
            'params': [],
            'ports': [[],[]],
            'nodes': [
                {
                    'id': 'c',
                    'type': 'command',
                    'commandId': 'new',
                    'label': 'new',
                    'srcs': {},
                    'dsts': {
                        'o': 'd'
                    },
                    'args': {},
                },
                {
                    'id': 'd',
                    'type': 'frame',
                    'label': 'd',
                    'dataSource': 'csv'
                },
                {
                    'id': 'c1',
                    'type': 'command',
                    'commandId': 'select',
                    'label': 'select',
                    'srcs': {
                        'i': 'd'
                    },
                    'dsts': {
                        'o': 'd1'
                    },
                    'args': {
                        'cols': 'A'
                    },
                },
                {
                    'id': 'd1',
                    'type': 'frame',
                    'label': 'd1',
                    'dataSource': 'csv'
                },
            ],
        }

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # ルートデータストアを取得する
        root = self.finder2.data.load_root()

        # フローを実行する
        # selectコマンドのrun()が実行され例外が送出される
        flow = root.create_flow(flow_json['label'], FlowData(flow_json))
        job = await aexecute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_job_exs(job)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(results))

        # 期待するExceptionが得られるか
        # Exception("col引数に<class 'str'>型の要素が指定されました")
        ex = results['d1'][0]
        self.assertIsInstance(ex, CommandException)
        self.assertIsInstance(ex.innerException, Exception)
