import nysol.mcmd as nm

from kskp.engine import Port, NysolModule, Frame, Cache
from kskp.core import Command

# TODO: Storeに移動させる
# とりあえずコマンドだけ避難しておく
# kskp-data-storeに移動させたら消してください

# ※ sml_modelingコマンドはKコマンドを使う関係上、importで場所を指定している
#   今はテストで動かしている部分があるため、ローカルで動く様なパス設定をしてある
class TestCommand(Command):
    """
    inputとoutputが1つずつの擬似的なコマンド
    """

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'int')]
        self.o_ports = [Port('o', 'int')]

    def run(self, args, inputs):
        return {'o': inputs['i'] + 200}

class Square(Command):
    """
    与えられた数値を2乗する
    """

    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'int')]
        self.o_ports = [Port('o_sq', 'int')]

    def run(self, args, inputs):
        # 厳密にはframeじゃないが、まぁテスト用のコマンドなので
        # ラップするのはなんでもいいかなと思いframeにした。
        frame = Frame()
        frame.set_content([[inputs['i'][0][0] ** 2]])
        return {self.o_ports[0].name: frame}

class MselstrCommand(Command):
    """
    mselstrコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd'), Port('u', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        cmd_o = nm.mselstr(args)

        nysol_module_o = NysolModule()
        nysol_module_u = NysolModule()

        nysol_module_o.set_content(cmd_o)
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class M2crossCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.m2cross(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McalCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mcal(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McatCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('*', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        # 結合順が不定っぽい
        # とりあえず今は不定のまま、時間があったら調べて解決したい

        # 例：
        # A,B     A,B
        # 2,4     4,5
        #
        # 上2つを結合すると、
        #
        # A,B    A,B
        # 2,4    4,5
        # 4,5    2,4

        # のどちらかになる。
        inputs_for_arg_i = []
        from nysol.mcmd.nysollib.core import NysolMOD_CORE
        for key, input in inputs.items():
            if isinstance(input, NysolMOD_CORE):
                inputs_for_arg_i.append(input)
            else:
                # 一度nysol_module化する
                f = None
                f <<= nm.m2tee(i=input)
                inputs_for_arg_i.append(f)

        args['i'] = inputs_for_arg_i
        cmd_o = nm.m2cat(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McrossCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mcross(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McutCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mcut(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MnumberCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mnumber(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MselCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame'), Port('u', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.msel(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        nysol_module_u= NysolModule()
        nysol_module_u.set_content(cmd_o.redirect('u'))
        return {'o': nysol_module_o, 'u': nysol_module_u}

class MsetstrCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.msetstr(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsortfCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.msortf(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MsummaryCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.msummary(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MjoinCommand(Command):
    """
    mjoinコマンド（きちんとコマンドをstoreに置いたら消そう）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('m', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        args['m'] = inputs['m']
        nysol_module = NysolModule()
        nysol_module.set_content(nm.mjoin(args))
        return {'o': nysol_module}

class MteeCommand(Command):
    """
    Mteeコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        args['i'] = inputs['i']
        nysol_module = NysolModule()
        nysol_module.set_content(nm.m2tee(args))
        return {'o': nysol_module}

class MchkcsvCommand(Command):
    """
    Mchkcsvコマンド
    nysol_pythonにはないので、nm.cmdでNYSOLのmchkcsvを動かしている
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = 'mchkcsv'
        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class MfldnameCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mfldname(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MdformatCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mdformat(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MshareCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mshare(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class MchgnumCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mchgnum(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class McountCommand(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'frame')]

    def run(self, args, inputs):
        args['i'] = inputs['i']
        cmd_o = nm.mcount(args)
        nysol_module_o= NysolModule()
        nysol_module_o.set_content(cmd_o)
        return {'o': nysol_module_o}

class ColumnlistCommand(Command):
    """
    独自コマンドのColumnlistコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = 'kskp/engine/tmp_script_store/column_list.sh'
        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class GroupbyCommand(Command):
    """
    独自コマンドのGroupbyコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = 'kskp/engine/tmp_script_store/groupby.sh'
        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class ColumnUniqueNameCommand(Command):
    """
    独自コマンドのcolumn_unique_nameコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = 'kskp/engine/tmp_script_store/column_unique_name.sh'
        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class ColumnNameCommand(Command):
    """
    独自コマンドのcolumn_nameコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = 'kskp/engine/tmp_script_store/column_name.sh'
        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class SmlModelingCommand(Command):
    """
    独自コマンドのsml_modelingコマンド
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        import nysol.mcmd as nm
        f = None
        f <<= inputs['i']

        args_string = 'kskp/engine/tmp_script_store/sml_modeling.sh'
        args_string += ' kcmd_path=kskp/engine/commands/kcmd'
        args_string += ' temp_path=../../tmp_script_store/tmp'
        args_string += ' model_data_path=../../tmp_script_store/model'

        for key,value in args.items():
            if isinstance(value, bool):
                if value == True:
                    args_string +=  ' -' + key
            else:
                args_string += ' %s=%s' % (key, value)

        f <<= nm.cmd(args_string)
        nysol_module = NysolModule()
        nysol_module.set_content(f)
        return {'o': nysol_module}

class SaverCommand(Command):
    """
    指定されているstoreに出力するコマンド（テスト用）
    基本的にはlastsを保存するためにある
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        # 1. storeにsaveする
        uuid = inputs['store'].issue_uuid()
        datum_module = inputs['store'].save(args, inputs['i'], uuid)
        # 2. lasts用なのでコマンド実行のrunをする（繋げる必要はない）
        result = datum_module.run(msg='on')

        return {'o': self.wrap_datum(result, args, uuid)}

    def get_datum_obj(self):
        return Frame()

    def wrap_datum(self, datum_module, args, uuid):
        datum = self.get_datum_obj()
        datum.set_uuid(uuid)
        datum.set_cache_info(args)
        datum.set_content(datum_module)
        return datum

class CacheSaverCommand(SaverCommand):
    """
    指定されているstoreに出力するコマンド（テスト用）
    キャッシュ作成用で、Cache型で返すので別クラスで作った
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'frame'), Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        # 1. storeにsaveする(runはしない)
        uuid = inputs['store'].issue_uuid()
        datum_module = inputs['store'].save(args, inputs['i'], uuid)
        return {'o': self.wrap_datum(datum_module, args, uuid)}

    def get_datum_obj(self):
        # 書いて気づいたけどコンストラクタで決め打ちで設定でいいのかな。。。？
        return Cache()

class LoaderCommand(Command):
    """
    指定したstoreからデータを取ってくる（テスト用）
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('store', 'store')]
        self.o_ports = [Port('o', 'mcmd')]

    def run(self, args, inputs):
        nysol_module = NysolModule()
        nysol_module.set_content(inputs['store'].load(args['uuid']))
        return {'o': nysol_module}
