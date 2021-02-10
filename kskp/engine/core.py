from kskp.core import Datum

class Flow(Datum):
    def __init__(self, label):
        super().__init__(None, None, Datum.FLOW_TYPE, label)

        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.points = []
        self.substeps = []

        from kskp.store import ModuleStore
        self.module_store = ModuleStore()

    @property
    def lasts(self):
        # lasts = {}
        # for p in self.points:
        #     for t_tube in p.target:
        #         if t_tube.runnable is None:
        #             lasts[p.point_id] = p.datum

        # return lasts
        return {p.id: p.datum for p in self.points if p.is_last}

    @property
    def outs(self):
        return {p.id: p.datum for p in self.points if p.is_out}

    @property
    def is_datadst(self):
        """
        データデストの場合はTrueを返す
        """
        # TODO: いい条件が思い浮かばない,,,
        has_store = any (p for p in self.points if p.is_store)
        return len(self.i_ports) == 1 and len(self.lasts) == 1 and has_store

    def run(self, args, inputs):
        """
        pointではなくstepを基軸にして書き直し
        """
        # inputsを必要な部分に配置する
        self.prepare_inputs(inputs)

        # 実行準備が整ったstepのリストを取得する
        invokable_steps = self.search_invokable_steps()

        # print('invokable_steps1', invokable_steps, '\n')

        # 実行できるrunnableがある限りは動き続ける
        while len(invokable_steps) > 0:

            # stepのうち、実行準備が整ったものを実行する
            self.run_invokable_steps(invokable_steps, args)

            # print('invokable_steps2', '\n')  

            # 再度、実行準備が整ったstepのリストを取得しなおす
            invokable_steps = self.search_invokable_steps()

            # print('invokable_steps3', invokable_steps, self.points, '\n')

        # 実行すべきrunnableがもう残っていないなら、終了
        return self.make_outputs()

    def prepare_inputs(self, inputs):
        """
        inputsを必要な部分に配置する
        """

        input_points = [p for p in self.points if p.is_for_input]

        for input_point in input_points:
            if input_point.o_port.name not in inputs:
                # TODO: ポイントもポートもエラーメッセージにはlabel名を表示したい
                raise Exception(f'ポイント({input_point.id})の入力ポート({input_point.o_port.name})にデータが入力されませんでした')
            input_point.datum = inputs[input_point.o_port.name]

    def search_invokable_steps(self):
        """
        stepのうち、実行準備が整ったものを探して返す
        """

        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        # last_steps = set()
        # for p in self.points:
        #     for t_tube in p.target:
        #         if t_tube.runnable is None and p.datum is None:
        #             last_steps.add(p.o_runnable)
        last_steps = {p.o_runnable for p in self.points if p.is_last and p.datum is None}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        first_steps = union(self.search_first_steps_to_run(s) for s in last_steps)

        return first_steps

    def search_first_steps_to_run(self, original_step):
        """
        与えられたstepからフロー構造を逆に辿って、
        実行準備が整ったstepを見つけ出す
        """

        # 該当stepの実行に必要なpointを取得する
        # prev_points = set()
        # for p in self.points:
        #     for t_tube in p.target:
        #         if t_tube.runnable == original_step:
        #             prev_points.add(p)
        prev_points = {p for p in self.points if any(t_tube.runnable == original_step for t_tube in p.target)}

        # 全ての引数が埋まっていれば、実行可能とみなして走査終了
        if all([a.datum is not None for a in prev_points]):
            return {original_step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self.search_first_steps_to_run(a.o_runnable) for a in prev_points if a.datum is None and a.o_runnable is not None)

    def run_invokable_steps(self, steps, flow_args):
        """
        stepのうち、実行準備が整っている（＝引数が全て揃っている）ものを実行する
        実行後、結果をpointに格納する
        """
        from .job import Job

        for step in steps:

            # flow変数を使ってargsを書き換える
            if len(flow_args) > 0:
                step.replace_args(flow_args)

            # jobを作るためにinputsを集める
            # inputs = {a.target.port.name: a.datum for a in self.points if a.target.runnable == step}
            inputs = {}
            for p in self.points:
                for t_tube in p.target:
                    if t_tube.runnable == step:
                        # コマンドのinputs引数に値を格納する
                        inputs[t_tube.port.name] = p.datum

            # 実行したい処理の中にどのステップなのかを渡す
            step.runnable.context['step_id'] = step.id

            # jobを作る
            job = Job(step, inputs)

            # 実行開始
            result = job.start()

            # 結果をそれぞれのpointに入れる
            # まず、outputのpointを取得する
            output_points = {point for point in self.points if point.o_runnable == step}

            # それぞれのpointに結果を格納する
            for output_point in output_points:
                if not output_point.o_port.name in result:
                    raise Exception(f'STEP({step.id})に出力ポート{(output_point.o_port.name)}が存在しません')
                # 親フローに結果を戻す場合は戻す
                output_point.datum = result.pop(output_point.o_port.name)

            # どうやらf.redirect('u')したものをrunsに入れても実行できないみたい。
            # redirectしたものをm2teeなどのmコマンドと繋げるとrunsで実行できる。
            # なので、今の所ModuleStoreにはRunfuncCommandだけを入れるようにしている。
            from kskp.depo.std.commands import RunfuncCommand
            if isinstance(step.runnable, RunfuncCommand):
                for value in result.values():
                    self.module_store.append(value.content)

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
        # 何かの間違いがあった。

        # 例：
        # サブフローのo_portsが
        # [{"label": "出力1", "nodeId": "d3", "type": "frame"}, {"label": "出力2", "nodeId": "d4", "type": "frame"}]
        # の様に2つあって、/vizsなどによって片方（例えばd3）だけ使う様な場合、
        # d4をtarget.portとするpointは存在しない（使わないpointは切り捨てている）ので、ここを通ることになる。

        # なので、ここで例外を出すと正常に最後まで実行できなくなる。
        # とりあえずこのままにしておく
        return None

        # points = list(filter(lambda a:a.i_port == o_port, self.points))
        # return points[0]

    def select_point_by_node_id(self, node_id):
        """
        指定したnode_idをもつpointを１つ返す
        """
        return [point for point in self.points if point.id == node_id][0]

    def select_point_by_id(self, point_id):
        """
        self.pointsの中から
        指定したidのpointを取得する
        """
        for point in self.points:
            if point.id == point_id:
                return point
 
        raise Exception(f'指定されたPoint({point_id})がFlow({self.label})にありませんでした')

    def get_module_list(self):
        """
        substepsのmoduleをextendして返す
        """
        for substep in self.substeps:
            if isinstance(substep.runnable, Flow):
                self.module_store.extend(substep.runnable.get_module_list())

        return self.module_store.module_list

    # def find_activity(self):
    #     """
    #     Activity Stepをメインフローから再帰的に探し出す
    #     """
    #     from kskp.store import Activity
    #     # 自身がActivityを持っている場合
    #     # for activity in self.lasts.values():
    #     for activity in [p.datum for p in self.points]:
    #         if isinstance(activity, Activity):
    #             return activity
    #     # 自身が持っていない場合、サブフローを探しに行く
    #     # (データデストのみを用いている場合)
    #     for substep in self.substeps:
    #         if substep.is_flow :
    #             result = substep.runnable.find_activity()
    #             if result is not None:
    #                 return result
    #     # Activityが見つからなかった場合
    #     return None

    def dtor(self, args):
        # 配下のflowのdtorも動かす
        for substep in self.substeps:
            from kskp.core import Command
            if isinstance(substep.runnable, Flow) or isinstance(substep.runnable, Command):
                substep.dtor()
            else:
                raise Exception('substep.runnableにFlowまたはCommand以外のオブジェクトが格納されています')


def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
