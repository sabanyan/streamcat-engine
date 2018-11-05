import unittest
# import uuid

from kskp.store import Command
from kskp.engine import execute, Flow, Step
# from kskp.engine.data import PathFileSource, Frame
# from kskp.mcmd import McmdLink

class EngineTestCase(unittest.TestCase):
    def test_empty_command(self):
        """
        仮想的にコマンドを作成して動かす
        """

        class TestCommand(Command):
            def run(self, args, inputs):
                print('i am test command!')
                return {}

        class EmptyLink:
            def resolve(self):
                return TestCommand()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    def test_empty_flow(self):
        """
        仮想的にフローを作成して動かす
        """

        class EmptyLink:
            def resolve(self):
                return Flow()

        result = execute(EmptyLink(), {}, {})
        self.assertEqual(result, {})

    def test_flow_with_one_runnable(self):
        """
        runnableが1つだけのフローを作成して動かす        
        """

        # 各flowを表すJSONファイルの構造としては、stepをたくさん持っている形になっている。
        # そして、stepはその下にrunnableへのlinkを持っている。

        # 仮に、上記構造をそのままPythonで表現するとなると、flow.stepsと、各々のstepの中にrunnableが存在することになる。
        # 例えばflow.steps[0].resolve().run()のように使うことになる。

        # ただし、実際にはflow.stepsは属性として不要。JSONをパースした時点で、
        # job.subjobsという風になるのが良さそう（この仕様だとkskp-betaの時と変わらない）。

        # 今回のパターンだと、具体的にどのような手順で解析が進むのかを考えてみよう。
        # job.start()時に、subjobsをそれぞれ連動してstart()する必要があるだろう。

        # 1. 対象フローをlastsから逆に辿って解析する。
        #    各jobごとのsubjobsもここで設定される。
        # 2. その構造をいったん、Pythonのデータ構造として保存する（？）。
        # 3. 然るべき場所から実行を開始する。
        # （必要であれば、マルチコアの割り振りも行う）


        # 仕様を考える上で理解ができていない部分がある。
        # job.subjobsを設定した時点で初めてjob.start()ができるようになるとすると、
        # パースした時点でjobが全て出来上がっている必要がある。
        # それらを解決するには、FlowLinkに最初からargsやinputsも渡す必要がある？

        # 上記の問題を言い換えると、おそらく、こうだろう。
        # FlowLinkは、resolve()されるとFlowを返すのだが、
        # 実際に必要な処理の流れとしては、rootのjobのsubjobsで

        # core3.pyでのparse_jobの引数は以下。        
        #
        # def parse_job(obj, flow_uuid, args, srcs, dsts, inputs):
        # rootjobならば、最後4つはほぼ空dict{}

        # flow_uuidがあればFlowLinkにはなる。
        # argsとinputsも当然（？）コンストラクタに入れれば良いかと。
        # 問題はsrcsとdstsだ。arrowの領域。
        # 引数の数だけarrowができる。

        # JSON内のsrcs, dstsはarrowに使われる印象。
        # まず、各stepを包むjobが作られて、それに対してsrcs,dstsからarrowが作成され、作ったばかりのjobに追加される。

        # というか、JSONのパース手順は、結構、単純に以下を行えばいいだけではないのか。
        # 1. 各nodeに対して、それがstepであればjobを作り、そうでなければarrowを作る。
        # 2. 1で作成したjobそれぞれで、対応するstepのsrcやdstsから、arrow.domやarrow.codを設定する。

        # 上記の方法と結果としては同じことだが、先にarrowを、後にstepを処理すればパース回数が減るような気がする。
        # いやまあ、大差ない気もしてきた。

        # 単純に1枚のフローだけを読むのであればいいが、実際にはrunnableにはlinkが貼ってある。これをどう扱うか。
        # 質問の仕方を変えると、runnableへのlinkが解決されるのは、JSONパース時？フロー解析時？フロー実行時？

        # ジョブを作成するためには、runnableへのlink、そこから伸びるinputsとarrow、そしてデータ。
        # JSONパース後の、フロー解析時にまず行うのは、lastsを探すこと。
        # そこからarrowを伝って、開始地点を探す。ここまでがフロー解析。

        # なんとなく、処理の順番として、flowがarrowsを持ってもいい気がしてきた。
        # （持たなくても、JSONオブジェクト内にあるので不要といえば不要）
        # arrowは共有する必要がある。

        # 具体例で考えてみよう。
        # 1つのinputと1つのoutputを持つcommandを持つflowをパースする場合。
        # jobは1つ。arrowは2つ。どちらを先に作るべき？
        # それともそこまで気にする必要はないんかな。
        # jobを作るときに、nestする可能性があるのがややこしいな。
        # あくまで、stepにぶら下がっているのはその時点では解決前のlinkに過ぎないので。

        # flowlinkから作成可能なのは、まずはsubjobs。それを返却して、自分を包むjobに持ってもらう。

        # お昼休みで考えていたが、以下の順番で進めることにしよう
        class TestCommand(Command):
            def run(self, args, inputs):
                print('i am test command!')
                return {}        

        class FlowLink:
            def resolve(self):
                flow = Flow()
                step = Step(TestCommand(), {})
                flow.steps.append(step)
                return flow
        
        result = execute(FlowLink(), {}, {})
        self.assertEqual(result, {})

    # def test_mcut(self):    
    #     s = PathFileSource('csv', '', 'a.csv')
    #     f = Frame(uuid.uuid4(), s)
    #     result = main.execute(McmdLink('mcut'), {'f': 'b,c'}, {'i': f})
    #     self.assertEqual(result, {})