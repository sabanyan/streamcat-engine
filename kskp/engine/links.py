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
    def __init__(self, json_str, step_id=None):
        self.json_str = json_str
        self.step_id = step_id

    def node2link(self, node):
        if 'link' in node:
            return SampleFlowJsonLink()

        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(Path('kskp/flows'), node['uuid'])

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
                        # まだ終端扱い（targetのportとrunnableがNone）なら、上書き
                        # 既に中間点としてparseされていたら、Tubeを追加する
                        if src_point.target[0].port is None and src_point.target[0].runnable is None:
                            src_point.target = [Tube(src_port, step)]
                        else:
                            src_point.target.append(Tube(src_port, step))
                    else:
                        src_point = Point(srcs[src_port.name], [Tube(None, None)], None, [Tube(src_port, step)])
                        flow.points.append(src_point)

                    if len(flow.i_ports) > 0:
                        for origin in src_point.origin:
                            if origin.port is None and origin.runnable is None:
                                for i_port in flow.i_ports:
                                    if i_port.name == src_point.id:
                                        src_point.origin = [Tube(i_port, None)]

                    # if len(flow.i_ports) > 0 and src_point.o_port is None:
                    #     src_point.origin = [Tube(src_port, None)]

                for dst_port in step.runnable.o_ports:
                    dsts = node['dsts']
                    # ２つのo_portsを持つコマンドで、片方のoutputしか使わない（片方しかフローに配置しない）ということもあるかもしれないので
                    # len(step.runnable.o_ports) == 1　と
                    # if dsts.get(dst_port.name) is None:
                    # 　　continue
                    # を追記
                    if dst_port.name not in dsts and len(step.runnable.o_ports) == 1:
                        raise Exception(f"指定しているport名({dst_port.name})がrunnable {node['id']}のdsts({dsts})のキー中に存在しません")

                    if dsts.get(dst_port.name) is None:
                        continue

                    # 対象のpointがすでに存在すればそれを取得する
                    if dsts[dst_port.name] in point_ids:
                        dst_point = [point for point in flow.points if point.id == dsts[dst_port.name]][0]
                        # 複数のoriginをもつPointはないとは思うが、一応書いておく
                        if dst_point.origin[0].port is None and dst_point.origin[0].runnable is None:
                            dst_point.origin = [Tube(dst_port, step)]
                        else:
                            dst_point.origin.append(Tube(dst_port, step))
                    else:
                        dst_point = Point(dsts[dst_port.name], [Tube(dst_port, step)], None, [Tube(None, None)])
                        flow.points.append(dst_point)

                    if len(flow.o_ports) > 0:
                        for target in dst_point.target:
                            if target.port is None and target.runnable is None:
                                for o_port in flow.o_ports:
                                    if o_port.name == dst_point.id:
                                        dst_point.target = [Tube(o_port, None)]

                    # if len(flow.o_ports) > 0 and dst_point.target is [Tube(dst_port, step)]:
                    #     dst_point.target = [Tube(dst_port, None)]

        for node in json_obj['nodes']:
            # pointにdatumを入れていく
            if not self.is_node_runnable(node):
                if 'value' in node and node['value'] is not None:
                    target_point = [point for point in flow.points if point.id == node['id']][0]
                    target_point.datum = node['value']

        return flow

    def delete_point(self, flow, step_id):
        dom = None
        # プレビューするstep_idの場所で止める
        # 今はtargetのtubeをNone,Noneにしているけど、いい止め方なのかな。。。？
        for point in flow.points:
            if point.id == step_id:
                last_point = point
                point.target = [Tube(None, None)]
                break


        flow.points = self.search_connection_point(flow, last_point)
        flow.points.append(last_point)
        return flow

    def search_connection_point(self, flow, current_point):
        """
        プレビューするdatumを作成するために必要なPointを絞り込む
        どこまで登るかは、originのtarget・o_portがNoneのものにぶつかるまで？それともdatumを持つpointに行き着くまで？
        今は後者でやっているけど、どうかな〜

        1. 指定されたstep_idをもつpointのidを始点にする
        2. 始点のo_portをi_portにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再度処理を行う
        """
        points = []
        # current_pointの上につながっているPointを探す
        for point in flow.points:
            for p_target in point.target:
                if p_target.runnable == current_point.origin[0].runnable:
                    points.append(point)
                    # datumがNoneではないpointに行き着くまで登る
                    if point.datum is None:
                        points = points + self.search_connection_point(flow, point)

        return points

    def preview(func):
        """
        プレビュー処理を行う
        flowがもつPointを、step_idを元に必要なものだけに絞り込んでいる
        """
        @functools.wraps(func)
        def _deco(self):
            flow = func(self)
            if self.step_id is not None:
                flow = self.delete_point(flow, self.step_id)
            return flow
        return _deco

    @preview
    def resolve(self):
        f = self.make_flow(self.json_str)

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
