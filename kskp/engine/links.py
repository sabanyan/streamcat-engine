from kskp.store import Command
from kskp.engine import Flow, Step, Arrow, Port

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

                arrow_ids = [arrow.id for arrow in flow.arrows]

                # srcとdstからarrowを作る
                for src_port in step.runnable.i_ports:
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
                        src_arrow.o_port = src_port

                for dst_port in step.runnable.o_ports:
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
                        dst_arrow.i_port = dst_port

        for node in json_obj['nodes']:
            # arrowにdatumを入れていく
            if not self.is_node_runnable(node):
                if 'value' in node and node['value'] is not None:
                    target_arrow = [arrow for arrow in flow.arrows if arrow.id == node['id']][0]
                    target_arrow.datum = node['value']

        return flow

    def init_flow(self, flow, step_id):
        # 不要なArrowを削除する
        f = self.delete_arrow(flow, step_id)
        return flow

    def delete_arrow(self, flow, step_id):
        dom = None
        # 不要なArrowを削除する
        for arrow in flow.arrows:
            if arrow.id == step_id:
                last_arrow = arrow
                # プレビューするstep_idの場所で止める
                arrow.i_port = None
                arrow.cod = None
                break

        # プレビューするdatumより後ろのarrowsを削除する
        # 実行開始場所に行き着くまで（Arrowのdomとo_portがNoneのものにぶつかるまで？それともdatumを持つarrowに行き着くまで？）繰り返す
            # step_id（止まるdatum）を始点にする
            # 始点のo_portをi_portにもつarrowを保持する（上に上がっていく）
            # 保持対象のarrowのidを新たな始点として再度処理を行う
        flow.arrows = self.search_connection_arrow(flow, last_arrow)
        flow.arrows.append(last_arrow)
        return flow

    def search_connection_arrow(self, flow, current_arrow):
        arrows = []
        for arrow in flow.arrows:
            if arrow.cod == current_arrow.dom:
                arrows.append(arrow)
                # 自身の上に繋がっているarrowがてっぺんに当たるまでarrowを集めてくる
                if not (arrow.o_port is None and arrow.dom is None):
                    arrows = arrows + self.search_connection_arrow(flow, arrow)

        return arrows

    def resolve(self, step_id=None):
        f = self.make_flow(self.json_str)

        # プレビューの場合、不要なArrowを削除する
        if step_id is not None:
            f = self.init_flow(f, step_id)

        print(f.arrows)
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
