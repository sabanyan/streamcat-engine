import unittest
import json
# import uuid

from kskp.store import Command, Port
from kskp.engine import execute, Flow, Step, Point, Job, Tube
from pathlib import Path
from kskp.engine.links import FlowJsonLink, Square, FlowUuidLink

class MjoinTestCommand(Command):
    """
    複数inputのテストで使うだけのコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        cmd = nm.mjoin(i=inputs['i'], m=inputs['m'], k=args['k'])
        return {'o': cmd}


class MselTestCommand(Command):
    """
    複数outputのテストで使うだけのコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'frame')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        cmd_o = nm.msel(i=inputs['i'], c='${金額}>30')
        cmd_u = cmd_o.redirect('u')
        return {'o': cmd_o, 'u': cmd_u}

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
        # 3. JSONのstepごとのsrcs/dstsを基に、pointを作って2. で作成したstepをつなげていく
        # 4. 実行時にはsubjobsとpointsを親につけて、それらを使って実行フェーズに入る

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

                # 3. i_ports / o_ports からpointを作る
                i_points = [Point(port.name, None, None, 100, step.runnable.i_ports[0], step) for port in step.runnable.i_ports]
                o_points = [Point(port.name, step, step.runnable.o_ports[0], None, None, None) for port in step.runnable.o_ports]

                flow.substeps = [step]
                flow.points = i_points + o_points

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
                flow.points = [Point('d1', None, None, 5, step1.runnable.i_ports[0], step1),
                               Point('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                               Point('d3', step2, step2.runnable.o_ports[0], None, None, None)]

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
                flow.i_ports = [Port('d1', 'int')]
                flow.o_ports = [Port('d3', 'int')]

                step1 = Step('s1', Square(), {})
                step2 = Step('s2', Square(), {})

                flow.substeps = [step1, step2]
                flow.points = [Point('d1', [Tube(flow.i_ports[0], None)], None, [Tube(step1.runnable.i_ports[0], step1)]),
                               Point('d2', [Tube(step1.runnable.o_ports[0], step1)], None, [Tube(step2.runnable.i_ports[0], step2)]),
                               Point('d3', [Tube(step2.runnable.o_ports[0], step2)], None, [Tube(flow.o_ports[0], None)])]
                print(flow.points)
                return flow

        class MainFlowLink:
            """
            フローへのリンク(親)
            """
            def resolve(self):
                flow = Flow()
                flow.i_ports = []
                flow.o_ports = []

                ss1 = Step('ss1', Square(), {})
                ss2 = Step('ss2', SubFlowLink().resolve(), {})

                flow.substeps = [ss1, ss2]
                flow.points = [Point('dd1', [Tube(None, None)], 4, [Tube(ss1.runnable.i_ports[0], ss1)]),
                               Point('dd2', [Tube(ss1.runnable.o_ports[0], ss1)], None, [Tube(ss2.runnable.i_ports[0], ss2)]),
                               Point('dd3', [Tube(ss2.runnable.o_ports[0], ss2)], None, [Tube(None, None)])]
                print(flow.points)
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
                [],
                []
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
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
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

    @unittest.skip
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
                flow.points = [Point('d1', None, None, 1, step1.runnable.i_ports[0], step1),
                               Point('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                               Point('d3', step2, step2.runnable.o_ports[0], None, None, None)]
                return flow

        result = execute(McmdTestLink(), {}, {})
        self.assertEqual(result, {'o': [['0', '2', '4']]})

    @unittest.skip
    def test_m_command_with_two_inputs(self):
        """
        複数inputのコマンドのテスト
        """

        class MjoinFlowLink:
            """
            フローへのリンク
            """

            def resolve(self):
                flow = Flow()

                step = Step('s1', MjoinTestCommand(), {'k': 'k'})
                flow.substeps = [step]

                flow.points = [Point('ii', None, None, [['k', 'a'], [0, 2]], step.runnable.i_ports[0], step),
                               Point('mm', None, None, [['k', 'b'], [0, 4]], step.runnable.i_ports[1], step),
                               Point('rr', step, step.runnable.o_ports[0], None, None, None)]

                return flow

        result = execute(MjoinFlowLink(), {}, {})
        self.assertEqual(result, {'rr': [['0', '2', '4']]})

    @unittest.skip
    def test_m_command_json_with_two_inputs(self):
        """
        複数inputのコマンドのテストをJSONで行う
        """

        class MjoinLink:
            def resolve(self):
                return MjoinTestCommand()

        class MjoinFlowLink(FlowJsonLink):
            """
            テスト用にMjoinTestCommandを返すようにカスタマイズ
            """

            def node2link(self, node):
                if node['commandId'] == 'mjoin':
                    return MjoinLink()
                else:
                    return super().node2link(node)

        json_flow = '''{
            "description": "複数inputフロー",
            "label": "複数inputフロー",
            "params": [],
            "ports": [[], []],
            "nodes": [
                {
                    "id": "ii",
                    "type": "frame",
                    "value": [["k", "a"], [0, 2]],
                    "uuid": null
                },
                {
                    "id": "mm",
                    "type": "frame",
                    "value": [["k", "b"], [0, 4]],
                    "uuid": null
                },
                {
                    "id": "s1",
                    "type": "command",
                    "commandId": "mjoin",
                    "args": { "k": "k" },
                    "srcs": { "i": "ii", "m": "mm" },
                    "dsts": { "o": "rr" }
                },
                {
                    "id": "rr",
                    "type": "mcmd",
                    "uuid": null
                }
            ]
        }'''

        result = execute(MjoinFlowLink(json_flow), {}, {})
        self.assertEqual(result, {'rr': [['0', '2', '4']]})

    @unittest.skip
    def test_m_command_with_two_outputs(self):
        """
        複数outputのコマンドのテスト
        """

        class MselFlowLink:
            """
            フローへのリンク
            """

            def resolve(self):
                flow = Flow()

                step = Step('s1', MselTestCommand(), {'k': 'k'})
                flow.substeps = [step]

                dat1 = [['顧客', '数量', '金額'],
                        ['A', 1, 10],
                        ['A', 2, 20],
                        ['B', 1, 30],
                        ['B', 3, 40],
                        ['B', 1, 50]]

                flow.points = [Point('ii', None, None, dat1, step.runnable.i_ports[0], step),
                               Point('oo', step, step.runnable.o_ports[0], None, None, None),
                               Point('uu', step, step.runnable.o_ports[1], None, None, None)]

                return flow

        result = execute(MselFlowLink(), {}, {})
        correct = {'oo': [['B', '3', '40'], ['B', '1', '50']],
                   'uu': [['A', '1', '10'], ['A', '2', '20'], ['B', '1', '30']]}
        self.assertEqual(result, correct)

    @unittest.skip
    def test_m_command_json_with_two_outputs(self):
        """
        複数outputのコマンドのテストをJSONで行う
        """

        class MselLink:
            def resolve(self):
                return MselTestCommand()

        class MselFlowLink(FlowJsonLink):
            """
            テスト用にMselTestCommandを返すようにカスタマイズ
            """

            def node2link(self, node):
                if node['commandId'] == 'msel':
                    return MselLink()
                else:
                    return super().node2link(node)

        json_flow = '''{
            "description": "複数outputフロー",
            "label": "複数outputフロー",
            "params": [],
            "ports": [[], []],
            "nodes": [
                {
                    "id": "ii",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "s1",
                    "type": "command",
                    "commandId": "msel",
                    "args": {},
                    "srcs": { "i": "ii" },
                    "dsts": { "o": "oo", "u": "uu" }
                },
                {
                    "id": "oo",
                    "type": "mcmd",
                    "uuid": null
                },
                {
                    "id": "uu",
                    "type": "mcmd",
                    "uuid": null
                }
            ]
        }'''

        result = execute(MselFlowLink(json_flow), {}, {})
        correct = {'oo': [['B', '3', '40'], ['B', '1', '50']],
                   'uu': [['A', '1', '10'], ['A', '2', '20'], ['B', '1', '30']]}
        self.assertEqual(result, correct)

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

class ExecuteTestCase(unittest.TestCase):
    """
    実際の実行のテスト
    """

    import json

    # シンプルなmコマンド１つのフロー
    flow_data = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "f": "0,1",
            "x": True
          },
          "commandId": "mcut"
        }
      ]
    }

    # シンプルなmコマンド１つのフロー（csvから読み取り）
    flow_data_use_by_csv = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": None,
          "dataSource": "csv",
          "uuid": "test_data"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "f": "0,1",
            "x": True
          },
          "commandId": "mcut"
        }
      ]
    }

    # inputが2つあるシンプルなフロー
    flow_data_inputs = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "id": "i2",
          "type": "frame",
          "label": "テストデータ2",
          "value": [["顧客", "年齢"],
              ["A", 21],
              ["B", 31]],
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i",
            "m": "i2"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "k": "顧客",
            "f": "年齢"
          },
          "commandId": "mjoin"
        }
      ]
    }

    # outputが２つあるシンプルなフロー
    flow_data_outputs = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d2",
            "u": "d3"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }
      ]
    }

    # @unittest.skip
    def test_simple_flow_execute(self):
        """
        mコマンド１個のフロー実行
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
        result = get_frame_by_uuid(lasts['d1'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d1'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_two_commands_execute(self):
        """
        mコマンド２個のフロー実行
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}
        result = get_frame_by_uuid(lasts['d2'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d2'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_two_commands_preview(self):
        """
        mコマンド２個のフロー実行
        真ん中のdatumでプレビューする
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d1'])
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
        result = get_frame_by_uuid(lasts['d1'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d1'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_three_commands_preview(self):
        """
        mコマンド３個のフロー実行
        ２個目のdatumでプレビューする
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d2'])
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}
        result = get_frame_by_uuid(lasts['d2'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d2'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_three_commands_execute(self):
        """
        mコマンド３個のフロー実行（逆Y字の分岐）
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "顧客",
            "v": "B"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']], 'd3': [['B', '1'], ['B', '3'], ['B', '1']]}
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid, 'kskp/data/result/')
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/result/')
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d2'].uuid + '.csv').unlink()
        Path('kskp/data/result/' + lasts['d3'].uuid + '.csv').unlink()

    @unittest.skip
    def test_simple_flow_three_commands_preview_d2(self):
        """
        mコマンド３個のフロー実行（逆Y字の分岐）
        片方（d2）をプレビュー
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "顧客",
            "v": "B"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d2'])
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}
        result = get_frame_by_uuid(lasts['d2'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d2'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_execute_two_inputs(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_inputs))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}
        result = get_frame_by_uuid(lasts['d1'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d1'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_execute_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']],
                   'd3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid, 'kskp/data/result/')
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/result/')
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d2'].uuid + '.csv').unlink()
        Path('kskp/data/result/' + lasts['d3'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_preview_d2_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロープレビュー
        oだけのテスト（d2）
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs), ['d2'])
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}
        result = get_frame_by_uuid(lasts['d2'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d2'])
        self.assertIsNone(lasts.get('d3'))

        # 後片付け
        Path('kskp/data/result/' + lasts['d2'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_preview_d3_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロープレビュー
        uだけのテスト（d3）
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs), ['d3'])
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}
        result = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d3'])
        self.assertIsNone(lasts.get('d2'))

        # 後片付け
        Path('kskp/data/result/' + lasts['d3'].uuid + '.csv').unlink()

    @unittest.skip
    def test_long_flow_execute_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフロー実行
        """

        add_datum_1 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d4",
          "label": "d4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3",
            "u": "d4"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/result/')
        result_d4 = get_frame_by_uuid(lasts['d4'].uuid, 'kskp/data/result/')
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d3'].uuid + '.csv').unlink()
        Path('kskp/data/result/' + lasts['d4'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_long_flow_preview_d2_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフロープレビュー
        oだけのテスト（d3）
        """

        add_datum_1 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d4",
          "label": "d4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3",
            "u": "d4"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d3'])
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1'], ['A', '2']]}
        result = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d3'])
        self.assertIsNone(lasts.get('d4'))

        # 後片付け
        Path('kskp/data/result/' + lasts['d3'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_long_flow_preview_d3_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフロープレビュー
        uだけのテスト（d4）
        """
        add_datum_1 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d4",
          "label": "d4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3",
            "u": "d4"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d4'])
        lasts = execute(flow_link, {}, {})
        correct = {'d4': [['B', '1'], ['B', '3'], ['B', '1']]}
        result = get_frame_by_uuid(lasts['d4'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d4'])
        self.assertIsNone(lasts.get('d3'))

        # 後片付け
        Path('kskp/data/result/' + lasts['d4'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_execute_include_subflow(self):
        """
        サブフローを１個をもつフローを実行する
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [[4]],
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
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": null
                }
            ]
        }'''

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd3': [['65536']]}
        result = get_frame_by_uuid(lasts['dd3'].uuid, 'kskp/data/result/', header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd3'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_execute_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [[4]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" }
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
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": null
                }
            ]
        }'''

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd3': [['4294967296']]}
        result = get_frame_by_uuid(lasts['dd3'].uuid, 'kskp/data/result/', header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd3'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_preview_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        真ん中のdatumでプレビューする
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [[4]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" }
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
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": null
                }
            ]
        }'''

        lasts = execute(FlowJsonLink(json_mainflow, ['dd2']), {}, {})
        correct = {'dd2': [['256']]}
        result = get_frame_by_uuid(lasts['dd2'].uuid, 'kskp/data/result/', header=False)
        self.assertEqual(result, correct['dd2'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd2'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_execute_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid, 'kskp/data/result/')
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid, 'kskp/data/result/')
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd2'].uuid + '.csv').unlink()
        Path('kskp/data/result/' + lasts['dd3'].uuid + '.csv').unlink()

    # @unittest.skip
    def test_simple_flow_preview_dd2_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）

        片方のdatum(dd2)をプレビューする
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        lasts = execute(FlowJsonLink(json_mainflow, ['dd2']), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']]}
        result = get_frame_by_uuid(lasts['dd2'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['dd2'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd2'].uuid + '.csv').unlink()

    @unittest.skip
    def test_simple_flow_preview_dd3_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）

        片方のdatum(dd3)をプレビューする
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        lasts = execute(FlowJsonLink(json_mainflow, ['dd3']), {}, {})
        correct = {'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}
        result = get_frame_by_uuid(lasts['dd3'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd3'].uuid + '.csv').unlink()

    @unittest.skip
    def test_complex_flow_execute_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        lasts = execute(FlowJsonLink(json.dumps(json_flow)), {}, {})
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}
        result_dd4 = get_frame_by_uuid(lasts['dd4'].uuid, 'kskp/data/result/')
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid, 'kskp/data/result/')
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd4'].uuid + '.csv').unlink()
        Path('kskp/data/result/' + lasts['dd5'].uuid + '.csv').unlink()

    @unittest.skip
    def test_complex_flow_preview_include_branch_output_subflowss(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        dd5をプレビュー
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        lasts = execute(FlowJsonLink(json.dumps(json_flow), ['dd5']), {}, {})
        correct = {'dd5': [['1'], ['3'], ['1']]}
        result = get_frame_by_uuid(lasts['dd5'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['dd5'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd5'].uuid + '.csv').unlink()

    @unittest.skip
    def test_complex_flow_two_preview_include_branch_output_subflowss(self):
        """
        おまけ（プレビューを２つしてみた。）
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        lasts = execute(FlowJsonLink(json.dumps(json_flow), ['dd2', 'dd5']), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd5': [['1'], ['3'], ['1']]}
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid, 'kskp/data/result/')
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid, 'kskp/data/result/')
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd5, correct['dd5'])

        # 後片付け
        Path('kskp/data/result/' + lasts['dd2'].uuid + '.csv').unlink()
        Path('kskp/data/result/' + lasts['dd5'].uuid + '.csv').unlink()

    @unittest.skip
    def test_simple_flow_execute_generate_one_cache(self):
        """
        mコマンド３個のフロー実行
        真ん中のdatumをキャッシュする
        """

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": "",
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }


        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        path = Path('kskp/flows/test.json')
        write_data_to_json(path, json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(Path('kskp/flows'), 'test')
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1']]}
        result = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d3'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d2']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            Path('kskp/data/cache_frames/' + node['uuid'] + '.csv').unlink()

        # 後片付け
        path.unlink()
        Path('kskp/data/result/' + lasts['d3'].uuid + '.csv').unlink()

    @unittest.skip
    def test_simple_flow_execute_generate_last_cache(self):
        """
        mコマンド３個のフロー実行
        最後のdatumをキャッシュする
        """

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": ""
        }


        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        path = Path('kskp/flows/test.json')
        write_data_to_json(path, json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(Path('kskp/flows'), 'test')
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1']]}
        result = get_frame_by_uuid(lasts['d3'].uuid, 'kskp/data/cache_frames/')
        self.assertEqual(result, correct['d3'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d3']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            Path('kskp/data/cache_frames/' + node['uuid'] + '.csv').unlink()

        # 後片付け
        path.unlink()

    # @unittest.skip
    def test_complex_flow_execute_include_branch_output_subflows_generate_cache(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている

        サブフローの出力するdd2と、結果をmcutしたdd5をキャッシュする
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": True,
                    "cacheCreatedAt": ""
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": ""
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        path = Path('kskp/flows/test.json')
        write_data_to_json(path, json_flow)

        # 単純なlastsのテスト
        flow_link = FlowUuidLink(Path('kskp/flows'), 'test')
        lasts = execute(flow_link, {}, {})
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}
        result_dd4 = get_frame_by_uuid(lasts['dd4'].uuid, 'kskp/data/result/')
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid, 'kskp/data/cache_frames/')
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['dd2', 'dd5']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            Path('kskp/data/cache_frames/' + node['uuid'] + '.csv').unlink()

        # 後片付け
        Path('kskp/data/result/' + lasts['dd4'].uuid + '.csv').unlink()
        path.unlink()

    @unittest.skip
    def test_simple_flow_data_source_from_csv(self):
        """
        1つのmコマンドを持つフローを実行する
        valueで指定したデータで始まるのではなく、csvから始める（loaderのテスト）
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_use_by_csv))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
        result = get_frame_by_uuid(lasts['d1'].uuid, 'kskp/data/result/')
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Path('kskp/data/result/' + lasts['d1'].uuid + '.csv').unlink()

# Helpler
def get_frame_by_uuid(uuid, dir_path, header=True):
    """
    指定したuuidのframeを取得する
    """
    import csv
    result = []
    with open(dir_path + uuid + '.csv', 'r') as f:
        rows = csv.reader(f)
        if header:
            header = next(rows)
        for row in rows:
            result.append(row)

    return result

def write_data_to_json(path, data):
    """
    データをJSONとしてファイルに書き込むヘルパー
    """
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
