import unittest
import json
# import uuid

from kskp.store import Command, Port
from kskp.engine import execute, Flow, Step, Arrow, Job

from kskp.engine.links import FlowJsonLink, Square

class EngineTestCase(unittest.TestCase):

    @unittest.skip
    def test_empty_command(self):
        """
        仮想的にコマンドを作成して動かす
        """

        class TestCommand(Command):
            def run(self, args, inputs):
                # print('i am test command!')
                return {}

        class EmptyLink:
            def resolve(self):
                return TestCommand()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    @unittest.skip
    def test_empty_flow(self):
        """
        仮想的にフローを作成して動かす
        """

        class EmptyLink:
            def resolve(self):
                return Flow()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    @unittest.skip
    def test_flow_with_one_runnable(self):
        """
        runnableが1つだけのフローを作成して動かす        
        """

        # 以下の順番で進めることにしよう
        # 1. 該当フロー以下の全てのrunnableを作る（この時点でネストするかもしれない）
        # 2. 1. でできたrunnableをstepに入れる
        # 3. JSONのstepごとのsrcs/dstsを基に、arrowを作って2. で作成したstepをつなげていく
        # 4. 実行時にはsubjobsとarrowsを親につけて、それらを使って実行フェーズに入る

        class TestCommand(Command):
            """
            inputとoutputが1つずつの擬似的なコマンド
            """

            def __init__(self):
                super().__init__()
                self.i_ports = [Port('i', 'int')]
                self.o_ports = [Port('o', 'int')]

            def run(self, args, inputs):
                # print('i am test command!')
                print('inputs:', inputs)
                print(f"i is { inputs['i'] }")
                return {'o': inputs['i'] + 200}

        class FlowLink:
            """
            フローへのリンク
            """

            def resolve(self):
                flow = Flow()                

                # 本来はこのTestCommand()もlinkから作るべきかも
                step = Step('s1', TestCommand(), {}) # 1と2
                
                # 3. i_ports / o_ports からarrowを作る
                i_arrows = [Arrow(port.name, None, None, 100, step.runnable.i_ports[0], step) for port in step.runnable.i_ports]
                o_arrows = [Arrow(port.name, step, step.runnable.o_ports[0], None, None, None) for port in step.runnable.o_ports]
                
                flow.substeps = [step]
                flow.arrows = i_arrows + o_arrows

                return flow
        
        result = execute(FlowLink(), {}, {})
        self.assertEqual(result, {'o': 300})

    @unittest.skip
    def test_flow_json_with_one_runnable(self):
        """
        test_flow_with_one_runnableと同内容の
        flowを表すJSONを読み込んで実行する
        """

        # "projectId": 1, # プロジェクトIDそのものはなくても妥当なflowとみなす
        # "creator": "開発用", # creatorそのものはなくても妥当なflowとみなす
        # "createdAt": "2018-07-27T08:25:19+09:00", # createdAtそのものはなくても妥当なflowとみなす

        json_sample = '''{                
            "description": "",
            "label": "フローテスト",
            "params": [],
            "ports": [[], []],
            "nodes": [
                {
                    "id": "Bi",
                    "type": "int",
                    "value": 100,
                    "uuid": null                          
                },
                {
                    "id": "s1",
                    "type": "command",
                    "commandId": "test",
                    "args": {
                        "c": "${A}>2",
                        "f1": "B,C",
                        "f2": "A"
                    },
                    "srcs": { "i": "Bi" },
                    "dsts": { "o": "Bt" }
                },
                {
                    "id": "Bt",
                    "type": "int",                    
                    "uuid": null
                }
            ]
        }'''

        result = execute(FlowJsonLink(json_sample), {}, {})
        self.assertEqual(result, {'Bt': 300})

    @unittest.skip
    def test_flow_with_two_runnable(self):
        """
        runnableが2つ(command)のフローを作成して動かす        
        """

        class Square(Command):
            """
            与えられた数値を2乗する            
            """

            def __init__(self):
                super().__init__()
                self.i_ports = [Port('i', 'int')]
                self.o_ports = [Port('o', 'int')]

            def run(self, args, inputs):
                # print('i am test command1!')
                print('inputs:', inputs)
                print(f"i is { inputs['i'] }")
                return {'o': inputs['i'] ** 2}

        class FlowLink:
            """
            フローへのリンク
            """

            def resolve(self):
                flow = Flow()                

                step1 = Step('s1', Square(), {})
                step2 = Step('s2', Square(), {})
                                
                flow.substeps = [step1, step2]
                flow.arrows = [Arrow('d1', None, None, 5, step1.runnable.i_ports[0], step1),
                               Arrow('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                               Arrow('d3', step2, step2.runnable.o_ports[0], None, None, None)]

                return flow
        
        result = execute(FlowLink(), {}, {})
        self.assertEqual(result, {'d3': 625})

    @unittest.skip
    def test_flow_json_with_two_runnable(self):
        """
        test_flow_with_two_runnableと同内容の
        flowを表すJSONを読み込んで実行する
        """

        json_sample = '''{                
            "description": "",
            "label": "",
            "params": [],
            "ports": [[], []],
            "nodes": [
                {
                    "id": "d1",
                    "type": "int",
                    "value": 5,
                    "uuid": null                          
                },
                {
                    "id": "s1",
                    "type": "command",
                    "commandId": "square",
                    "args": {
                        "c": "${A}>2",
                        "f1": "B,C",
                        "f2": "A"
                    },
                    "srcs": { "i": "d1" },
                    "dsts": { "o_sq": "d2" }
                },
                {
                    "id": "d2",
                    "type": "int",                    
                    "uuid": null
                },
                {
                    "id": "s2",
                    "type": "command",
                    "commandId": "square",
                    "args": {},
                    "srcs": { "i": "d2" },
                    "dsts": { "o_sq": "d3" }
                },
                {
                    "id": "d3",
                    "type": "int",                    
                    "uuid": null
                }
            ]
        }'''

        result = execute(FlowJsonLink(json_sample), {}, {})
        self.assertEqual(result, {'d3': 625})

    @unittest.skip
    def test_flow_with_subflow(self):
        """
        サブフローからの結果を正しく取得できるかのテスト
        """

        class SubFlowLink:
            """
            フローへのリンク(子)
            """

            def resolve(self):
                flow = Flow()                
                flow.i_ports = [Port('ii', 'int')]
                flow.o_ports = [Port('oo', 'int')]

                step1 = Step('s1', Square(), {})
                step2 = Step('s2', Square(), {})
                                
                flow.substeps = [step1, step2]
                flow.arrows = [Arrow('d1', None, flow.i_ports[0], None, step1.runnable.i_ports[0], step1),
                               Arrow('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                               Arrow('d3', step2, step2.runnable.o_ports[0], None, flow.o_ports[0], None)]                               
                print(flow.arrows)
                return flow
        
        class MainFlowLink:
            """
            フローへのリンク(親)
            """
            def resolve(self):
                flow = Flow()                
                flow.i_ports = [Port('iii', 'int')]
                flow.o_ports = [Port('ooo', 'int')]

                ss1 = Step('ss1', Square(), {})
                ss2 = Step('ss2', SubFlowLink().resolve(), {})
                                
                flow.substeps = [ss1, ss2]
                flow.arrows = [Arrow('dd1', None, flow.i_ports[0], 4, ss1.runnable.i_ports[0], ss1),
                               Arrow('dd2', ss1, ss1.runnable.o_ports[0], None, ss2.runnable.i_ports[0], ss2),
                               Arrow('dd3', ss2, ss2.runnable.o_ports[0], None, flow.o_ports[0], None)]
                print(flow.arrows)
                return flow

        result = execute(MainFlowLink(), {}, {})

        self.assertEqual(result, {'dd3': 65536})        

    @unittest.skip
    def test_flow_json_with_subflow(self):
        """
        test_flow_with_subflowと同内容の
        flowを表すJSONを読み込んで実行する
        """

        json_mainflow = '''{                
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [{"name": "iii", "type": "int"}],
                [{"name": "ooo", "type": "int"}]
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": 4,
                    "uuid": null                          
                },
                {
                    "id": "ss1",
                    "type": "command",
                    "commandId": "square",
                    "args": {},
                    "srcs": { "i": "dd1" },
                    "dsts": { "o_sq": "dd2" }
                },
                {
                    "id": "dd2",
                    "type": "int",                    
                    "uuid": null
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "ii": "dd2" },
                    "dsts": { "oo": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",                    
                    "uuid": null
                }
            ]
        }'''

        result = execute(FlowJsonLink(json_mainflow), {}, {})
        self.assertEqual(result, {'dd3': 65536})

    def test_m_command_runnable(self):
        """
        runnableというかmcmdがちゃんとrunされるかのテスト
        """

        class McmdTestCommand(Command):
            def __init__(self):
                super().__init__()
                self.i_ports = [Port('i', 'mcmd')]
                self.o_ports = [Port('o', 'mcmd')]

            def run(self, args, inputs):
                print('run')
                i = [['a', 'b', 'c'], [1, 2, 3]]
                import nysol.mcmd as nm
                if isinstance(inputs['i'], nm.mcut):
                    ret = inputs['i']
                    ret <<= nm.mcut(f=args['f'])
                else:
                    ret = nm.mcut(i=i, f=args['f'])
                return {'o': ret}

        class McmdTestLink:
            def resolve(self):
                flow = Flow()                

                step1 = Step('s1', McmdTestCommand(), {'f': 'a,b'})
                step2 = Step('s2', McmdTestCommand(), {'f': 'a'})
                                
                flow.substeps = [step1, step2]
                flow.arrows = [Arrow('d1', None, None, 1, step1.runnable.i_ports[0], step1),
                               Arrow('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                               Arrow('d3', step2, step2.runnable.o_ports[0], None, None, None)]                               
                return flow

        result = execute(McmdTestLink(), {}, {})
        self.assertEqual(result, {'d3': [['1']]})

    @unittest.skip
    def test_exception_in_command(self):
        """
        例外をだすコマンドをエンジンに捕まえてもらうテスト
        """

        class TestCommand(Command):
            def run(self, args, inputs):
                raise Exception('wowow')

        class EmptyLink:
            def resolve(self):
                return TestCommand()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    # def test_mcut(self):    
    #     s = PathFileSource('csv', '', 'a.csv')
    #     f = Frame(uuid.uuid4(), s)
    #     result = main.execute(McmdLink('mcut'), {'f': 'b,c'}, {'i': f})
    #     self.assertEqual(result, {})