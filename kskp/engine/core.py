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

class Flow:
    def __init__(self):
        self.i_ports = []
        self.o_ports = []
        self.params = []

        self.arrows = []
        self.substeps = []

        self.lasts = {}

    def run(self, args, inputs):
        result = {}

        print('substeps:', self.substeps)

        for _ in range(len(self.substeps) + 1):
            print('ループ開始')
            # まず、グラフ構造を解析する必要がある
            # beta版同様、lastsを探す

            # 最初に「最後の矢印」を集める
            last_arrows = [a for a in self.arrows if a.cod is None]

            print('last_arrows:', last_arrows)

            # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
            first_arrows = set()
            for last_arrow in last_arrows:
                first_arrows |= self.search_first_arrows(last_arrow)

            print('first_arrows:', first_arrows)

            # 対象のrunnableを集める
            first_steps = {first_arrow.cod for first_arrow in list(first_arrows) if first_arrow.cod is not None}

            print('first_steps:', first_steps)
                
            # 実行すべきrunnableがもう残っていないなら、終了
            if len(first_steps) == 0:                

                # lastsを設定する
                self.lasts = {a.id: a.datum for a in self.arrows if a.cod is None}
                print('result lasts:', self.lasts)

                # 結果を返却する(lastsとは内容が違う可能性がある)
                # TODO: これはサブフローとして使われるのならば、keyを戻す必要がある
                print('result ending:', result)
                return result


            # 解析が終わったので、実行開始

            for first_step in first_steps:     
                # jobを作るためにinputsを集める
                inputs = {a.i_port.name: a.datum for a in self.arrows if a.cod == first_step}

                # jobを作る
                job = Job(first_step, inputs)

                # 実行開始
                result = job.start()
                print('result processing:', result)

                # 結果をそれぞれのarrowに入れる

                # まず、outputのarrowを取得する
                output_arrows = {arrow for arrow in self.arrows if arrow.dom == first_step}
                print('output_arrows:', output_arrows)

                # それぞれのarrowに結果を格納する
                for output_arrow in output_arrows:
                    # print('output_arrow:', output_arrow)
                    output_arrow.datum = result[output_arrow.o_port.name]            
                    # print('output_arrow.datum:', output_arrow.datum)

        # 通常はここは通らない
        return None

    def search_first_arrows(self, target):
        """
        与えられた引数からフロー構造を逆に辿って、
        もっとも先頭のarrowを見つけ出す
        """
            
        # 最後のデータがすでに存在する場合は走査を打ち切り、空のsetを返すことにする
        if target.datum is not None or target.dom is None:
        # if target.dom is None:
            # print('prev_arrows end:', target)
            return {target}

        prev_arrows = {arrow for arrow in self.arrows if arrow.cod == target.dom}
        prev_arrows_new = set()
        for prev_arrow in prev_arrows:
            # print('prev_arrow これで再帰を目論む:', prev_arrow)
            r = self.search_first_arrows(prev_arrow)
            # print('prev_arrow 再帰を目論んだ結果:', r)
            prev_arrows_new |= r

        # print('prev_arrows_new:', prev_arrows_new)

        return prev_arrows_new

class Step:
    def __init__(self, id, runnable, args):
        self.id = id
        self.runnable = runnable
        self.args = args

    def __repr__(self):
        return self.id

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
        return f"{self.id}, {self.dom} -> {self.cod}"
            

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
