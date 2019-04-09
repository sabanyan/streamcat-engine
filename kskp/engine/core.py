import uuid
from pathlib import Path
from kskp.store import Command, Datum

class Job:
    def __init__(self, step, inputs):
        self.step = step
        self.inputs = inputs

        self.errors = []

    def start(self):
        try:
            return self.step.runnable.run(self.step.args, self.inputs)
        except Exception as e:
            print(repr(e))
            self.errors.append(e)
            raise

    def dtor(self):
        if isinstance(self.step.runnable, Flow):
            for a in self.step.runnable.points:
                if a.datum is not None:
                    pass
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定

class Store(Datum):
    """
    できたdatumを入れておく場所
    """
    def __init__(self):
        self.data = {} # dict keyはUUID、valはdatum？

    def issue_uuid(self):
        """
        uuidを発行する
        """
        new_uuid = str(uuid.uuid4())
        self.data[new_uuid] = None
        return new_uuid

    def set_datum(self, datum, uuid):
        """
        指定したuuidとdatumを対応づけて保存しておく
        """
        if self.data[uuid] is None:
            self.data[uuid] = datum
        else:
            # 上書きするか、Falseを返すかどうしよう？
            pass

        return True

    def save(self, datum):
        """
        override用
        """
        pass

    def load(self, uuid):
        """
        override用
        引数uuidにしているけど、いいのか？
        """
        pass

class Folder(Store):
    """
    ディレクトリに保存するStore
    """
    def __init__(self):
        super().__init__()
        # TODO: どのディレクトリにでも保存できるように決め打ちはやめたほうがいいよね。
        self.cache_dir_path = Path('kskp/data/cache_frames')
        self.frame_dir_path = Path('kskp/data')

    def save(self, datum):
        import nysol.mcmd as nm
        uuid = self.issue_uuid()
        self.set_datum(datum, uuid)

        args = {}
        args['i'] = datum
        args['o'] = (self.cache_dir_path / (uuid + '.csv')).as_posix()

        # ここら辺でdbにuuidとファイル名を保存する感じ？
        # 今はファイル名＝uuidだが。
        cmd_o = nm.m2tee(args)
        return cmd_o

    def load(self, uuid):
        import nysol.mcmd as nm

        # TODO: 本当はuuidを使ってdbからcsvの場所を取ってくる

        # 今はとりあえず直接取ってくる(uuid==csvのファイル名)
        path = None
        for flow_path in self.frame_dir_path.iterdir():
            if flow_path.stem == uuid:
                path = flow_path
                break

        args = {}
        args['i'] = flow_path.as_posix()
        cmd_o = nm.m2tee(args)
        return cmd_o

    @property
    def content(self):
        return self

class NysolModule(Datum):
    def __init__(self):
        super().__init__()
        self.uuid = None
        self._content = None

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    def run(self, msg=False):
        # NysolModuleなので実行できるdatum
        # NysolModule.content.run()するよりはいいかなと思ったのだがどうだろう？
        if msg:
            return self._content.run(msg='on')
        else:
            return self._content.run()

    @property
    def content(self):
        return self._content

class Frame(Datum):
    def __init__(self):
        super().__init__()
        self.uuid = None
        self._content = None

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

class Step:
    def __init__(self, id, runnable, args):
        self.id = id
        self.runnable = runnable
        self.args = args

    def __repr__(self):
        return self.id

class Flow(Datum):
    def __init__(self):
        super().__init__()

        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.points = []
        self.substeps = []

    @property
    def lasts(self):
        lasts = {}
        for p in self.points:
            for t_tube in p.target:
                if t_tube.runnable is None:
                    lasts[p.id] = p.datum

        # return {a.id: a.datum for a in self.points if a.target.runnable is None}
        return lasts

    @property
    def point_ids(self):
        return [point.id for point in self.points]

    def run(self, args, inputs):
        """
        pointではなくstepを基軸にして書き直し
        """
        # inputsを必要な部分に配置する
        self.prepare_inputs(inputs)

        # 実行準備が整ったstepのリストを取得する
        invokable_steps = self.search_invokable_steps()

        # print('invokable_steps1', self.points)

        # 実行できるrunnableがある限りは動き続ける
        while len(invokable_steps) > 0:

            # stepのうち、実行準備が整ったものを実行する
            self.run_invokable_steps(invokable_steps)

            # print('invokable_steps2', invokable_steps, self.points)

            # 再度、実行準備が整ったstepのリストを取得しなおす
            invokable_steps = self.search_invokable_steps()

            # print('invokable_steps3', invokable_steps, self.points)

        # FIXME: mcmd専用なので外に出す予定
        for k, last in self.lasts.items():
            # from nysol.mcmd.nysollib.core import NysolMOD_CORE
            # サブフローの最後はまだrun()する必要はないので、
            # len(self.o_ports) == 0を条件に追記
            if isinstance(last, NysolModule) and len(self.o_ports) == 0:
                # 最後のものは一応Frameで作っておく
                # 現状FrameとNysolModuleには明確な違いがない。。。
                frame = Frame()
                frame.set_content(last.run(msg=True))
                target_point = [point for point in self.points if point.id == k][0]
                target_point.datum = frame

        # 実行すべきrunnableがもう残っていないなら、終了
        return self.make_outputs()

    def prepare_inputs(self, inputs):
        """
        inputsを必要な部分に配置する
        """

        input_points = [a for a in self.points if a.is_for_input]
        # print('aaa', input_points, inputs)
        for input_point in input_points:
            input_point.datum = inputs[input_point.o_port.name]

    def search_invokable_steps(self):
        """
        stepのうち、実行準備が整ったものを探して返す
        """

        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        last_steps = set()
        for p in self.points:
            for t_tube in p.target:
                if t_tube.runnable is None and p.datum is None:
                    last_steps.add(p.o_runnable)
        # last_steps = {p.o_runnable for p in self.points if p.target.runnable is None and p.datum is None}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        first_steps = union(self.search_first_steps_to_run(s) for s in last_steps)

        return first_steps

    def search_first_steps_to_run(self, original_step):
        """
        与えられたstepからフロー構造を逆に辿って、
        実行準備が整ったstepを見つけ出す
        """

        # 該当stepの実行に必要なpointを取得する
        prev_points = set()
        for p in self.points:
            for t_tube in p.target:
                if t_tube.runnable == original_step:
                    prev_points.add(p)
        # prev_points = {a for a in self.points if a.target.runnable == original_step}

        # 全ての引数が埋まっていれば、実行可能とみなして走査終了
        if all([a.datum is not None for a in prev_points]):
            return {original_step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self.search_first_steps_to_run(a.o_runnable) for a in prev_points if a.o_runnable is not None)

    def run_invokable_steps(self, steps):
        """
        stepのうち、実行準備が整っている（＝引数が全て揃っている）ものを実行する
        実行後、結果をpointに格納する
        """

        # print('steps in run_invokable_steps:', steps)

        for step in steps:
            # jobを作るためにinputsを集める
            # inputs = {a.target.port.name: a.datum for a in self.points if a.target.runnable == step}
            inputs = {}
            for p in self.points:
                for t_tube in p.target:
                    if t_tube.runnable == step:
                        inputs[t_tube.port.name] = p.datum.content if isinstance(p.datum, Datum) else p.datum

            # 実行したい処理の中にどのステップなのかを渡す
            step.runnable.context['step_id'] = step.id
            # print('context in run_invokable_steps:', step.runnable.context)

            # jobを作る
            job = Job(step, inputs)

            # 実行開始
            result = job.start()
            # print('result of job.start():', result)
            # 結果をそれぞれのpointに入れる
            # まず、outputのpointを取得する
            output_points = {point for point in self.points if point.o_runnable == step}

            # それぞれのpointに結果を格納する
            for output_point in output_points:
                # 親フローに結果を戻す場合は戻す
                output_point.datum = result[output_point.o_port.name]
                # print('output_point:', output_point)

    def make_outputs(self):
        """
        実行すべきstepがなくなった後呼び出される
        pointsの結果をまとめてoutputの形式に合うように整えて返す
        """
        return {port.name: self.get_output_point(port).datum for port in self.o_ports if self.get_output_point(port) is not None}
        # result = {port.name: self.get_output_point(port).datum.run() for port in self.o_ports}
        # print('make_outputs result:', result)
        # return result

    def get_output_point(self, o_port):
        """
        指定された出力ポートに対応するデータを返す
        """
        points = []
        for point in self.points:
            for target in point.target:
                if target.port == o_port:
                    return point
        # 一応、何かの間違いで当てはまるものがなかった時のためにNone返しておく
        # TODO: いつかちゃんとする
        return None

        # points = list(filter(lambda a:a.i_port == o_port, self.points))
        # return points[0]

    def get_point_by_node_id(self, node_id):
        """
        指定したnode_idをもつpointを１つ返す
        """
        return [point for point in self.points if point.id == node_id][0]

class Point:
    """
    o->iの順番なので注意
    """

    def __init__(self, id, origin_tubes, datum, target_tubes, cache=False):
        self.id = id

        self.origin = origin_tubes
        self.datum = datum
        self.target = target_tubes

        self.cache = cache

    def __repr__(self):

        if self.o_port is not None:
            if self.o_runnable is None:
                dom_o = f"self.{self.o_port.name}"
            else:
                dom_o = f"{self.o_runnable}.{self.o_port.name}"
        else:
            dom_o = f"{self.o_runnable}.None"

        cod_i = ""
        for tube in self.target:
            if tube.port is not None:
                if tube.runnable is None:
                    cod_i += f"(self.{tube.port.name})"
                else:
                    cod_i += f"({tube.runnable}.{tube.port.name})"
            else:
                cod_i += f"({tube.runnable}.None)"

        if self.datum is None:
            return f"{self.id}<{dom_o} -> {cod_i}>"
        else:
            return f"{self.id}<{dom_o} -({self.datum})-> {cod_i}>"

    @property
    def is_for_input(self):
        return self.o_runnable is None and self.o_port is not None and self.datum is None

    @property
    def o_port(self):
        return self.origin[0].port

    @property
    def o_runnable(self):
        return self.origin[0].runnable

    @property
    def is_last(self):
        """
        指定したポイントが終端のものかどうかを調べる
        """
        return self.target[0].port is None and self.target[0].runnable is None

    @property
    def is_first(self):
        """
        指定したポイントが始端かどうかを調べる
        サブフローの場合は、始端のpointのportはNoneではないので
        runnableだけで判断している
        """
        return self.o_runnable is None

    def update_origin(self, tube):
        """
        指定したTubeでoriginを更新する
        複数のoriginをもつPointはないので、上書きだけ（appendする必要がない）
        """
        self.origin = [tube]

    def update_target(self, tube):
        """
        指定したTubeでtargetを更新する
        既にtargetに有効なTubeがあった場合は追加、
        そうではなかったら上書きする
        """
        if self.is_last:
            self.target = [tube]
        else:
            self.target.append(tube)

class Tube:
    """
    portとrunnableの入れ物
    """
    def __init__(self, port, runnable):
        self.port = port
        self.runnable = runnable

def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
