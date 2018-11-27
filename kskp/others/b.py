import io
import sys
import nysol.mcmd as nm
import re

dat=[
["customer","date","amount"],
["A","20180101",5200],
["B","20180101",800],
["B","20180112",3500],
["A","20180105",2000],
["B","20180107",4000]
]

class ErrorInfo():
    def __init__(self, description, input, output, called_at):
        self.description = description
        self.number_of_input = input
        self.number_of_output = output
        self.called_at = called_at

    @classmethod
    def parse_stderr(cls, s):
        """
        以下のようなMCMDの実行時のエラー文字列をparseしてオブジェクトに起こす
        '#ERROR# field name not found: `c' in a.csv (kgcut); kgcut f=c i=a.csv; IN=0 OUT=0; 2018/06/14 20:57:21'
        """
        # s = "#ERROR# field name not found: `c' in a.csv (kgcut); kgcut f=c i=a.csv; IN=1253 OUT=5624; 2018/06/14 20:57:21"
        # まず、セミコロンで区切る
        ss = s.split(';')

        # 入力と出力の件数をパースする
        io = re.search(r'IN=(\d+) OUT=(\d+)', ss[2]).groups()

        return cls(ss[0].replace('#ERROR# ', ''), int(io[0]), int(io[1]), ss[3])

class MCMDError(Exception):
    def __init__(self, errors):
        self.errors = errors

class Command():
    pass

class Mcut(Command):
    def __init__(self):
        pass

    def execute(self):
        with io.StringIO() as output:
            oldstderr = sys.stderr
            sys.stderr = output        
            r = nm.mcut(i=dat, f='customer,date', x=True).run()            
            contents = output.getvalue()
            sys.stderr = oldstderr

            if len(contents) > 0:                
                errors = []
                for content in contents.split('\n'):
                    # print('mcut error:', content)
                    if '#ERROR#' in content and '#ERROR# ; kgshell' not in content:
                        errors.append(ErrorInfo.parse_stderr(content))

                if len(errors) > 0:
                    raise MCMDError(errors)
            else:
                return r

class Mselstr(Command):
    def execute(self):
        with io.StringIO() as output:
            oldstderr = sys.stderr
            sys.stderr = output        
            r = nm.mselstr(i=dat, f='date', v='20180101').run()
            contents = output.getvalue()
            sys.stderr = oldstderr

            if len(contents) > 0:                
                errors = []
                for content in contents.split('\n'):
                    print('mselstr error:', content)
                    if '#ERROR#' in content and '#ERROR# ; kgshell' not in content:
                        errors.append(ErrorInfo.parse_stderr(content))
                
                if len(errors) > 0:
                    raise MCMDError(errors)
            else:
                return r

# 起こった複数のエラーを集めたい、と漠然と今まで考えていたのだが、
# 上のように作ってみると、実は最初のエラーが起きた時点で例外を出せるのであり、そこで処理は中断する。
# したがって、複数のエラーが同時に生成されるという状況を考えないといけない。

# 思い返してみると、非同期的にエラーが発生するようなイメージがあった。
# つまり、お互いに独立性の高いタスクが二つほぼ並行で処理されるのであれば、
# 報告したいエラーが複数、同時に起こりうるのではないか。

from concurrent import futures

class Multi(Command):
    def execute_mcmd(self, cc):
        
        try:            
            if cc == 1:
                print('execute mcut')
                mcut = Mcut()
                r = mcut.execute()
                print(r)
            else:
                print('execute mselstr')
                mselstr = Mselstr()
                r2 = mselstr.execute()
                print(r2)

        except Exception as e:
            print('エラーだよ:', e)

    def execute(self):
        with futures.ProcessPoolExecutor() as executor:
            res = executor.map(self.execute_mcmd, [1, 2])

multi = Multi()
multi.execute()


# 困った。#ERROR#が一回のエラーで複数出る。
# no data foundがまず出て、次にメインっぽいエラー。
# しかしどちらがメインなのか、人間が見て判断はできるが、客観的な基準がないかもしれない。
# ということで、これらの情報を複数持つにはどうしたらいいのだろう。
# リストで持つのだが、それは1つのMCMDErrorの中にリストを持つのか、それとも
# MCMDErrorとエラー行は1対1に対応すると決めるのか、というのが主な論点になると思われる。
# でも一回分だし、リストにするか。。。

# リストにしました。


# で、次に何をすべきか。
# どうもここのあたりがはっきりしないので、コーディングは簡単なのに先に進まない印象。

# エンジン -> トップジョブ？（と勝手に呼ぶ、一番親のjob）-> その下のjob
# エラー情報はjobに持つことになる？


class Job:
    def __init__(self, command_or_flow, args, proxy):
        self.errors = []
    
    def start(self):
        pass

# ちなみにエンジンはどうなるんだったっけ？
# そうだ、Flowの一意性をどうやって確保するのか、という話だった。    
# それをUUIDだけに固定しないために、linkという概念を新しく追加したのだった。
# ということは、どういうこと？
# 自分で図を書いたつもりだったが、今見返してみると細部はよくわからんな。。。

# ともかく、linkを追加して柔軟性を確保したことによって、エンジンの呼出部分はどうなったのか、ということが今の主題。
# もともとは、以下のように書いている。

    """
    指定したフローを実行する

    json内の記法が原因で、flowやframeのパスがないと、外部のflowやframeが呼べなくなっている。
    だから、環境変数が存在することは仕方ないようにも思える。そこを変更してもコストの割にメリットがない。一貫性があるだけだ。
    そういう意味では、「flowインスタンスは、uuidで一意に特定されることを前提としている」と言って差し支えない。

    「デフォルトでは」uuidに沿って読み出すファイルのパスが決まっている。
    いざとなればディレクトリや詳しいパスを指定できるようにオプションを追加予定。
    もしくは、直接中身のJSONを書けるようにしてもいいかもね。
    それぞれexecute_json/execute_json_file/execute_flowに対応するという感じで。

    execute_json(obj)
    execute_json_file(path)
    execute_flow(flow_uuid)
    """

# executeはlinkを持つようにしたい、というのと実質同じ内容を、すでにここにも書いている。
# 結局、上記の3つのパターンは、execute_flow(link)に集約されるということだろうか。
# linkにUUIDLink / JSONPathLink / JSONLink / FLowLink みたいなのがあるということか。
# 昔もこういう設計したなあ。しかしちょっと細かいので、あんまり表には出したくないな。これはいざという時のための設計なので。
# 露骨に切替可能なIFにすると、ちょっとうるさい感じになってしまう。

# ともかく、LinkクラスにはFlow/Commandを生成する能力があればいい。
# つまり、出来上がったクラスがexecuteメソッドを持っていればいい。

# 厳密にクラスを分けるよりは、与えられたものの中身を見て処理を切り替えた方がPythonっぽいだろうか。
# ちょっとFluent Pythonを見てみることにする。

# どうやら、Duck TypingはPythonicと言っても大丈夫そうだが、
# 別にinstanceofを使うことはあまりオススメしていないようだ。つまり、型をチェックして分岐する、ということ。
# だったら、あくまでもexecuteメソッドを持つクラスを生成するクラスであれば問題ないということか。
# その「生成する」メソッドに名前をつけたいな。
# linkが参照先の実態を解決するわけなので。unboxという感じでしょうか。まずは暫定で。
# あとは、resolve。リンクに飛ぶ、ならjumpだけど、わかりにくいか。
# この中だと普通なのはresolveだね。


# というわけで、簡単な例。
# Bはlinkと言って良い。
def run_flow_by_uuid(uuid, args, inputs):
    b = B(uuid)
    run(b, args, inputs)

class A():
    def execute(self, args, inputs):
        pass

class B():
    def __init__(self, flow_uuid):
        self.flow_uuid = flow_uuid

    def resolve(self):
        return A()

def run(link, args, proxy):
    job = Job(link.resolve(), args, proxy)
    job.start()

# proxyからinputsを作るメソッドが必要。proxy.make_inputs()とか。
# ここでは、inputsそのものにもmake_inputs()をつければいいんかな。
# それとも、jobにはそのままinputsを渡せばいいんかな。
# いや、proxyのまま渡して、jobの実行時にそれらがinputsになるということですね。
# 仮に、先にinputsを入れるとすると、単体で結果が計算できるということになってしまうので、
# 木構造のインタプリタをワンパス処理するということになってしまう。

# jobはスタートすると、linkは解決されてexecutableになっている。
# そこにargsを設定して、proxyからinputsを作り出す。ここも何か欲しいなあ。
# しかし考えてみると、proxyという名前はふさわしくないかもね。
# 入力を産むもの。でもsourceは使ってしまっているなあ。

# adjacentという用語があるのを知った。