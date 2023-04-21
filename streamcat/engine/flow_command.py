from streamcat.core import Command
from streamcat.store import Flow
from .point import Point, Points
from .flow_port import FlowPort, FlowPorts

class FlowCommand(Command):
    """
    フローJSONを実行するコマンド
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

    def __init__(self, flow:Flow, lock_uuid:str=None, is_main:bool=True):
        super().__init__(flow.label)

        self._flow = flow
        self._lock_uuid = lock_uuid
        # メインフローであればTrue
        self._is_main = is_main

        # 実行前にフローJSONの書式の検証をする
        flow.flow_data.valid_flow_json_or_raise()

        # フローJSONをコピーする
        # (TODO: なぜコピーする必要があるのか忘れてしまった)
        self._flow_data = flow.flow_data.copy()

        # 仮引数を保持する
        self.params = self._flow_data.params or {}

        # SaverActivatorが中継した出力Portのリストを保持する
        # (Port.labelの重複をさせないためPortsを用いる)
        self.relayed_o_ports = FlowPorts()

        # TODO: 用途不明
        from streamcat.store import ModuleStore
        self.module_store = ModuleStore()

        # Steps, Points, i_ports, o_portsを保持する
        self._flow_elements = None

        # Activityはメインフローの実行時(run)に作成する
        self._activity = None

        # データソースを追加する
        from streamcat.store.factory import DatumFactory
        from .appenders import FolderDataSourcePrepender
        self._datum_factory = DatumFactory(flow._session)
        self._folder_data_source_prepender = FolderDataSourcePrepender(self._datum_factory)

    def run(self, args={}, inputs={}):
        """
        フローを実行する
        """
        from .saver_activator import SaverActivator
        from .outs_terminator import OutsTerminator
        from .pruner import Pruner
        from .invoker import Invoker

        # 実行前に全てのサブフローに対して縦型探索して、フローJSONの解釈とフローの前処理を全て終わらせておく
        if self._is_main:
            # プレビュー引数を取得する
            vis_args = args.get('vis') or {}
            # キャッシュ参照・保存引数を取得する
            use_cache = args.get('use_cache')
            # TODO: 指定がない場合は暫定的にuse_cache=Trueにする
            use_cache = use_cache is None or use_cache

            # フローJSONを解釈する
            self.parse(use_cache)

            # フローの実行毎にActivity Datumを新規作成する
            activity_folder = self._datum_factory.load_activity_folder()
            self._activity = activity_folder.create_activity(self.label, self._flow, args)

            # SaverCommandの副作用(出力処理)を実行する為に、その出力Pointをフローの出力Pointに設定する
            self.relayed_o_ports = FlowPorts()
            _saver_activator = SaverActivator(self._flow, self._datum_factory, self._activity)
            _saver_activator.traverse(flow_cmd=self)

            # フロー出力PointにRunsとActivityコマンドを、キャッシュ出力Pointにキャッシュデータデストを付加する
            outs_terminator = OutsTerminator(self, self._flow, self._datum_factory, self._lock_uuid, self._activity)
            outs_terminator.terminate(vis_args, use_cache)

            # フローを縦型探索して不要な接続を刈る
            Pruner(self._flow_elements, self._is_main).search_up_i_ports(self.o_ports)

        # フローが定義する仮引数とこれに対応する値をDictで用意する
        flow_args = self._make_complete_flow_args(args)

        # フローを実行し、outsを返す
        # 実行において、再び縦型探索される
        return Invoker(self._flow_elements, self._is_main).run(flow_args, inputs)

    def parse(self, use_cache:bool):
        # フローJSONを解釈する
        from .parser import Parser
        self._flow_elements = Parser(self._flow_data, self._datum_factory, self._is_main).parse(use_cache)

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

    @property
    def is_main(self):
        return self._is_main

    @property
    def points(self):
        return self._flow_elements.points

    @points.setter
    def points(self, points:Points):
        self._flow_elements.points = points

    @property
    def substeps(self):
        return self._flow_elements.substeps

    @property
    def i_ports(self):
        if self._flow_elements is None:
            return FlowPorts()
        else:
            return self._flow_elements.i_ports

    @i_ports.setter
    def i_ports(self, value):
        pass

    @property
    def o_ports(self):
        if self._flow_elements is None:
            return FlowPorts()
        else:
            return self._flow_elements.o_ports

    @o_ports.setter
    def o_ports(self, value):
        pass

    @property
    def lasts(self):
        return {p.id: p.datum for p in self.points if p.is_last}

    @property
    def activity(self):
        return self._activity

    @lasts.setter
    def lasts(self, value):
        pass

    # @property
    # def outs(self):
    #     return {p.point.id: p.point.datum for p in self.o_ports}

    def is_i_port(self, point:Point):
        return any(p.point==point for p in self.i_ports)

    def is_o_port(self, point:Point):
        return any(p.point==point for p in self.o_ports)

    def has_o_port(self, port_label:str):
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

        self.o_ports.add(new_o_port)

    def close_i_port(self, port_label:str):
        for port in self.i_ports:
            if port.label == port_label:
                self.i_ports.remove(port)
                return
        return Exception(f'指定されたPort({port_label})はFlow({self})に存在しません')

    def close_o_port(self, port_label:str):
        for port in self.o_ports:
            if port.label == port_label:
                self.o_ports.remove(port)
                return
        return Exception(f'指定されたPort({port_label})はFlow({self})に存在しません')

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
          Invokder._run_invokable_steps()においてdtor()される
        """
        # TmpファイルはNYSOL-Pythonコマンドの入力に使用するので
        # Nysol-Python(Runsコマンド)の実行が終了した後に削除する
        if self._is_main:
            from streamcat.core import Tmp
            Tmp.remove_files()
