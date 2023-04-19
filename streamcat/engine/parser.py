from streamcat.core import Port
from streamcat.store import Flow, FlowData
from streamcat.store.factory import DatumFactory
from .flow_command import FlowCommand
from .saver_activator import SaverActivator
from .stepoints import Stepoints
from .step import Steps
from .point import Point, Points
from .flow_port import FlowPort

class Parser:

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
                return self._node_json.get('commandId', self.id)
            else:
                return self._node_json.get('label', self.id)

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
        def is_frame(self):
            """
            指定されたnodeがFrameの場合はTrueを返す
            """
            return self.type == 'frame'

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

        @property
        def has_cache(self):
            """
            CacheをもつFrameの場合はTrueを返す
            """
            return self.get('cacheCreatedAt') is not None and self.get('uuid') is not None

    def __init__(self, flow_cmd:FlowCommand, flow_data:FlowData, datum_factory:DatumFactory, saver_activator:SaverActivator, is_main:bool=False) -> None:
        self._flow_cmd = flow_cmd
        self._flow_data = flow_data
        self._datum_factory = datum_factory
        self._saver_activator = saver_activator
        self.is_main = is_main

        from .appenders import FolderDataSourcePrepender
        self._folder_data_source_prepender = FolderDataSourcePrepender(self._datum_factory)

    def parse(self, vis_args, use_cache:bool, src_point:Point=None):
        # フローJSONからStepointを生成する
        if self._flow_data.has_nodes:
            # フローの参照権限がなくても実行権限があれば、フローJSONを参照する必要がある
            # そのため、use_exec_auth=Trueを指定する
            nodes_json = self._flow_data.get_nodes(use_exec_auth=True)
            # フローJSONからStepとPointを生成する
            stepoints = self._update_flow_by_runnable(nodes_json, vis_args, use_cache, src_point)
            # フローの入出力Portを作成する
            # (Stepoints.run()でPortが必要になる)
            stepoints.i_ports = self._parse_flow_ports(self._flow_data.i_ports, stepoints.points)
            stepoints.o_ports = self._parse_flow_ports(self._flow_data.o_ports, stepoints.points)
            # runnable以外のノードを走査する
            # (Portを作成した後に処理する)
            self._update_flow_by_other_than_runnable(nodes_json, stepoints, use_cache)
            # Stepointsを返す
            return stepoints
        else:
            return Stepoints(steps=Steps(), points=Points(), i_ports=[], o_ports=[])

    def _parse_flow_ports(self, ports_json, points:Points):
        """
        フローJSONからのリストからFlowPortのリストを作る
        """
        rets = []
        for port_json in ports_json:
            point = points.get(port_json['nodeId'])
            if point is None:
                raise Exception(f'Port({port_json["label"]})に紐づくPoint({port_json["nodeId"]})がフロー({self})に存在しません')
            # サブフローのポートの識別子には'label'を用いる
            new_port = FlowPort(port_json['label'], port_json.get('type') or port_json['types'], point)
            if new_port in rets:
                raise Exception(f'同じlabelのPort({new_port.label})が存在します')
            rets.append(new_port)
        return rets

    def _replace_variadic_port(self, ports, targets:dict):
        """
        *のPortを複数のPortに変換する
        """
        ret = []
        for port in ports:
            if port.label == '*':
                ret.extend([Port(p, port.types) for p in targets.keys()])
            else:
                ret.append(port)
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

    def _update_flow_by_runnable(self, nodes_json, vis_args, use_cache, src_point):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        from .step import Step
        from .tube import Tube

        substeps = Steps()
        points = Points()

        # Commandに繋がらない孤立したデータノードからもPointを生成する為
        # ここで全てのデータノードからPointを生成する
        for node_json in nodes_json:
            node = Parser.Node(node_json)
            if node.is_frame or node.is_store:
                p = Point(node.id, makeCache=node.get('makeCache'))
                p.label = node.get('label')
                points.add(p)

        # まず、runnableを集める
        for node_json in nodes_json:
            node = Parser.Node(node_json)

            if not node.is_runnable:
                continue

            # MCommandに不要な引数を設定するとエラーになる
            args = node.get('args') or {}
            srcs = node.get('srcs') or {}
            dsts = node.get('dsts') or {}

            # NOTE: SaverCommandの入力Pointのidを取得する為だけに残しているが、
            # Proprocessor._get_src_point_of_data_dst()にその機能を統合してもいいかも
            if len(srcs)==1 and len(dsts)==0:
                # データデストまたはSaverCommandには入力Pointのidを渡す
                src_point_id = next(iter(srcs.values()))
                node_src_point = points.get(src_point_id)
            else:
                # 中継する
                node_src_point = src_point

            # 
            # CommandまたはFlowCommandを取得する
            # 
            cmd = self._create_command(node, vis_args, use_cache, node_src_point)

            # フロー変数がフローコマンドの他の引数と名称が重複しないようにするため
            # 'args'の下にフロー変数を格納する
            # (params:仮引数、args:実引数)
            if node.type == 'flow':
                args = {'flow_args':args, 'use_cache':use_cache}

            # CommandoのPortのlabelに'*'が指定されていれば、可変長Port指定なので
            # Commandノードの入出力Port指定(srcsまたはdsts)からPortを生成する
            i_ports = self._replace_variadic_port(cmd.i_ports, srcs)
            o_ports = self._replace_variadic_port(cmd.o_ports, dsts)

            # runnableのインスタンス化を行う
            step = Step(node.id, cmd, args, o_ports=o_ports, classification=node.get('classification'))
            # Stepを集める
            substeps.add(step)

            # srcとdstからpointを作る
            for s_port_label, s_node_id in srcs.items():
                # 可変長Portで入力PointがNoneになる場合に備える
                if s_node_id is None:
                    raise Exception(f'コマンド({node})の入力({s_port_label})が指定されていません')

                # 定義上に存在しないポート名がsrcsに存在していないかの確認
                src_port = self._get_port_by_label(i_ports, s_port_label)
                if src_port is None:
                    raise Exception(f'指定しているport名({s_port_label})が"{node}"の定義しているポート群({i_ports})に存在しません')

                # pointを作成する（作成対象がすでにあれば更新する）
                self._connect_with_tube(points, id=s_node_id, dst_tube=Tube(src_port, step))

            for d_port_label, d_node_id in dsts.items():
                if d_node_id is None:
                    raise Exception(f'コマンド({node})の出力({d_port_label})が指定されていません')

                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self._get_port_by_label(step.command.o_ports, d_port_label)
                if dst_port is None:
                    raise Exception(f'指定しているport名({d_port_label})が"{node}"の定義しているポート群({step.command.o_ports})に存在しません')

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self._connect_with_tube(points, id=d_node_id, src_tube=Tube(dst_port, step))

                from streamcat.depo.std.commands import AssertCommand
                if isinstance(cmd, AssertCommand):
                    # 出力情報に、AssertCommandの出力ポイントのidを含めるため
                    args['asserted_point'] = dst_point.id
                    # AssertCommandで例外を検証対象とするため、例外の入力を許可する
                    step.ex_acceptable = True

        # 作成したStep及びPointのリストを返す
        return Stepoints(substeps, points, i_ports=[], o_ports=[])

    def _update_flow_by_other_than_runnable(self, nodes_json, stepoints:Stepoints, use_cache:bool):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        # 実行に関係ないnodeのtype群
        EXCEPT_TYPES = ['note']

        for node_json in nodes_json:
            node = Parser.Node(node_json)

            # pointにdatumを入れていく
            if node.is_runnable or node.type in EXCEPT_TYPES:
                continue

            target_point = stepoints.points.get(node.id)
            if target_point is None:
                continue

            # target_point.makeCache = node.get('makeCache')
            # target_point.label = node.get('label')

            # Storeの場合、StoreオブジェクトをPointに格納する
            if node.is_store:
                store_uuid = node.get('uuid')
                store = self._datum_factory.find_by_uuid(store_uuid)

                # StoreにDatabaseを設定する
                target_point.datum = store
                continue

            # 入出力Point以外の場合、そのPointに紐づくDatumオブジェクト格納する
            # ただし、メインフローの場合は入出力Pointか否かを条件にしない
            if self.is_main or not (self.is_i_port(stepoints.i_ports, target_point) or self.is_o_port(stepoints.o_ports, target_point)):
                if node.has_value:
                    # nodeのvalue属性はテストコードで用いている
                    if isinstance(node['value'], list):
                        from streamcat.store import Matrix
                        target_point.datum = Matrix(node['value'])
                    else:
                        target_point.datum = node['value']
                elif node.get('uuid') is not None:
                    # キャッシュを参照しない場合、キャッシュをLoaderで取得しない
                    if not use_cache and node.has_cache:
                        continue
                    # uuidが既に振られている場合は、Loaderから取ってくるようにする
                    try:
                        self._folder_data_source_prepender.do_prepend(stepoints.points, stepoints.substeps, target_point, node.get('uuid'))
                    except Exception as e:
                        if node.has_cache:
                            # キャッシュの参照ができなくてもフローの実行は中断しない
                            import warnings
                            warnings.warn(str(e) + '、キャッシュを参照できませんでした')
                        else:
                            raise e

                    # キャッシュが既にあるpointをTrueにしてもしょうがないのでFalseにする
                    target_point.makeCache = False

    def _create_command(self, node, vis_args, use_cache, src_point):
        from streamcat.store.auth import NotAuthorizedException
        from streamcat.depo.std.commands import CommandLink

        if node.type == 'command':
            return CommandLink(node['commandId']).resolve()
        elif node.type == 'flow':
            flow_json = node.get('flow')
            flow_uuid = node.get('uuid')
            if flow_json is not None:
                # リテラル定義されたフローを取得する
                sub_flow = Flow(self._datum_factory._session, None, node.get('label'), FlowData(flow_json))
            elif flow_uuid is not None:
                try:
                    # サブフローをDBから取得する
                    sub_flow = self._datum_factory.find_by_uuid(flow_uuid)
                except NotAuthorizedException:
                    raise NotAuthorizedException(f'共有フロー({node})の参照権限がありません')
            else:
                raise Exception(f'共有フロー({node})のUUIDまたはリテラルが指定されていません')
            # サブフローのFlowCommandを生成する
            flow_cmd = FlowCommand(sub_flow, is_main=False, saver_activator=self._saver_activator)
            # サブフローのフローJSONからStepointを生成する
            flow_cmd._stepoints = flow_cmd.parse(vis_args, use_cache, src_point)
            # サブフローを前処理する
            return self._saver_activator.traverse(flow_cmd=flow_cmd, src_point=src_point)
        else:
            raise Exception(f'ノード({node.id})のtypeが不正な値({node.type})です')

    def _connect_with_tube(self, points, id, src_tube=None, dst_tube=None):
        """
        PointにTubeを接続する
        """
        point = points.get(id)
        if point is None:
            # 指定したidのPointが無ければ、新たにPointを生成する
            point = Point(id, src_tube, None, dst_tube)
            points.add(point)
        else:
            # 既存のpointを更新する
            src_tube is None or point.add_src_tube(src_tube)
            dst_tube is None or point.add_dst_tube(dst_tube)
        return point

    def is_i_port(self, i_ports:list[FlowPort], point:Point):
        return any(p.point==point for p in i_ports)

    def is_o_port(self, o_ports:list[FlowPort], point:Point):
        return any(p.point==point for p in o_ports)
