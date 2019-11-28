import os
import copy
import json
import uuid
import unittest
import nysol.mcmd as nm

from pathlib import Path

from .make_flow_json import create_flow, delete_flow

from kskp.engine import execute, FlowJsonLink, FlowLinkContext
from kskp.core import Datum
from kskp.store import Library, Frame, Command, Port, STORE_DIR, Database, DatabaseConn
from kskp.store import List, Flow

root = Library.load_root()

class ExecuteTestCase(unittest.TestCase):
    """
    実際のフロー実行のテスト
    """

    TESTDATA_DIR = STORE_DIR.parent / Library.load_root().path

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

    # outputが２つあるフロー（独自コマンド）
    flow_data_outputs_pcmd = {
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
            "f": 2,
          },
          "commandId": "selrow"
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

    @classmethod
    def tearDownClass(cls):
        """
        rootFolderを削除する
        """
        from kskp.store import Folder, FLOW_FOLDER_UUID
        if Folder.exists(FLOW_FOLDER_UUID):
          Library.delete_folder(FLOW_FOLDER_UUID)
        root_dir = STORE_DIR.parent / Library.load_root().path
        import shutil
        shutil.rmtree(root_dir.as_posix())

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

    # @unittest.skip
    def test_simple_flow_execute(self):
        """
        mコマンド１個のフロー実行
        """
        flow = Flow(None, self.flow_data['label'], self.flow_data)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)

        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    # @unittest.skip
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    # @unittest.skip
    def test_simple_flow_two_commands_vis(self):
        """
        mコマンド２個のフロー実行
        真ん中のdatumでVisする
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        # Vis Args
        vis_args = {
          "d1": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_three_commands_vis(self):
        """
        mコマンド３個のフロー実行
        ２個目のdatumでVisする
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # Vis Args
        vis_args = {
          "d2": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['A', '1'], ['A', '2']], 'd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid)
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)

    # @unittest.skip
    def test_simple_flow_three_commands_vis_d2(self):
        """
        mコマンド３個のフロー実行（逆Y字の分岐）
        片方（d2）をVis
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # Vis Args
        vis_args = {
          "d2": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_execute_two_inputs(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        flow = Flow(None, self.flow_data_inputs['label'], self.flow_data_inputs)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d1': [['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        """
        flow = Flow(None, self.flow_data_outputs['label'], self.flow_data_outputs)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']],
                   'd3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid)
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_o(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        oだけ設置
        """
        # 出力uを消す
        flow_json = copy.deepcopy(self.flow_data_outputs)
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'o': 'd2'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd3']

        flow = Flow(None, flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result_d3, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_u(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        uだけ設置
        """
        # 出力oを消す
        flow_json = copy.deepcopy(self.flow_data_outputs)
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'u': 'd3'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd2']

        flow = Flow(None, flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)

    # @unittest.skip
    def test_simple_flow_vis_d2_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフローVis
        oだけのテスト（d2）
        """
        # Vis Args
        vis_args = {
          "d2": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, self.flow_data_outputs['label'], self.flow_data_outputs)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_vis_d3_two_outputs(self):
        """
        mコマンド１個（２つのoutputを持つ）のフローVis
        uだけのテスト（d3）
        """

        # Vis Args
        vis_args = {
          "d3": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, self.flow_data_outputs['label'], self.flow_data_outputs)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)
        Library.delete_frame(lasts['d4'].uuid)

    # @unittest.skip
    def test_long_flow_vis_d2_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフローVis
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # Vis Args
        vis_args = {
          "d3": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d3': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_long_flow_vis_d3_two_outputs(self):
        """
        mコマンド2個（２つのoutputを持つ）のフローVis
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # Vis Args
        vis_args = {
          "d4": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext(), vis_args)
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'d4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_execute_no_inputs_command(self):
        """
        mコマンド１個（1つもinputを持たない）のフロー実行
        mnewnumberの実行テスト
        """
        flow = Flow(None,
                    self.flow_data_inputs_mnewnumber['label'],
                    self.flow_data_inputs_mnewnumber)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
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
        result = get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        Library.delete_frame(lasts['d1'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_use_mnrcommon(self):
        """
        mコマンド１個（2つもinputを持ち、2つのoutputをもつ）のフロー実行
        mnrcommonの実行テスト
        """
        flow = Flow(None,
                    self.flow_data_outputs_and_inputs['label'],
                    self.flow_data_outputs_and_inputs)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['20080203', '10'], ['20080203', '45']],
                   'd3': [['20080123', '10'], ['20080203', '20'], ['20080410', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))

        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])
        result = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_include_subflow(self):
        """
        サブフローを１個をもつフローを実行する
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
                    "type": "int",
                    "value": [[4]],
                    "uuid": None
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
                    "uuid": None
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
                    "args": {},
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": None
                }
            ]
        }

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub1', sub_uuid)

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext()), {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd3': [['65536']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd3'].uuid, header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simple_flow_execute_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
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
                    "type": "int",
                    "value": [[4]],
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" }
                },
                {
                    "id": "dd2",
                    "type": "int",
                    "uuid": None
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
                    "args": {},
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": None
                }
            ]
        }

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub1', sub_uuid)

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext()), {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd3': [['4294967296']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['dd3'].uuid, header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd3'].uuid)

    # Nodeのvalue属性値がRowRangeCommandのinputsに入ってきてNysolエラーになる
    # そもそもNodeのvalue属性は仕様にない実装である。
    # テストコードの再利用を試みたがSquareCommandはNysolModuleを受け付けないしで、断念
    @unittest.skip
    def test_simple_flow_vis_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        真ん中のdatumでVisする
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
                    "type": "int",
                    "uuid": None
                },
                {
                    "id": "ss1",
                    "type": "flow",
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
                    "args": {},
                    "srcs": { "d1": "dd1" },
                    "dsts": { "d3": "dd2" }
                },
                {
                    "id": "dd2",
                    "type": "int",
                    "uuid": None
                },
                {
                    "id": "ss2",
                    "type": "flow",
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
                    "args": {},
                    "srcs": { "d1": "dd2" },
                    "dsts": { "d3": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": None
                }
            ]
        }

        data = [[4]]
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'cache_data_z.csv', data)
        update_flow_node_uuid(json_mainflow, 'dd1', frame_uuid)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub1', sub_uuid)

        # Vis Args
        vis_args = {
          "dd2": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext(), vis_args), {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'dd2': [['256']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))

    # @unittest.skip
    def test_simple_flow_execute_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext()), {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid)
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd2'].uuid)
        Library.delete_frame(lasts['dd3'].uuid)

    # @unittest.skip
    def test_simple_flow_vis_dd2_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）

        片方のdatum(dd2)をVisする
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        # Vis Args
        vis_args = {
          "dd2": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext(), vis_args), {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'dd2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))

    # @unittest.skip
    def test_simple_flow_vis_dd3_include_branch_output_subflows(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）

        片方のdatum(dd3)をVisする
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        # Vis Args
        vis_args = {
          "dd3": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext(), vis_args), {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))

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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        json_flow = copy.deepcopy(json_mainflow)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        flow = Flow(None, json_flow['label'], json_flow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext()), {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd4'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd5'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd4 = get_frame_by_uuid(lasts['dd4'].uuid)
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid)
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['dd4'].uuid)
        Library.delete_frame(lasts['dd5'].uuid)

    # @unittest.skip
    def test_complex_flow_vis_include_branch_output_subflowss(self):
        """
        outputが２つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3＝不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        dd5をVis
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        json_flow = copy.deepcopy(json_mainflow)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        # Vis Args
        vis_args = {
          "dd5": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext(), vis_args), {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))

    # @unittest.skip
    def test_complex_flow_two_vis_include_branch_output_subflowss(self):
        """
        おまけ（Visを２つしてみた。）
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        json_flow = copy.deepcopy(json_mainflow)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        # Vis Args
        vis_args = {
          "dd2": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          },
          "dd5": {
            "args": {
              "visualizer" : "csvtohtmltable",
              "offset" : 0,
              "limit"  : 100
            }
          }
        }

        flow = Flow(None, json_flow['label'], json_flow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext(), vis_args), {}, {})
        lasts = convert_from_activity_vis(activity)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))

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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = Library.save_flow(root.uuid, 'test', json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowJsonLink(flow, FlowLinkContext(flow.uuid))
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d3': [['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        result = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = flow.flow_data
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d2']]
        for node in cache_nodes:
            # キャッシュが生成されているか
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        delete_flow(flow.uuid)
        Library.delete_frame(lasts['d3'].uuid)
        for uuid in cache_uuids:
            Library.delete_frame(uuid)

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


        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = Library.save_flow(root.uuid, 'test', json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowJsonLink(flow, FlowLinkContext(flow.uuid))
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d3': [['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        result = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = flow.flow_data
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d3']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        delete_flow(flow.uuid)
        Library.delete_frame(lasts['d3'].uuid)
        for uuid in cache_uuids:
            Library.delete_frame(uuid)

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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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

        json_flow = copy.deepcopy(json_mainflow)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = Library.save_flow(root.uuid, 'test', json_flow)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        # 単純なlastsのテスト
        flow_link = FlowJsonLink(flow, FlowLinkContext(flow.uuid))
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト

        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd4'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd5'].uuid))
        result_dd4 = get_frame_by_uuid(lasts['dd4'].uuid)
        result_dd5 = get_frame_by_uuid(lasts['dd5'].uuid)
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = flow.flow_data
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['dd2', 'dd5']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        delete_flow(flow.uuid)
        delete_flow(sub_uuid)
        Library.delete_frame(lasts['dd4'].uuid)
        Library.delete_frame(lasts['dd5'].uuid)
        for uuid in cache_uuids:
            Library.delete_frame(uuid)

    # @unittest.skip
    def test_simploe_flow_include_subflow_execute_use_flowparam(self):
        """
        サブフローが１つのフローを実行する
        フローパラメータを使用する
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub3', sub_uuid)

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext()), {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid)
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid)
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
                    "uuid": "62dbe8d6-5f09-450e-a0b8-fab88ecfafd3",
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
                    "uuid": None
                },
                {
                    "id": "dd3",
                    "type": "frame",
                    "uuid": None
                }
            ]
        }

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub4', sub_uuid)

        flow = Flow(None, 'メインフロー', json_mainflow)
        activity = execute(FlowJsonLink(flow, FlowLinkContext()), {}, {})
        lasts = convert_from_activity(activity)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['dd2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['dd3'].uuid))
        result_dd2 = get_frame_by_uuid(lasts['dd2'].uuid)
        result_dd3 = get_frame_by_uuid(lasts['dd3'].uuid)
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

        flow = Flow(None,
                    self.flow_data_use_by_csv['label'],
                    self.flow_data_use_by_csv)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid)
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

        json_flow = copy.deepcopy(self.flow_data)
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

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d3': [['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        result = get_frame_by_uuid(lasts['d3'].uuid)
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
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub2', sub_uuid)

        flow = Library.load_flow(sub_uuid)
        flow_link = FlowJsonLink(flow, FlowLinkContext())

        inputs = {
            'd1': List([["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]])
        }
        activity = execute(flow_link, {}, inputs)
        lasts = convert_from_activity(activity)
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = get_frame_by_uuid(lasts['d4'].uuid)
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
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        create_flow('sub3', sub_uuid)

        flow = Library.load_flow(sub_uuid)
        flow_link = FlowJsonLink(flow, FlowLinkContext())

        inputs = {
            'd1': List([["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]])
        }

        args = {
            "sensor": "0,1",
            "customer": "顧客"
        }

        activity = execute(flow_link, args, inputs)
        lasts = convert_from_activity(activity)
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d4'].uuid))
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        self.assertTrue(delete_flow(sub_uuid))
        Library.delete_frame(lasts['d3'].uuid)
        Library.delete_frame(lasts['d4'].uuid)

    # もともとskip状態
    @unittest.skip
    def test_simple_flow_execute_use_mcat(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        mcatの実行テスト
        ※結合順不定なので、失敗することもある。（きちんと結合されてはいる）
        """
        flow = Flow(None, self.flow_data_inputs_mcat['label'], self.flow_data_inputs_mcat)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d1': List([['A', '1', '10'],
                              ['A', '2', '20'],
                              ['B', '1', '30'],
                              ['B', '3', '40'],
                              ['B', '1', '50'],
                              ["C", '3', '10'],
                              ["C", '4', '20']])
                  }

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid)
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2':[['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        result = get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

    # @unittest.skip
    def test_simple_flow_vis_use_nmcmd(self):
        """
        mコマンド２個のフローVis
        確認したいことはnm.cmdの動作（mchkcsvを実行している）
        nm.cmdから出るものをVisするテスト
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

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow = Flow(None, json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2':[['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        result = get_frame_by_uuid(lasts['d2'].uuid)
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
        flow = Library.save_flow(root.uuid, 'test', self.flow_data_use_mchkcsv)

        flow_link = FlowJsonLink(flow, FlowLinkContext(flow.uuid))
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d1':[['A', '1', '10'],['A', '2', '20'],['B', '1', '30'],['B', '3', '40'],['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        result = get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = flow.flow_data
        cache_nodes = [node for node in result_json['nodes'] if node['id'] in ['d1']]
        for node in cache_nodes:
            # キャッシュが生成されているか
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        delete_flow(flow.uuid)
        Library.delete_frame(lasts['d1'].uuid)
        Library.delete_frame(frame_uuid)
        for uuid in cache_uuids:
            Library.delete_frame(uuid)

    # @unittest.skip
    def test_simple_flow_execute_two_outputs_pcmd(self):
        """
        独自コマンド１個（２つのoutputを持つ）のフロー実行
        """
        data = [["顧客", "数量", "金額"],
                ["A", 1, 10],
                ["A", 2, 20],
                ["B", 1, 30],
                ["B", 3, 40],
                ["B", 1, 50]]

        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_data_outputs_pcmd, 'i', frame_uuid)
        flow = Flow(None, self.flow_data_outputs_pcmd['label'], self.flow_data_outputs_pcmd)
        flow_link = FlowJsonLink(flow, FlowLinkContext())

        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']],
                   'd3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = get_frame_by_uuid(lasts['d2'].uuid)
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(lasts['d3'].uuid)
        Library.delete_frame(frame_uuid)

    # 二股コマンドの片一方の出力先にPointを繋げない場合のテストになる
    # mselrowのFIFOの関係で、nm.runs()でフリーズする。
    # だが、そもそもそのようなフローはフローエディタでは作成不可能なので
    # このテストは無効である
    @unittest.skip
    def test_simple_flow_execute_two_outputs_pcmd_one_side_o(self):
        """
        独自コマンド１個（２つのoutputを持つ）のフロー実行
        oだけ設置
        """
        data = [["顧客", "数量", "金額"],
            ["A", 1, 10],
            ["A", 2, 20],
            ["B", 1, 30],
            ["B", 3, 40],
            ["B", 1, 50]]

        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_data_outputs_pcmd, 'i', frame_uuid)

        # 出力uを消す
        flow_json = self.flow_data_outputs_pcmd
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                # node['dsts'] = {'o': 'd2'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd3']

        flow = Flow(None, flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result_d3, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)
        Library.delete_frame(frame_uuid)

    # 二股コマンドの片一方の出力先にPointを繋げない場合のテストになる
    # mselrowのFIFOの関係で、nm.runs()でフリーズする。
    # だが、そもそもそのようなフローはフローエディタでは作成不可能なので
    # このテストは無効である
    @unittest.skip
    def test_simple_flow_execute_two_outputs_pcmd_one_side_u(self):
        """
        独自コマンド１個（２つのoutputを持つ）のフロー実行
        uだけ設置
        """
        data = [["顧客", "数量", "金額"],
                ["A", 1, 10],
                ["A", 2, 20],
                ["B", 1, 30],
                ["B", 3, 40],
                ["B", 1, 50]]

        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'cache_data_a.csv', data)
        update_flow_node_uuid(self.flow_data_outputs_pcmd, 'i', frame_uuid)

        # 出力oを消す
        flow_json = self.flow_data_outputs_pcmd
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                # ⬇️これしたらnm.runs()でフリーズ！
                # node['dsts'] = {'u': 'd3'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd2']

        flow = Flow(None, flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        Library.delete_frame(lasts['d3'].uuid)
        Library.delete_frame(frame_uuid)

@unittest.skip('古いので失敗する。改修予定')
class ExecuteTestCase2(unittest.TestCase):

    # mコマンド１つのフロー
    flow_data = {
      "label": "test用",
      "creator": "開発用",
      "createdAt": "2019-10-28 15:06:35",
      "projectId": None,
      "description": "",
      "ports": [
        [],
        []
      ],
      "params": [],
      "nodes": [
        {
          "id": "d",
          "type": "frame",
          "uuid": None,
          "error": {},
          "label": "d",
          "invalid": {},
          "makeCache": False,
          "dataSource": "csv",
          "cacheCreatedAt": None
        },
        {
          "id": "f",
          "args": {},
          "dsts": {
            "d1": "d"
          },
          "srcs": {},
          "type": "flow",
          "uuid": "8cfbce33-f2f9-4f52-a97d-ce170f70f6e3",
          "error": {},
          "label": "f",
          "invalid": {},
          "srcsOrder": []
        },
        {
          "id": "f1",
          "args": {},
          "dsts": {},
          "srcs": {
            "d1": "d"
          },
          "type": "flow",
          "uuid": "b3e980d4-8338-4e83-a238-dd4537148c43",
          "error": {},
          "label": "f1",
          "invalid": {},
          "srcsOrder": [
            "d1"
          ]
        },
        {
          "id": "f2",
          "args": {},
          "dsts": {},
          "srcs": {
            "d1": "d"
          },
          "type": "flow",
          "uuid": "b3e980d4-8338-4e83-a238-dd4537148c43",
          "error": {},
          "label": "PostgreSQLデータデスト",
          "invalid": {},
          "srcsOrder": [
            "d1"
          ]
        }
      ]
    }

    database_conn = DatabaseConn("postgresql", "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 5432, "kskp", "kskp", r'J2-pH|%B')

    # @unittest.skip
    def test_simple_flow_execute(self):
        """
        mコマンド１個のフロー実行
        """
        # DBストアの作成
        db = Database(root.uuid, 'postgresql', self.database_conn, None)
        db.uuid = 'c410cd16-2529-498d-8e7f-490ffa58dc95'
        db.save()

        # サブフロー(PostgreSQLデータソース)の作成
        postgre_src = '8cfbce33-f2f9-4f52-a97d-ce170f70f6e3'
        create_flow('postgre_src', postgre_src)

        # サブフロー(PostgreSQLデータデスト)の作成
        postgre_dst = 'b3e980d4-8338-4e83-a238-dd4537148c43'
        create_flow('postgre_dst', postgre_dst)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = Flow(None, self.flow_data['label'], self.flow_data)
        flow_link = FlowJsonLink(flow, FlowLinkContext())
        activity = execute(flow_link, {}, {})
        lasts = convert_from_activity(activity)

        # テスト
        # DBにframeデータが生成されているか
        # self.assertIsNotNone(Library.load_frame(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        # result = get_frame_by_uuid(lasts['d1'].uuid)
        # self.assertEqual(result, correct['d1'])

        # 後片付け
        self.assertTrue(delete_flow(postgre_src))
        self.assertTrue(delete_flow(postgre_dst))

# Helpler
def get_frame_by_uuid(uuid, header=True):
    """
    指定したuuidのframeを取得する
    """
    import csv
    result = []
    frame = Library.load_frame(uuid)
    try:
      with open(STORE_DIR.parent / frame.path, 'r') as f:
          rows = csv.reader(f)
          if header:
              header = next(rows)
          for row in rows:
              result.append(row)
    except Exception as e:
      import pprint
      pprint.pprint(f)
      raise e

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
    frame = Library.save_frame(root.uuid, str(uuid.uuid4()), file_path_obj)
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

def convert_from_activity(activity):
    """
    execute()の戻り値であるActivityから
    pointのidとframeのDictに置き換える
    """
    return {point.id : frame for point, frame in activity.result}

def convert_from_activity_vis(activity):
    """
    execute()の戻り値であるActivityから
    pointのidとvisのDictに置き換える
    """
    return {point.id : vis.result['reader'] for point, vis in activity.result}
