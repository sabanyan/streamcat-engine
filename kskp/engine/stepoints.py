from typing import List
from kskp.core import Port
from .step import Step
from .point import Point

class Stepoints():

    def __init__(self, steps:List[Step], points:List[Point], o_ports:List[Port], is_root:bool):
        self.substeps = steps
        self.points = points
        self.o_ports = o_ports
        self.is_root = is_root

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
        inputsで渡されたDatumを、フローの入力PortのPointに格納する
        """
        input_points = [p for p in self.points if p.is_for_input]

        for input_point in input_points:
            src_port_label = input_point.src_tubes.select_flow_tube().port.label

            if src_port_label in inputs:
                input_point.datum = inputs[src_port_label]
            elif not self.is_root:
                # TODO: ポイントもポートもエラーメッセージにはlabel名を表示したい
                raise Exception(f'ポイント({input_point.id})の入力ポート({src_port_label})にデータが入力されませんでした')
            else:
                # メインフローの場合は、入力PortのPointは無視するのでDatumの格納はしない
                pass

    def _search_invokable_steps(self):
        """
        stepのうち、実行準備が整ったものを探して返す
        """

        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        # 「最後」とはis_out=TrueのPointのことである
        # last_steps = set()
        # for p in self.points:
        #     if p.is_out and p.datum is None:
        #         for src_tube in p.src_tubes:
        #             last_steps.add(src_tube.step)
        last_steps = {src_tube.step for p in self.points if p.is_out and p.datum is None for src_tube in p.src_tubes}

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
        #     if p.dst_tubes.have_step(original_step):
        #         prev_points.add(p)
        prev_points = {p for p in self.points if p.dst_tubes.have_step(original_step)}

        # Stepの入力にフローの出力Pointが含まれていたら、そこで試合終了ですよ
        if any([p.is_out for p in prev_points]):
            return set()

        # 全ての入力値が埋まっていれば、実行可能とみなして走査終了
        if all([p.datum is not None for p in prev_points]):
            return {original_step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self._search_first_steps_to_run(src_tube.step)
                     for p in prev_points if p.datum is None for src_tube in p.src_tubes if src_tube.step is not None)

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
            inputs = {}
            for p in self.points:
                for dst_tube in p.dst_tubes.filter_by_step(step):
                    # コマンドのinputs引数に値を格納する
                    inputs[dst_tube.port.label] = p.datum

            # 実行したい処理の中にどのステップなのかを渡す
            step.runnable.context['step_id'] = step.id

            # jobを作る
            job = Job(step, inputs)

            # 実行開始
            results = job.start()

            # 結果をそれぞれのpointに入れる
            # まず、outputのpointを取得する
            output_points = {point for point in self.points if point.src_tubes.have_step(step)}

            # それぞれのpointに結果を格納する
            for output_point in output_points:
                src_port_label = output_point.src_tubes.filter_by_step(step)[0].port.label
                if not src_port_label in results:
                    raise Exception(f'STEP({step.id})に出力ポート{(src_port_label)}が存在しません')
                # 親フローに結果を戻す場合は戻す
                output_point.datum = results.pop(src_port_label)

            # どうやらf.redirect('u')したものをrunsに入れても実行できないみたい。
            # redirectしたものをm2teeなどのmコマンドと繋げるとrunsで実行できる。
            # なので、今の所ModuleStoreにはRunfuncCommandだけを入れるようにしている。
            from kskp.depo.std.commands import RunfuncCommand
            if isinstance(step.runnable, RunfuncCommand):
                for value in results.values():
                    self.module_store.append(value.content)

    def _make_outputs(self):
        """
        実行すべきstepがなくなった後呼び出される
        pointsの結果をまとめてoutputの形式に合うように整えて返す
        """
        return {port.label: self._get_output_point(port).datum for port in self.o_ports if self._get_output_point(port) is not None}
        # results = {port.label: self.get_output_point(port).datum.run() for port in self.o_ports}
        # return results

    def _get_output_point(self, o_port):
        """
        指定された出力ポートに対応するデータを返す
        """
        points = []
        for point in self.points:
            for dst_tube in point.dst_tubes:
                if dst_tube.port is not None and dst_tube.port == o_port:
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
