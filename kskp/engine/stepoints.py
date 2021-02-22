class Stepoints():

    def __init__(self, steps, points, o_ports):
        self.points = points
        self.substeps = steps
        self.o_ports = o_ports

    def run(self, args, inputs):
        """
        pointではなくstepを基軸にして書き直し
        """
        # inputsを必要な部分に配置する
        self._prepare_inputs(inputs)

        # 実行準備が整ったstepのリストを取得する
        invokable_steps = self._search_invokable_steps()

        # print('invokable_steps1', invokable_steps, '\n')

        # 実行できるrunnableがある限りは動き続ける
        while len(invokable_steps) > 0:

            # stepのうち、実行準備が整ったものを実行する
            self._run_invokable_steps(invokable_steps, args)

            # print('invokable_steps2', '\n')  

            # 再度、実行準備が整ったstepのリストを取得しなおす
            invokable_steps = self._search_invokable_steps()

            # print('invokable_steps3', invokable_steps, self.points, '\n')

        # 実行すべきrunnableがもう残っていないなら、終了
        return self._make_outputs()

    def _prepare_inputs(self, inputs):
        """
        inputsを必要な部分に配置する
        """

        input_points = [p for p in self.points if p.is_for_input]

        for input_point in input_points:
            if input_point.src_port.label not in inputs:
                # TODO: ポイントもポートもエラーメッセージにはlabel名を表示したい
                raise Exception(f'ポイント({input_point.id})の入力ポート({input_point.src_port.label})にデータが入力されませんでした')
            input_point.datum = inputs[input_point.src_port.label]

    def _search_invokable_steps(self):
        """
        stepのうち、実行準備が整ったものを探して返す
        """

        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        # last_steps = set()
        # for p in self.points:
        #     for t_tube in p.dst_tubes:
        #         if t_tube.runnable is None and p.datum is None:
        #             last_steps.add(p.src_runnable)
        last_steps = {p.src_runnable for p in self.points if p.is_last and p.datum is None}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        first_steps = union(self._search_first_steps_to_run(s) for s in last_steps)

        return first_steps

    def _search_first_steps_to_run(self, original_step):
        """
        与えられたstepからフロー構造を逆に辿って、
        実行準備が整ったstepを見つけ出す
        """

        # 該当stepの実行に必要なpointを取得する
        # prev_points = set()
        # for p in self.points:
        #     for t_tube in p.dst_tubes:
        #         if t_tube.runnable == original_step:
        #             prev_points.add(p)
        prev_points = {p for p in self.points if any(t_tube.runnable == original_step for t_tube in p.dst_tubes)}

        # 全ての引数が埋まっていれば、実行可能とみなして走査終了
        if all([a.datum is not None for a in prev_points]):
            return {original_step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self._search_first_steps_to_run(a.src_runnable) for a in prev_points if a.datum is None and a.src_runnable is not None)

    def _run_invokable_steps(self, steps, flow_args):
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
            # inputs = {a.dst_tube.port.label: a.datum for a in self.points if a.dst_tube.runnable == step}
            inputs = {}
            for p in self.points:
                for t_tube in p.dst_tubes:
                    if t_tube.runnable == step:
                        # コマンドのinputs引数に値を格納する
                        inputs[t_tube.port.label] = p.datum

            # 実行したい処理の中にどのステップなのかを渡す
            step.runnable.context['step_id'] = step.id

            # jobを作る
            job = Job(step, inputs)

            # 実行開始
            result = job.start()

            # 結果をそれぞれのpointに入れる
            # まず、outputのpointを取得する
            output_points = {point for point in self.points if point.src_runnable == step}

            # それぞれのpointに結果を格納する
            for output_point in output_points:
                if not output_point.src_port.label in result:
                    raise Exception(f'STEP({step.id})に出力ポート{(output_point.src_port.label)}が存在しません')
                # 親フローに結果を戻す場合は戻す
                output_point.datum = result.pop(output_point.src_port.label)

            # どうやらf.redirect('u')したものをrunsに入れても実行できないみたい。
            # redirectしたものをm2teeなどのmコマンドと繋げるとrunsで実行できる。
            # なので、今の所ModuleStoreにはRunfuncCommandだけを入れるようにしている。
            from kskp.depo.std.commands import RunfuncCommand
            if isinstance(step.runnable, RunfuncCommand):
                for value in result.values():
                    self.module_store.append(value.content)

    def _make_outputs(self):
        """
        実行すべきstepがなくなった後呼び出される
        pointsの結果をまとめてoutputの形式に合うように整えて返す
        """
        return {port.label: self._get_output_point(port).datum for port in self.o_ports if self._get_output_point(port) is not None}
        # result = {port.label: self.get_output_point(port).datum.run() for port in self.o_ports}
        # print('_make_outputs result:', result)
        # return result

    def _get_output_point(self, o_port):
        """
        指定された出力ポートに対応するデータを返す
        """
        points = []
        for point in self.points:
            for dst_tube in point.dst_tubes:
                if dst_tube.port == o_port:
                    return point
        # 一応、何かの間違いで当てはまるものがなかった時のためにNone返しておく
        # 何かの間違いがあった。

        # 例：
        # サブフローのo_portsが
        # [{"label": "出力1", "nodeId": "d3", "type": "frame"}, {"label": "出力2", "nodeId": "d4", "type": "frame"}]
        # の様に2つあって、/vizsなどによって片方（例えばd3）だけ使う様な場合、
        # d4をdst_tube.portとするpointは存在しない（使わないpointは切り捨てている）ので、ここを通ることになる。

        # なので、ここで例外を出すと正常に最後まで実行できなくなる。
        # とりあえずこのままにしておく
        return None

        # points = list(filter(lambda a:a.i_port == o_port, self.points))
        # return points[0]

def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
