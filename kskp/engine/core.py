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
            for a in self.step.runnable.arrows:
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

        self.arrows = []
        self.substeps = []

    @property
    def lasts(self):
        return {a.id: a.datum for a in self.arrows if a.cod is None}

    def run(self, args, inputs):
        """
        arrowではなくstepを基軸にして書き直し
        """

        # inputsを必要な部分に配置する
        self.prepare_inputs(inputs)

        # 実行準備が整ったstepのリストを取得する
        invokable_steps = self.search_invokable_steps()

        # print('invokable_steps1', self.arrows)

        # 実行できるrunnableがある限りは動き続ける
        while len(invokable_steps) > 0:

            # stepのうち、実行準備が整ったものを実行する
            self.run_invokable_steps(invokable_steps)

            # print('invokable_steps2', invokable_steps, self.arrows)

            # 再度、実行準備が整ったstepのリストを取得しなおす
            invokable_steps = self.search_invokable_steps()

            # print('invokable_steps3', invokable_steps, self.arrows)

        # FIXME: mcmd専用なので外に出す予定
        for k, last in self.lasts.items():
            from nysol.mcmd.nysollib.core import NysolMOD_CORE

            if isinstance(last, NysolMOD_CORE):
                r = last.run(msg='on')
                target_arrow = [arrow for arrow in self.arrows if arrow.id == k][0]
                target_arrow.datum = r

        # 実行すべきrunnableがもう残っていないなら、終了
        return self.make_outputs()

    def prepare_inputs(self, inputs):
        """
        inputsを必要な部分に配置する
        """

        input_arrows = [a for a in self.arrows if a.is_for_input]
        for input_arrow in input_arrows:
            input_arrow.datum = inputs[input_arrow.o_port.name]

    def search_invokable_steps(self):
        """
        stepのうち、実行準備が整ったものを探して返す
        """

        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        last_steps = {a.dom for a in self.arrows if a.cod is None and a.datum is None}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        first_steps = union(self.search_first_steps_to_run(s) for s in last_steps)

        return first_steps

    def search_first_steps_to_run(self, original_step):
        """
        与えられたstepからフロー構造を逆に辿って、
        実行準備が整ったstepを見つけ出す
        """

        # 該当stepの実行に必要なarrowを取得する
        prev_arrows = {a for a in self.arrows if a.cod == original_step}

        # 全ての引数が埋まっていれば、実行可能とみなして走査終了
        if all([a.datum is not None for a in prev_arrows]):
            return {original_step}

        # 埋まっていないarrowがあれば、それを逆に辿る
        return union(self.search_first_steps_to_run(a.dom) for a in prev_arrows if a.dom is not None)

    def run_invokable_steps(self, steps):
        """
        stepのうち、実行準備が整っている（＝引数が全て揃っている）ものを実行する
        実行後、結果をarrowに格納する
        """

        # print('steps in run_invokable_steps:', steps)

        for step in steps:

            # jobを作るためにinputsを集める
            inputs = {a.i_port.name: a.datum for a in self.arrows if a.cod == step}

            # 実行したい処理の中にどのステップなのかを渡す
            step.runnable.context['step_id'] = step.id
            # print('context in run_invokable_steps:', step.runnable.context)

            # jobを作る
            job = Job(step, inputs)

            # 実行開始
            result = job.start()
            # print('result of job.start():', result)
            # 結果をそれぞれのarrowに入れる

            # まず、outputのarrowを取得する
            output_arrows = {arrow for arrow in self.arrows if arrow.dom == step}

            # それぞれのarrowに結果を格納する
            for output_arrow in output_arrows:

                # 親フローに結果を戻す場合は戻す
                output_arrow.datum = result[output_arrow.o_port.name]
                # print('output_arrow:', output_arrow)

    def make_outputs(self):
        """
        実行すべきstepがなくなった後呼び出される
        arrowsの結果をまとめてoutputの形式に合うように整えて返す
        """
        return {port.name: self.get_output_arrow(port).datum for port in self.o_ports}
        # result = {port.name: self.get_output_arrow(port).datum.run() for port in self.o_ports}
        # print('make_outputs result:', result)
        # return result

    def get_output_arrow(self, o_port):
        """
        指定された出力ポートに対応するデータを返す
        """
        arrows = list(filter(lambda a:a.i_port == o_port, self.arrows))
        return arrows[0]


class Arrow:
    """
    o->iの順番なので注意
    """

    def __init__(self, id, dom, o_port, datum, i_port, cod):
        self.id = id

        self.dom = dom
        self.o_port = o_port
        self.datum = datum
        self.i_port = i_port
        self.cod = cod

    def __repr__(self):
        if self.o_port is not None:
            if self.dom is None:
                dom_o = f"self.{self.o_port.name}"
            else:
                dom_o = f"{self.dom}.{self.o_port.name}"
        else:
            dom_o = f"{self.dom}.None"

        if self.i_port is not None:
            if self.cod is None:
                cod_i = f"self.{self.i_port.name}"
            else:
                cod_i = f"{self.cod}.{self.i_port.name}"
        else:
            cod_i = f"{self.cod}.None"

        if self.datum is None:
            return f"{self.id}<{dom_o} -> {cod_i}>"
        else:
            return f"{self.id}<{dom_o} -({self.datum})-> {cod_i}>"

    @property
    def is_for_input(self):
        return self.dom is None and self.o_port is not None and self.datum is None


def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
