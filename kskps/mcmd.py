import io
import sys

class Mcommand():
    def run(self, args, inputs):        
        with io.StringIO() as messages_mem:
            with RedirectStdStreams(stderr=messages_mem):
                # 実際の内部の処理を呼び出す
                res = self.run_internal(args, inputs)
            
                messages = messages_mem.getvalue()
                
                if '#ERROR#' in messages:
                    content = [lin for lin in messages.split('\n') if lin.startswith('#ERROR#') and 'kgshell' not in lin][0]
                    err = MCMDError([MCMDErrorInfo.parse_stderr(content)])

                    print(err)

                    raise err
                else:
                    return res

    def run_internal(self, args, inputs):
        """ override用 """
        return ''

class McutTest(Mcommand):
    def run_internal(self, args, inputs):
        import nysol.mcmd as nm
        return nm.mcut(i=inputs['i'], f=args['f']).run(msg='on') # amountをtypoしている

class MCMDError(Exception):
    def __init__(self, errors):
        self.errors = errors

    def __repr__(self):
        return repr(self.errors[0])

class MCMDErrorInfo():
    def __init__(self, description, input_n, output_n, called_at):
        self.description = description
        self.number_of_input = input_n
        self.number_of_output = output_n
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
        if len(ss) >= 3:
            import re
            io = re.search(r'IN=(\d+) OUT=(\d+)', ss[2]).groups()
            return cls(ss[0].replace('#ERROR#', ''), int(io[0]), int(io[1]), ss[3])
        else:
            print('re:', s)

    def __repr__(self):
        return f'MCMDError:{self.description}'

class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        self._stderr.close() # for ResoucredWarning: unclosed file
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

# import re # for MCMDError

# from kskps.engine.core import Command, UnixCommand, Parameter, Port
# from kskps.engine.data import UnixCommandSource

# class McmdLink:
#     def __init__(self, id):
#         self.id = id

#     def resolve(self):
#         if self.id == 'mcut':
#             return McutOld()
#         else:
#             return Command()

# class MCommand(UnixCommand):

#     def command_args(self, args, inputs):
#         res = self.name.split()
#         for k, v in args.items():
#             # booleanに対応していないのでひとまず
#             if k == 'x':
#                 if v == True or v == "true":
#                     res.append('-x')
#             elif k == 'rng':
#                 if v == True:
#                     res.append('-rng')
#             elif k == 'r':
#                 if v == True or v == "true":
#                     res.append('-r')
#             else:
#                 res.append('%s=%s' % (k, v))
#         return res

#     # @property
#     def source(self, args, inputs):
#         return UnixCommandSource('csv', self.command_args(args, inputs), stdin=self.stdin(inputs))

# class Mcut(Command):
#     def __init__(self):
#         self.id = 'mcut'
#         self.i_ports = [Port('i', 'frame')]
#         self.o_ports = [Port('o', 'frame')]
#         self.params = []   
#         self.params.append(Parameter('f', '対象列名(必須)'))
#         self.description = '列選択'

#     def run(self, args, inputs):
#         pass

# class McutOld(MCommand):
#     def __init__(self):
#         super().__init__()
#         self.name = 'mcut'
#         self.params.append(Parameter('f', '対象列名(必須)'))
#         self.description = '列選択'
