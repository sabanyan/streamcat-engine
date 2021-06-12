from kskp.core import Command, Port
from kskp.store import Flow, FlowData
from .stepoints import Stepoints
from .point import Point, Points
from .flow_port import FlowPort
from .ports import Ports

class FlowCommand(Command):
    """
    フローコマンド
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

    def __init__(self, flow:Flow, lock_uuid:str=None, is_main:bool=True, preprocessor=None):
        super().__init__()

        # 実行前にフローJSONの書式の検証をする
        flow.flow_data.valid_flow_json_or_raise()

        # フローJSONをコピーする
        # (TODO: なぜコピーする必要があるのか忘れてしまった)
        self._flow_data = flow.flow_data.copy()

        # 仮引数を保持する
        self.params = self._flow_data.params or {}

        # メインフローであればTrue
        self.is_main = is_main

        # FlowJsonLinkが中継した出力Portのリストを保持する
        # (Port.labelの重複をさせないためPortsを用いる)
        self.relayed_o_ports = Ports()

        # TODO: 用途不明
        from kskp.store import ModuleStore
        self.module_store = ModuleStore()

        # 
        # self.context = {}

        # Steps, Points, i_ports, o_portsを保持する
        self._stepoints = None

        # データソースを追加する
        from kskp.store.factory import DatumFactory
        from .appenders import FolderDataSourcePrepender
        self._datum_factory = DatumFactory(flow._session)
        self._folder_data_source_prepender = FolderDataSourcePrepender(self._datum_factory)

        # Activity期間中は同じPreprocessorインスタンスを使う
        from .preprocessor import Preprocessor
        self._preprocessor = preprocessor or Preprocessor(flow, self._datum_factory, lock_uuid)

        # 
        # データデストか否かの判定をする
        # 
        # データデストのself.o_portsには、データデストの出力を親フローに繋げる為に
        # フローの前処理でPortを追加するので、Flowオブジェクトの生成時に判定する
        # self._is_datadst = len(self.i_ports) == 1 and len(self.o_ports) == 0

    def run(self, args={}, inputs={}):
        """
        フローを実行する
        """
        # 実行前に全てのサブフローに対して縦型探索して、フローJSONの解釈とフローの前処理を全て終わらせておく
        if self.is_main:
            # プレビュー引数を取得する
            vis_args = args.get('vis') or {}
            # キャッシュ参照・保存引数を取得する
            use_cache = args.get('use_cache')
            # TODO: 指定がない場合は暫定的にuse_cache=Trueにする
            if use_cache is None:
                use_cache = True
            # フローJSONを解釈する
            self._parse_nodes(vis_args, use_cache)
            # フローを前処理する
            self._preprocessor.execute(flow_cmd=self, vis_args=vis_args, use_cache=use_cache)

        # フローが定義する仮引数とこれに対応する値をDictで用意する
        flow_args = self._make_complete_flow_args(args)

        # フローを実行する
        # 実行において、再び縦型探索される
        return self._stepoints.run(flow_args, inputs)

    def _make_complete_flow_args(self, args:dict) -> dict:
        """
        フローが定義する仮引数にフロー変数の値(実引数)を設定する
        仮引数に対応するフロー変数の値が無い場合は空文字を設定する
        (params:仮引数、args:実引数)
        """
        # フロー変数の値を取得する
        flow_args = args.get('flow_args') or {}

        # フローが定義する仮引数に対応する値を設定する
        complete_flow_args = {}
        for param in self.params:
            param_name = param['name']
            complete_flow_args[param_name] = flow_args.get(param_name, '')

        return complete_flow_args

    def _parse_nodes(self, vis_args, use_cache:bool, src_point:Point=None):
        # フローJSONからStepointを生成する
        if self._flow_data.has_nodes:
            # フローの参照権限がなくても実行権限があれば、フローJSONを参照する必要がある
            # そのため、use_exec_auth=Trueを指定する
            nodes_json = self._flow_data.get_nodes(use_exec_auth=True)
            # フローJSONからStepとPointを生成する
            self._stepoints = self._update_flow_by_runnable(nodes_json, vis_args, use_cache, src_point)
            # フローの入出力Portを作成する
            # (Stepoints.run()でPortが必要になる)
            self._stepoints.i_ports = self._parse_flow_ports(self._flow_data.i_ports)
            self._stepoints.o_ports = self._parse_flow_ports(self._flow_data.o_ports)
            # runnable以外のノードを走査する
            # (Portを作成した後に処理する)
            self._update_flow_by_other_than_runnable(nodes_json, use_cache)
        else:
            self._stepoints = Stepoints(steps=[], points=Points(), i_ports=self.i_ports, o_ports=self.o_ports, is_main=self.is_main)

    def _parse_flow_ports(self, ports_json):
        """
        フローJSONからのリストからFlowPortのリストを作る
        """
        rets = []
        for port_json in ports_json:
            point = self.points.get(port_json['nodeId'])
            if point is None:
                raise Exception(f'Port({port_json["label"]})に紐づくPoint({port_json["nodeId"]})がフロー({self})に存在しません')
            # TODO: 'nodeId'はサブフロー内でのノードIdなので、ポートの識別子には'label'を使うべきか？
            # Commandではポートの識別に'label'を用いているので、Flowも合わせるべきでは？
            new_port = FlowPort(port_json['nodeId'], port_json['type'], point)
            if new_port in rets:
                raise Exception(f'同じlabelのPort({new_port.label})が存在します')
            rets.append(new_port)
        return rets

    def _replace_variadic_port(self, i_ports, srcs):
        """
        *のPortを複数のPortに変換する
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

    def _update_flow_by_runnable(self, nodes_json, vis_args, use_cache, src_point):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        from .stepoints import Stepoints
        from .point import Points
        from .step import Step
        from .tube import Tube

        substeps = []
        points = Points()

        # Commandに繋がらない孤立したデータノードからもPointを生成する為
        # ここで全てのデータノードからPointを生成する
        for node_json in nodes_json:
            node = FlowCommand.Node(node_json)
            if node.is_frame or node.is_store:
                p = Point(node.id, makeCache=node.get('makeCache'))
                p.label = node.get('label')
                points.add(p)

        # まず、runnableを集める
        for node_json in nodes_json:
            node = FlowCommand.Node(node_json)

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
            # Commandノードの入出力ポート指定(srcsまたはdsts)からPortを生成する
            i_ports = self._replace_variadic_port(cmd.i_ports, srcs)
            o_ports = self._replace_variadic_port(cmd.o_ports, dsts)

            # runnableのインスタンス化を行う
            step = Step(node.id, cmd, args, o_ports=o_ports, classification=node.get('classification'))
            # Stepを集める
            substeps.append(step)

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
                self._upsert_point(points, id=s_node_id, dst_tube=Tube(src_port, step))

            for d_port_label, d_node_id in dsts.items():
                if d_node_id is None:
                    raise Exception(f'コマンド({node})の出力({d_port_label})が指定されていません')

                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self._get_port_by_label(step.command.o_ports, d_port_label)
                if dst_port is None:
                    raise Exception(f'指定しているport名({d_port_label})が"{node}"の定義しているポート群({step.command.o_ports})に存在しません')

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self._upsert_point(points, id=d_node_id, src_tube=Tube(dst_port, step))

                from kskp.depo.std.commands import AssertCommand
                if isinstance(cmd, AssertCommand):
                    # 出力情報に、AssertCommandの出力ポイントのidを含めるため
                    args['asserted_point'] = dst_point.id
                    # AssertCommandで例外を検証対象とするため、例外の入力を許可する
                    step.ex_acceptable = True

        # 作成したStep及びPointのリストを返す
        return Stepoints(substeps, points, i_ports=[], o_ports=[], is_main=self.is_main)

    def _update_flow_by_other_than_runnable(self, nodes_json, use_cache:bool):
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
            if self.is_main or not (self.is_i_port(target_point) or self.is_o_port(target_point)):
                if node.has_value:
                    # nodeのvalue属性はテストコードで用いている
                    if isinstance(node['value'], list):
                        from kskp.store import List
                        target_point.datum = List(node['value'])
                    else:
                        target_point.datum = node['value']
                elif node.get('uuid') is not None:
                    # キャッシュを参照しない場合、キャッシュをLoaderで取得しない
                    if not use_cache and node.has_cache:
                        continue
                    # uuidが既に振られている場合は、Loaderから取ってくるようにする
                    try:
                        self._folder_data_source_prepender.do_prepend(self, target_point, node.get('uuid'))
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
        from kskp.store.auth import NotAuthorizedException
        from kskp.depo.std.commands import CommandLink

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
            flow_cmd = FlowCommand(sub_flow, is_main=False, preprocessor=self._preprocessor)
            # サブフローのフローJSONからStepointを生成する
            flow_cmd._parse_nodes(vis_args, use_cache, src_point)
            # サブフローを前処理する
            return self._preprocessor.execute(flow_cmd=flow_cmd, vis_args=vis_args, src_point=src_point)
        else:
            raise Exception(f'ノード({node.id})のtypeが不正な値({node.type})です')

    def _upsert_point(self, points, id, src_tube=None, dst_tube=None):
        """
        指定したpoint_idのpointを作成する
        既に同じpoint_idが存在していればそのpointを更新する
        """
        point = points.get(id)
        if point is None:
            point = Point(id, src_tube, None, dst_tube)
            points.add(point)
        else:
            # 既存のpointを更新する
            src_tube is None or point.src_tubes.add(src_tube)
            dst_tube is None or point.dst_tubes.add(dst_tube)
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
    def i_ports(self):
        if self._stepoints is None:
            return []
        else:
            return self._stepoints.i_ports

    @i_ports.setter
    def i_ports(self, value):
        pass

    @property
    def o_ports(self):
        if self._stepoints is None:
            return []
        else:
            return self._stepoints.o_ports

    @o_ports.setter
    def o_ports(self, value):
        pass

    @property
    def lasts(self):
        return {p.id: p.datum for p in self.points if p.is_last}

    @lasts.setter
    def lasts(self, value):
        pass

    @property
    def outs(self):
        return {p.point.id: p.point.datum for p in self.o_ports}

    def is_i_port(self, point:Point):
        return any(p.point==point for p in self.i_ports)

    def is_o_port(self, point:Point):
        return any(p.point==point for p in self.o_ports)

    def has_o_port(self, port_label):
        return any(p.label==port_label for p in self.o_ports)

    def open_o_port(self, new_o_port:FlowPort):
        """
        指定するPointを出力Pointに設定する
        """
        point = new_o_port.point

        if new_o_port in self.o_ports:
            raise Exception(f'指定されたPort({new_o_port})と同じlabelのPortがFlow({self})にあります')
        if point not in self.points:
            raise Exception(f'指定されたPoint({point.id})がFlow({self})にありませんでした')

        self.o_ports.append(new_o_port)

    def close_o_port_by_point(self, point):
        for port in self.o_ports:
            if port.point == point:
                self.o_ports.remove(port)
                return
        return Exception(f'指定されたPoint({port})はFlow({self})の出力Pointではありません')

    def close_all_o_ports(self):
        self.o_ports.clear()

    def dtor(self, args={}):
        """
        終了処理
        - self.substepsの各Stepは
          Stepoints._run_invokable_steps()においてdtor()される
        """
        # TmpファイルはNYSOL-Pythonコマンドの入力に使用するので
        # Nysol-Python(Runsコマンド)の実行が終了した後に削除する
        if self.is_main:
            from kskp.core import Tmp
            Tmp.remove_files()
