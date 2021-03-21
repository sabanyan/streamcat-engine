from kskp.core import Port
from kskp.store import FlowData        
from .stepoints import Stepoints
from .point import Point
from .appenders import FolderDataSourcePrepender

class Flow(FlowData):
    """
    TODO: 名称変更した方がいい？
    """
    def __init__(self, flow_data, is_root, link_context, datum_factory):
        # to_json()によりflow_jsonはコピーされる
        super().__init__(flow_data.to_json())

        # UUIDを採番する
        import uuid
        self.uuid = str(uuid.uuid4())

        # Portを設定する
        self.i_ports = self._parse_ports(self.ports[0])
        self.o_ports = self._parse_ports(self.ports[1])

        self.is_root = is_root
        self.link_context = link_context
        self.datum_factory = datum_factory
        self.folder_data_source_prepender = FolderDataSourcePrepender(datum_factory)

        self.stepoints = Stepoints(steps=[], points=[], o_ports=self.o_ports, is_root=is_root)

        # flowを設定する
        if flow_data.has_nodes:
            # フローの参照権限がなくても実行権限があれば、フローJSONを参照する必要がある
            # そのため、use_exec_auth=Trueを指定する
            substeps, points = self._update_flow_by_runnable(self.get_nodes(use_exec_auth=True))
            # StepsとPointsを格納する
            self.stepoints = Stepoints(steps=substeps, points=points, o_ports=self.o_ports, is_root=is_root)
            # 
            self._update_flow_by_other_than_runnable(self.get_nodes(use_exec_auth=True))


        # 
        # データデストか否かの判定をする
        # 
        # データデストのself.o_portsには、データデストの出力を親フローに繋げる為に、Portを追加するので
        # Flowオブジェクトの生成時に判定する
        # 
        # TODO: いい条件が思い浮かばない,,,
        # has_store = any (p for p in self.points if p.is_store)
        # self._is_datadst = len(self.i_ports) == 1 and len(self.lasts) == 1 and has_store
        self._is_datadst = len(self.i_ports) == 1 and len(self.o_ports) == 0


        from kskp.store import ModuleStore
        self.module_store = ModuleStore()

        self.context = {}

    def _parse_ports(self, port_dict_list):
        """
        dictのリストからportインスタンスのリストを作る
        """
        # TODO: 'nodeId'はサブフロー内でのノードIdなので、ポートの識別子には'label'を使うべきか？
        # Commandではポートの識別に'label'を用いているので、Flowも合わせるべきでは？
        return [Port(p['nodeId'], p['type']) for p in port_dict_list]

    def _update_flow_by_runnable(self, nodes):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        from kskp.depo.std.commands import SCommand
        from .step import Step
        from .tube import Tube

        substeps = []
        points = set()

        # まず、runnableを集める
        for node in nodes:
            if not self._is_runnable_node(node):
                continue

            # CommandまたはFlowを取得する
            cmd_or_flow = self._node2link(node).resolve()
            
            if isinstance(cmd_or_flow, SCommand):
                # SCommand共通引数を作成する
                args = {'flow'         : self.link_context.flow_datum,
                        'flow_uuid'    : self.link_context.flow_uuid,
                        'flow_label'   : self.link_context.flow_label,
                        'result_folder': self.link_context.flow_datum.find_parent(),
                        'start_time'   : self.link_context.start_time,
                        'activity_uuid': self.link_context.activity_uuid}
                # 引数の設定が重複した場合は、コマンドの個別引数の方を優先する
                args.update(node['args'])
            else:
                # MCommandに不要な引数を設定するとエラーになる
                args = node['args']

            srcs = node['srcs']
            dsts = node['dsts']

            i_ports = self._replace_multi_inputs(cmd_or_flow.i_ports, srcs)
            o_ports = self._replace_multi_inputs(cmd_or_flow.o_ports, dsts)

            # runnableのインスタンス化を行う
            step = Step(node['id'], cmd_or_flow, args, i_ports=i_ports, o_ports=o_ports)
            # Stepを集める
            substeps.append(step)

            # srcとdstからpointを作る
            for s_port_label, s_node_id in srcs.items():
                # 可変長引数で入力PointがNoneになる場合に備える
                if s_node_id is None:
                    raise Exception(f"コマンド({node['label']})の入力({s_port_label})が指定されていません")

                # 定義上に存在しないポート名がsrcsに存在していないかの確認
                src_port = self._get_port_by_label(i_ports, s_port_label)
                if src_port is None:
                    raise Exception(f"指定しているport名({s_port_label})がrunnable {node['id']}の定義しているポート群({i_ports})に存在しません")

                # out/inポートフラグの取得
                is_in = self.has_as_in_point(s_node_id)
                is_out = self.has_as_out_point(s_node_id)

                # pointを作成する（作成対象がすでにあれば更新する）
                src_point = self._upsert_point(flow=self, point_id=s_node_id, is_in=is_in, is_out=is_out,
                                              src_tube=Tube(None, None), dst_tube=Tube(src_port, step))

                # 上記src_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにoriginを置き換える
                [src_point.add_src_tube(Tube(i_port, None)) for i_port in self.i_ports if i_port.label == src_point.id]

                # Pointを集める
                points.add(src_point)

            for d_port_label, d_node_id in dsts.items():
                if d_node_id is None:
                    raise Exception(f"コマンド({node['label']})の出力({d_port_label})が指定されていません")

                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self._get_port_by_label(step.runnable.o_ports, d_port_label)
                if dst_port is None:
                    raise Exception(f"指定しているport名({d_port_label})がrunnable {node['id']}の定義しているポート群({step.runnable.o_ports})に存在しません")

                # out/inポートフラグの取得
                is_in = self.has_as_in_point(d_node_id) 
                is_out = self.has_as_out_point(d_node_id)

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self._upsert_point(flow=self, point_id=d_node_id, is_in=is_in, is_out=is_out,
                                              src_tube=Tube(dst_port, step), dst_tube=Tube(None, None))

                # 上記dst_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにdst_tubesを置き換える
                # (メインフローの場合は繋げる必要がない、かつ次のStepへ繋げる為にdst_tubes変数が必要なので、何もしない)
                if not self.is_root:
                    [dst_point.add_dst_tube(Tube(o_port, None)) for o_port in self.o_ports if o_port.label == dst_point.id]

                from kskp.depo.std.commands import AssertCommand
                if isinstance(cmd_or_flow, AssertCommand):
                    # 出力情報に、AssertCommandの出力ポイントのidを含めるため
                    args['asserted_point'] = dst_point.id
                    # AssertCommandで例外を検証対象とするため、例外の入力を許可する
                    step.ex_acceptable = True

                # Pointを集める
                points.add(dst_point)

        # 作成したStep及びPointのリストを返す
        return substeps, list(points)

    def _update_flow_by_other_than_runnable(self, nodes):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        # 実行に関係ないnodeのtype群
        except_type_list = ['note']

        for node in nodes:
            # pointにdatumを入れていく
            if self._is_runnable_node(node) or node['type'] in except_type_list:
                continue
                
            target_points = [point for point in self.points if point.id == node['id']]
            if len(target_points) < 1:
                continue

            target_point = target_points[0]
            target_point.cache = node.get('makeCache')
            target_point.label = node.get('label')

            # Storeの場合、StoreオブジェクトをPointに格納する
            if self._is_store_node(node):
                store_uuid = node.get('uuid')
                store = self.datum_factory.find_by_uuid(store_uuid)

                # StoreにDatabaseを設定する
                target_point.datum = store
                continue

            # 入力Point以外の場合、そのPointに紐づくDatumオブジェクト格納する
            # ただし、メインフローの場合は入力Pointか否かを条件にしない
            if self.is_root or not target_point.is_in:
                if self._is_value_node(node):
                    # nodeのvalue属性はテストコードで用いている
                    if isinstance(node['value'], list):
                        from kskp.store import List
                        target_point.datum = List(node['value'])
                    else:
                        target_point.datum = node['value']
                elif node.get('uuid') is not None:
                    # uuidが既に振られている場合は、loaderから取ってくるようにする
                    # self._put_loader(node.get('uuid'), target_point, self, Folder)
                    self.folder_data_source_prepender.do_prepend(self, target_point, node.get('uuid'))
                    # キャッシュが既にあるpointをTrueにしてもしょうがないのでFalseにする
                    target_point.cache = False

    def _node2link(self, node):
        from kskp.depo.std.commands import CommandLink
        from .links import FlowJsonLink

        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            # ret = FlowUuidLink(node['uuid'], {}, self.link_context)
            from kskp.store.auth import NotAuthorizedException
            try:
                sub_flow = self.datum_factory.find_by_uuid(node['uuid'])
                ret = FlowJsonLink(sub_flow, None, {}, self.link_context, is_root=False)
            except NotAuthorizedException:
                raise NotAuthorizedException(f'共有フロー({node.get("id")})の参照権限がありません')

            # # かなりの力技・・・。
            # # 実行を行う場合、サブフロー内で余分な処理が走らないように
            # # 親フローが子フロー（使用するサブフロー）に、このoutputが必要だということを教える。

            # # メインフローで/vizs時、どのdstsを通るかを求める
            # dst_ids = self._pick_necessary_dst_ids(self.flow_data, self.vis_ids)
            # # メインフローで使われるdstsの中に、対象のnode（サブフロー）が出力するものがあれば教えてあげる
            # if len(dst_ids) > 0:
            #     ret.last_ids = [port for port, datum_id in node['dsts'].items() for dst_id in dst_ids if datum_id == dst_id]
        else:
            raise Exception(f'ノード({node.get("id")})のtypeが不正な値({node["type"]})です')

        return ret

    def _get_port_by_label(self, runnable_ports, port_label):
        """
        指定したport_labelをもつportを取得する。
        runnableというクラスがあったらそこにあるべきなのだろうけど
        今はないし、作るの面倒なのでとりあえずここに。
        絶対必要になった時に作ろう。。。
        """
        for runnable_port in runnable_ports:
            if runnable_port.label == port_label:
                return runnable_port
        return None

    def _replace_multi_inputs(self, i_ports, srcs):
        """
        *のportをport群に変換する
        """
        ret = []
        for src_port in i_ports:
            if src_port.label == '*':
                ret.extend([Port(p, 'frame') for p in srcs.keys()])
            else:
                ret.append(src_port)
        return ret

    def _upsert_point(self, flow, point_id, is_in, is_out, src_tube, dst_tube):
        """
        指定したpoint_idのpointを作成する
        対象のpointがすでに存在していればそのpointを更新する
        """
        point_ids = [point.id for point in flow.points]
        if point_id in point_ids:
            point = flow.select_point_by_id(point_id)
            # 既存のpointを更新する
            src_tube.is_null or point.add_src_tube(src_tube)
            dst_tube.is_null or point.add_dst_tube(dst_tube)
            point.is_in = is_in
            point.is_out = is_out
        else:
            point = Point(point_id, src_tube, None, dst_tube, is_in, is_out)
            flow.points.append(point)
        return point


    def _is_value_node(self, node):
        """
        valueをもつnodeかどうか
        uuidが入っていたらそっちを優先する
        """
        return node.get('value') is not None and node.get('uuid') is None

    def _is_store_node(self, node):
        """
        指定されたnodeがStoreの場合はTrueを返す
        """
        return node['type'] == 'store'

    def _is_runnable_node(self, node):
        """
        指定されたnodeがrunnableかどうかを判断する
        """
        return node['type'] == 'command' or node['type'] == 'flow'

    @property
    def is_datadst(self):
        """
        データデストの場合はTrueを返す
        """
        return self._is_datadst

    @property
    def points(self):
        return self.stepoints.points

    @points.setter
    def points(self, points):
        self.stepoints.points = points

    @property
    def substeps(self):
        return self.stepoints.substeps

    @property
    def lasts(self):
        return {p.id: p.datum for p in self.points if p.is_last}

    @property
    def outs(self):
        return {p.id: p.datum for p in self.points if p.is_out}

    def run(self, args, inputs):
        """
        pointではなくstepを基軸にして書き直し
        """
        return self.stepoints.run(args, inputs)
        
    def select_point_by_id(self, point_id):
        """
        self.pointsの中から
        指定したidのpointを取得する
        """
        for point in self.points:
            if point.id == point_id:
                return point
 
        raise Exception(f'指定されたPoint({point_id})がFlow({self.label})にありませんでした')

    def has_as_in_point(self, node_id):
        for port in self.i_ports:
            if port.label == node_id:
                return True
        return False

    def has_as_out_point(self, node_id):
        for port in self.o_ports:
            if port.label == node_id:
                return True
        return False

    def get_module_list(self):
        """
        substepsのmoduleをextendして返す
        """
        for substep in self.substeps:
            if isinstance(substep.runnable, Flow):
                self.module_store.extend(substep.runnable.get_module_list())

        return self.module_store.module_list

    # def find_activity(self):
    #     """
    #     Activity Stepをメインフローから再帰的に探し出す
    #     """
    #     from kskp.store import Activity
    #     # 自身がActivityを持っている場合
    #     # for activity in self.lasts.values():
    #     for activity in [p.datum for p in self.points]:
    #         if isinstance(activity, Activity):
    #             return activity
    #     # 自身が持っていない場合、サブフローを探しに行く
    #     # (データデストのみを用いている場合)
    #     for substep in self.substeps:
    #         if substep.is_flow :
    #             result = substep.runnable.find_activity()
    #             if result is not None:
    #                 return result
    #     # Activityが見つからなかった場合
    #     return None

    def dtor(self, args):
        # 配下のflowのdtorも動かす
        for substep in self.substeps:
            from kskp.core import Command
            if isinstance(substep.runnable, Flow) or isinstance(substep.runnable, Command):
                substep.dtor()
            else:
                raise Exception('substep.runnableにFlowまたはCommand以外のオブジェクトが格納されています')

