import unittest

from kskp.store import Source, add_source, sources()

class StoreTestCase(unittest.TestCase):
    def test_make_datum(self):
        """
        不要な気もする
        """
        pass

    def test_make_frame(self):
        """
        Frameは別モジュールにするべきだろうか？
        実質、同じでいいとも思うけれど(現在、frameしか扱えない)
        """
        frame = Frame()

    def test_make_binary_frame(self):
        """
        直接表形式データを作る
        """
        d = {
            "a": [1],
            "b": [2],
            "c": [3]
        }
        frame = Frame(d)

    def test_make_path_frame(self):
        """
        パスを与えて表形式データを作る……
        はずなのだが、これでpath情報をコンストラクタに与えることになってしまうと、
        以前の設計（datumがsourceを持つ）に戻ってしまう。。。

        つまり、datumの作成とは、常にsourceと一緒に行われるべき？
        うーん、その場合は、frameを作成するコードはどのような形になるのがわかりやすいだろうか？        
        """

        # まずsourceを先に作る？
        path = '/kskp/data/frames'
        path_file_source = PathFileSource(path)

        # そしてそこにframeを入れる？

        # 問題なのは、例えばpathの場合、pathの他にframeを作る意義が存在しないことなんですよね。
        # pathの先にあるファイルがvalidなCSVであるかどうかの判別すらできない。
        # 別にそれはいいんだけど。うーん。
        # だから、sourceごとに追加用メソッドのシグニチャが変わるということ？

        # frame = Frame()

        # これで、実質、新しいframeを追加できる
        path_file_source.add_frame('csv', file_name) 

        # ファイル名をUUIDにするという規約を採用するならば、以下だけでいい
        path_file_source.add_frame('csv')

        # でもcsvは本来、enumだよねきっと(Pythonらしくない、というか見慣れないコード)
        path_file_source.add_frame(FrameKind.CSV)

        # さらに言うなら、普通はCSVはframeにしかならないので、そこらへんはどうなんでしょうね。
        # こんな感じでしょうか。うーん。うーん。中でたくさん分岐を書くのはいやだなあ。
        path_file_source.add_frame(FrameKind.Pandas)

        # これらはファイル/バイナリのどちらかのフォーマットなわけで、
        # そういう意味ではもう少しちゃんと区別したいような気もする
        path_file_source.add_frame(FileFormat.CSV)
        path_file_source.add_frame(BinaryFormat.Pandas)

        # だったらこれらの引数は別のもののはず
        path_file_source.add_frame(fileformat=FileFormat.CSV)
        path_file_source.add_frame(binaryformat=BinaryFormat.Pandas)

        # じゃあ組み合わせも可能？
        # なんとなく、binaryformatの方を先に規定すべきかと(必ず必要なので)
        path_file_source.add_frame(binaryformat=BinaryFormat.Pandas, fileformat=FileFormat.CSV)

        # BinaryFormat.TwoDimList # 二次元リストってもっといい呼び方がないだろうか
        # BinaryFormat.Dict
        # BinaryFormat.Pandas

        # FileFormat.CSV
        # FileFormat.Arrow # Apache Arrowですね
        # FileFormat.PNG
        # FileFormat.JPEG

        # まあ、各々のFormatは実際に必要になった時に指定するのでもいい気はします。
        # その場合は、Undefined、もしくは未指定、が必要。
        # BinaryFormat.Unspecified
        # FileFormat.Unspecified
        path_file_source.add_frame() # それぞれUnspecifiedになる

        # でも、先に指定することに意味はないかなあ。いや、Binaryはあるな。むしろ必須か。
        # ただ、こんなん、見たらわかることでは？instanceofでいけそう。
        # だから、初期データを設定すると勝手に判断してbinaryformatが設定される感じでしょうかね。
        path_file_source.add_frame(binaryformat=BinaryFormat.Dict)

        # 要するに、両方ともあえて設定することはないですね。
        d = {
            "a": [1],
            "b": [2],
            "c": [3]
        }
        path_file_source.add_frame(d) # これで中身はBinaryFormat.Dictになる

        # で、source間の変換は、どうするのか。
        # 肝心のcommand_to_fileは？
        unix_command_source = UnixCommandSource()
        unix_command_source.add_frame(['ls', '-al'])
       
    def test_make_visualizer(self):
        """
        ビジュアライズの結果を持つ
        これはすでに採用が決まっている
        ただし、実際のファイル形式はいくつか候補が考えられるので、そこはどう分けるのかが問題4
        画像
        HTML
        これらは同一のdatumクラスのインスタンスだろうか？
        """
        pass

    def test_add_source(self):
        source = Source()
        add_source(source)

    def test_show_sources(self):
        sources = sources()

    # sourceどうしの型変換（？）はRustでいうところのFromトレイトみたいなものか
    # それぞれはSourceクラスを継承している？Sourceに実質中身がない状態であるならば、
    # 特にSourceクラスも必要なくなる。

    # 一応、incr_

    # 結局、source/generator/datumの3つに分かれるのは確定である。
    # これは概念的な話であって、必ずしもその通りにクラスを分けなければならないわけではない。
    # さて、ただ、ネーミングに困っている。generatorの話だ。別にgeneratorでもいいのかもしれないが。

    # generatorは大げさというか、広すぎる気がしている、というのが理由だ。
    # RDBであれば、クエリだろう。UnixCommandならば、コマンドの列である。
    # なんにせよ、「元の大きなソースから結果のデータを取得するための情報」というものなのだが、
    # これをうまい具合に言い表すtermが欲しいわけです。
    # ちょっとこれは難しいけど、単純に適切な言葉に気が付いていないだけという気もしている。condition？うーん、それでも少し長い。

    # コマンドCommandだと当然まずい。QueryはSQLしか受け付けないっぽいし、UnixコマンドラインをQueryと呼べるのかは疑問。

    # もしくは、上記のソースをStoreにして、GeneratorをSourceと呼ぶ方法もあるのだろうか？