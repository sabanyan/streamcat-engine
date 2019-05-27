import functools
import json
import uuid
from pathlib import Path

from kskp.engine import Flow, Step, Point, Port, Tube, Folder

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
        # 循環import避けるためにここに書いている。。。
        from .tests.test_main import Square

        table = {
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
                ret.last_ids = [port for port, datum_id in node['dsts'].items() for dst_id in dst_ids if datum_id == dst_id]

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
            # TODO: パスで作成するのではなくuuidでFolderを取得したい
            store = Folder(Path('kskp/data/library/フロー実行キャッシュ'))
            self.put_saver(point, f, store, CacheSaverCommand())

        # lasts出力処理（メインフローの場合のみ）
        if self.is_root:
            last_points = [point for point in f.points if point.is_last]
            for point in last_points:
                # TODO: パスで作成するのではなくuuidでFolderを取得したい
                store = Folder(Path('kskp/data/library/フロー実行結果'))
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
            if not self.is_runnable_node(node):
                continue

            # runnableのインスタンス化を行う
            step = Step(node['id'], self.node2link(node).resolve(), node['args'])
            flow.substeps.append(step)

            srcs = node['srcs']
            dsts = node['dsts']

            self.replace_multi_inputs(step, srcs)

            # srcとdstからpointを作る
            for s_port_name, s_node_id in srcs.items():
                # 定義上に存在しないポート名がsrcsに存在していないかの確認
                src_port = self.get_port_by_name(step.runnable.i_ports, s_port_name)
                if src_port is None:
                    raise Exception(f"指定しているport名({s_port_name})がrunnable {node['id']}の定義しているポート群({step.runnable.i_ports})に存在しません")

                # pointを作成する（作成対象がすでにあれば更新する）
                src_point = self.upsert_point(flow=flow, point_id=s_node_id,
                                              origin=Tube(None, None), target=Tube(src_port, step))

                # 上記src_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにoriginを置き換える
                [self.update_point(point=src_point, origin=Tube(i_port, None))
                 for i_port in flow.i_ports if i_port.name == src_point.id]

            for d_port_name, d_node_id in dsts.items():
                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self.get_port_by_name(step.runnable.o_ports, d_port_name)
                if dst_port is None:
                    raise Exception(f"指定しているport名({d_port_name})がrunnable {node['id']}の定義しているポート群({step.runnable.o_ports})に存在しません")

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self.upsert_point(flow=flow, point_id=d_node_id,
                                              origin=Tube(dst_port, step), target=Tube(None, None))

                # 上記dst_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにtargetを置き換える
                [self.update_point(point=dst_point, target=Tube(o_port, None))
                 for o_port in flow.o_ports if o_port.name == dst_point.id]

    def get_port_by_name(self, runnable_ports, port_name):
        """
        指定したport_nameをもつportを取得する。
        runnableというクラスがあったらそこにあるべきなのだろうけど
        今はないし、作るの面倒なのでとりあえずここに。
        絶対必要になった時に作ろう。。。
        """
        for runnable_port in runnable_ports:
            if runnable_port.name == port_name:
                return runnable_port
        return None

    def replace_multi_inputs(self, step, srcs):
        """
        *のportをport群に変換する
        """
        for src_port in step.runnable.i_ports:
            if src_port.name == '*':
                step.runnable.i_ports = [Port(p, 'frame') for p in srcs.keys()]

    def upsert_point(self, flow, point_id, target, origin):
        """
        指定したpoint_idのpointを作成する
        対象のpointがすでに存在していればそのpointを更新する
        """
        point_ids = [point.id for point in flow.points]
        if point_id in point_ids:
            point = self.update_point(point=flow.select_point_by_node_id(point_id), origin=origin, target=target)
        else:
            point = self.insert_point(flow=flow, point_id=point_id, origin=[origin], target=[target])
        return point

    def insert_point(self, flow, point_id, origin, target):
        """
        pointを新規作成し、flowのpointsに追加する
        """
        point = Point(point_id, origin, None, target)
        flow.points.append(point)
        return point

    def update_point(self, point, origin=Tube(None, None), target=Tube(None, None)):
        """
        既存のpointを更新する
        """
        if not origin.is_None:
            point.update_origin(origin)

        if not target.is_None:
            point.update_target(target)

        return point

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

        # saverのargs設定
        # FlowUuidLinkならキャッシュ生成後にjsonを書き換える必要があるのでその情報を渡す。そうでないならflowのjsonが存在しないということでとりあえず何も渡さない
        args = {'flow_uuid': self.flow_uuid, 'datum_id':point.id} if isinstance(self, FlowUuidLink) else {}
        # saverが作るframe及びcacheのlabelはここで設定できる
        args['label'] = point.id

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
