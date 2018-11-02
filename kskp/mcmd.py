import re # for MCMDError

from kskp.engine.core import Command, UnixCommand, Parameter, Port
from kskp.engine.data import UnixCommandSource

class McmdLink:
    def __init__(self, id):
        self.id = id

    def resolve(self):
        if self.id == 'mcut':
            return McutOld()
        else:
            return Command()

class MCommand(UnixCommand):

    def command_args(self, args, inputs):
        res = self.name.split()
        for k, v in args.items():
            # booleanに対応していないのでひとまず
            if k == 'x':
                if v == True or v == "true":
                    res.append('-x')
            elif k == 'rng':
                if v == True:
                    res.append('-rng')
            elif k == 'r':
                if v == True or v == "true":
                    res.append('-r')
            else:
                res.append('%s=%s' % (k, v))
        return res

    # @property
    def source(self, args, inputs):
        return UnixCommandSource('csv', self.command_args(args, inputs), stdin=self.stdin(inputs))

class MCMDError(Exception):
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

class Mcut(Command):
    def __init__(self):
        self.id = 'mcut'
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]
        self.params = []   
        self.params.append(Parameter('f', '対象列名(必須)'))
        self.description = '列選択'

    def run(self, args, inputs):
        pass

class McutOld(MCommand):
    def __init__(self):
        super().__init__()
        self.name = 'mcut'
        self.params.append(Parameter('f', '対象列名(必須)'))
        self.description = '列選択'
