from streamcat.core import Command
from streamcat.store import Flow
from .elements import Points, FlowPort, FlowPorts

class FlowCommand(Command):
    """
    フローJSONを実行するコマンド
    """
    def __init__(self, flow:Flow, lock_uuid:str=None, is_main:bool=True):
        super().__init__(flow.label)

        self._flow = flow
        self._lock_uuid = lock_uuid

        # メインフローであればTrue
        self._is_main = is_main

        # Steps, Points, i_ports, o_portsを保持する
        self._flow_elements = None

        # Activityはメインフローの実行時(run)に作成する
        self._activity = None

        # 実行前にフローJSONの書式の検証をする
        flow.flow_data.valid_flow_json_or_raise()

        # フローJSONをコピーする
        # (TODO: なぜコピーする必要があるのか忘れてしまった)
        self._flow_data = flow.flow_data.copy()

        # データソースを追加する
        from streamcat.store.finder import DatumFactory
        self._datum_factory = DatumFactory(flow._session)

        # 仮引数を保持する
        self.params = self._flow_data.params or {}

        # SaverActivatorが中継した出力Portのリストを保持する
        # (Port.labelの重複をさせないためPortsを用いる)
        self.relayed_o_ports = FlowPorts()

        # TODO: 用途不明
        from streamcat.store import ModuleStore
        self.module_store = ModuleStore()

    def run(self, args:dict={}, inputs:dict={}):
        """
        フローを実行する
        """
        from .core import SaverActivator, OutsTerminator, Pruner, Invoker

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
            SaverActivator(self, self._flow, self._datum_factory, self._activity).traverse()

            # フロー出力PointにRunsとActivityコマンドを、キャッシュ出力Pointにキャッシュデータデストを付加する
            OutsTerminator(self, self._flow, self._datum_factory, self._lock_uuid, self._activity).terminate(vis_args, use_cache)

            # フローを縦型探索して不要な接続を刈る
            Pruner(self._flow_elements, self._is_main).traverse()

        # フローが定義する仮引数とこれに対応する値をDictで用意する
        flow_args = self._make_complete_flow_args(args)

        # フローを実行し、outsを返す
        # 実行において、再び縦型探索される
        return Invoker(self._flow_elements, self._is_main).run(flow_args, inputs)

    def parse(self, use_cache:bool):
        # フローJSONを解釈する
        from .core.parser import Parser
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
    def steps(self):
        return self._flow_elements.steps

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

    @lasts.setter
    def lasts(self, value):
        pass

    @property
    def activity(self):
        return self._activity

    # @property
    # def outs(self):
    #     return {p.point.id: p.point.datum for p in self.o_ports}

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

    def dtor(self, args={}):
        """
        終了処理
        - self.stepsの各Stepは
          Invokder._run_invokable_steps()においてdtor()される
        """
        # TmpファイルはNYSOL-Pythonコマンドの入力に使用するので
        # Nysol-Python(Runsコマンド)の実行が終了した後に削除する
        if self._is_main:
            from streamcat.core import Tmp
            Tmp.remove_files()
