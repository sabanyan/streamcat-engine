import unittest
# import uuid

from kskp.store import Command, Port
from kskp.engine import execute, Flow, Step, Arrow, Job

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
        self.assertEqual(result, {'o': 3})

    # @unittest.skip
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
        self.assertEqual(result, {'o': 3})

    # def test_mcut(self):    
    #     s = PathFileSource('csv', '', 'a.csv')
    #     f = Frame(uuid.uuid4(), s)
    #     result = main.execute(McmdLink('mcut'), {'f': 'b,c'}, {'i': f})
    #     self.assertEqual(result, {})