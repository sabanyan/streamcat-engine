from kskp.store import Command
from kskp.engine import Flow, Step, Point, Port

import json

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

class McutCommand(Command):
    """
    mcutコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        cmd_o = nm.mcut(args)
        return {'o': cmd_o}

class MselstrCommand(Command):
    """
    mselstrコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        cmd_o = nm.mselstr(args)
        return {'o': cmd_o}

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
            'square': Square(),
            'mcut': McutCommand(),
            'mselstr': MselstrCommand()
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
            ret = FlowUuidLink(None, node['uuid'])

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

                point_ids = [point.id for point in flow.points]

                # srcとdstからpointを作る
                for src_port in step.runnable.i_ports:
                    srcs = node['srcs']
                    if src_port.name not in srcs:
                        raise Exception(f"指定しているport名({src_port.name})がrunnable {node['id']}のsrcs({srcs})のキー中に存在しません")
                    # 対象のpointがすでに存在すればそれを取得する
                    if srcs[src_port.name] in point_ids:
                        src_point = [point for point in flow.points if point.id == srcs[src_port.name]][0]
                        src_point.i_port = src_port
                        src_point.cod = step
                    else:
                        src_point = Point(srcs[src_port.name], None, None, None, src_port, step)
                        flow.points.append(src_point)
                    if len(flow.i_ports) > 0 and src_point.o_port is None:
                        src_point.o_port = src_port

                for dst_port in step.runnable.o_ports:
                    dsts = node['dsts']
                    if dst_port.name not in dsts:
                        raise Exception(f"指定しているport名({dst_port.name})がrunnable {node['id']}のdsts({dsts})のキー中に存在しません")
                    # 対象のpointがすでに存在すればそれを取得する
                    if dsts[dst_port.name] in point_ids:
                        dst_point = [point for point in flow.points if point.id == dsts[dst_port.name]][0]
                        dst_point.dom = step
                        dst_point.o_port = dst_port
                    else:
                        dst_point = Point(dsts[dst_port.name], step, dst_port, None, None, None)
                        flow.points.append(dst_point)
                    if len(flow.o_ports) > 0 and dst_point.i_port is None:
                        dst_point.i_port = dst_port

        for node in json_obj['nodes']:
            # pointにdatumを入れていく
            if not self.is_node_runnable(node):
                if 'value' in node and node['value'] is not None:
                    target_point = [point for point in flow.points if point.id == node['id']][0]
                    target_point.datum = node['value']

        return flow

    def init_flow(self, flow, step_id):
        # 不要なPointを削除する
        f = self.delete_point(flow, step_id)
        return flow

    def delete_point(self, flow, step_id):
        dom = None
        # 不要なPointを削除する
        for point in flow.points:
            if point.id == step_id:
                last_point = point
                # プレビューするstep_idの場所で止める
                point.i_port = None
                point.cod = None
                break

        # プレビューするdatumより後ろのpointsを削除する
        # 実行開始場所に行き着くまで（Pointのdomとo_portがNoneのものにぶつかるまで？それともdatumを持つpointに行き着くまで？）繰り返す
            # step_id（止まるdatum）を始点にする
            # 始点のo_portをi_portにもつpointを保持する（上に上がっていく）
            # 保持対象のpointのidを新たな始点として再度処理を行う
        flow.points = self.search_connection_point(flow, last_point)
        flow.points.append(last_point)
        return flow

    def search_connection_point(self, flow, current_point):
        points = []
        for point in flow.points:
            if point.cod == current_point.dom:
                points.append(point)
                # 自身の上に繋がっているpointがてっぺんに当たるまでpointを集めてくる
                if not (point.o_port is None and point.dom is None):
                    points = points + self.search_connection_point(flow, point)

        return points

    def resolve(self, step_id=None):
        f = self.make_flow(self.json_str)

        # プレビューの場合、不要なPointを削除する
        if step_id is not None:
            f = self.init_flow(f, step_id)

        print(f.points)
        return f

class FlowUuidLink(FlowJsonLink):
    """
    UUIDを元にFlowを返却するリンク
    """

    def __init__(self, source, flow_uuid):
        self.source = source
        self.flow_uuid = flow_uuid
        if source is None:
            super().__init__('''{
                "ports": [[], []],
                "nodes": []
            }''')
        else:
            p = self.source.joinpath(f'{flow_uuid}.json')
            super().__init__(p.read_text())

    def node2link(self, node):
        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(self.source, node['uuid'])

        return ret

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
