from kskp.core import Port
from kskp.store import FlowData        
from .stepoints import Stepoints
from .point import Point, Points

class FlowCommand(FlowData):
    """
    実行可能フロー
    """

    class Node():
        """
        ノード
        """
        def __init__(self, node_json):
            self.id = node_json['id']
            self.type = node_json['type']
            self._node_json = node_json

        def __repr__(self):
            if self.type == 'command':
                return self._node_json.get('commandId')
            else:
                return self._node_json.get('label')

        def __getitem__(self, key:str):
            value = self._node_json.get(key)
            if value is None:
                raise Exception(f'Node({self.id})に"{key}"は存在しません')
            else:
                return value

        def get(self, key:str):
            return self._node_json.get(key)

        @property
        def is_store(self):
            """
            指定されたnodeがStoreの場合はTrueを返す
            """
            return self.type == 'store'

        @property
        def is_runnable(self):
            """
            指定されたnodeがrunnableかどうかを判断する
            """
            return self.type == 'command' or self.type == 'flow'

        @property
        def has_value(self):
            """
            valueをもつnodeかどうか
            uuidが入っていたらそっちを優先する
            """
            return self.get('value') is not None and self.get('uuid') is None

    def __init__(self, flow_datum, vis_args={}, is_root=True, preprocessor=None):
        # 実行前にフローJSONの書式の検証をする
        flow_datum.flow_data.valid_flow_json_or_raise()

        # to_json()によりflow_jsonはコピーされる
        super().__init__(flow_datum.flow_data.to_json())

        self._vis_args = vis_args

        # メインフローであればTrue
        self.is_root = is_root

        # FlowJsonLinkが中継した出力Portのリストを保持する
        self.relayed_o_ports = []

        # Portを設定する
        self.i_ports = self._parse_ports(self.ports[0])
        self.o_ports = self._parse_ports(self.ports[1])
        
        # TODO: 用途不明
        from kskp.store import ModuleStore
        self.module_store = ModuleStore()

        # 
        self.context = {}

        # データソースを追加する
        from kskp.store.factory import DatumFactory
        from .appenders import FolderDataSourcePrepender
        self._datum_factory = DatumFactory(flow_datum._session)
        self._folder_data_source_prepender = FolderDataSourcePrepender(self._datum_factory)

        # Activity期間中は同じPreprocessorインスタンスを使う
        from .preprocessor import Preprocessor
        self._preprocessor = preprocessor or Preprocessor(flow_datum, self._datum_factory)

        # 
        # データデストか否かの判定をする
        # 
        # データデストのself.o_portsには、データデストの出力を親フローに繋げる為に
        # フローの前処理でPortを追加するので、Flowオブジェクトの生成時に判定する
        self._is_datadst = len(self.i_ports) == 1 and len(self.o_ports) == 0

    def run(self, args, inputs):
        """
        フローを実行する
        """
        # 実行前に全てのサブフローに対して縦型探索して、フローJSONの解釈とフローの前処理を全て終わらせておく
        if self.is_root:
            # フローJSONを解釈する
            self._parse_nodes(self._vis_args)
            # フローを前処理する
            self._preprocessor.execute(flow_command=self, vis_args=self._vis_args)

        # フローを実行する
        # 実行において、再び縦型探索される
        return self._stepoints.run(args, inputs)

    def _parse_nodes(self, vis_args):
        # フローJSONからStepointを生成する
        if self.has_nodes:
            nodes_json = self.get_nodes(use_exec_auth=True)
            # フローの参照権限がなくても実行権限があれば、フローJSONを参照する必要がある
            # そのため、use_exec_auth=Trueを指定する
            self._stepoints = self._update_flow_by_runnable(nodes_json, vis_args)
            # runnable以外のノードを走査する
            self._update_flow_by_other_than_runnable(nodes_json)
        else:
            self._stepoints = Stepoints(steps=[], points=Points(), o_ports=self.o_ports, is_root=self.is_root)

    def _parse_ports(self, port_dict_list):
        """
        dictのリストからportインスタンスのリストを作る
        """
        # TODO: 'nodeId'はサブフロー内でのノードIdなので、ポートの識別子には'label'を使うべきか？
        # Commandではポートの識別に'label'を用いているので、Flowも合わせるべきでは？
        return [Port(p['nodeId'], p['type']) for p in port_dict_list]

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

    def _update_flow_by_runnable(self, nodes_json, vis_args):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        from .stepoints import Stepoints
        from .point import Points
        from .step import Step
        from .tube import Tube

        substeps = []
        points = Points()

        # まず、runnableを集める
        for node_json in nodes_json:
            node = FlowCommand.Node(node_json)
            if not node.is_runnable:
                continue

            # CommandまたはFlowを取得する
            cmd = self._create_command(node, vis_args)
            
            # MCommandに不要な引数を設定するとエラーになる
            args = node['args']
            srcs = node['srcs']
            dsts = node['dsts']

            i_ports = self._replace_multi_inputs(cmd.i_ports, srcs)
            o_ports = self._replace_multi_inputs(cmd.o_ports, dsts)

            # runnableのインスタンス化を行う
            step = Step(node.id, cmd, args, i_ports=i_ports, o_ports=o_ports)
            # Stepを集める
            substeps.append(step)

            # srcとdstからpointを作る
            for s_port_label, s_node_id in srcs.items():
                # 可変長引数で入力PointがNoneになる場合に備える
                if s_node_id is None:
                    raise Exception(f'コマンド({node})の入力({s_port_label})が指定されていません')

                # 定義上に存在しないポート名がsrcsに存在していないかの確認
                src_port = self._get_port_by_label(i_ports, s_port_label)
                if src_port is None:
                    raise Exception(f'指定しているport名({s_port_label})が"{node}"の定義しているポート群({i_ports})に存在しません')

                # out/inポートフラグの取得
                is_in = self.has_as_in_point(s_node_id)
                is_out = self.has_as_out_point(s_node_id)

                # pointを作成する（作成対象がすでにあれば更新する）
                src_point = self._upsert_point(points, id=s_node_id, dst_tube=Tube(src_port, step), is_in=is_in, is_out=is_out)

                # 上記src_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにoriginを置き換える
                [src_point.src_tubes.add(Tube(i_port, None)) for i_port in self.i_ports if i_port.label == src_point.id]

            for d_port_label, d_node_id in dsts.items():
                if d_node_id is None:
                    raise Exception(f'コマンド({node})の出力({d_port_label})が指定されていません')

                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self._get_port_by_label(step.runnable.o_ports, d_port_label)
                if dst_port is None:
                    raise Exception(f'指定しているport名({d_port_label})が"{node}"の定義しているポート群({step.runnable.o_ports})に存在しません')

                # out/inポートフラグの取得
                is_in = self.has_as_in_point(d_node_id) 
                is_out = self.has_as_out_point(d_node_id)

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self._upsert_point(points, id=d_node_id, src_tube=Tube(dst_port, step), is_in=is_in, is_out=is_out)

                # 上記dst_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにdst_tubesを置き換える
                # (メインフローの場合は繋げる必要がない、かつ次のStepへ繋げる為にdst_tubes変数が必要なので、何もしない)
                if not self.is_root:
                    [dst_point.dst_tubes.add(Tube(o_port, None)) for o_port in self.o_ports if o_port.label == dst_point.id]

                from kskp.depo.std.commands import AssertCommand
                if isinstance(cmd, AssertCommand):
                    # 出力情報に、AssertCommandの出力ポイントのidを含めるため
                    args['asserted_point'] = dst_point.id
                    # AssertCommandで例外を検証対象とするため、例外の入力を許可する
                    step.ex_acceptable = True

        # 作成したStep及びPointのリストを返す
        return Stepoints(substeps, points, o_ports=self.o_ports, is_root=self.is_root)

    def _update_flow_by_other_than_runnable(self, nodes_json):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        # 実行に関係ないnodeのtype群
        EXCEPT_TYPES = ['note']

        for node_json in nodes_json:
            node = FlowCommand.Node(node_json)

            # pointにdatumを入れていく
            if node.is_runnable or node.type in EXCEPT_TYPES:
                continue

            target_point = self.points.get(node.id)
            if target_point is None:
                continue

            target_point.cache = node.get('makeCache')
            target_point.label = node.get('label')

            # Storeの場合、StoreオブジェクトをPointに格納する
            if node.is_store:
                store_uuid = node.get('uuid')
                store = self._datum_factory.find_by_uuid(store_uuid)

                # StoreにDatabaseを設定する
                target_point.datum = store
                continue

            # 入力Point以外の場合、そのPointに紐づくDatumオブジェクト格納する
            # ただし、メインフローの場合は入力Pointか否かを条件にしない
            if self.is_root or not target_point.is_in:
                if node.has_value:
                    # nodeのvalue属性はテストコードで用いている
                    if isinstance(node['value'], list):
                        from kskp.store import List
                        target_point.datum = List(node['value'])
                    else:
                        target_point.datum = node['value']
                elif node.get('uuid') is not None:
                    # uuidが既に振られている場合は、loaderから取ってくるようにする
                    # self._put_loader(node.get('uuid'), target_point, self, Folder)
                    self._folder_data_source_prepender.do_prepend(self, target_point, node.get('uuid'))
                    # キャッシュが既にあるpointをTrueにしてもしょうがないのでFalseにする
                    target_point.cache = False

    def _create_command(self, node, vis_args):
        from kskp.store.auth import NotAuthorizedException
        from kskp.depo.std.commands import CommandLink

        if node.type == 'command':
            return CommandLink(node['commandId']).resolve()
        elif node.type == 'flow':
            try:
                # サブフローをDBから取得する
                sub_flow_datum = self._datum_factory.find_by_uuid(node['uuid'])
            except NotAuthorizedException:
                raise NotAuthorizedException(f'共有フロー({node})の参照権限がありません')
            # サブフローのFlowCommandを生成する
            flow_cmd = FlowCommand(sub_flow_datum, is_root=False, preprocessor=self._preprocessor)
            # サブフローのフローJSONからStepointを生成する
            flow_cmd._parse_nodes(vis_args)
            # フローを前処理する
            return self._preprocessor.execute(flow_command=flow_cmd, vis_args=vis_args)
        else:
            raise Exception(f'ノード({node.id})のtypeが不正な値({node.type})です')

    def _upsert_point(self, points, id, src_tube=None, dst_tube=None, is_in=False, is_out=False):
        """
        指定したpoint_idのpointを作成する
        既に同じpoint_idが存在していればそのpointを更新する
        """
        point = points.get(id)
        if point is None:
            point = Point(id, src_tube, None, dst_tube, is_in, is_out)
            points.add(point)
        else:
            # 既存のpointを更新する
            src_tube is None or point.src_tubes.add(src_tube)
            dst_tube is None or point.dst_tubes.add(dst_tube)
            point.is_in = is_in
            point.is_out = is_out 
        return point

    @property
    def points(self):
        return self._stepoints.points

    @points.setter
    def points(self, points:Points):
        self._stepoints.points = points

    @property
    def substeps(self):
        return self._stepoints.substeps

    @property
    def lasts(self):
        return {p.id: p.datum for p in self.points if p.is_last}

    @property
    def outs(self):
        return {p.id: p.datum for p in self.points if p.is_out}

    @property
    def is_datadst(self):
        """
        データデストの場合はTrueを返す
        """
        return self._is_datadst

    def open_o_port(self, o_port, point):
        """
        指定するPointを出力Pointに設定する
        """
        if o_port in self.o_ports:
            raise Exception(f'指定されたPort({o_port})と同じlabelのPortがFlow({self.label})にあります')
        if point not in self.points:
            raise Exception(f'指定されたPoint({point.id})がFlow({self.label})にありませんでした')

        # is_outは単なるフラグなのでTrueに設定する
        point.is_out = True
        from .tube import Tube
        point.dst_tubes.add(Tube(o_port, None))
        self.o_ports.append(o_port)

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

    def dtor(self, args):
        # 配下のflowのdtorも動かす
        for substep in self.substeps:
            from kskp.core import Command
            if isinstance(substep.runnable, FlowCommand) or isinstance(substep.runnable, Command):
                substep.dtor()
            else:
                raise Exception('substep.runnableにFlowまたはCommand以外のオブジェクトが格納されています')
