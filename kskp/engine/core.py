import uuid

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
            from nysol.mcmd.nysollib.core import NysolMOD_CORE

            if isinstance(last, NysolMOD_CORE):
                r = last.run(msg='on')
                target_point = [point for point in self.points if point.id == k][0]
                target_point.datum = r

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
                        inputs[t_tube.port.name] = p.datum

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
        return {port.name: self.get_output_point(port).datum for port in self.o_ports}
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
        # いつかちゃんとする
        return None
        
        # points = list(filter(lambda a:a.i_port == o_port, self.points))
        # return points[0]


class Point:
    """
    o->iの順番なので注意
    """

    def __init__(self, id, origin_tubes, datum, target_tubes):
        self.id = id

        self.origin = origin_tubes
        self.datum = datum
        self.target = target_tubes

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
