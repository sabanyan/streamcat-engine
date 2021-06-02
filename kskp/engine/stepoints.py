from typing import List
from .flow_port import FlowPort
from .point import Points
from .step import Step

class Stepoints():

    def __init__(self, steps:List[Step], points:Points, i_ports:List[FlowPort], o_ports:List[FlowPort], is_main:bool):
        self.substeps = steps
        self.points = points
        self.i_ports = i_ports
        self.o_ports = o_ports
        self.is_main = is_main

    def run(self, flow_args:dict, inputs:dict):
        """
        pointではなくstepを基軸にして書き直し
        """
        # inputsを必要な部分に配置する
        self._prepare_inputs(inputs)

        # 実行準備が整ったstepのリストを取得する
        prev_invokable_steps = set()
        invokable_steps = self._search_invokable_steps()
        # print('invokable_steps1', invokable_steps)

        # 実行前後のrunnableのSetに変化が無ければ終了する(無限Loop対策)
        # while len(invokable_steps) > 0:
        while invokable_steps != prev_invokable_steps:

            # 実行前のrunnableのSet
            prev_invokable_steps = invokable_steps

            # stepのうち、実行準備が整ったものを実行する
            self._run_invokable_steps(invokable_steps, flow_args)
            # print('invokable_steps2')

            # 再度、実行準備が整ったstepのリストを取得しなおす
            invokable_steps = self._search_invokable_steps()
            # print('invokable_steps3', invokable_steps, self.points, '\n')

        # 実行すべきrunnableがもう残っていないなら、終了
        return self._make_outputs()

    def _prepare_inputs(self, inputs:dict):
        """
        inputsで渡されたDatumを、フローの入力Portに紐づくPointに格納する
        """
        for i_port in self.i_ports:
            if i_port.label in inputs:
                i_port.point.datum = inputs[i_port.label]
            elif self.is_main:
                # メインフローの場合は、入力PortのPointは無視するのでDatumの格納はしない
                pass
            else:
                # TODO: ポイントもポートもエラーメッセージにはlabel名を表示したい
                raise Exception(f'入力ポート({i_port.label})にデータが入力されませんでした')

    def _search_invokable_steps(self):
        """
        stepのうち、実行準備が整ったものを探して返す
        """
        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        # 「最後」とはis_out=TrueのPointのことである
        # last_steps = set()
        # for p in self.o_ports:
        #     if p.point.datum is None:
        #         for src_tube in p.point.src_tubes:
        #             last_steps.add(src_tube.step)
        last_steps = {src_tube.step for p in self.o_ports if p.point.datum is None for src_tube in p.point.src_tubes}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        first_steps = union(self._search_first_steps_to_run(s) for s in last_steps)

        return first_steps

    def _search_first_steps_to_run(self, original_step:Step):
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
        if not self.is_main and any(p.point in prev_points for p in self.o_ports):
            return set()

        # 全ての入力値が埋まっていれば、実行可能とみなして走査終了
        if all([p.datum is not None for p in prev_points]):
            return {original_step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self._search_first_steps_to_run(src_tube.step)
                     for p in prev_points if p.datum is None for src_tube in p.src_tubes if src_tube.step is not None)

    def _run_invokable_steps(self, invokable_steps:List[Step], flow_args:dict):
        """
        stepのうち、実行準備が整っている（＝引数が全て揃っている）ものを実行する
        実行後、結果をpointに格納する
        """
        from .job import Job

        for step in invokable_steps:

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
            step.command.context['step_id'] = step.id

            # jobを作る
            job = Job(step, inputs)

            # 実行開始
            results = job.start()

            # 結果をそれぞれのpointに入れる
            # まず、outputのpointを取得する
            output_points = {point for point in self.points if point.src_tubes.have_step(step)}

            # それぞれのpointに結果を格納する
            for output_point in output_points:
                for src_tube in output_point.src_tubes.filter_by_step(step):
                    src_port_label = src_tube.port.label
                    if src_port_label not in results:
                        raise Exception(f'Step({step.id})の出力にPort({src_port_label})が存在しません')
                    # 親フローに結果を戻す場合は戻す
                    if output_point.datum is not None:
                        raise Exception(f'Step({step.id})の複数の出力が1つのPoint({output_point.id})にデータを格納しようとしました')
                    output_point.datum = results.pop(src_port_label)

            # どうやらf.redirect('u')したものをrunsに入れても実行できないみたい。
            # redirectしたものをm2teeなどのmコマンドと繋げるとrunsで実行できる。
            # なので、今の所ModuleStoreにはRunfuncCommandだけを入れるようにしている。
            from kskp.depo.std.commands import RunfuncCommand
            if isinstance(step.command, RunfuncCommand):
                for value in results.values():
                    self.module_store.append(value.content)

            # jobの終了処理
            job.dtor()

    def _make_outputs(self):
        """
        実行すべきstepがなくなった後呼び出される
        pointsの結果をまとめてoutputの形式に合うように整えて返す
        """
        return {p.label: p.point.datum for p in self.o_ports}


def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
