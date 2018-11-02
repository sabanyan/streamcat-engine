import uuid
from enum import Enum, auto

from kskp.store import Command
# from kskp.engine.data import Frame

class Parameter:
    """
    パラメータ定義1つを表す

    :param name: パラメータ名。必須
    :param caption: このパラメータを表す短いタイトル。GUI上でのラベルとして使われる。
                    オプショナルで、未指定だとnameと同じになる。
    """

    class WidgetType(Enum):
        """
        パラメータ値の分類を表す。
        type属性に使われ、
        この値によってGUI上で使われる部品が変化することを想定している
        """
        TEXTBOX = auto()


    def __init__(self, name, caption=None):
        assert name is not None and name != '', 'nameは必須です'

        self.name = name
        if caption is None:
            self.caption = name
        else:
            self.caption = caption

        self.widget_type = self.WidgetType.TEXTBOX

        # self.default = None
        # self.validation = None

class Port:
    def __init__(self, name, port_type):
        self.name = name
        self.type = port_type

class Step:
    def __init__(self, runnable, args):
        self.runnable = runnable
        self.args = args

class Arrow:
    def __init__(self, id, dom, cod, datum):
        self.id = id
        self.dom = dom
        self.cod = cod
        self.datum = datum

# class Command:
#     def __init__(self):
#         self.i_ports = []
#         self.o_ports = []
#         self.params = []

#     def run(self, args, inputs):
#         return {}

#     @property
#     def out_key(self):
#         return self.o_ports[0].name

class Flow:
    def __init__(self):
        self.i_ports = []
        self.o_ports = []
        self.params = []

    def run(self, args, inputs):
        return {}

class Job:
    def __init__(self, step, arrows):
        self.step = step
        self.arrows = arrows
        self.lasts = {}

    def start(self):
        inputs = {a.id: a.datum for a in self.arrows}
        # 以下、暫定
        res = self.step.runnable.run(self.step.args, inputs)

        for r in res:
            # 適当です、あとで直します            
            print('res:', res)
            self.lasts['o'] = res['o'].command_to_file()

    def dtor(self):
        for a in self.arrows:
            a.datum.command_to_file().dtor()

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
