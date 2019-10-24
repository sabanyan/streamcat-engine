import json
import uuid

from kskp.store import Datum

class Job:
    def __init__(self, step, inputs):
        self.step = step
        self.inputs = inputs

        self.errors = []

        # 実行を終了したらTrueにするフラグ
        self.already_ran = False

    def start(self):
        try:
            return self.step.runnable.run(self.step.args, self.inputs)
        except Exception as e:
            print(repr(e))
            self.errors.append(e)
            raise

    def runs(self):
        """
        runsを実行する
        """
        try:
            last_modules = []
            for point_datum in self.step.runnable.results.values():
                last_modules.append(point_datum.content)

            module_list = self.step.runnable.get_module_list()
            last_modules.extend(module_list)

            # 実行
            import nysol.mcmd as nm
            nm.runs(last_modules, msg='on')
        except Exception as e:
            print(repr(e))
            self.errors.append(e)
            raise

    def dtor(self):
        if isinstance(self.step.runnable, Flow):
            # 今のFlowのdtorは、cacheやlastsを保存しているだけ
            self.step.runnable.dtor()

            for point in self.step.runnable.points:
                if point.datum is not None:
                    pass
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定

class Step:
    def __init__(self, step_id, runnable, args):
        self.id = step_id
        self.runnable = runnable
        self.args = args
        self.already_ran = False

    def __repr__(self):
        return self.id

    @property
    def is_flow(self):
        return isinstance(self.runnable, Flow)

    @property
    def is_datadst(self):
        return self.is_flow and self.runnable.is_datadst

    def replace_args(self, flow_args):
        """
        自身のargsにフロー変数を使っている箇所があれば、argsの値で置き換える

        FIXME?: フロー変数を書き換えるのはStep以外でもいいが、
        早めに書き換えたかったので、とりあえずStepに記載してある
        """
        import re
        # TODO: 正規表現やreplace対象を外に出す。
        for param, value in flow_args.items():
            for step_param, step_value in self.args.items():
                # ネスト深くなるので、continueを利用してネストを浅くした
                if not isinstance(step_value, str):
                    continue


                for r in re.finditer(r'@\[(\S*?)\]', step_value):
                    if r is None:
                        continue

                    for g in r.groups():
                        if param == g:
                            self.args[step_param] = self.args[step_param].replace(f'@[{g}]', value)

class Flow(Datum):
    def __init__(self, label):
        super().__init__(None, Datum.FLOW_TYPE, label)

        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.points = []
        self.substeps = []

        # TODO:FrameStoreは外部にあるべき？
        # contextに'framestore'というキーを作ってそこに入れる？
        # それともこのままでいい？
        from kskp.store import FrameStore, ModuleStore
        self.cache_store = FrameStore()
        self.lasts_store = FrameStore()

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
    def results(self):
        """
        最後にできる結果
        """
        return self.lasts_store.data

    @property
    def caches(self):
        """
        作成したキャッシュ
        """
        return self.cache_store.data

    @property
    def is_datadst(self):
        """
        データデストの場合はTrueを返す
        """
        # いい条件が思い浮かばない,,,
        has_store = any (p for p in self.points if p.is_store)
        return len(self.o_ports) == 0 and len(self.lasts) == 1 and has_store

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
            self.run_invokable_steps(invokable_steps, args)

            # print('invokable_steps2', invokable_steps, self.points)

            # 再度、実行準備が整ったstepのリストを取得しなおす
            invokable_steps = self.search_invokable_steps()

            # print('invokable_steps3', invokable_steps, self.points)

        # 実行すべきrunnableがもう残っていないなら、終了
        return self.make_outputs()

    def prepare_inputs(self, inputs):
        """
        inputsを必要な部分に配置する
        """

        input_points = [p for p in self.points if p.is_for_input]
        # print('aaa', input_points, inputs)
        for input_point in input_points:
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

        # 未実行かつ出力のないサブフローを集める
        last_sub_flows = {p.t_runnable for p in self.points \
                          if not p.is_last and len(p.t_runnable.runnable.o_ports) == 0 and not p.t_runnable.already_ran}

        # lastsと出力のないサブフローを纏める
        last_steps.update(last_sub_flows)

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
        return union(self.search_first_steps_to_run(a.o_runnable) for a in prev_points if a.o_runnable is not None)

    def run_invokable_steps(self, steps, flow_args):
        """
        stepのうち、実行準備が整っている（＝引数が全て揃っている）ものを実行する
        実行後、結果をpointに格納する
        """

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
                        # content（datumのラップ対象、生nysol_moduleなど）を渡すか、datumを渡すかで悩んでいる
                        # datumを渡すと受け手側で必ずinputs['i'].contentみたいにとり出させるのが煩わしかったのでcontent渡している
                        # commandがpointのcontentを知っているのも気持ち悪いし。。。
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

            # 実行を終了したフラグをたてる
            step.already_ran = True

            # それぞれのpointに結果を格納する
            for output_point in output_points:
                # 親フローに結果を戻す場合は戻す
                output_point.datum = result.pop(output_point.o_port.name)
                self.put_datum_in_store(output_point.id, output_point.datum)
                # print('output_point:', output_point)

            # stepがデータデストの場合は、データデスト内のlastsを取得する
            if step.is_datadst:
                for last_frame in step.runnable.lasts.values():
                    self.put_datum_in_store(step.id, last_frame)

            # どうやらf.redirect('u')したものをrunsに入れても実行できないみたい。
            # redirectしたものをm2teeなどのmコマンドと繋げるとrunsで実行できる。
            # なので、今の所ModuleStoreにはRunfuncCommandだけを入れるようにしている。
            from kskp.store import RunfuncCommand
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

    def put_datum_in_store(self, id, datum):
        """
        Cacheなどを後で保存処理を行うためにstoreに入れておく
        """
        from kskp.store import Cache, Frame
        if isinstance(datum, Cache):
            self.cache_store.append(id, datum)
        elif isinstance(datum, Frame):
            self.lasts_store.append(id, datum)

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
        # の様に2つあって、プレビューなどによって片方（例えばd3）だけ使う様な場合、
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

    def get_module_list(self):
        """
        substepsのmoduleをextendして返す
        """
        for substep in self.substeps:
            if isinstance(substep.runnable, Flow):
                self.module_store.extend(substep.runnable.get_module_list())

        return self.module_store.module_list

    def dtor(self):
        self.cache_store.save()
        self.lasts_store.save()
        # 配下のflowのdtorも動かす
        for substep in self.substeps:
            from kskp.store import Command
            if isinstance(substep.runnable, Flow) or isinstance(substep.runnable, Command):
                substep.runnable.dtor()
            else:
                raise Exception('substep.runnableにFlowまたはCommand以外のオブジェクトが格納されています')

class Point:
    """
    o->iの順番なので注意
    """

    def __init__(self, point_id, origin_tubes, datum, target_tubes, cache=False):
        self.id = point_id
        self.label = ''

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
    def is_store(self):
        from kskp.store import Store
        return self.datum is not None and isinstance(self.datum, Store)

    @property
    def o_port(self):
        return self.origin[0].port

    @property
    def o_runnable(self):
        """
        out_runableの略称ではないことに注意!
        """
        return self.origin[0].runnable

    @property
    def t_runnable(self):
        return self.target[0].runnable

    @property
    def is_last(self):
        """
        フローの終端のものかどうか（サブ、rootどちらでも良い）
        targetのrunnableにNoneがある場合は終端となっている
        """
        return any(t_tube.runnable is None for t_tube in self.target)

    @property
    def is_root_last(self):
        """
        rootのフローの終端かどうか
        """
        return any(t_tube.runnable is None and t_tube.port is None for t_tube in self.target)

    @property
    def is_out(self):
        """
        サブフローの終端かどうか
        """
        return any(t_tube.runnable is None and t_tube.port is not None for t_tube in self.target)

    @property
    def is_first(self):
        """
        フローの始端のものかどうか（サブ、rootどちらでも良い）
        """
        return self.o_runnable is None

    @property
    def is_root_first(self):
        """
        rootのフローの始端かどうか
        """
        return self.o_runnable is None and self.o_port is None

    @property
    def is_in(self):
        """
        サブフローの始端かどうか
        """
        return self.o_runnable is None and self.o_port is not None

    @property
    def is_cache(self):
        """
        キャッシュを生成するかどうか
        """
        return self.cache

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

        初期値が[Tube(None, None)]のため、appendするとTube(None, None)が残る
        なので、上書きしている
        """
        if self.is_root_last:
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

    @property
    def is_None(self):
        return self.port is None and self.runnable is None

def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
