import uuid

from kskp.store import Command
# from kskp.engine.data import Frame

class Job:
    def __init__(self, step, inputs):
        self.step = step
        self.inputs = inputs

        self.errors = []

    def start(self):
        return self.step.runnable.run(self.step.args, self.inputs)

    def dtor(self):
        if isinstance(self.step.runnable, Flow):
            for a in self.step.runnable.arrows:
                if a.datum is not None:
                    pass
                    # print('a.datum:', a.datum)
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定

class Step:
    def __init__(self, id, runnable, args):
        self.id = id
        self.runnable = runnable
        self.args = args

    def __repr__(self):
        return self.id

class Flow:
    def __init__(self):
        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.arrows = []
        self.substeps = []

        self.lasts = {}

    def run(self, args, inputs):
        print('flow inputs:', inputs)

        result = {}

        # print('substeps:', self.substeps)

        for _ in range(len(self.substeps) + 1):
            print('ループ開始')
            # まず、グラフ構造を解析する必要がある
            # beta版同様、lastsを探す

            # 最初に「最後の矢印」を集める
            last_arrows = [a for a in self.arrows if a.cod is None]

            # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
            first_arrows = set()
            for last_arrow in last_arrows:
                first_arrows |= self.search_first_arrows(last_arrow, inputs)

            # 対象のrunnableを集める
            first_steps = {first_arrow.cod for first_arrow in list(first_arrows) if first_arrow.cod is not None}

            # 実行すべきrunnableがもう残っていないなら、終了
            if len(first_steps) == 0:                

                # lastsを設定する
                self.lasts = {a.id: a.datum for a in self.arrows if a.cod is None}
                print('result lasts:', self.lasts)

                # 結果を返却する(lastsとは内容が違う可能性がある)

                # キーを書き換える
                new_result = {}
                for child_o_port_name, val in result.items():                    
                    input_arrow = None
                    for a in self.arrows:
                        if a.o_port is not None and a.o_port.name == child_o_port_name:
                            if a.i_port is not None:
                                new_result.update({a.i_port.name: val})

                # print('result ending:', result)
                print('result ending new:', new_result)                
                return new_result


            # 解析が終わったので、実行開始

            for first_step in first_steps:     
                # jobを作るためにinputsを集める
                inputs = {a.i_port.name: a.datum for a in self.arrows if a.cod == first_step}

                # jobを作る
                job = Job(first_step, inputs)

                # 実行開始
                result = job.start()
                # print('result processing:', result)

                # 結果をそれぞれのarrowに入れる

                # まず、outputのarrowを取得する
                output_arrows = {arrow for arrow in self.arrows if arrow.dom == first_step}                

                # それぞれのarrowに結果を格納する
                for output_arrow in output_arrows:
                    # print('output_arrow:', output_arrow)
                    # 親フローに結果を戻す場合は戻す                    

                    print('result:', result)                                  
                    output_arrow.datum = result[output_arrow.o_port.name] 

        # 通常はここは通らない
        return None

    def search_first_arrows(self, target, inputs):
        """
        与えられた引数からフロー構造を逆に辿って、
        もっとも先頭のarrowを見つけ出す
        """
        
        # データがすでに存在する場合は走査を打ち切る
        if target.datum is not None:
            return {target}
        
        # 親フローからデータが渡ってきた場合はそれを受け取ってセットする
        # 条件は "o_portがあるのにdom stepが存在しない"
        # (通常は出口がある以上、その基になるdom stepが必ず存在する)
        if target.dom is None:
            if target.o_port is not None:
                target.datum = inputs[target.o_port.name]
                return {target}
            else:
                # ここを通るということはフローの先頭なのに元のデータもないし、
                # かつ、親フローからのデータ受取口でもないということ
                # 正しい状態ではないのでエラー
                # エラー情報はのちほど追加
                raise Exception()

        prev_arrows = {arrow for arrow in self.arrows if arrow.cod == target.dom}
        prev_arrows_new = set()
        for prev_arrow in prev_arrows:
            # print('prev_arrow これで再帰を目論む:', prev_arrow)
            r = self.search_first_arrows(prev_arrow, inputs)
            # print('prev_arrow 再帰を目論んだ結果:', r)
            prev_arrows_new |= r

        # print('prev_arrows_new:', prev_arrows_new)

        return prev_arrows_new

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
            dom_o = f"{self.dom}.{self.o_port.name}"
        else:
            dom_o = self.dom
        if self.i_port is not None:
            cod_i = f"{self.cod}.{self.i_port.name}"
        else:
            cod_i = self.cod

        return f"{self.id}, {dom_o} -> {cod_i}"
            

class UnixCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        source = self.source(args, inputs)
        # for input in inputs.values():
        #     if isinstance(input.source, PathFileSource):
        #         source.deletable_uuids.append(input.uuid)
        #     elif isinstance(input.source, UnixCommandSource) or \
        #          isinstance(input.source, PandasSource) or \
        #          isinstance(input.source, NysolPythonSource):
        #         source.deletable_uuids = input.source.deletable_uuids
        #         source.deletable_uuids.append(input.uuid)
        frame = Frame(str(uuid.uuid4()), source)
        return { self.out_key: frame }

    def source(self, args, inputs):
        """ for override """
        raise Exception()

    def command_args(self, args, inputs):
        """ for override """
        raise Exception()

    def stdin(self, inputs):
        print('inputs:', inputs)
        return list(inputs.values())[0].source.fd

class FlowUuidLink:
    def resolve(self):
        return Flow()
