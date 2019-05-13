from kskp.engine import Flow, Step, Point, Port, Tube, NysolModule, Frame, Datum, Store, Folder, Cache
import functools
import json
import uuid
from pathlib import Path

from .tmp_command import *

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
        TODO: 下記の対応表をなくす様に実装する
        """
        table = {
            'test': TestCommand(),
            'square': Square(),
            'mcut': McutCommand(),
            'mselstr': MselstrCommand(),
            "mjoin": MjoinCommand(),
            "store": SaverCommand(),
            "mtee": MteeCommand(),
            "mcat": McatCommand(),
            "msetstr": MsetstrCommand(),
            "msummary": MsummaryCommand(),
            "msortf": MsortfCommand(),
            "msel": MselCommand(),
            "mnumber": MnumberCommand(),
            "mcross": McrossCommand(),
            "m2cross": M2crossCommand(),
            "mcal": McalCommand(),
            "mchkcsv": MchkcsvCommand(),
            "column_list": ColumnlistCommand(),
            "mdformat": MdformatCommand(),
            "mshare": MshareCommand(),
            "mchgnum": MchgnumCommand(),
            "groupby": GroupbyCommand(),
            "mfldname": MfldnameCommand(),
            "mcount": McountCommand(),
            "column_unique_name": ColumnUniqueNameCommand(),
            "column_name": ColumnNameCommand(),
            "sml_modeling": SmlModelingCommand()
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
        self.is_root = False

    def node2link(self, node):
        if 'link' in node:
            return SampleFlowJsonLink()

        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(Path('kskp/flows'), node['uuid'])

            # かなりの力技・・・。
            # 実行を行う場合、サブフロー内で余分な処理が走らないように
            # 親フローが子フロー（使用するサブフロー）に、このoutputが必要だということを教える。

            # メインフローでプレビュー時、どのdstsを通るかを求める
            dst_ids = self.pick_necessary_dst_ids(json.loads(self.json_str), self.last_ids)
            # メインフローで使われるdstsの中に、対象のnode（サブフロー）が出力するものがあれば教えてあげる
            if len(dst_ids) > 0:
                ret.last_ids = [port for port, datum_id in node['dsts'].items() for id in dst_ids if datum_id == id]

        return ret

    def resolve(self):
        f = self.make_flow(self.json_str)

        # flowがもつPointを、実行に必要なものだけを絞り込んで取得している。

        # self.last_idsには
        # メインフローの場合 ： プレビューするdatumのid群
        # サブフローの場合　 ： 親の実行に必要なlastのid群
        # が入っている。（はず）
        # プレビューしない場合はメインフローのlastのid群を使って絞り込みを行う。
        lasts = self.last_ids if len(self.last_ids) > 0 else f.lasts.keys()
        f.points = self.pick_necessary_points(f, lasts)

        # キャッシュ作成処理
        cache_points = [point for point in f.points if point.is_cache]
        for point in cache_points:
            # cacheの保存先を生成、pointのfor文の中で生成しているのでpoint毎に保存先は変えられるが、使う機会ある？？
            store = Folder(Path('kskp/data/cache_frames'))
            self.put_saver(point, f, store, CacheSaverCommand())

        # lasts出力処理（メインフローの場合のみ）
        if self.is_root:
            last_points = [point for point in f.points if point.is_last]
            for point in last_points:
                store = Folder(Path('kskp/data/result'))
                self.put_saver(point, f, store, SaverCommand())

        print(f.points)
        return f

    def make_flow(self, json_str):

        # JSONを読み込む
        json_obj = json.loads(json_str)

        flow = Flow()

        # portを読む
        ports = json_obj['ports']
        flow.i_ports = self.parse_ports(ports[0])
        flow.o_ports = self.parse_ports(ports[1])

        # flowを更新する
        self.update_flow_by_runnable(flow, json_obj['nodes'])
        self.update_flow_by_other_than_runnable(flow, json_obj['nodes'])
        return flow

    def parse_ports(self, port_dict_list):
        """ dictのリストからportインスタンスのリストを作る """
        return [Port(p['nodeId'], p['type']) for p in port_dict_list]

    def update_flow_by_runnable(self, flow, nodes):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        # まず、runnableを集める
        for node in nodes:
            if self.is_runnable_node(node):

                # runnableのインスタンス化を行う
                step = Step(node['id'], self.node2link(node).resolve(), node['args'])

                flow.substeps.append(step)

                point_ids = [point.id for point in flow.points]

                for src_port in step.runnable.i_ports:
                    srcs = node['srcs']
                    if src_port.name == '*':
                        step.runnable.i_ports = [Port(p, 'frame') for p in node['srcs'].keys()]

                # srcとdstからpointを作る
                for src_port in step.runnable.i_ports:
                    srcs = node['srcs']
                    if src_port.name not in srcs:
                        raise Exception(f"指定しているport名({src_port.name})がrunnable {node['id']}のsrcs({srcs})のキー中に存在しません")
                    # 対象のpointがすでに存在すればそれを取得する
                    if srcs[src_port.name] in point_ids:
                        src_point = flow.select_point_by_node_id(srcs[src_port.name])
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
                        dst_point = flow.select_point_by_node_id(dsts[dst_port.name])
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

    def update_flow_by_other_than_runnable(self, flow, nodes):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        # 実行に関係ないnodeのtype群
        except_type_list = ['note']

        for node in nodes:
            # pointにdatumを入れていく
            if not self.is_runnable_node(node) and not node['type'] in except_type_list:
                target_point = [point for point in flow.points if point.id == node['id']][0]
                target_point.cache = node.get('makeCache')

                # データの取得先の設定
                # サブフローの先頭は外部からデータをもらうので、それ以外の場合に処理を行う
                if not (len(flow.i_ports) > 0 and target_point.is_first):
                    if self.is_value_node(node):
                        target_point.datum = node['value']
                    # uuidが既に振られている場合は、loaderから取ってくるようにする
                    elif node.get('uuid') is not None:
                        self.put_loader(node.get('uuid'), target_point, flow, Folder(Path('kskp/data')))
                        # キャッシュが既にあるpointをTrueにしてもしょうがないのでFalseにする
                        target_point.cache = False
        return flow

    def is_value_node(self, node):
        """
        valueをもつnodeかどうか
        uuidが入っていたらそっちを優先する
        """
        return node.get('value') is not None and node.get('uuid') is None

    def is_runnable_node(self, node):
        """ 指定されたnodeがrunnableかどうかを判断する """
        return node['type'] == 'command' or node['type'] == 'flow'

    def pick_necessary_dst_ids(self, nodes, datum_ids):
        """
        指定したnodesの中で、指定したdatum_id群を取得するのに必要なdstsのid群を取得する
        """
        ids = []
        for datum_id in datum_ids:
            for node in nodes['nodes']:
                if self.is_outputting_datum_node(node, datum_id):
                    # 対象のnode
                    ids.extend(self.pick_necessary_dst_ids(nodes, list(node['srcs'].values())))
            ids.append(datum_id)
        return list(set(ids))

    def is_outputting_datum_node(self, node, datum_id):
        """
        指定したdatumを出力するnodeかを調べる
        """
        return self.is_runnable_node(node) and datum_id in list(node['dsts'].values())

    def pick_necessary_points(self, flow, last_ids):
        """
        実行するのに必要なpointを取得する
        """
        necessary_points = []
        for id in last_ids:
            lasts_point = flow.select_point_by_id(id)
            if not len(flow.o_ports) > 0:
                # 今はプレビュー対象のdatumで終わるように、プレビュー対象pointのtargetのtubeをNone,Noneにしている。（正しいんかな？）
                lasts_point.target = [Tube(None, None)]

            # lasts_pointの上に繋がっているpointsを取得する
            necessary_points.extend(self.search_necessary_point(flow.points, lasts_point))
            necessary_points.append(lasts_point)

        return list(set(necessary_points))

    def search_necessary_point(self, points, current_point):
        """
        プレビューするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、origin.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のorigin.runnableをtarget.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        necessary_points = []
        # current_pointの上につながっているPointを探す
        for point in points:
            for p_target in point.target:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）
                if p_target.runnable is current_point.o_runnable:
                    necessary_points.append(point)
                    if not (point.datum is not None or point.is_first):
                        necessary_points.extend(self.search_necessary_point(points, point))

        return necessary_points

    def put_loader(self, frame_uuid, target_point, flow, store):
        """
        target_point(uuidが既にあるdatumのpoint)の前に
        LoaderStepとStorePointをくっつける
        Loaderは指定したstoreからデータを取ってくる
        """
        loader_step = self.make_loader_step(frame_uuid)
        store_point = Point(frame_uuid + '_loader_point', [Tube(None, None)], store, [Tube(Port('store', 'store'), loader_step)])
        target_point.origin = [Tube(Port('o', 'frame'), loader_step)]
        flow.points.append(store_point)
        flow.substeps.append(loader_step)

    def make_loader_step(self, node_uuid):
        """
        指定したuuidのデータを取ってくるLoaderStepを作成する
        """
        return Step(str(uuid.uuid4()), LoaderCommand(), {'uuid':node_uuid})

    def put_saver(self, point, flow, store, saver):
        """
        指定したpointを保存する。保存先はstoreオブジェクトが指定する場所に。
        lastsなら最後に設置し、そうでないなら間に挟むように設置する
        """
        # 出力コマンドとそれが出すpointを追加
        # FlowUuidLinkならキャッシュ生成後にjsonを書き換える必要があるのでその情報を渡す。そうでないならflowのjsonが存在しないということでとりあえず何も渡さない
        args = {'flow_uuid': self.flow_uuid, 'datum_id':point.id} if isinstance(self, FlowUuidLink) else {}
        saver_step = self.make_saver_step(args, saver)
        store_point = Point(point.id + '_store_point', [Tube(None, None)], store, [Tube(Port('store', 'store'), saver_step)])
        saver_point = Point(point.id, [Tube(Port('o', 'mcmd'), saver_step)], None, [Tube(None, None)])
        point.id = str(uuid.uuid4())

        # lastsじゃない場合は追加したpointを次のstepに繋げる
        if not point.is_last:
            saver_point.target = point.target
        # pointの向き先を変更する
        point.target = [Tube(Port('i', 'frame'), saver_step)]

        flow.substeps.append(saver_step)
        flow.points.extend([saver_point, store_point])

    def make_saver_step(self, args, saver):
        """
        saverコマンドのstepを作成する
        """
        return Step(str(uuid.uuid4()), saver, args)

class FlowUuidLink(FlowJsonLink):
    """
    UUIDを元にFlowを返却するリンク
    """

    def __init__(self, source, flow_uuid, last_ids=[]):
        self.source = source
        self.flow_uuid = flow_uuid
        if source is None:
            super().__init__('''{
                "ports": [[], []],
                "nodes": []
            }''')
        else:
            p = self.source.joinpath(f'{flow_uuid}.json')
            super().__init__(p.read_text(), last_ids)

    def node2link(self, node):
        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(self.source, node['uuid'])

        return ret
