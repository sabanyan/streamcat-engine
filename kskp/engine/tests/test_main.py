import unittest
# import uuid

from kskp.store import Command
from kskp.engine import execute, Flow
# from kskp.engine.data import PathFileSource, Frame
# from kskp.mcmd import McmdLink

class EngineTestCase(unittest.TestCase):
    def test_empty_command(self):
        """
        仮想的にコマンドを作成して動かす
        """

        class TestCommand(Command):
            def run(self, args, inputs):
                print('i am test command!')
                return {}

        class EmptyLink:
            def resolve(self):
                return TestCommand()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    def test_empty_flow(self):
        """
        仮想的にフローを作成して動かす
        """

        class EmptyLink:
            def resolve(self):
                return Flow()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    def test_flow_with_one_runnable(self):
        """
        datumが1つだけのフローを作成して動かす
        """

        class FlowLink:
            def resolve(self):
                flow = Flow()
                return flow
        
        result = execute(FlowLink(), {}, {})
        self.assertEqual(result, {})

    # def test_mcut(self):    
    #     s = PathFileSource('csv', '', 'a.csv')
    #     f = Frame(uuid.uuid4(), s)
    #     result = main.execute(McmdLink('mcut'), {'f': 'b,c'}, {'i': f})
    #     self.assertEqual(result, {})