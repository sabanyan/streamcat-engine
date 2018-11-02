class Source:
    """
    データの取得元、もしくは書込先になる情報をもつクラス
    基本的にはDataクラスのsource属性を介して使用される
    """
    
    def __init__(self, source_type=''):
        self.type = source_type
        self.deletable_uuids = []

    def incr_ref_count(self, flow_uuid):
        if flow_uuid in ref_counts:
            ref_counts[flow_uuid] += 1
        else:
            ref_counts[flow_uuid] = 1
        # print('incr:', flow_uuid, ref_counts[flow_uuid])

    def decr_ref_count(self, flow_uuid):
        if flow_uuid in ref_counts:
            ref_counts[flow_uuid] -= 1
            # print('decr:', flow_uuid, ref_counts[flow_uuid])
            if ref_counts[flow_uuid] == 0:
                del ref_counts[flow_uuid]
                # print('del:', flow_uuid)
                # self.dtor()

    @property
    def ext(self):
        # ファイルの拡張子はdatum.source.typeから決定する
        if self.type == 'csv':
            return '.csv'
        elif self.type == '':
            return ''
        elif self.type == 'pickle':
            return '.pickle'
        else:
            # その他の場合は今は考えない
            raise Exception()

    def dtor(self):
        pass

class FileSource(Source):
    """
    一つのファイルを表すSource。読み書き共に可能
    """

    def __init__(self, source_type):
        super().__init__(source_type)

    @property
    def fd(self):
        pass

    @fd.setter
    def fd(self, value):
        pass

    def save(self, stdout):
        """ for override """
        pass
        
class UnixCommandSource(FileSource):
    """
    UNIXコマンド実行列を持つFileSource。
    読み取りのみが可能
    """

    def __init__(self, source_type, args, stdin=None):
        super().__init__(source_type)
        self.args = args
        self.stdin = stdin
        self.popen = None

    @property
    def fd(self):
        # if self.popen is not None and self.popen.stdin is not None and self.popen.stdin.closed:
        #     print(f'pid: {self.popen.pid} args: {self.args}')
        self.popen = subprocess.Popen(self.args, stdin=self.stdin, stdout=subprocess.PIPE, universal_newlines=True)
        if self.stdin is not None:
            self.stdin.close()
        return self.popen.stdout

    @fd.setter
    def fd(self, value):
        raise Exception()

    def save(self, stdout):
        """ engineから使う最後の保存用 """
        if self.stdin is not None and self.stdin.closed:
            # print('closed:', self.args)
            return
        popen = subprocess.Popen(self.args, stdin=self.stdin, stdout=stdout)
        if self.stdin is not None:
            self.stdin.close()
        popen.wait()

    def __repr__(self):
        # return f'UnixCommandSource args: {self.args} {self.stdin}'
        return f'args: {self.args}'

    def dtor(self):
        # if self.popen is not None:
        #     print(f'UnixCommandSource pid: {self.popen.pid} args:', self.args)
        # else:
        #     print(f'UnixCommandSource self.popen: None args:', self.args)
        if self.popen is not None:
            self.popen.stdout.close()
            # print(f'close pid: {self.popen.pid} args: {self.args}')
            self.popen.wait()

class PathFileSource(FileSource):
    """
    パスでファイルを表すFileSource。
    読み書き共に可能
    """

    def __init__(self, source_type, source_dir, file_name):
        super().__init__(source_type)
        self.source_dir = source_dir
        self.file_name = file_name
        self._fd = None

    @property
    def fd(self):
        self._fd = open(self.fullpath, 'r')
        return self._fd

    @fd.setter
    def fd(self, value):
        pass

    @property
    def fullpath(self):
        return Path(self.source_dir).joinpath(f'{self.file_name}')

    def __repr__(self):
        return f'path: {self.file_name}'

    def dtor(self):
        if self._fd is not None:
            self._fd.close()

class Datum:
    """
    データ全般を表すクラス

    :param source: データソース。現時点では以下のどれかの文字列が入る予定
                   'popen', 'csv', 'json', 'postgres', 'mysql', 'nysol_python'
                   Noneの場合は直接メモリ上だけにデータを持っていることになる
    :param uuid: 各frameを一意に識別するためのID
                 source is Noneであればframe_uuidもNoneであるが、
                 それ以外の場合ではuuid is not Noneのはず
                 (但し代入の順番の都合もあるかもしれないのでチェックはしない)
    """

    def __init__(self, uuid=None, source=None):
        self.uuid = uuid
        self.source = source
        self.is_temp = True

    def read(self):
        raise Exception()

    def write(self):
        raise Exception()

    def dtor(self):
        s = self.source
        if s is not None:
            s.dtor()
            if isinstance(s, PathFileSource):
                if self.is_temp and s.fullpath.exists():
                    pass
                    # s.fullpath.unlink()

import os
import uuid

from pathlib import Path

class Frame(Datum):
    """
    列指向の表形式データ
    """

    def __init__(self, frame_uuid=None, source=None):
        super().__init__(frame_uuid, source)

    def command_to_file(self):        
        if self.source is not None and not isinstance(self.source, PathFileSource):            
            file_name = self.uuid + self.source.ext
            new_source = PathFileSource(self.source.type, os.environ['KENG_FRAMES_PATH'], file_name)
            if isinstance(self.source, NysolPythonSource):
                self.source.save(new_source.fullpath.as_posix())
            else:
                with new_source.fullpath.open(mode='w', encoding='utf-8') as fd:
                    self.source.save(fd)
            for flow_uuid in self.source.deletable_uuids:
                self.source.decr_ref_count(flow_uuid)
            # self.source.dtor()
            self.source = new_source
            self.source.incr_ref_count(self.uuid)
        return self

    def command_to_tempfile(self):
        if not isinstance(self.source, PathFileSource):
            new_source = TempPathFileSource(self.source.type)
            with new_source.fullpath.open(mode='w', encoding='utf-8') as fd:
                self.source.save(fd)
            for flow_uuid in self.source.deletable_uuids:
                self.source.decr_ref_count(flow_uuid)
            self.source.dtor()
            self.source = new_source
            self.source.incr_ref_count(self.uuid)
        return self

    @property
    def contents(self):
        if self.source is None:
            return '(no contents)'

        with self.source.fd as fd:
            reader = csv.reader(fd)
            res = {}
            first_row = True

            for row in reader:
                if first_row:
                    for col in row:
                        res[col] = []
                    cols = row
                    first_row = False
                else:
                    for i, col in enumerate(cols):
                        res[col].append(row[i])

        return res

    def __repr__(self):
        # return f'<Frame({ self.source }) contents:{self.contents.__repr__()}>'
        return f'<Frame({ self.source })>'

class Store:
    """
    できたdatumを入れておく場所    
    """

    def __init__(self):
        self.data = {} # dict keyはUUID、valはdatum？

"""
(想定している仕様)
engineにはメモリベースのStoreが一つ存在していてengine.storeでアクセスできるようにする

そこから実際にCSVとして値を取り出すときには、そのstoreから、別のstoreに対象datumを移す。
現在のcommand_to_fileはその時点で走った方が設計として美しいのではないかな、と考えている。
少なくとも、ダメなものがダメだとわかる方が良い気がする。
"""