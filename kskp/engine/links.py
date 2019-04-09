from kskp.store import Command
from kskp.engine import Flow, Step, Point, Port, Tube, NysolModule, Frame, Datum
import functools
import json
import uuid
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
        # 厳密にはframeじゃないが、まぁテスト用のコマンドなので
        # ラップするのはなんでもいいかなと思いframeにした。
        frame = Frame()
        frame.set_content(inputs['i'] ** 2)
        return {self.o_ports[0].name: frame}

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
        nysol_module = NysolModule()
        nysol_module.set_content(nm.mcut(args))
        return {'o': nysol_module}

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

        nysol_module_o = NysolModule()
        nysol_module_u = NysolModule()

        nysol_module_o.set_content(cmd_o)
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

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
        nysol_module = NysolModule()
        nysol_module.set_content(nm.mjoin(args))
        return {'o': nysol_module}

class MteeCommand(Command):
    """
    Mteeコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        args['m'] = inputs['m']
        cmd_o = nm.mjoin(args)
        return {'o': cmd_o}

class SaverCommand(Command):
    """
    指定した場所に出力するコマンド（テスト用）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        from unittest.mock import MagicMock
        mock_input = MagicMock()
        mock_input['store'].save.side_effect = self.save
        # cmd_o = inputs['store'].save(inputs['i'])
        cmd_o = mock_input['store'].save(inputs['i'])
        return {'o': cmd_o}

    def save(self, input):
        import nysol.mcmd as nm
        frame_name = str(uuid.uuid4())
        args = {}
        args['i'] = input
        args['o'] = 'kskp/data/' + frame_name + '.csv'
        cmd_o = nm.m2tee(args)
        return cmd_o

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
            "mjoin": MjoinCommand(),
            "store": SaverCommand(),
            "mtee": MteeCommand()
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

                point_ids = [point.id for point in flow.points]

                # srcとdstからpointを作る
                for src_port in step.runnable.i_ports:
                    srcs = node['srcs']
                    if src_port.name not in srcs:
                        raise Exception(f"指定しているport名({src_port.name})がrunnable {node['id']}のsrcs({srcs})のキー中に存在しません")
                    # 対象のpointがすでに存在すればそれを取得する
                    if srcs[src_port.name] in point_ids:
                        src_point = flow.get_point_by_node_id(srcs[src_port.name])
                        src_point.update_target(Tube(src_port, step))
                    else:
                        src_point = Point(srcs[src_port.name], [Tube(None, None)], None, [Tube(src_port, step)])
                        flow.points.append(src_point)

                    # inを外に出しているサブフローの場合は、
                    # てっぺんのPointのorigin.portを、外に出しているポート名にする
                    if len(flow.i_ports) > 0 and src_point.is_first:
                        for i_port in flow.i_ports:
                            # 今は「フローのi_port名」＝「datum_id（pointのid）」なのでこの条件にしている
                            if i_port.name == src_point.id:
                                src_point.update_origin(Tube(i_port, None))

                for dst_port in step.runnable.o_ports:
                    dsts = node['dsts']
                    # ２つのo_portsを持つコマンドで、片方のoutputしか使わない（片方しかフローに配置しない）ということもあるかもしれないので
                    # len(step.runnable.o_ports) == 1（runnableの元々の出力ポートが１つの場合）　と
                    # if dsts.get(dst_port.name) is None:
                    # 　　continue
                    # を追記
                    if dst_port.name not in dsts and len(step.runnable.o_ports) == 1:
                        raise Exception(f"指定しているport名({dst_port.name})がrunnable {node['id']}のdsts({dsts})のキー中に存在しません")

                    if dsts.get(dst_port.name) is None:
                        continue

                    # 対象のpointがすでに存在すればそれを取得する
                    if dsts[dst_port.name] in point_ids:
                        dst_point = flow.get_point_by_node_id(dsts[dst_port.name])
                        dst_point.update_origin(Tube(dst_port, step))
                    else:
                        dst_point = Point(dsts[dst_port.name], [Tube(dst_port, step)], None, [Tube(None, None)])
                        flow.points.append(dst_point)

                    # outを外に出しているサブフローの場合は、末端のPointのtarget.portを
                    # 外に出しているポート名にする
                    if len(flow.o_ports) > 0:
                        for target in dst_point.target:
                            if target.port is None and target.runnable is None:
                                for o_port in flow.o_ports:
                                    # 今は「フローのo_port名」＝「pointのid（datum_id）」なのでこの条件にしている
                                    if o_port.name == dst_point.id:
                                        dst_point.update_target(Tube(o_port, None))

        return flow

    def update_flow_by_other_than_runnable(self, nodes, flow):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        for node in nodes:
            # pointにdatumを入れていく
            if not self.is_node_runnable(node):
                target_point = [point for point in flow.points if point.id == node['id']][0]
                target_point.cache = node.get('makeCache')
                if 'value' in node and node['value'] is not None:
                    target_point.datum = node['value']

        return flow

    def pick_necessary_points(self, flow, last_ids):
        # プレビュー実行するのに必要なpointを取得する
        # 今はプレビュー対象のdatumで終わるように、プレビュー対象pointのtargetのtubeをNone,Noneにしている。（正しいんかな？）
        necessary_points = []
        for id in last_ids:
            for point in flow.points:
                if point.id == id:
                    if not len(flow.o_ports) > 0:
                        point.target = [Tube(None, None)]
                    last_point = point
                    break

            necessary_points = necessary_points + self.search_necessary_point(flow, last_point)
            necessary_points.append(last_point)

        return list(set(necessary_points))

    def search_necessary_point(self, flow, current_point):
        """
        プレビューするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、origin.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のorigin.runnableをtarget.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        points = []
        # current_pointの上につながっているPointを探す
        for point in flow.points:
            for p_target in point.target:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）
                # print('p_target:',id(p_target.runnable), 'current_point:',id(current_point.o_runnable))
                if p_target.runnable is current_point.o_runnable:
                    points.append(point)
                    # どこまで登るかを判定している場所
                    # もっといい書き方あるはず
                    if point.datum is None:
                        # 上にrunnableがある限りは登り続ける
                        if not point.is_first:
                            points = points + self.search_necessary_point(flow, point)

        return points

    def preview(func):
        """
        プレビュー処理を行う
        flowがもつPointを、last_idsを元に実行に必要なものだけを絞り込んで取得している
        """
        @functools.wraps(func)
        def _deco(self):
            flow = func(self)
            if len(self.last_ids) > 0:
                flow.points = self.pick_necessary_points(flow, self.last_ids)

            print(flow.points)
            return flow
        return _deco

    def resolve(self):
        f = self.make_flow(self.json_str)

        # プレビュー処理を行う
        # flowがもつPointを、last_idsを元に実行に必要なものだけを絞り込んで取得している
        if len(self.last_ids) > 0:
            f.points = self.pick_necessary_points(f, self.last_ids)

        # キャッシュ処理
        cache_point = [point for point in f.points if point.cache]
        for point in cache_point:
            # pointが末端ならm2teeを入れない
            if point.is_last:
                pass
            else:
                # 出力コマンドとそれが出すpointを追加
                mtee_id = str(uuid.uuid4())
                step = Step(mtee_id, SaverCommand(), None)
                add_point = Point(mtee_id, [Tube(Port('o', 'mcmd'), step)], None, [Tube(None, None)])

                # cacheするpointと追加したpointのtargetを設定する
                add_point.target = point.target
                point.target = [Tube(Port('i', 'frame'), step)]

                f.substeps.append(step)
                f.points.append(add_point)
            # jsonを更新する
            pass

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
