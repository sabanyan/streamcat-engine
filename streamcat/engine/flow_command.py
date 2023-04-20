from streamcat.core import Command
from streamcat.store import Flow
from .point import Point, Points
from .flow_port import FlowPort
from .ports import Ports

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

    def __init__(self, flow:Flow, lock_uuid:str=None, is_main:bool=True, saver_activator=None):
        super().__init__(flow.label)

        # 実行前にフローJSONの書式の検証をする
        flow.flow_data.valid_flow_json_or_raise()

        # フローJSONをコピーする
        # (TODO: なぜコピーする必要があるのか忘れてしまった)
        self._flow_data = flow.flow_data.copy()

        # 仮引数を保持する
        self.params = self._flow_data.params or {}

        # メインフローであればTrue
        self.is_main = is_main

        # SaverActivatorが中継した出力Portのリストを保持する
        # (Port.labelの重複をさせないためPortsを用いる)
        self.relayed_o_ports = Ports()

        # TODO: 用途不明
        from streamcat.store import ModuleStore
        self.module_store = ModuleStore()

        # 
        # self.context = {}

        # Steps, Points, i_ports, o_portsを保持する
        self._stepoints = None

        # データソースを追加する
        from streamcat.store.factory import DatumFactory
        from .appenders import FolderDataSourcePrepender
        self._datum_factory = DatumFactory(flow._session)
        self._folder_data_source_prepender = FolderDataSourcePrepender(self._datum_factory)

        # Activity期間中は同じSaverActivatorインスタンスを使う
        from .outs_terminator import OutsTerminator
        from .saver_activator import SaverActivator
        if saver_activator is None:
            self._outs_terminator = OutsTerminator(self, flow, self._datum_factory, lock_uuid)
            self._saver_activator = SaverActivator(flow, self._datum_factory, self._outs_terminator.activity)
        else:
            # saver_activatorが指定された場合はサブフローなので、OutsTerminatorは使わない
            self._outs_terminator = None
            self._saver_activator = saver_activator

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
            self._stepoints = self._parse(vis_args, use_cache)
            # run()をリエントラント可能にするため、ここでappenderとrelayed_o_portsを初期化する
            self._outs_terminator.init(args)
            self._saver_activator.set_activity(self._outs_terminator.activity)
            self.relayed_o_ports = Ports()
            # フローを前処理する
            self._saver_activator.traverse(flow_cmd=self)
            # フロー出力PointにRunsとActivityコマンドを、キャッシュ出力Pointにキャッシュデータデストを付加する
            self._outs_terminator.terminate(vis_args, use_cache)
            # フローを縦型探索して不要な接続を刈る
            from .pruner import Pruner
            Pruner(self.substeps, self.points, self.i_ports, self.is_main).search_up_i_ports(self.o_ports)

        # フローが定義する仮引数とこれに対応する値をDictで用意する
        flow_args = self._make_complete_flow_args(args)

        # フローを実行し、outsを返す
        # 実行において、再び縦型探索される
        from .invoker import Invoker
        return Invoker(self.points, self.i_ports, self.o_ports, self.is_main).run(flow_args, inputs)

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

    def _parse(self, vis_args, use_cache:bool, src_point:Point=None):
        # フローJSONを解釈する
        from .parser import Parser
        return Parser(self, self._flow_data, self._datum_factory, self._saver_activator, self.is_main).parse(vis_args, use_cache, src_point)

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

        self.o_ports.append(new_o_port)

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

    @property
    def activity(self):
        return self._saver_activator._context.activity

    def dtor(self, args={}):
        """
        終了処理
        - self.substepsの各Stepは
          Invokder._run_invokable_steps()においてdtor()される
        """
        # TmpファイルはNYSOL-Pythonコマンドの入力に使用するので
        # Nysol-Python(Runsコマンド)の実行が終了した後に削除する
        if self.is_main:
            from streamcat.core import Tmp
            Tmp.remove_files()
