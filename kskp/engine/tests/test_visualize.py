import unittest
import nysol.mcmd as nm
import uuid

from pathlib import Path
from kskp.store import Library, FRAME_FOLDER_UUID, CACHE_FOLDER_UUID, CommandLink

class ExecuteViualizeTestCase(unittest.TestCase):
    """
    visualize用コマンドの実行テスト
    """
    RESULT_DIR = 'kskp/data/library/フロー実行結果/'
    CACHE_DIR = 'kskp/data/library/フロー実行キャッシュ/'
    TESTDATA_DIR = 'kskp/data/'

    def setUp(self):
        pass

    def test_execute_table(self):
        """
        表形式でデータを出力するテスト
        """
        table_command = CommandLink('csvtohtmltable').resolve()
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame_path = Path(self.TESTDATA_DIR) / 'test_data.csv'
        frame_uuid = create_data(frame_path, data)

        args = {
            'limit': 3,
            'offset': 0
        }

        inputs = {
            'i': frame_path.as_posix()
        }

        result = table_command.run(args, inputs)

        correct = {
            'header':['顧客', '数量', '金額\n'],
            'reader':[['A', '1', '10\n'], ['A', '2', '20\n'], ['B', '1', '30\n']]
        }

        self.assertIsNotNone(result['o'])
        self.assertEqual(result['o']['header'], correct['header'])
        self.assertEqual(result['o']['reader'], correct['reader'])

        # 後片付け
        Library.delete_frame(frame_uuid)

def create_data(file_path_obj, data=None):
    """
    テストデータ作成用
    frameのuuidが返る
    """
    if data is not None:
        nm.mread(i=data, o=file_path_obj.as_posix()).run()
    frame = Library.save_frame(FRAME_FOLDER_UUID, str(uuid.uuid4()), file_path_obj)
    return frame.uuid
