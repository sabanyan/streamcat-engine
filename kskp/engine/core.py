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

    def update_src_points(self, node_id, tube):
        """
        指定したnode_idとtubeでpointsを更新する
        """
        # 対象のpointがすでに存在すればそれを取得する
        if node_id in self.point_ids:
            src_point = self.get_point_by_node_id(node_id)
            src_point.update_target(tube)
        else:
            src_point = Point(node_id, [Tube(None, None)], None, [tube])
            self.points.append(src_point)

        # inを外に出しているサブフローの場合は、
        # てっぺんのPointのorigin.portを、外に出しているポート名にする
        if len(self.i_ports) > 0 and src_point.is_first:
            for i_port in self.i_ports:
                # 今は「フローのi_port名」＝「datum_id（pointのid）」なのでこの条件にしている
                if i_port.name == src_point.id:
                    src_point.update_origin(Tube(i_port, None))

    def update_dst_points(self, node_id, tube):
        """
        指定したnode_idとtubeでpointsを更新する
        """
        # 対象のpointがすでに存在すればそれを取得する
        if node_id in self.point_ids:
            dst_point = self.get_point_by_node_id(node_id)
            dst_point.update_origin(tube)
        else:
            dst_point = Point(node_id, [tube], None, [Tube(None, None)])
            self.points.append(dst_point)

        # outを外に出しているサブフローの場合は、末端のPointのtarget.portを
        # 外に出しているポート名にする
        if len(self.o_ports) > 0:
            for target in dst_point.target:
                if target.port is None and target.runnable is None:
                    for o_port in self.o_ports:
                        # 今は「フローのo_port名」＝「pointのid（datum_id）」なのでこの条件にしている
                        if o_port.name == dst_point.id:
                            dst_point.update_target(Tube(o_port, None))

    def update_point_by_value(self, node_id, value):
        """
        指定したnode_idをもつpointのdatumをvalueで置き換える
        """
        target_point = self.get_point_by_node_id(node_id)
        target_point.datum = value

    def pick_necessary_points(self, last_ids):
        """
        プレビュー実行するのに必要なpointを取得する
        今はプレビュー対象のdatumで終わるように、プレビュー対象pointのtargetのtubeをNone,Noneにしている。（正しいんかな？）
        """
        necessary_points = []
        for id in last_ids:
            for point in self.points:
                if point.id == id:
                    if not len(self.o_ports) > 0:
                        point.target = [Tube(None, None)]
                    last_point = point
                    break

            necessary_points = necessary_points + self.search_necessary_point(last_point)
            necessary_points.append(last_point)

        self.points = list(set(necessary_points))

    def search_necessary_point(self, current_point):
        """
        プレビューするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、origin.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のorigin.runnableをtarget.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        points = []
        # current_pointの上につながっているPointを探す
        for point in self.points:
            for p_target in point.target:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）
                # print('p_target:',id(p_target.runnable), 'current_point:',id(current_point.o_runnable))
                if p_target.runnable is current_point.o_runnable:
                    points.append(point)
                    # TODO: どこまで登るかを判定している場所、もっといい書き方ある…と思う
                    if point.datum is None and not point.is_first:
                        # 上にrunnableがある限りは登り続ける
                        points = points + self.search_necessary_point(point)

        return points

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
