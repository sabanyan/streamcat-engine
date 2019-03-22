from kskp.store import Command
from kskp.engine import Flow, Step, Point, Port, Tube
import functools
import json
from pathlib import Path

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
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        cmd_o = nm.mselstr(args)
        cmd_u = cmd_o.redirect('u')
        return {'o': cmd_o, 'u': cmd_u}

class MjoinCommand(Command):
    """
    mjoinコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        args['m'] = inputs['m']
        cmd_o = nm.mjoin(args)
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
            'mselstr': MselstrCommand(),
            "mjoin": MjoinCommand()
        }

        if runnable_id not in table:
            raise Exception(f"存在しないcommandId'{runnable_id}'が指定されています")

        return table[runnable_id]

class FlowJsonLink:
    """
    フローへのリンク
    """
    def __init__(self, json_str, last_ids=[]):
        self.json_str = json_str
        self.last_ids = last_ids

    def node2link(self, node):
        if 'link' in node:
            return SampleFlowJsonLink()

        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(Path('kskp/flows'), node['uuid'])

            # かなりの力技・・・。
            # プレビューを行う場合、サブフロー内で余分な処理が走らないように
            # 親フローが子フロー（使用するサブフロー）に、このoutputが必要だということを教える。

            # メインフローでプレビュー時、どのdstsを通るかを求める
            dst_ids = self.pick_necessary_dst_ids(json.loads(self.json_str), self.last_ids)
            # メインフローで使われるdstsの中に、対象のnode（サブフロー）が出力するものがあれば教えてあげる
            if len(dst_ids) > 0:
                ret.last_ids = [port for port, datum_id in node['dsts'].items() for id in dst_ids if datum_id == id]

        return ret

    def pick_necessary_dst_ids(self, nodes, datum_ids):
        ids = []
        for datum_id in datum_ids:
            for node in nodes['nodes']:
                if self.is_node_runnable(node) and datum_id in list(node['dsts'].values()):
                    # 対象のnode
                    ids = ids + self.pick_necessary_dst_ids(nodes, list(node['srcs'].values()))
            ids.append(datum_id)
        return list(set(ids))

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

        # flowを更新する
        flow = self.update_flow_by_runnable(json_obj['nodes'], flow)
        flow = self.update_flow_by_other_than_runnable(json_obj['nodes'], flow)
        return flow

    def update_flow_by_runnable(self, nodes, flow):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        # まず、runnableを集める
        for node in nodes:
            if self.is_node_runnable(node):

                # runnableのインスタンス化を行う
                step = Step(node['id'], self.node2link(node).resolve(), node['args'])

                flow.substeps.append(step)

                # srcとdstからpointを作る
                for src_port in step.runnable.i_ports:
                    srcs = node['srcs']
                    if src_port.name not in srcs:
                        raise Exception(f"指定しているport名({src_port.name})がrunnable {node['id']}のsrcs({srcs})のキー中に存在しません")
                    # flowのpointsをsrcを使って更新する
                    # pointはflowの属性なので、flowが自身のpointを更新する方がいいかなと思い、Flowに移動しました。
                    # Flowクラスにもともとあったメソッド群もself.pointsを元に動いているので移動先としてはおかしくないかと
                    # FlowJsonLinkクラスはPointを完全に知らなくなり、FlowクラスだけがPointの存在を知っているようになった（単一責任原則を守るようになった？）
                    # それだけFlowクラスのメソッドが多くなってしまったが、大丈夫かな。。。？
                    # そのままFlowクラスに移しただけなのでFlow側で別途リファクタはいるかも
                    flow.update_src_points(srcs[src_port.name], Tube(src_port, step))

                for dst_port in step.runnable.o_ports:
                    dsts = node['dsts']
                    if dst_port.name not in dsts and len(step.runnable.o_ports) == 1:
                        raise Exception(f"指定しているport名({dst_port.name})がrunnable {node['id']}のdsts({dsts})のキー中に存在しません")
                    # 2つのdstをもつstepが片方しか使っていないかどうかのチェック、チェックしないと余計なPointを作ってしまうので。
                    if dsts.get(dst_port.name) is None and len(step.runnable.o_ports) > 1:
                        continue
                    # flowのpointsをdstを使って更新する
                    flow.update_dst_points(dsts[dst_port.name], Tube(dst_port, step))

        return flow

    def update_flow_by_other_than_runnable(self, nodes, flow):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        for node in nodes:
            # pointにdatumを入れていく
            if not self.is_node_runnable(node):
                if 'value' in node and node['value'] is not None:
                    flow.update_point_by_value(node['id'], node['value'])

        return flow

    def resolve(self):
        f = self.make_flow(self.json_str)

        # プレビュー処理を行う
        # flowがもつPointを、last_idsを元に実行に必要なものだけを絞り込んで取得している
        if len(self.last_ids) > 0:
            f.pick_necessary_points(self.last_ids)

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
