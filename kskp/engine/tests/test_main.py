import unittest
import json
# import uuid

from kskp.store import Command, Port
from kskp.engine import execute, Flow, Step, Arrow, Job

class TestCommand(Command):
    """
    inputとoutputが1つずつの擬似的なコマンド
    """

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'int')]
        self.o_ports = [Port('o', 'int')]

    def run(self, args, inputs):
        return {'o': inputs['i'] + 200}

class Square(Command):
    """
    与えられた数値を2乗する            
    """

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'int')]
        self.o_ports = [Port('o_sq', 'int')]

    def run(self, args, inputs):
        return {self.o_ports[0].name: inputs['i'] ** 2}

class CommandLink:
    """
    コマンド名を解決するリンク
    """

    def __init__(self, command_id):
        self.command_id = command_id

    def resolve(self):
        return self.select_runnable(self.command_id)

    def select_runnable(self, runnable_id):
        """
        idとなる文字列を受け取ってrunnableのインスタンスを返却する
        """
        table = {
            'test': TestCommand(),
            'square': Square()
        }

        if runnable_id not in table:
            raise Exception(f"存在しないcommandId'{runnable_id}'が指定されています")

        return table[runnable_id]

class FlowJsonLink:
    """
    フローへのリンク
    """
    def __init__(self, json_str):
        self.json_str = json_str

    def node2link(self, node):
        if 'link' in node:
            return SampleFlowJsonLink()

        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(node['uuid'])

        return ret

    def make_ports(self, port_dict_list):
        """ dictのリストからportインスタンスのリストを作る """
        return [Port(p['name'], p['type']) for p in port_dict_list]

    def is_node_runnable(self, node):
        """ 指定されたnodeがrunnableかどうかを判断する """
        return node['type'] == 'command' or node['type'] == 'flow'

    def make_flow(self, json_str):

        # JSONを読み込む
        json_obj = json.loads(json_str)

        flow = Flow()                

        # portを読む
        ports = json_obj['ports']
        flow.i_ports = self.make_ports(ports[0])
        flow.o_ports = self.make_ports(ports[1])

        # まず、runnableを集める
        for node in json_obj['nodes']:
            if self.is_node_runnable(node):
                # runnableのインスタンス化を行う
                step = Step(node['id'], self.node2link(node).resolve(), node['args'])
                    
                flow.substeps.append(step)

                arrow_ids = [arrow.id for arrow in flow.arrows]

                # srcとdstからarrowを作る
                src_port = step.runnable.i_ports[0]
                srcs = node['srcs']
                if src_port.name not in srcs:
                    raise Exception(f"指定しているport名({src_port.name})がrunnable {node['id']}のsrcs({srcs})のキー中に存在しません")
                # 対象のarrowがすでに存在すればそれを取得する
                if srcs[src_port.name] in arrow_ids:
                    src_arrow = [arrow for arrow in flow.arrows if arrow.id == srcs[src_port.name]][0]                
                    src_arrow.i_port = src_port
                    src_arrow.cod = step
                else:
                    src_arrow = Arrow(srcs[src_port.name], None, None, None, src_port, step)
                    flow.arrows.append(src_arrow)
                if len(flow.i_ports) > 0 and src_arrow.o_port is None:
                    # FIXME: portが1つの前提
                    src_arrow.o_port = flow.i_ports[0]
                

                dst_port = step.runnable.o_ports[0]
                dsts = node['dsts']
                if dst_port.name not in dsts:
                    raise Exception(f"指定しているport名({dst_port.name})がrunnable {node['id']}のdsts({dsts})のキー中に存在しません")
                # 対象のarrowがすでに存在すればそれを取得する
                if dsts[dst_port.name] in arrow_ids:
                    dst_arrow = [arrow for arrow in flow.arrows if arrow.id == dsts[dst_port.name]][0]
                    dst_arrow.dom = step
                    dst_arrow.o_port = dst_port
                else:
                    dst_arrow = Arrow(dsts[dst_port.name], step, dst_port, None, None, None)
                    flow.arrows.append(dst_arrow)
                if len(flow.o_ports) > 0 and dst_arrow.i_port is None:
                    # FIXME: portが1つの前提
                    dst_arrow.i_port = flow.o_ports[0]
                

                # sublflow
                # flow.arrows = [Arrow('d1', None, flow.i_ports[0], None, step1.runnable.i_ports[0], step1),
                #                Arrow('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                #                Arrow('d3', step2, step2.runnable.o_ports[0], None, flow.o_ports[0], None)]   

                # mainflow 
                # flow.arrows = [Arrow('dd1', None, flow.i_ports[0], 4, ss1.runnable.i_ports[0], ss1),
                #                Arrow('dd2', ss1, ss1.runnable.o_ports[0], None, ss2.runnable.i_ports[0], ss2),
                #                Arrow('dd3', ss2, ss2.runnable.o_ports[0], None, flow.o_ports[0], None)]

        substep = list(flow.substeps)[0]
        for node in json_obj['nodes']:
            # arrowにdatumを入れていく
            if not self.is_node_runnable(node):
                if 'value' in node and node['value'] is not None:
                    target_arrow = [arrow for arrow in flow.arrows if arrow.id == node['id']][0]
                    target_arrow.datum = node['value']                    

        return flow

    def resolve(self):
        f = self.make_flow(self.json_str)

        print(f.arrows)        
        return f

class FlowUuidLink(FlowJsonLink):
    """
    UUIDを元にFlowを返却するリンク
    """
    
    def __init__(self, flow_uuid):
        self.flow_uuid = flow_uuid

        import pathlib        
        p = pathlib.Path(f'kskp/flows/{flow_uuid}.json')    
        super().__init__(p.read_text())


class SampleFlowJsonLink(FlowJsonLink):
    """ temp """

    def __init__(self):
        json_subflow = '''{               
            "description": "サブフロー",
            "label": "サブフロー",
            "params": [],
            "ports": [
                [{"name": "ii", "type": "int"}],
                [{"name": "oo", "type": "int"}]
            ],
            "nodes": [
                {
                    "id": "d1",
                    "type": "int",
                    "uuid": null                          
                },
                {
                    "id": "s1",
                    "type": "command",
                    "commandId": "square",
                    "args": {},
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
        super().__init__(json_subflow)

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

    # @unittest.skip
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