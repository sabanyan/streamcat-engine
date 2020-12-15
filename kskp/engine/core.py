from kskp.store import Datum

class Job:
    def __init__(self, step, inputs):
        self.step = step
        self.inputs = inputs

        self.errors = []

    def start(self):
        try:
            return self.step.run(self.inputs)
        except Exception as e:
            self.errors.append(e)
            raise

    # def runs(self):
    #     """
    #     runsを実行する
    #     """
    #     try:
    #         last_modules = []
    #         for point_datum in self.step.runnable.results.values():
    #             last_modules.append(point_datum.content)

    #         module_list = self.step.runnable.get_module_list()
    #         last_modules.extend(module_list)

    #         # import pprint
    #         # pprint.pprint('runs :')  
    #         # pprint.pprint(last_modules)

    #         # 実行
    #         import nysol.mcmd as nm
    #         nm.runs(last_modules, msg='on')
    #     except Exception as e:
    #         self.errors.append(e)
    #         raise

    def dtor(self):
        # Tmpファイルを削除する
        from kskp.core import Tmp
        Tmp.remove_files()

        if isinstance(self.step.runnable, Flow):
            # 今のFlowのdtorは、cacheやlastsを保存しているだけ
            self.step.dtor()

            for point in self.step.runnable.points:
                if point.datum is not None:
                    pass
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定

class Step:
    def __init__(self, step_id, runnable, args, i_ports=None, o_ports=None, ex_acceptable=False):
        self.id = step_id
        self.runnable = runnable
        self.args = args
        # 入力データが例外の場合、コマンドに渡すか否か
        self.ex_acceptable = ex_acceptable
        # コマンドのPortが'*'の場合、実行時にPortが展開されるので、Stepにもその情報を持たせる
        self.i_ports = i_ports or runnable.i_ports
        self.o_ports = o_ports or runnable.o_ports

    def __repr__(self):
        return self.id

    @property
    def is_flow(self):
        return isinstance(self.runnable, Flow)

    @property
    def is_datadst(self):
        return self.is_flow and self.runnable.is_datadst

    def run(self, inputs):
        """
        コマンドを実行する
        (コマンドの実行で例外が送出されても、最後のコマンドまで実行する)
        """
        from kskp.store import CommandException

        def make_exception_outputs(o_ports, cmd_ex):
            """
            全ての出力ポートに例外を格納する
            """
            outputs = {}
            for o_port in o_ports:
                outputs[o_port.name] = cmd_ex
            return outputs

        try:
            if not self.ex_acceptable:
                # 入力データに1つでも例外があれば、全ての出力ポートに例外を格納する
                for input in inputs.values():
                    if isinstance(input, CommandException):
                        return make_exception_outputs(self.o_ports, cmd_ex=input)
            
            # コマンドを実行する
            return self.runnable.run(self.args, inputs)
        except AttributeError as e:
            raise e
        except Exception as e:
            # 
            # TODO: コマンドからの例外は全てCommandExceptionとしたい
            #

            import traceback
            traceback.print_exc()

            # コマンドのrun()から例外が送出された場合、全ての出力ポートに例外を格納する
            return make_exception_outputs(self.o_ports, cmd_ex=CommandException(e))

    def dtor(self):
        self.runnable.dtor(self.args)

    def replace_args(self, flow_args):
        """
        自身のargsにフロー変数を使っている箇所があれば、argsの値で置き換える

        FIXME?: フロー変数を書き換えるのはStep以外でもいいが、
        早めに書き換えたかったので、とりあえずStepに記載してある
        """
        
        # TODO: 正規表現やreplace対象を外に出す。
        for param, value in flow_args.items():
            for step_param, step_value in self.args.items():                
                if isinstance(step_value, str):
                    # 文字列の場合は通常通り置換を行う
                    self.replace_arg_internal(self.args, param, value, step_param, step_value)
                elif isinstance(step_value, list):
                    # リストの場合は、リストの要素それぞれに対して置換を行う
                    for list_value in step_value:
                        if isinstance(list_value, dict):
                            # リストの要素がDictの場合
                            for list_value_dict_key, list_value_dict_val in list_value.items():
                                self.replace_arg_internal(list_value, param, value, list_value_dict_key, list_value_dict_val)
                        else:
                            # リストの要素がDict以外の場合(msimとmsummary)
                            for list_value_dict_val in list_value:
                                self.replace_arg_internal(list_value, param, value, step_param, list_value_dict_val)                       

    def replace_arg_internal(self, args, param, value, step_param, step_value):
        """
        特定のargのペア（いわゆるオプションのキー名と値）に
        変数名（e.g. @[variable]）が入っている場合には、
        実際に与えられた値で置き換える

        param/value 親フローに与えられた値、いわば「実引数」
        args/step_param/step_value それぞれのstepに与えられた「仮引数」        
        """
        import re        
        for r in re.finditer(r'@\[(\S*?)\]', step_value):
            if r is None:
                continue

            for g in r.groups():
                if param == g:
                    args[step_param] = args[step_param].replace(f'@[{g}]', value)


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
        # いい条件が思い浮かばない,,,
        has_store = any (p for p in self.points if p.is_store)
        return len(self.i_ports) == 1 and len(self.lasts) == 2 and has_store

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
            from kskp.store import Command
            if isinstance(substep.runnable, Flow) or isinstance(substep.runnable, Command):
                substep.dtor()
            else:
                raise Exception('substep.runnableにFlowまたはCommand以外のオブジェクトが格納されています')

class Point:
    """
    o->iの順番なので注意
    """

    def __init__(self, point_id, origin_tubes, datum, target_tubes, is_in=False, is_out=False, cache=False):
        if point_id is None:
            raise Exception('point_idにNoneは指定できません')

        self.id = point_id
        self.label = ''

        self.origin = origin_tubes
        self.datum = datum
        self.target = target_tubes

        # フローの入力ポートか
        self.is_in = is_in
        # フローの出力ポートか
        self.is_out = is_out
        
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

    def __hash__(self):
        # PointをDictのキーとして扱う場合同じインスタンスで同じとみなす
        return id(self)

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

    def __repr__(self):
        return f'({self.port.name}, {str(self.runnable)})'

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
