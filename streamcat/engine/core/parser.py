from streamcat.core import Port
from streamcat.store import Flow, FlowData
from streamcat.store.finder import DatumFinder
from .. import FlowCommand
from ..elements import FlowElements, Steps, Point, Points, FlowPort, FlowPorts

class Parser:
    """
    フローJSONを解釈する
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

    def __init__(self, flow_data:FlowData, datum_finder:DatumFinder, is_main:bool=False) -> None:
        self._flow_data = flow_data
        self._datum_finder = datum_finder
        self._is_main = is_main

        from .appenders import FolderDataSourcePrepender
        self._folder_data_source_prepender = FolderDataSourcePrepender(self._datum_finder)

    def parse(self, use_cache:bool):
        # フローJSONからFlowElementsを生成する
        if self._flow_data.has_nodes:
            # フローの参照権限がなくても実行権限があれば、フローJSONを参照する必要がある
            # そのため、use_exec_auth=Trueを指定する
            nodes_json = self._flow_data.get_nodes(use_exec_auth=True)
            # フローJSONからStepとPointを生成する
            flow_elements = self._update_flow_by_runnable(nodes_json, use_cache)
            # フローの入出力Portを作成する
            flow_elements.i_ports = self._parse_flow_ports(self._flow_data.i_ports, flow_elements.points)
            flow_elements.o_ports = self._parse_flow_ports(self._flow_data.o_ports, flow_elements.points)
            # runnable以外のノードを走査する
            # (Portを作成した後に処理する)
            self._update_flow_by_other_than_runnable(nodes_json, flow_elements, use_cache)
            # FlowElementsを返す
            return flow_elements
        else:
            return FlowElements()

    def _parse_flow_ports(self, ports_json:list[dict], points:Points):
        """
        フローJSONのリストからFlowPortのリストを作る
        """
        rets = FlowPorts()
        for port_json in ports_json:
            point = points.get(port_json['nodeId'])
            if point is None:
                raise Exception(f'Port({port_json["label"]})に紐づくPoint({port_json["nodeId"]})がフローに存在しません')
            # サブフローのポートの識別子には'label'を用いる
            new_port = FlowPort(port_json['label'], port_json.get('type') or port_json['types'], point)
            if new_port in rets:
                raise Exception(f'同じlabelのPort({new_port.label})が存在します')
            rets.add(new_port)
        return rets

    def _replace_variadic_port(self, ports:list[Port], targets:dict):
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

    def _replace_variadic_flow_port(self, ports:FlowPorts, targets:dict):
        """
        *のFlowPortを複数のFlowPortに変換する
        """
        for port in ports:
            if port.label == '*':
                raise NotImplementedError('FlowCommandのportに"*"を設定した場合の処理は実装していません')
        # NOTE: FlowCommandのo_portsはStepと共有する必要があるので同じオブジェクトを返すこと
        return ports

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

    def _update_flow_by_runnable(self, nodes_json, use_cache):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        from ..elements import Step, Tube

        steps = Steps()
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

            # 
            # CommandまたはFlowCommandを取得する
            # 
            cmd = self._create_command(node, use_cache)

            if node.type == 'flow':
                # フロー変数がフローコマンドの他の引数と名称が重複しないようにするため
                # 'args'の下にフロー変数を格納する
                # (params:仮引数、args:実引数)
                args = {'flow_args':args, 'use_cache':use_cache}

                # FlowCommandのPortは'*'指定に今のところ対応していない
                # FlowCommandのportsオブジェクトはStepと共有する
                i_ports = self._replace_variadic_flow_port(cmd.i_ports, srcs)
                o_ports = self._replace_variadic_flow_port(cmd.o_ports, srcs)
            else:
                # CommandのPortのlabelに'*'が指定されていれば、可変長Port指定なので
                # Commandノードの入出力Port指定(srcsまたはdsts)からPortを生成する
                i_ports = self._replace_variadic_port(cmd.i_ports, srcs)
                o_ports = self._replace_variadic_port(cmd.o_ports, dsts)

            # runnableのインスタンス化を行う
            step = Step(node.id, cmd, args, o_ports=o_ports, classification=node.get('classification'))
            # Stepを集める
            steps.add(step)

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
        return FlowElements(steps, points)

    def _update_flow_by_other_than_runnable(self, nodes_json, flow_elements:FlowElements, use_cache:bool):
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

            target_point = flow_elements.points.get(node.id)
            if target_point is None:
                continue

            # target_point.makeCache = node.get('makeCache')
            # target_point.label = node.get('label')

            # Storeの場合、StoreオブジェクトをPointに格納する
            if node.is_store:
                store_uuid = node.get('uuid')
                store = self._datum_finder.find_by_uuid(store_uuid)

                # StoreにDatabaseを設定する
                target_point.datum = store
                continue

            # 入出力Point以外の場合、そのPointに紐づくDatumオブジェクトを格納する
            # ただし、メインフローの場合は入出力Pointか否かを条件にしない
            if self._is_main or not (flow_elements.i_ports.exists_by_point(target_point) or flow_elements.o_ports.exists_by_point(target_point)):
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
                        self._folder_data_source_prepender.do_prepend(flow_elements.points, flow_elements.steps, target_point, node.get('uuid'))
                    except Exception as e:
                        if node.has_cache:
                            # キャッシュの参照ができなくてもフローの実行は中断しない
                            import warnings
                            warnings.warn(str(e) + '、キャッシュを参照できませんでした')
                        else:
                            raise e

                    # キャッシュが既にあるpointをTrueにしてもしょうがないのでFalseにする
                    target_point.makeCache = False

    def _create_command(self, node:Node, use_cache:bool):
        from streamcat.store.auth import NotAuthorizedException
        from streamcat.depo.std.commands import CommandLink

        if node.type == 'command':
            return CommandLink(node['commandId']).resolve()
        elif node.type == 'flow':
            flow_json = node.get('flow')
            flow_uuid = node.get('uuid')
            if flow_json is not None:
                # リテラル定義されたフローを取得する
                sub_flow = Flow(self._datum_finder._session, None, node.get('label'), FlowData(flow_json))
            elif flow_uuid is not None:
                try:
                    # サブフローをDBから取得する
                    sub_flow = self._datum_finder.find_by_uuid(flow_uuid)
                except NotAuthorizedException:
                    raise NotAuthorizedException(f'共有フロー({node})の参照権限がありません')
            else:
                raise Exception(f'共有フロー({node})のUUIDまたはリテラルが指定されていません')
            # サブフローのFlowCommandを生成する
            flow_cmd = FlowCommand(sub_flow, is_main=False)
            # サブフローのフローJSONを解釈する
            flow_cmd.parse(use_cache)
            return flow_cmd
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
