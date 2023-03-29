from .flow_port import FlowPort
from .step import Step, Steps
from .point import Point, Points
from .tube import Tube

class Stepoints():

    def __init__(self, steps:Steps, points:Points, i_ports:list[FlowPort], o_ports:list[FlowPort], is_main:bool):
        self.substeps = steps
        self.points = points
        self.i_ports = i_ports
        self.o_ports = o_ports
        self.is_main = is_main

    def run(self, flow_args:dict, inputs:dict, o_ports:list):
        """
        フローを実行する
        """
        # inputsを必要な部分に配置する
        self._prepare_inputs(inputs)

        # 実行準備が整った全てのStepを取得する
        prev_invokable_steps = set()
        invokable_steps = self._search_up_all_invokable_steps(o_ports)
        # print('invokable_steps1', invokable_steps)

        # 実行前後のrunnableのSetに変化が無ければ終了する(無限Loop対策)
        # while len(invokable_steps) > 0:
        while invokable_steps != prev_invokable_steps:

            # 実行準備が整った全てのStep
            prev_invokable_steps = invokable_steps

            # 実行準備が整った全てのStepを実行する
            self._run_invokable_steps(invokable_steps, flow_args)
            # print('invokable_steps2')

            # 再度、実行準備が整った全てのStepを取得する
            invokable_steps = self._search_up_all_invokable_steps(o_ports)
            # print('invokable_steps3', invokable_steps, self.points)

        # 実行すべきStepがもう残っていないなら終了する
        return self._make_outs()

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

    def _search_up_all_invokable_steps(self, o_ports:set[FlowPort]):
        """
        指定されたo_portsからフロー構造を逆に辿って、実行準備が整ったstepを見つけ出す
        """
        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        # 「最後」とはis_out=TrueのPointのことである
        # last_steps = set()
        # for p in self.o_ports:
        #     if p.point.datum is None:
        #         for src_tube in p.point.src_tubes:
        #             last_steps.add(src_tube.step)
        last_tubes = {src_tube for p in o_ports if not self._is_start_point(p.point) for src_tube in p.point.src_tubes}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        start_steps = union(self._search_up_invokable_steps(last_tube) for last_tube in last_tubes)

        return start_steps

    def _search_up_invokable_steps(self, last_tube:Tube):
        """
        指定された最後のTubeからフロー構造を逆に辿って、実行準備が整ったstepを見つけ出す
        """
        step = last_tube.step
        o_port = last_tube.port

        # 該当stepの実行に必要なpointを取得する
        # prev_points = set()
        # for p in self.points:
        #     if p.dst_tubes.have_step(step):
        #         prev_points.add(p)

        if step.is_flow:
            # サブフローCommand
            subflow = step.command

            # 指定するフロー出力PortをFlowPort型で取得する
            o_ports = {p for p in subflow.o_ports if p == o_port}

            # サブフローの出力Portからサブフローの開始Stepと入力Portを取得する
            start_steps, i_ports = subflow.search_up_i_ports(o_ports)

            # そのサブフローの入力Portに紐づく入力Pointを取得する
            prev_points = {p for i_port in i_ports for p in self.points if p.dst_tubes.have_tube(i_port, step)}

            # サブフローの実行に必要な出力PortだけをStepに設定する
            if 'o_ports' not in step.args:
                step.args['o_ports'] = set()
            step.args['o_ports'].update(o_ports)

        else:
            prev_points = {p for p in self.points if p.dst_tubes.have_step(step)}

        # # Stepの入力にフローの出力Pointが含まれていたら、そこで試合終了ですよ
        # if not self.is_main and any(p.point in prev_points for p in self.o_ports):
        #     return set()

        # 全ての入力値が埋まっていれば、実行可能とみなして走査終了
        if all([self._is_start_point(p) for p in prev_points]):
            return {step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self._search_up_invokable_steps(last_tube=src_tube)
                     for p in prev_points if not self._is_start_point(p) for src_tube in p.src_tubes if src_tube.step is not None)

    def _search_up_i_ports(self, o_ports:set[FlowPort]):
        """
        指定するフロー出力Portからフロー構造を逆に辿って、実行可能Stepとフロー入力Portを返す
        """
        # 指定するフロー出力Portから実行可能Stepを取得する
        invokable_steps = self._search_up_all_invokable_steps(o_ports)

        # 指定するフロー出力Portに紐づく開始Pointを取得する
        in_points = {p.point for p in o_ports if self._is_start_point(p.point)}

        # 実行可能Stepの入力Pointを取得する
        in_points.update({p for s in invokable_steps for p in self.points if p.dst_tubes.have_step(s)})

        # 開始Pointに紐づくフローの入力Portを取得する
        filtered_i_ports = {i_port for in_point in in_points for i_port in self.i_ports if i_port.point == in_point}

        # 実行可能Stepとフロー入力Portを返す
        return invokable_steps, filtered_i_ports

    def _is_start_point(self, p:Point):
        """
        入力値が埋まっている、または、サブフローかつフロー入力Pointの場合はTrueを返す
        """
        return p.datum is not None or (not self.is_main and p in {i_port.point for i_port in self.i_ports})

    def _run_invokable_steps(self, invokable_steps:list[Step], flow_args:dict):
        """
        stepのうち、実行準備が整っている（=引数が全て揃っている）ものを実行する
        実行後、結果をpointに格納する
        """
        for step in invokable_steps:

            # flow変数を使ってargsを書き換える
            if len(flow_args) > 0:
                step.replace_args(flow_args)

            # jobを作るためにinputを集める
            input_list = []
            for p in self.points:
                for dst_tube in p.dst_tubes.filter_by_step(step):
                    # コマンドのinputs引数に渡す値を集める
                    input = (dst_tube.port, p.datum)
                    input_list.append(input)

            # inputsは入力Portでソートする
            # (m2catで入力Port順に併合するため)
            sorted_input_list = sorted(input_list, key=lambda x: x[0])
            inputs = {input[0].label : input[1] for input in sorted_input_list}

            # 実行したい処理の中にどのステップなのかを渡す
            step.command.context['step_id'] = step.id

            # 実行する
            results = step.run(inputs)

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
            from streamcat.depo.std.commands import RunfuncCommand
            if isinstance(step.command, RunfuncCommand):
                for value in results.values():
                    self.module_store.append(value.content)

            # stepの終了処理
            step.dtor()

    def _make_outs(self):
        """
        実行すべきstepがなくなった後呼び出される
        pointsの結果をまとめてoutputの形式に合うように整えて返す
        """
        return {p.label: p.point.datum for p in self.o_ports}


def union(sets:list[set]):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
