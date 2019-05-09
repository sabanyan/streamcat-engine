import uuid
import json
from pathlib import Path
from kskp.core import Command, Datum
from datetime import datetime, timedelta, timezone

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
            # 今のFlowのdtorは、cacheやlastsを保存しているだけ
            self.step.runnable.dtor()

            for point in self.step.runnable.points:
                if point.datum is not None:
                    pass
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定

# TODO: kskp-data-storeに移す
class Store(Datum):
    """
    できたdatumを入れておく場所
    """
    def __init__(self):
        super().__init__()
        self.data = {} # dict keyはUUID、valはdatum？

    def issue_uuid(self):
        """
        uuidを発行する
        """
        new_uuid = str(uuid.uuid4())
        self.data[new_uuid] = None
        return new_uuid

    def set_datum(self, datum, uuid):
        """
        指定したuuidとdatumを対応づけて保存しておく
        """
        if self.data[uuid] is None:
            self.data[uuid] = datum
        else:
            # 上書きするか、Falseを返すかどうしよう？
            pass

        return True

    def save(self, datum):
        """
        override用
        """
        pass

    def load(self, uuid):
        """
        override用
        """
        pass

class Folder(Store):
    """
    ディレクトリに保存するStore
    コンストラクタで指定したディレクトリに保存する
    指定したディレクトリパスはpathlibのPathオブジェクト
    """
    def __init__(self, dir_path):
        super().__init__()
        self.dir_path = dir_path

    def save(self, args, datum, uuid):
        import nysol.mcmd as nm
        self.set_datum(datum, uuid)

        args['frame_path'] = (self.dir_path / (uuid + '.csv'))

        command_args = {}
        command_args['i'] = datum
        command_args['o'] = args['frame_path'].as_posix()

        return nm.m2tee(command_args)

    def load(self, uuid):
        import nysol.mcmd as nm

        # TODO: 本当はuuidを使ってdbからcsvの場所を取ってくる
        # 今はとりあえず直接取ってくる(uuid==csvのファイル名)
        path = None
        for flow_path in self.dir_path.iterdir():
            if flow_path.stem == uuid:
                path = flow_path
                break

        nysol_module = NysolModule()
        nysol_module.set_content(nm.m2tee({'i':path.as_posix()}))

        return nysol_module

    @property
    def content(self):
        return self

class FrameStore(Store):
    """
    Frameを置いておくStore
    """
    def __init__(self):
        super().__init__()
        self.datum_list = []

    def save(self):
        for cache in self.datum_list:
            cache.save()

    def append(self, cache_point):
        self.datum_list.append(cache_point)

class NysolModule(Datum):
    """
    NysolModule1をラップするクラス
    """
    def __init__(self):
        super().__init__()
        self._content = None

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

class Frame(Datum):
    """
    実際の実行のrunではない時に作られ、DB保存の情報を持っている。
    storeに一旦集められてから、jobのdtorのタイミングでDBへの保存処理が走る。

    storeのメソッド内で保存しようと思ったけど、わざわざFrame（または下記のCache）クラスの中身を見て
    それを取り出して保存するのも手間が増えてるだけなので、今はstoreのsaveでこのクラスのsaveを呼び出すことにしている。
    """
    def __init__(self):
        super().__init__()
        self.info = {}

    def set_uuid(self, uuid):
        self.uuid = uuid

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

    def set_cache_info(self, params):
        self.info = params

    def save(self):
        # キャッシュが作成されているか確認
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

    def save_to_db(self):
        # TODO: DBと連携するようになったら処理を記載する
        # この2つがあれば最低限登録できる・・・と思っている。。。
        # uuid・・・self.uuid
        # path・・・self.info.get('dir_path')（saverで付与済み）
        pass

    @property
    def created(self):
        if self.info.get('frame_path') is not None:
            return self.info.get('frame_path').exists()
        else:
            return False

class Cache(Frame):
    """
    FrameもCacheもどちらも実ファイルを生成するdatumであり、
    違いはflowのjsonを書き換えるか書き換えないか（今の所）
    ということでFrameを継承したものにしてみた。
    """
    def __init__(self):
        super().__init__()

    def save(self):
        # キャッシュが作成されているか確認
        if not self.created:
            # とりあえずfalseを返す
            return False

        # dbに保存
        self.save_to_db()

        # jsonのnodeのuuidを変更
        self.update_json_node()

    def update_json_node(self):
        if self.info.get('flow_uuid') is None:
            return

        flow_path = [path for path in Path('kskp/flows').iterdir() if path.stem == self.info.get('flow_uuid')][0]
        flow_json = json.loads(flow_path.read_text())
        for node in flow_json['nodes']:
            if node['id'] == self.info.get('datum_id'):
                node['uuid'] = self.uuid
                node['cacheCreatedAt'] = datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%Y-%m-%d %H:%M:%S')
        flow_path.write_text(json.dumps(flow_json, ensure_ascii=False, indent=2), encoding='utf-8')

class Step:
    def __init__(self, id, runnable, args):
        self.step_id = id
        self.runnable = runnable
        self.args = args

    def __repr__(self):
        return self.step_id

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

                r = re.search(r'@\[(\S*?)\]', step_value)

                if r is None:
                    continue

                for g in r.groups():
                    if param == g:
                        self.args[step_param] = step_value.replace(f'@[{g}]', value)

class Flow(Datum):
    def __init__(self):
        super().__init__()

        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.points = []
        self.substeps = []

        # TODO:Flowに持たせるのではなく、どこか共通の場所にする
        self.cache_store = FrameStore()
        self.lasts_store = FrameStore()

    @property
    def lasts(self):
        # lasts = {}
        # for p in self.points:
        #     for t_tube in p.target:
        #         if t_tube.runnable is None:
        #             lasts[p.point_id] = p.datum

        # return lasts
        return {p.point_id: p.datum for p in self.points if any(t_tube.runnable is None for t_tube in p.target)}

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
        last_steps = {p.o_runnable for p in self.points if any(t_tube.runnable is None and p.datum is None for t_tube in p.target)}

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

        # print('steps in run_invokable_steps:', steps)

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
            step.runnable.context['step_id'] = step.step_id
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
                self.put_datum_in_store(output_point.datum)
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

    def put_datum_in_store(self, datum):
        """
        Cacheなどを後で保存処理を行うためにstoreに入れておく
        """
        if isinstance(datum, Cache):
            self.cache_store.append(datum)
        elif isinstance(datum, Frame):
            self.lasts_store.append(datum)

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
        return [point for point in self.points if point.point_id == node_id][0]

    def select_point_by_id(self, id):
        """
        self.pointsの中から
        指定したidのpointを取得する
        """
        for point in self.points:
            if point.point_id == id:
                return point

    def dtor(self):
        self.cache_store.save()
        self.lasts_store.save()
        # 配下のflowのdtorも動かす
        for substep in self.substeps:
            if isinstance(substep.runnable, Flow):
                substep.runnable.dtor()

class Point:
    """
    o->iの順番なので注意
    """

    def __init__(self, id, origin_tubes, datum, target_tubes, cache=False):
        self.point_id = id

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
            return f"{self.point_id}<{dom_o} -> {cod_i}>"
        else:
            return f"{self.point_id}<{dom_o} -({self.datum})-> {cod_i}>"

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
        フローの終端のものかどうか（サブ、rootどちらでも良い）
        """
        return self.target[0].runnable is None

    @property
    def is_root_last(self):
        """
        rootのフローの終端かどうか
        """
        return self.target[0].runnable is None and self.target[0].port is None

    @property
    def is_out(self):
        """
        サブフローの終端かどうか
        """
        return self.target[0].runnable is None and self.target[0].port is not None

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

def union(sets):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r
