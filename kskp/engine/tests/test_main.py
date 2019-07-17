import os
import json
import uuid
import unittest
import nysol.mcmd as nm

from pathlib import Path

from .make_flow_json import create_flow, delete_flow

from kskp.engine import execute, FlowJsonLink, FlowUuidLink
from kskp.store import Library, FRAME_FOLDER_UUID, CACHE_FOLDER_UUID, FLOW_PATH, Frame, Command, Port, Datum, STORE_DIR

class Integer(Datum):
    """
    テスト用のクラス
    下記のSquareCommandで使うdatumをラップするためのもの
    """
    def __init__(self):
        super().__init__()
        self._content = None

    def set_content(self, module):
        self._content = module

    @property
    def content(self):
        return self._content

class Square(Command):
    """
    与えられた数値を2乗する
    テストコード内でのみ使用のため、ここに置いておく
    """
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'integer')]
        self.o_ports = [Port('o_sq', 'integer')]

    def run(self, args, inputs):
        # 厳密にはframeじゃないが、まぁテスト用のコマンドなので
        # ラップするのはなんでもいいかなと思いframeにした。
        frame = Integer()
        frame.set_content([[inputs['i'][0][0] ** 2]])
        return {self.o_ports[0].name: frame}

class ExecuteTestCase(unittest.TestCase):
    """
    実際のフロー実行のテスト
    """

    RESULT_DIR = STORE_DIR / 'frames/csv/フロー実行結果/'
    CACHE_DIR = STORE_DIR / 'frames/csv/フロー実行キャッシュ/'
    TESTDATA_DIR = STORE_DIR / 'frames/csv/'

    # mコマンド１つのフロー
    flow_data = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "f": "0,1",
            "x": True
          },
          "commandId": "mcut"
        }
      ]
    }

    # mコマンド１つのフロー（csvから読み取り）
    flow_data_use_by_csv = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": None,
          "dataSource": "csv",
          "uuid": "test_data"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "f": "0,1",
            "x": True
          },
          "commandId": "mcut"
        }
      ]
    }

    # mコマンド１つのフロー（csvから読み取り）
    # mchkcsv単体の実行テスト用
    flow_data_use_mchkcsv = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": None,
          "dataSource": "csv",
          "uuid": "test_data"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": ""
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {},
          "commandId": "mchkcsv"
        }
      ]
    }

    # inputが2つあるフロー
    flow_data_inputs = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "id": "i2",
          "type": "frame",
          "label": "テストデータ2",
          "value": [["顧客", "年齢"],
              ["A", 21],
              ["B", 31]],
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i",
            "m": "i2"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "k": "顧客",
            "f": "年齢"
          },
          "commandId": "mjoin"
        }
      ]
    }

    # inputが2つあるフロー（mcat）
    flow_data_inputs_mcat = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "id": "i2",
          "type": "frame",
          "label": "テストデータ2",
          "value": [["顧客", "数量", "金額"],
              ["C", 3, 10],
              ["C", 4, 20]],
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "*1": "i",
            "*2": "i2"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {},
          "commandId": "mcat"
        }
      ]
    }

    # inputが0個のあるフロー（mnewnumber）
    flow_data_inputs_mnewnumber = {
      "label": "mnewnumber",
      "ports": [
        [],
        []
      ],
      "params": [],
      "description": "",
      "nodes": [
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "makeCache": False,
          "cacheCreatedAt": "",
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c",
          "label": "c",
          "srcs": {},
          "dsts": {
            "o": "d1"
          },
          "args": {
              "a": "No."
          },
          "commandId": "mnewnumber"
        }
      ]
    }

    # outputが２つあるフロー
    flow_data_outputs = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d2",
            "u": "d3"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }
      ]
    }

    # inputとoutputが２つあるフロー
    flow_data_outputs_and_inputs = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["日付", "金額"],
              ["20080123", 10],
              ["20080203", 10],
              ["20080203", 20],
              ["20080203", 45],
              ["20080410", 50]],
          "dataSource": "csv"
        },
        {
          "id": "m",
          "type": "frame",
          "label": "テストデータ",
          "value": [["日付", "金額F", "金額T"],
              ["20080203", 5, 15],
              ["20080203", 40, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i",
            "m": "m"
          },
          "dsts": {
            "o": "d2",
            "u": "d3"
          },
          "args": {
            "k": "日付",
            "R": "金額F,金額T",
            "rf": "金額%n"
          },
          "commandId": "mnrcommon"
        }
      ]
    }

    def setUp(self):
        """
        フォルダの準備
        libraryが出力用ディレクトリを作成するため、コメントアウト
        """
        pass
        # def mkdir(path_str):
        #     result_path = Path(path_str)
        #     if not result_path.exists():
        #         result_path.mkdir()

        # mkdir(self.RESULT_DIR)
        # mkdir(self.CACHE_DIR)

    @unittest.skip
    def test_simple_flow_execute(self):
        """
        mコマンド１個のフロー実行
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data))
        lasts = execute(flow_link, {}, {})

        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    @unittest.skip
    def test_simple_flow_two_commands_execute(self):
        """
        mコマンド２個のフロー実行
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    @unittest.skip
    def test_simple_flow_two_commands_preview(self):
        """
        mコマンド２個のフロー実行
        真ん中のdatumでプレビューする
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d1'])
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    @unittest.skip
    def test_simple_flow_three_commands_preview(self):
        """
        mコマンド３個のフロー実行
        ２個目のdatumでプレビューする
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d2'])
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    @unittest.skip
    def test_simple_flow_three_commands_execute(self):
        """
        mコマンド３個のフロー実行（逆Y字の分岐）
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "顧客",
            "v": "B"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']], 'd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)

    @unittest.skip
    def test_simple_flow_three_commands_preview_d2(self):
        """
        mコマンド３個のフロー実行（逆Y字の分岐）
        片方（d2）をプレビュー
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "顧客",
            "v": "B"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d2'])
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    @unittest.skip
    def test_simple_flow_execute_two_inputs(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_inputs))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    @unittest.skip
    def test_simple_flow_execute_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']],
                   'd3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)

    @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_o(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        oだけ設置
        """
        # 出力uを消す
        flow_json = json.loads(json.dumps(self.flow_data_outputs))
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'o': 'd2'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd3']

        flow_link = FlowJsonLink(json.dumps(flow_json))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result_d3, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_u(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        uだけ設置
        """
        # 出力oを消す
        flow_json = json.loads(json.dumps(self.flow_data_outputs))
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'u': 'd3'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd2']

        flow_link = FlowJsonLink(json.dumps(flow_json))
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)

    @unittest.skip
    def test_simple_flow_preview_d2_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロープレビュー
        oだけのテスト（d2）
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs), ['d2'])
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])
        self.assertIsNone(lasts.get('d3'))

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    @unittest.skip
    def test_simple_flow_preview_d3_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロープレビュー
        uだけのテスト（d3）
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs), ['d3'])
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d3'])
        self.assertIsNone(lasts.get('d2'))

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)

    @unittest.skip
    def test_long_flow_execute_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフロー実行
        """

        add_datum_1 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d4",
          "label": "d4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3",
            "u": "d4"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        result_d4 = get_frame_by_uuid(lasts['d4'].uuid, self.RESULT_DIR)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)
        Library.delete_frame(lasts['d4'].uuid)

    @unittest.skip
    def test_long_flow_preview_d2_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフロープレビュー
        oだけのテスト（d3）
        """

        add_datum_1 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d4",
          "label": "d4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3",
            "u": "d4"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d3'])
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d3'])
        self.assertIsNone(lasts.get('d4'))

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)

    @unittest.skip
    def test_long_flow_preview_d3_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフロープレビュー
        uだけのテスト（d4）
        """
        add_datum_1 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d4",
          "label": "d4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d3",
            "u": "d4"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow_link = FlowJsonLink(json.dumps(json_flow), ['d4'])
        lasts = execute(flow_link, {}, {})
        correct = {'d4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d4'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d4'])
        self.assertIsNone(lasts.get('d3'))

        # 後片付け
        Library.delete_frame(lasts['d4'].uuid)

    @unittest.skip
    def test_simple_flow_execute_no_inputs_command(self):
        """
        mコマンド１個（1つもinputを持たない）のフロー実行
        mnewnumberの実行テスト
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_inputs_mnewnumber))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['0'],
                          ['1'],
                          ['2'],
                          ['3'],
                          ['4'],
                          ["5"],
                          ["6"],
                          ["7"],
                          ["8"],
                          ["9"]]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    @unittest.skip
    def test_simple_flow_execute_use_mnrcommon(self):
        """
        mコマンド１個（2つもinputを持ち、2つのoutputをもつ）のフロー実行
        mnrcommonの実行テスト
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_outputs_and_inputs))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['20080203', '10'], ['20080203', '45']],
                   'd3': [['20080123', '10'], ['20080203', '20'], ['20080410', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))

        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])
        result = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_include_subflow(self):
        """
        サブフローを１個をもつフローを実行する
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [[4]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "command",
                    "commandId": "square",
                    "args": {},
                    "srcs": { "i": "dd1" },
                    "dsts": { "o_sq": "dd2" }
                },
                {
                    "id": "dd2",
                    "type": "int",
                    "uuid": null
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'a'
        create_flow('sub1', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd3': [['65536']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd3'].uuid, self.RESULT_DIR, header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [[4]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" }
                },
                {
                    "id": "dd2",
                    "type": "int",
                    "uuid": null
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'a'
        create_flow('sub1', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd3': [['4294967296']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd3'].uuid, self.RESULT_DIR, header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simple_flow_preview_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        真ん中のdatumでプレビューする
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [[4]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" }
                },
                {
                    "id": "dd2",
                    "type": "int",
                    "uuid": null
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "a",
                    "args": {},
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": null
                }
            ]
        }'''
        # サブフローの作成
        sub_uuid = 'a'
        create_flow('sub1', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow, ['dd2']), {}, {})
        correct = {'dd2': [['256']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd2'].uuid, self.RESULT_DIR, header=False)
        self.assertEqual(result, correct['dd2'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid, self.RESULT_DIR)
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid, self.RESULT_DIR)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simple_flow_preview_dd2_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）

        片方のdatum(dd2)をプレビューする
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow, ['dd2']), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['dd2'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)

    # @unittest.skip
    def test_simple_flow_preview_dd3_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）

        片方のdatum(dd3)をプレビューする
        """

        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow, ['dd3']), {}, {})
        correct = {'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_complex_flow_execute_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        lasts = execute(FlowJsonLink(json.dumps(json_flow)), {}, {})
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd4'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd5'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd4 = get_frame_by_uuid(lasts['dd4'].uuid, self.RESULT_DIR)
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid, self.RESULT_DIR)
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd4'].uuid)
        Library.delete_frame(lasts['dd5'].uuid)

    # @unittest.skip
    def test_complex_flow_preview_include_branch_output_subflowss(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        dd5をプレビュー
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        lasts = execute(FlowJsonLink(json.dumps(json_flow), ['dd5']), {}, {})
        correct = {'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd5'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd5'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['dd5'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd5'].uuid)

    # @unittest.skip
    def test_complex_flow_two_preview_include_branch_output_subflowss(self):
        """
        おまけ（プレビューを２つしてみた。）
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        lasts = execute(FlowJsonLink(json.dumps(json_flow), ['dd2', 'dd5']), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd5'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid, self.RESULT_DIR)
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid, self.RESULT_DIR)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd5, correct['dd5'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)
        Library.delete_frame(lasts['dd5'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_generate_one_cache(self):
        """
        mコマンド３個のフロー実行
        真ん中のdatumをキャッシュする
        """

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": "",
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }


        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        path = Path(FLOW_PATH) / 'test.json'
        write_data_to_json(path, json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(Path(FLOW_PATH), 'test')
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        result = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d3'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d2']]
        for node in cache_nodes:
            # キャッシュが生成されているか
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            Library.delete_frame(node['uuid'])

        # 後片付け
        path.unlink()
        Library.delete_frame(lasts['d3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_generate_last_cache(self):
        """
        mコマンド３個のフロー実行
        最後のdatumをキャッシュする
        """

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": ""
        }


        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        path = Path(FLOW_PATH) / 'test.json'
        write_data_to_json(path, json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(Path(FLOW_PATH), 'test')
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        result = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d3'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d3']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            Library.delete_frame(node['uuid'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)
        path.unlink()

    # @unittest.skip
    def test_complex_flow_execute_include_branch_output_subflows_generate_cache(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている

        サブフローの出力するdd2と、結果をmcutしたdd5をキャッシュする
        """

        json_mainflow = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": True,
                    "cacheCreatedAt": ""
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "dd2"
          },
          "dsts": {
            "o": "dd4"
          },
          "args": {
            "f": "0",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "dd4",
          "label": "dd4",
          "uuid": None,
          "dataSource": "csv"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "dd3"
          },
          "dsts": {
            "o": "dd5"
          },
          "args": {
            "f": "1",
            "x": True
          },
          "commandId": "mcut"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "dd5",
          "label": "dd5",
          "uuid": None,
          "dataSource": "csv",
          "makeCache": True,
          "cacheCreatedAt": ""
        }

        json_flow = json.loads(json.dumps(json_mainflow))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        path = Path(FLOW_PATH) / 'test.json'
        write_data_to_json(path, json_flow)

        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        # 単純なlastsのテスト
        flow_link = FlowUuidLink(Path(FLOW_PATH), 'test')
        lasts = execute(flow_link, {}, {})
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd4'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd5'].uuid))
        result_dd4 = get_frame_by_uuid(lasts['dd4'].uuid, self.RESULT_DIR)
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid, self.RESULT_DIR)
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['dd2', 'dd5']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            Library.delete_frame(node['uuid'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd4'].uuid)
        Library.delete_frame(lasts['dd5'].uuid)
        path.unlink()

    # @unittest.skip
    def test_simploe_flow_include_subflow_execute_use_flowparam(self):
        """
        サブフローが１つのフローを実行する
        フローパラメータを使用する
        """
        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b_param",
                    "args": {
                        "sensor": "0,1",
                        "customer": "顧客"
                    },
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'b_param'
        create_flow('sub3', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid, self.RESULT_DIR)
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid, self.RESULT_DIR)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simploe_flow_include_subflow_execute_use_flowparams_in_one_line(self):
        """
        サブフローが１つのフローを実行する
        1つの項目で2つのフローパラメータを使用する
        """
        json_mainflow = '''{
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "frame",
                    "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
                    "uuid": null
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "b_param2",
                    "args": {
                        "sensor1": "顧客",
                        "sensor2": "数量",
                        "customer": "顧客"
                    },
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" , "d4": "dd3"}
                },
                {
                    "id": "dd2",
                    "type": "frame",
                    "uuid": null
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": null
                }
            ]
        }'''

        # サブフローの作成
        sub_uuid = 'b_param2'
        create_flow('sub4', sub_uuid)

        lasts = execute(FlowJsonLink(json_mainflow), {}, {})
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid, self.RESULT_DIR)
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid, self.RESULT_DIR)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_data_source_from_csv(self):
        """
        1つのmコマンドを持つフローを実行する
        フローの先頭のdatumのuuidが既に入っている
        """
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]

        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'test_data.csv', data)
        update_flow_node_uuid(self.flow_data_use_by_csv, 'i', frame_uuid)

        flow_link = FlowJsonLink(json.dumps(self.flow_data_use_by_csv))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_simple_flow_execute_data_source_from_cache(self):
        """
        mコマンド３個のフロー実行
        フローの途中（d2）のdatumのuuidが既に入っている
        """
        add_cmd_1 = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_cmd_2 = {
          "type": "command",
          "id": "c3",
          "label": "c3",
          "srcs": {
            "i": "d2"
          },
          "dsts": {
            "o": "d3"
          },
          "args": {
            "f": "数量",
            "v": "1"
          },
          "commandId": "mselstr"
        }

        add_datum_1 = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": "cache_data",
          "dataSource": "csv"
        }

        add_datum_2 = {
          "type": "frame",
          "id": "d3",
          "label": "d3",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # 中間データ作成
        data = [
            ['顧客','数量'],
            ['A',1],
            ['A',2]
        ]

        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(json_flow, 'd2', frame_uuid)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d3': [['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        result = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)
        Library.delete_frame(frame_uuid)

    # @unittest.skip
    def test_simple_subflow_execute_by_append_inputs(self):
        """
        1つのサブフローを実行する
        外部からframeを与えて実行する
        args指定はなし
        """
        # サブフローの作成
        sub_uuid = 'b'
        create_flow('sub2', sub_uuid)

        with open(FLOW_PATH + '/b.json') as f:
            flow_link = FlowJsonLink(json.dumps(json.load(f)))
            inputs = {
                'd1': [["顧客", "数量", "金額"],
                    ["A", 1, 10],
                    ["A", 2, 20],
                    ["B", 1, 30],
                    ["B", 3, 40],
                    ["B", 1, 50]]
            }
            lasts = execute(flow_link, {}, inputs)
            correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

            # テスト
            # DBにframeデータが生成されているか
            self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
            self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
            result_d3 = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
            result_d4 = get_frame_by_uuid(lasts['d4'].uuid, self.RESULT_DIR)
            self.assertEqual(result_d3, correct['d3'])
            self.assertEqual(result_d4, correct['d4'])

            # 後片付け
            self.assertTrue(delete_flow(sub_uuid))
            Library.delete_frame(lasts['d3'].uuid)
            Library.delete_frame(lasts['d4'].uuid)

    # @unittest.skip
    def test_simple_subflow_execute_by_append_inputs_and_args(self):
        """
        1つのサブフローを実行する
        外部からframeを与えて実行する
        args指定する
        """
        # サブフローの作成
        sub_uuid = 'b_param'
        create_flow('sub3', sub_uuid)

        with open(FLOW_PATH + '/b_param.json') as f:
            flow_link = FlowJsonLink(json.dumps(json.load(f)))

            inputs = {
                'd1': [["顧客", "数量", "金額"],
                    ["A", 1, 10],
                    ["A", 2, 20],
                    ["B", 1, 30],
                    ["B", 3, 40],
                    ["B", 1, 50]]
            }

            args = {
                "sensor": "0,1",
                "customer": "顧客"
            }

            lasts = execute(flow_link, args, inputs)
            correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

            # テスト
            # DBにframeデータが生成されているか
            self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
            self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
            result_d3 = get_frame_by_uuid(lasts['d3'].uuid, self.RESULT_DIR)
            result_d4 = get_frame_by_uuid(lasts['d4'].uuid, self.RESULT_DIR)
            self.assertEqual(result_d3, correct['d3'])
            self.assertEqual(result_d4, correct['d4'])

            # 後片付け
            self.assertTrue(delete_flow(sub_uuid))
            Library.delete_frame(lasts['d3'].uuid)
            Library.delete_frame(lasts['d4'].uuid)

    @unittest.skip
    def test_simple_flow_execute_use_mcat(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        mcatの実行テスト
        ※結合順不定なので、失敗することもある。（きちんと結合されてはいる）
        """
        flow_link = FlowJsonLink(json.dumps(self.flow_data_inputs_mcat))
        lasts = execute(flow_link, {}, {})
        correct = {'d1': [['A', '1', '10'],
                          ['A', '2', '20'],
                          ['B', '1', '30'],
                          ['B', '3', '40'],
                          ['B', '1', '50'],
                          ["C", '3', '10'],
                          ["C", '4', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_use_nmcmd(self):
        """
        mコマンド２個のフロー実行
        確認したいことはnm.cmdの動作（mchkcsvを実行している）
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {},
          "commandId": "mchkcsv"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2':[['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    # @unittest.skip
    def test_simple_flow_preview_use_nmcmd(self):
        """
        mコマンド２個のフロープレビュー
        確認したいことはnm.cmdの動作（mchkcsvを実行している）
        nm.cmdから出るものをプレビューするテスト
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {},
          "commandId": "mchkcsv"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = json.loads(json.dumps(self.flow_data))
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2':[['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        result = get_frame_by_uuid(lasts['d2'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_use_mchkcsv_create_cache(self):
        """
        mコマンド1個のフロー実行
        確認したいことはmchkcsvの動作（nm.cmdより実行している）

        ベータ版のengineではキャッシュの生成時の実行で失敗したので
        """
        # テストデータ作成
        data = [
            ['顧客', '数量', '金額'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]

        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_data_use_mchkcsv, 'i', frame_uuid)

        # キャッシュ生成時にjsonを書き換える処理があるため、一旦物理ファイル化
        flow_json_path = Path(FLOW_PATH) / 'mchkcsv_flow.json'
        with open(flow_json_path.as_posix(), 'w') as f:
            json.dump(json.loads(json.dumps(self.flow_data_use_mchkcsv)), f, ensure_ascii=False)

        flow_link = FlowUuidLink(Path(FLOW_PATH), 'mchkcsv_flow')
        lasts = execute(flow_link, {}, {})
        correct = {'d1':[['A', '1', '10'],['A', '2', '20'],['B', '1', '30'],['B', '3', '40'],['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid, self.RESULT_DIR)
        self.assertEqual(result, correct['d1'])

        # uuidが書き換わっているかのテスト
        result_json = json.loads(flow_json_path.read_text())
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d1']]
        for node in cache_nodes:
            # キャッシュが生成されているか
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            Library.delete_frame(node['uuid'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)
        Library.delete_frame(frame_uuid)
        flow_json_path.unlink()


class ExecuteSampleFlowTestCase(unittest.TestCase):
    """
    実際の実行のテスト
    βにあったflowを実行する
    """
    import json

    RESULT_DIR = STORE_DIR / 'frames/csv/フロー実行結果/'
    CACHE_DIR = STORE_DIR / 'frames/csv/フロー実行キャッシュ/'
    TESTDATA_DIR = STORE_DIR / 'frames/csv/'

    @unittest.skip
    def test_ni_flow_execute(self):
        """
        NI様のフローの実行テスト
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = 'ni_flow'
        create_flow('ni', main_uuid)

        with open(FLOW_PATH + '/ni_flow.json') as fj:
            flow_json = json.load(fj)
            update_flow_node_uuid(flow_json, 'i', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'ni_test.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'ni_test')
            lasts = execute(flow_link, {}, {})
            uuid = [value for value in lasts.values()][0].uuid

            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())

            # 後片付け
            self.assertTrue(delete_flow(main_uuid))
            Library.delete_frame(uuid)
            flow_json_path.unlink()

    @unittest.skip
    def test_ni_flow_preview(self):
        """
        NI様のフローのプレビュー実行テスト
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = 'ni_flow'
        create_flow('ni', main_uuid)

        with open(FLOW_PATH + '/ni_flow.json') as fj:
            flow_json = json.load(fj)
            update_flow_node_uuid(flow_json, 'i', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'ni_test.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'ni_test', ['new e9c09a48-901a-45d7-8bf3-91a323801277'])
            lasts = execute(flow_link, {}, {})
            uuid = [value for value in lasts.values()][0].uuid

            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())

            # 後片付け
            self.assertTrue(delete_flow(main_uuid))
            Library.delete_frame(uuid)
            flow_json_path.unlink()

    @unittest.skip
    def test_ni_flow_execute_generate_four_caches(self):
        """
        NI様のフローの実行テスト
        とりあえず全部キャッシュを作成する
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = 'ni_flow'
        create_flow('ni', main_uuid)

        with open(FLOW_PATH + '/ni_flow.json') as fj:
            # キャッシュを設定する
            flow_json = json.load(fj)
            for node in flow_json['nodes']:
                if node['type'] == 'frame':
                    if node['uuid'] is None:
                        node['makeCache'] = True
                        node['cacheCreatedAt'] = ""

            update_flow_node_uuid(flow_json, 'i', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'ni_test.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'ni_test')
            lasts = execute(flow_link, {}, {})
            uuid = [value for value in lasts.values()][0].uuid

            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())

            # uuidが書き換わっているかのテスト
            result_json = json.loads(flow_json_path.read_text())
            cache_nodes = [node for node in result_json['nodes'] if node['type'] == 'frame' and node['uuid'] != frame_uuid]
            for node in cache_nodes:
                self.assertIsNotNone(node['uuid'])
                self.assertIsNotNone(Library.load_frame(node['uuid']))
                self.assertIsNotNone(node['cacheCreatedAt'])
                Library.delete_frame(node['uuid'])

            # 後片付け
            self.assertTrue(delete_flow(main_uuid))
            Library.delete_frame(uuid)
            flow_json_path.unlink()

    @unittest.skip
    def test_ryudo_flow_execute(self):
        """
        デモ用のフロー実行（粒度分布計）
        lastsは8個ある
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'ryudo_demo.csv')

        # フローの作成
        main_uuid = 'ryudo_demo1'
        sub1_uuid = 'ryudo_sub1_demo1'
        sub2_uuid = 'ryudo_sub2_demo1'
        create_flow('ryudo', main_uuid)
        create_flow('ryudo_sub1', sub1_uuid)
        create_flow('ryudo_sub2', sub2_uuid)

        with open(FLOW_PATH + '/ryudo_demo1.json') as fj:
            flow_json = json.load(fj)
            update_flow_node_uuid(flow_json, 'compdata20190319.csv', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'ryudo_demo2.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'ryudo_demo2')
            lasts = execute(flow_link, {}, {})
            for datum in lasts.values():
                # テスト
                # DBにframeデータが生成されているか
                frame = Library.load_frame(datum.uuid)
                self.assertIsNotNone(frame)
                self.assertTrue(Path(frame.path).exists())
                # 後片付け
                Library.delete_frame(datum.uuid)

            self.assertTrue(delete_flow(main_uuid))
            self.assertTrue(delete_flow(sub1_uuid))
            self.assertTrue(delete_flow(sub2_uuid))
            flow_json_path.unlink()

    @unittest.skip
    def test_ryudo_flow_cache(self):
        """
        デモ用のフロー実行（粒度分布計）
        キャッシュをとりあえず全部作成する
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'ryudo_demo.csv')

        # フローの作成
        main_uuid = 'ryudo_demo1'
        sub1_uuid = 'ryudo_sub1_demo1'
        sub2_uuid = 'ryudo_sub2_demo1'
        create_flow('ryudo', main_uuid)
        create_flow('ryudo_sub1', sub1_uuid)
        create_flow('ryudo_sub2', sub2_uuid)

        with open(FLOW_PATH + '/ryudo_demo1.json') as fj:
            # キャッシュを設定する
            flow_json = json.load(fj)
            for node in flow_json['nodes']:
                if node['type'] == 'frame':
                    if node['uuid'] is None:
                        node['makeCache'] = True
                        node['cacheCreatedAt'] = ""

            update_flow_node_uuid(flow_json, 'compdata20190319.csv', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'ryudo_demo2.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'ryudo_demo2')
            lasts = execute(flow_link, {}, {})
            for datum in lasts.values():
                # テスト
                # DBにframeデータが生成されているか
                frame = Library.load_frame(datum.uuid)
                self.assertIsNotNone(frame)
                self.assertTrue(Path(frame.path).exists())
                # 後片付け
                Library.delete_frame(datum.uuid)

            # uuidが書き換わっているかのテスト
            result_json = json.loads(flow_json_path.read_text())
            cache_nodes = [node for node in result_json['nodes'] if node['type'] == 'frame' and node['uuid'] != frame_uuid]
            for node in cache_nodes:
                self.assertIsNotNone(node['uuid'])
                self.assertIsNotNone(Library.load_frame(node['uuid']))
                self.assertIsNotNone(node['cacheCreatedAt'])
                Library.delete_frame(node['uuid'])

            self.assertTrue(delete_flow(main_uuid))
            self.assertTrue(delete_flow(sub1_uuid))
            self.assertTrue(delete_flow(sub2_uuid))
            flow_json_path.unlink()

    @unittest.skip
    def test_ryudo_flow_preview(self):
        """
        デモ用のフロープレビュー（粒度分布計）
        プレビューデータは適当
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'ryudo_demo.csv')

        # フローの作成
        main_uuid = 'ryudo_demo1'
        sub1_uuid = 'ryudo_sub1_demo1'
        sub2_uuid = 'ryudo_sub2_demo1'
        create_flow('ryudo', main_uuid)
        create_flow('ryudo_sub1', sub1_uuid)
        create_flow('ryudo_sub2', sub2_uuid)

        with open(FLOW_PATH + '/ryudo_demo1.json') as fj:
            flow_json = json.load(fj)
            update_flow_node_uuid(flow_json, 'compdata20190319.csv', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'ryudo_demo2.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'ryudo_demo2', ['d14'])
            lasts = execute(flow_link, {}, {})
            self.assertIsNotNone(lasts['d14'])
            frame = Library.load_frame(lasts['d14'].uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())

            self.assertTrue(delete_flow(main_uuid))
            self.assertTrue(delete_flow(sub1_uuid))
            self.assertTrue(delete_flow(sub2_uuid))
            flow_json_path.unlink()
            Library.delete_frame(frame.uuid)

    @unittest.skip
    def test_shindo_flow_execute(self):
        """
        デモ用のフロー実行（振動データ）
        lasts11個ある
        """
        # 単純な実行結果のテスト
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = 'shindo_demo1'
        sub1_uuid = 'shindo_sub1_demo1'
        sub2_uuid = 'shindo_sub2_demo1'
        sub3_uuid = 'shindo_sub3_demo1'
        sub4_uuid = 'shindo_sub4_demo1'
        sub5_uuid = 'shindo_sub5_demo1'
        sub6_uuid = 'shindo_sub6_demo1'
        create_flow('shindo', main_uuid)
        create_flow('shindo_sub1', sub1_uuid)
        create_flow('shindo_sub2', sub2_uuid)
        create_flow('shindo_sub3', sub3_uuid)
        create_flow('shindo_sub4', sub4_uuid)
        create_flow('shindo_sub5', sub5_uuid)
        create_flow('shindo_sub6', sub6_uuid)

        with open(FLOW_PATH + '/shindo_demo1.json') as fj:
            flow_json = json.load(fj)
            update_flow_node_uuid(flow_json, '180127_1535_4sensor_5sec.csv', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'shindo_demo2.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'shindo_demo2')
            lasts = execute(flow_link, {}, {})
            for datum in lasts.values():
                # テスト
                # DBにframeデータが生成されているか
                frame = Library.load_frame(datum.uuid)
                self.assertIsNotNone(frame)
                self.assertTrue(Path(frame.path).exists())
                # 後片付け
                Library.delete_frame(datum.uuid)

            self.assertTrue(delete_flow(main_uuid))
            self.assertTrue(delete_flow(sub1_uuid))
            self.assertTrue(delete_flow(sub2_uuid))
            self.assertTrue(delete_flow(sub3_uuid))
            self.assertTrue(delete_flow(sub4_uuid))
            self.assertTrue(delete_flow(sub5_uuid))
            self.assertTrue(delete_flow(sub6_uuid))
            flow_json_path.unlink()

    @unittest.skip
    def test_shindo_flow_cache(self):
        """
        デモ用のフロー実行（振動データ）
        キャッシュをとりあえず全部作成する
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = 'shindo_demo1'
        sub1_uuid = 'shindo_sub1_demo1'
        sub2_uuid = 'shindo_sub2_demo1'
        sub3_uuid = 'shindo_sub3_demo1'
        sub4_uuid = 'shindo_sub4_demo1'
        sub5_uuid = 'shindo_sub5_demo1'
        sub6_uuid = 'shindo_sub6_demo1'
        create_flow('shindo', main_uuid)
        create_flow('shindo_sub1', sub1_uuid)
        create_flow('shindo_sub2', sub2_uuid)
        create_flow('shindo_sub3', sub3_uuid)
        create_flow('shindo_sub4', sub4_uuid)
        create_flow('shindo_sub5', sub5_uuid)
        create_flow('shindo_sub6', sub6_uuid)

        with open(FLOW_PATH + '/shindo_demo1.json') as fj:
            # キャッシュを設定する
            flow_json = json.load(fj)
            for node in flow_json['nodes']:
                if node['type'] == 'frame':
                    if node['uuid'] is None and not node['id'] == 'd1':
                        node['makeCache'] = True
                        node['cacheCreatedAt'] = ""

            update_flow_node_uuid(flow_json, '180127_1535_4sensor_5sec.csv', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'shindo_demo2.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'shindo_demo2')
            lasts = execute(flow_link, {}, {})
            for datum in lasts.values():
                # テスト
                # DBにframeデータが生成されているか
                frame = Library.load_frame(datum.uuid)
                self.assertIsNotNone(frame)
                self.assertTrue(Path(frame.path).exists())
                # 後片付け
                Library.delete_frame(datum.uuid)

            # uuidが書き換わっているかのテスト
            result_json = json.loads(flow_json_path.read_text())
            cache_nodes = [node for node in result_json['nodes'] if node['type'] == 'frame' and node['uuid'] != frame_uuid and node['id'] != 'd1']
            for node in cache_nodes:
                self.assertIsNotNone(node['uuid'])
                self.assertIsNotNone(Library.load_frame(node['uuid']))
                self.assertIsNotNone(node['cacheCreatedAt'])
                Library.delete_frame(node['uuid'])

            self.assertTrue(delete_flow(main_uuid))
            self.assertTrue(delete_flow(sub1_uuid))
            self.assertTrue(delete_flow(sub2_uuid))
            self.assertTrue(delete_flow(sub3_uuid))
            self.assertTrue(delete_flow(sub4_uuid))
            self.assertTrue(delete_flow(sub5_uuid))
            self.assertTrue(delete_flow(sub6_uuid))
            flow_json_path.unlink()

    @unittest.skip
    def test_shindo_flow_preview(self):
        """
        デモ用のフロープレビュー（振動データ）
        プレビューデータは適当
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = 'shindo_demo1'
        sub1_uuid = 'shindo_sub1_demo1'
        sub2_uuid = 'shindo_sub2_demo1'
        sub3_uuid = 'shindo_sub3_demo1'
        sub4_uuid = 'shindo_sub4_demo1'
        sub5_uuid = 'shindo_sub5_demo1'
        sub6_uuid = 'shindo_sub6_demo1'
        create_flow('shindo', main_uuid)
        create_flow('shindo_sub1', sub1_uuid)
        create_flow('shindo_sub2', sub2_uuid)
        create_flow('shindo_sub3', sub3_uuid)
        create_flow('shindo_sub4', sub4_uuid)
        create_flow('shindo_sub5', sub5_uuid)
        create_flow('shindo_sub6', sub6_uuid)

        with open(FLOW_PATH + '/shindo_demo1.json') as fj:
            flow_json = json.load(fj)
            update_flow_node_uuid(flow_json, '180127_1535_4sensor_5sec.csv', frame_uuid)

            # uuidを更新したflowを作成する
            flow_json_path = Path(FLOW_PATH) / 'shindo_demo2.json'
            with open(flow_json_path.as_posix(), 'w') as f:
                json.dump(flow_json, f, ensure_ascii=False)

            # 単純な実行結果のテスト
            flow_link = FlowUuidLink(Path(FLOW_PATH), 'shindo_demo2', ['d12'])
            lasts = execute(flow_link, {}, {})
            self.assertIsNotNone(lasts['d12'])
            frame = Library.load_frame(lasts['d12'].uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())

            self.assertTrue(delete_flow(main_uuid))
            self.assertTrue(delete_flow(sub1_uuid))
            self.assertTrue(delete_flow(sub2_uuid))
            self.assertTrue(delete_flow(sub3_uuid))
            self.assertTrue(delete_flow(sub4_uuid))
            self.assertTrue(delete_flow(sub5_uuid))
            self.assertTrue(delete_flow(sub6_uuid))
            flow_json_path.unlink()
            Library.delete_frame(frame.uuid)


# Helpler
def get_frame_by_uuid(uuid, dir_path, header=True):
    """
    指定したuuidのframeを取得する
    """
    import csv
    result = []
    frame = Library.load_frame(uuid)
    with open(frame.path, 'r') as f:
        rows = csv.reader(f)
        if header:
            header = next(rows)
        for row in rows:
            result.append(row)

    return result

def write_data_to_json(path, data):
    """
    データをJSONとしてファイルに書き込むヘルパー
    """
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def create_data(file_path_obj, data=None):
    """
    テストデータ作成用
    frameのuuidが返る
    """
    if data is not None:
        nm.mread(i=data, o=file_path_obj.as_posix()).run()
    frame = Library.save_frame(FRAME_FOLDER_UUID, str(uuid.uuid4()), file_path_obj)
    return frame.uuid

def update_flow_node_uuid(flow_json, node_id, uuid):
    """
    指定したflow_jsonのnode_idをuuidで更新する
    """
    for node in flow_json['nodes']:
        if node['id'] == node_id:
            node['uuid'] = uuid
            return True
    return False
