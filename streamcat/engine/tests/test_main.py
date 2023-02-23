import copy
import unittest
from pathlib import Path
from streamcat.store import FlowData, Matrix, CommandException
from streamcat.store.tests.test_case_base import TestCaseBase
from streamcat.depo.std.commands.scmd.mcmd_error_info import MCMDError
from streamcat.engine import execute, FlowCommand
from .make_flow_json import get_flow_json_by_flow_id

class MainTest(TestCaseBase):
    """
    実際のフロー実行のテスト
    """

    # mコマンド1つのフロー
    flow_json = {
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

    # mコマンド1つのフロー（csvから読み取り）
    flow_json_use_by_csv = {
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

    # mコマンド1つのフロー（csvから読み取り）
    # mchkcsv単体の実行テスト用
    flow_json_use_mchkcsv = {
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
    flow_json_inputs = {
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
    flow_json_inputs_mcat = {
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
    flow_json_inputs_mnewnumber = {
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

    # outputが2つあるフロー
    flow_json_outputs = {
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

    # outputが2つあるフロー（独自コマンド）
    flow_json_outputs_pcmd = {
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

    # inputとoutputが2つあるフロー
    flow_json_outputs_and_inputs = {
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
        super().setUp()
        self.root = self.factory.data.load_root()
        self.TESTDATA_DIR = self.root.path

    # @unittest.skip
    def test_simple_flow_execute(self):
        """
        mコマンド1個のフロー実行
        """
        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        correct = {'d1': [['顧客', '数量'], ['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_simple_flow_two_commands_execute(self):
        """
        mコマンド2個のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd)
        flow_json['nodes'].append(add_datum)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['顧客', '数量'], ['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_simple_flow_two_commands_vis(self):
        """
        mコマンド1個のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd)
        flow_json['nodes'].append(add_datum)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_three_commands_vis(self):
        """
        mコマンド3個のフロー実行
        2個目のdatumでVisする
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_2)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_three_commands_execute(self):
        """
        mコマンド3個のフロー実行（逆Y字の分岐）
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_2)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'd3': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = self.get_frame_by_uuid(lasts['d2'].uuid)
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        lasts['d2'].delete()
        lasts['d3'].delete()

    # @unittest.skip
    def test_simple_flow_three_commands_vis_d2(self):
        """
        mコマンド3個のフロー実行（逆Y字の分岐）
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_2)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_execute_two_inputs(self):
        """
        mコマンド1個（2つのinputを持つ）のフロー実行
        """
        flow_json = copy.deepcopy(self.flow_json_inputs)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d1': [['顧客%0', '数量', '金額', '年齢'],
                          ['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_simple_flow_execute_two_outputs(self):
        """
        mコマンド1個（2つのoutputを持つ）のフロー実行
        """
        flow_json = copy.deepcopy(self.flow_json_outputs)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))
        flow_json['nodes'].append(self.create_data_dst_node('d3'))
        
        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['顧客', '数量', '金額'], ['A', '1', '10'], ['A', '2', '20']],
                   'd3': [['顧客', '数量', '金額'], ['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = self.get_frame_by_uuid(lasts['d2'].uuid)
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        lasts['d2'].delete()
        lasts['d3'].delete()

    # @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_o(self):
        """
        mコマンド1個（2つのoutputを持つ）のフロー実行
        oだけ設置
        """
        # 出力uを消す
        flow_json = copy.deepcopy(self.flow_json_outputs)
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'o': 'd2'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd3']
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['顧客', '数量', '金額'], ['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result_d3, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_u(self):
        """
        mコマンド1個（2つのoutputを持つ）のフロー実行
        uだけ設置
        """
        # 出力oを消す
        flow_json = copy.deepcopy(self.flow_json_outputs)
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'u': 'd3'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd2']
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量', '金額'], ['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        lasts['d3'].delete()

    # @unittest.skip
    def test_simple_flow_vis_d2_two_outputs(self):
        """
        mコマンド1個（2つのoutputを持つ）のフローVis
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

        flow = self.root.create_flow(self.flow_json_outputs['label'], FlowData(self.flow_json_outputs))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_vis_d3_two_outputs(self):
        """
        mコマンド1個（2つのoutputを持つ）のフローVis
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

        flow = self.root.create_flow(self.flow_json_outputs['label'], FlowData(self.flow_json_outputs))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_long_flow_execute_two_outputs(self):
        """
        mコマンド2個（2つのoutputを持つ）のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)
        flow_json['nodes'].append(self.create_data_dst_node('d3'))
        flow_json['nodes'].append(self.create_data_dst_node('d4'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'd4': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d4'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = self.get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        lasts['d3'].delete()
        lasts['d4'].delete()

    # @unittest.skip
    def test_long_flow_vis_d2_two_outputs(self):
        """
        mコマンド2個（2つのoutputを持つ）のフローVis
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d3': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_long_flow_vis_d3_two_outputs(self):
        """
        mコマンド2個（2つのoutputを持つ）のフローVis
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'d4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_execute_no_inputs_command(self):
        """
        mコマンド1個（1つもinputを持たない）のフロー実行
        mnewnumberの実行テスト
        """

        flow_json = copy.deepcopy(self.flow_json_inputs_mnewnumber)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d1': [['No.'],
                          ['0'],
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
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_simple_flow_execute_use_mnrcommon(self):
        """
        mコマンド1個（2つもinputを持ち、2つのoutputをもつ）のフロー実行
        mnrcommonの実行テスト
        """
        flow_json = copy.deepcopy(self.flow_json_outputs_and_inputs)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['日付%0', '金額'], ['20080203', '10'], ['20080203', '45']],
                   'd3': [['日付%0', '金額'], ['20080123', '10'], ['20080203', '20'], ['20080410', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))

        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])
        result = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        # 後片付け
        lasts['d2'].delete()
        lasts['d3'].delete()

    # @unittest.skip
    def test_simple_flow_execute_include_subflow(self):
        """
        サブフローを1個をもつフローを実行する
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd2" },
                    "dsts": { "出力": "dd3" }
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
        self.create_flow('sub1', sub_uuid)

        mainflow_json['nodes'].append(self.create_data_dst_node('dd3'))

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd3': [['65536']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['dd3'].uuid, header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['dd3'].delete()

    # @unittest.skip
    def test_simple_flow_execute_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力": "dd2" }
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
                    "srcs": { "入力": "dd2" },
                    "dsts": { "出力": "dd3" }
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
        self.create_flow('sub1', sub_uuid)

        mainflow_json['nodes'].append(self.create_data_dst_node('dd3'))

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd3': [['4294967296']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['dd3'].uuid, header=False)
        self.assertEqual(result, correct['dd3'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['dd3'].delete()

    # Nodeのvalue属性値がRowRangeCommandのinputsに入ってきてNysolエラーになる
    # そもそもNodeのvalue属性は仕様にない実装である。
    # テストコードの再利用を試みたがSquareCommandはNysolModuleを受け付けないしで、断念
    @unittest.skip('無効')
    def test_simple_flow_vis_include_two_subflows(self):
        """
        サブフローを2個をもつフローを実行する
        真ん中のdatumでVisする
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力": "dd2" }
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
                    "srcs": { "入力": "dd2" },
                    "dsts": { "出力": "dd3" }
                },
                {
                    "id": "dd3",
                    "type": "int",
                    "uuid": None
                }
            ]
        }

        data = [[4]]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data_z.csv', data)
        update_flow_node_uuid(mainflow_json, 'dd1', frame.uuid)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub1', sub_uuid)

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

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'dd2': [['256']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

    # @unittest.skip
    def test_simple_flow_execute_include_branch_output_subflows(self):
        """
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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
        self.create_flow('sub2', sub_uuid)

        mainflow_json['nodes'].append(self.create_data_dst_node('dd2'))
        mainflow_json['nodes'].append(self.create_data_dst_node('dd3'))

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd2': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'dd3': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd2 = self.get_frame_by_uuid(lasts['dd2'].uuid)
        result_dd3 = self.get_frame_by_uuid(lasts['dd3'].uuid)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['dd2'].delete()
        lasts['dd3'].delete()

    # @unittest.skip
    def test_simple_flow_vis_dd2_include_branch_output_subflows(self):
        """
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）

        片方のdatum(dd2)をVisする
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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
        self.create_flow('sub2', sub_uuid)

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

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

    # @unittest.skip
    def test_simple_flow_vis_dd3_include_branch_output_subflows(self):
        """
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）

        片方のdatum(dd3)をVisする
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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
        self.create_flow('sub2', sub_uuid)

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

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

    # @unittest.skip
    def test_complex_flow_execute_include_branch_output_subflows(self):
        """
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        """

        mainflow_json = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                [
                  {
                    "type": "frame",
                    "label": "ラベル1",
                    "nodeId": "dd4"
                  },
                  {
                    "type": "frame",
                    "label": "ラベル2",
                    "nodeId": "dd5"
                  }
                ]
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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

        flow_json = copy.deepcopy(mainflow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)

        # データデストの追加
        flow_json['nodes'].append(self.create_data_dst_node('dd4'))
        flow_json['nodes'].append(self.create_data_dst_node('dd5'))

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub2', sub_uuid)

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        lasts = execute(FlowCommand(flow), {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd4': [['顧客'], ['A'], ['A']], 'dd5': [['数量'], ['1'], ['3'], ['1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd4'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd5'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_dd4 = self.get_frame_by_uuid(lasts['dd4'].uuid)
        result_dd5 = self.get_frame_by_uuid(lasts['dd5'].uuid)
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['dd4'].delete()
        lasts['dd5'].delete()

    # @unittest.skip
    def test_complex_flow_vis_include_branch_output_subflowss(self):
        """
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        dd5をVis
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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

        flow_json = copy.deepcopy(mainflow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub2', sub_uuid)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

    # @unittest.skip
    def test_complex_flow_two_vis_include_branch_output_subflowss(self):
        """
        おまけ（Visを2つしてみた。）
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）
        さらにメインフローで結果をそれぞれmcutしている
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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

        flow_json = copy.deepcopy(mainflow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub2', sub_uuid)

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

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

    # @unittest.skip
    def test_simple_flow_execute_generate_one_cache(self):
        """
        mコマンド3個のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_2)
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = self.save_flow('test', flow_json)

        # 単純な実行結果のテスト
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量'],['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        result = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = self.factory.data.find_by_uuid(flow.uuid)
        flow_data = flow.flow_data
        cache_nodes = [node for node in flow_data.get_nodes() if node['id'] in ['d2']]
        for node in cache_nodes:
            # キャッシュが生成されているか
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(self.factory.data.find_by_uuid(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        self.delete_flow(flow.uuid)
        lasts['d3'].delete()
        self.delete_caches(cache_uuids)

    # @unittest.skip
    def test_simple_flow_execute_generate_last_cache(self):
        """
        mコマンド3個のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_2)
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = self.save_flow('test', flow_json)

        # 単純な実行結果のテスト
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量'],['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        result = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = self.factory.data.find_by_uuid(flow.uuid)
        flow_data = flow.flow_data
        cache_nodes = [node for node in flow_data.get_nodes() if node['id'] in ['d3']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(self.factory.data.find_by_uuid(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        self.delete_flow(flow.uuid)
        lasts['d3'].delete()
        self.delete_caches(cache_uuids)

    # @unittest.skip
    def test_complex_flow_execute_include_branch_output_subflows_generate_cache(self):
        """
        outputが2つのサブフローをもつフローを実行する
        サブフロー内ではmcutで['顧客', '数量']列を取得し、
        mselstrで顧客がAのものを返している（dd2=一致出力、dd3=不一致出力）
        さらにメインフローで結果をそれぞれmcutしている

        サブフローの出力するdd2と、結果をmcutしたdd5をキャッシュする
        """

        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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

        flow_json = copy.deepcopy(mainflow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_datum_2)
        flow_json['nodes'].append(self.create_data_dst_node('dd4'))
        flow_json['nodes'].append(self.create_data_dst_node('dd5'))

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub2', sub_uuid)

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = self.save_flow('test', flow_json)

        # 単純なlastsのテスト
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd4': [['顧客'], ['A'], ['A']], 'dd5': [['数量'], ['1'], ['3'], ['1']]}

        # テスト

        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd4'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd5'].uuid))
        result_dd4 = self.get_frame_by_uuid(lasts['dd4'].uuid)
        result_dd5 = self.get_frame_by_uuid(lasts['dd5'].uuid)
        self.assertEqual(result_dd4, correct['dd4'])
        self.assertEqual(result_dd5, correct['dd5'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = self.factory.data.find_by_uuid(flow.uuid)
        flow_data = flow.flow_data
        cache_nodes = [node for node in flow_data.get_nodes() if node['id'] in ['dd2', 'dd5']]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(self.factory.data.find_by_uuid(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        self.delete_flow(flow.uuid)
        self.delete_flow(sub_uuid)
        lasts['dd4'].delete()
        lasts['dd5'].delete()
        self.delete_caches(cache_uuids)

    # @unittest.skip
    def test_simploe_flow_include_subflow_execute_use_flowparam(self):
        """
        サブフローが1つのフローを実行する
        フローパラメータを使用する
        """
        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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
        self.create_flow('sub3', sub_uuid)

        mainflow_json['nodes'].append(self.create_data_dst_node('dd2'))
        mainflow_json['nodes'].append(self.create_data_dst_node('dd3'))

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd2': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'dd3': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd3'].uuid))
        result_dd2 = self.get_frame_by_uuid(lasts['dd2'].uuid)
        result_dd3 = self.get_frame_by_uuid(lasts['dd3'].uuid)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue(self.delete_flow(sub_uuid))
        lasts['dd2'].delete()
        lasts['dd3'].delete()

    # @unittest.skip
    def test_simploe_flow_include_subflow_execute_use_flowparams_in_one_line(self):
        """
        サブフローが1つのフローを実行する
        1つの項目で2つのフローパラメータを使用する
        """
        mainflow_json = {
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
                    "srcs": { "入力": "dd1" },
                    "dsts": { "出力1": "dd2" , "出力2": "dd3"}
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
        self.create_flow('sub4', sub_uuid)

        mainflow_json['nodes'].append(self.create_data_dst_node('dd2'))
        mainflow_json['nodes'].append(self.create_data_dst_node('dd3'))

        flow = self.root.create_flow('メインフロー', FlowData(mainflow_json))
        lasts = execute(FlowCommand(flow), {}, {})
        lasts = convert_from_job(lasts)
        correct = {'dd2': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'dd3': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['dd3'].uuid))
        result_dd2 = self.get_frame_by_uuid(lasts['dd2'].uuid)
        result_dd3 = self.get_frame_by_uuid(lasts['dd3'].uuid)
        self.assertEqual(result_dd2, correct['dd2'])
        self.assertEqual(result_dd3, correct['dd3'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['dd2'].delete()
        lasts['dd3'].delete()

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

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'test_data.csv', data)
        update_flow_node_uuid(self.flow_json_use_by_csv, 'i', frame.uuid)

        flow_json = copy.deepcopy(self.flow_json_use_by_csv)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow= self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d1': [['顧客', '数量'], ['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()
        frame.delete()

    # @unittest.skip
    def test_simple_flow_execute_data_source_from_cache(self):
        """
        mコマンド3個のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd_1)
        flow_json['nodes'].append(add_datum_1)
        flow_json['nodes'].append(add_cmd_2)
        flow_json['nodes'].append(add_datum_2)
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        # 中間データ作成
        data = [
            ['顧客','数量'],
            ['A',1],
            ['A',2]
        ]

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(flow_json, 'd2', frame.uuid)

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量'],['A', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        result = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result, correct['d3'])

        # 後片付け
        lasts['d3'].delete()
        frame.delete()

    # @unittest.skip
    def test_simple_subflow_execute_by_append_inputs(self):
        """
        1つのサブフローを実行する
        外部からframeを与えて実行する
        args指定はなし
        """
        # フローJSONを取得する
        flow_json = copy.deepcopy(get_flow_json_by_flow_id('sub2'))
        # サブフローにデータデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d3'))
        flow_json['nodes'].append(self.create_data_dst_node('d4'))
        # サブフローを作成する
        flow = self.root.create_flow('sub2', FlowData(flow_json))
        flow.uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        flow.save()

        # フローを実行する
        inputs = {
            '入力': Matrix([["顧客", "数量", "金額"],
                           ["A", 1, 10],
                           ["A", 2, 20],
                           ["B", 1, 30],
                           ["B", 3, 40],
                           ["B", 1, 50]])
        }
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, inputs)
        print(lasts)
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'd4': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d4'].uuid))
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = self.get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        self.assertTrue (self.delete_flow(flow.uuid))
        lasts['d3'].delete()
        lasts['d4'].delete()

    # @unittest.skip
    def test_simple_subflow_execute_by_append_inputs_and_args(self):
        """
        1つのサブフローを実行する
        外部からframeを与えて実行する
        args指定する
        """
        # フローJSONを取得する
        flow_json = get_flow_json_by_flow_id('sub3')
        # サブフローにデータデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d3'))
        flow_json['nodes'].append(self.create_data_dst_node('d4'))
        # サブフローを作成する
        flow = self.root.create_flow('sub3', FlowData(flow_json))
        flow.uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        flow.save()

        # フローを実行する
        inputs = {
            '入力': Matrix([["顧客", "数量", "金額"],
                           ["A", 1, 10],
                           ["A", 2, 20],
                           ["B", 1, 30],
                           ["B", 3, 40],
                           ["B", 1, 50]])
        }
        args = {
          'flow_args': {
            "sensor": "0,1",
            "customer": "顧客"
          }
        }
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, args, inputs)
        lasts = convert_from_job(lasts)
        correct = {'d3': [['顧客', '数量'], ['A', '1'], ['A', '2']], 'd4': [['顧客', '数量'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d4'].uuid))
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = self.get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        self.assertTrue(self.delete_flow(flow.uuid))
        lasts['d3'].delete()
        lasts['d4'].delete()

    @unittest.skip('もともとskip状態')
    def test_simple_flow_execute_use_mcat(self):
        """
        mコマンド1個（2つのinputを持つ）のフロー実行
        mcatの実行テスト
        ※結合順不定なので、失敗することもある。（きちんと結合されてはいる）
        """
        flow_data = FlowData(self.flow_json_inputs_mcat)
        flow = self.root.create_flow(self.flow_json_inputs_mcat['label'], flow_data)
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d1': Matrix([['A', '1', '10'],
                              ['A', '2', '20'],
                              ['B', '1', '30'],
                              ['B', '3', '40'],
                              ['B', '1', '50'],
                              ["C", '3', '10'],
                              ["C", '4', '20']])
                  }

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    @unittest.skip('MCMDのmchkcsvに代わり、nysol_pythonのutil.mchkcsvに変更したので、このテストは失敗する')
    def test_simple_flow_execute_use_nmcmd(self):
        """
        mコマンド2個のフロー実行
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

        flow_json = copy.deepcopy(self.flow_json)
        flow_json['nodes'].append(add_cmd)
        flow_json['nodes'].append(add_datum)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2':[['顧客', '数量'], ['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        result = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

    @unittest.skip('MCMDのmchkcsvに代わり、nysol_pythonのutil.mchkcsvに変更したので、このテストは失敗する')
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

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_json_use_mchkcsv, 'i', frame.uuid)

        # キャッシュ生成時にjsonを書き換える処理があるため、一旦物理ファイル化
        flow_json = copy.deepcopy(self.flow_json_use_mchkcsv)
        flow_json['nodes'].append(self.create_data_dst_node('d1'))
        flow = self.save_flow('test', flow_json)

        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        caches = convert_from_job_cache(lasts)
        results = convert_from_job(lasts)

        correct = {'d1':[['顧客', '数量', '金額'],['A', '1', '10'],['A', '2', '20'],['B', '1', '30'],['B', '3', '40'],['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(results['d1'].uuid))
        result = self.get_frame_by_uuid(results['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # キャッシュが生成されているか
        self.assertEqual(len(caches), 1, msg='Cache CommandのPort(u)をActivity Commandに繋げてないためcacheを取得できない')
        self.assertIsNotNone(self.factory.data.find_by_uuid(caches['d1'].uuid))
        result = self.get_frame_by_uuid(caches['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = self.factory.data.find_by_uuid(flow.uuid)
        flow_data = flow.flow_data
        cache_nodes = [node for node in flow_data.get_nodes() if node['id'] in ['d1']]
        for node in cache_nodes:
            # キャッシュが生成されているか
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(self.factory.data.find_by_uuid(node['uuid']))
            cache_uuids.append(node['uuid'])

        # 後片付け
        self.delete_flow(flow.uuid)
        results['d1'].delete()
        frame.delete()
        self.delete_caches(cache_uuids)

    @unittest.skip('selrow無くなったので、、')
    def test_simple_flow_execute_two_outputs_pcmd(self):
        """
        独自コマンド1個（2つのoutputを持つ）のフロー実行
        """
        data = [["顧客", "数量", "金額"],
                ["A", 1, 10],
                ["A", 2, 20],
                ["B", 1, 30],
                ["B", 3, 40],
                ["B", 1, 50]]

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_json_outputs_pcmd, 'i', frame.uuid)

        flow_json = copy.deepcopy(self.flow_json_outputs_pcmd)
        flow_json['nodes'].append(self.create_data_dst_node('d2'))
        flow_json['nodes'].append(self.create_data_dst_node('d3'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)

        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']],
                   'd3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d2 = self.get_frame_by_uuid(lasts['d2'].uuid)
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d2, correct['d2'])
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        lasts['d2'].delete()
        lasts['d3'].delete()
        frame.delete()

    # 二股コマンドの片一方の出力先にPointを繋げない場合のテストになる
    # mselrowのFIFOの関係で、nm.runs()でフリーズする。
    # だが、そもそもそのようなフローはフローエディタでは作成不可能なので
    # このテストは無効である
    @unittest.skip('無効')
    def test_simple_flow_execute_two_outputs_pcmd_one_side_o(self):
        """
        独自コマンド1個（2つのoutputを持つ）のフロー実行
        oだけ設置
        """
        data = [["顧客", "数量", "金額"],
            ["A", 1, 10],
            ["A", 2, 20],
            ["B", 1, 30],
            ["B", 3, 40],
            ["B", 1, 50]]

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_json_outputs_pcmd, 'i', frame.uuid)

        # 出力uを消す
        flow_json = self.flow_json_outputs_pcmd
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                # node['dsts'] = {'o': 'd2'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd3']
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result_d3, correct['d2'])

        # 後片付け
        lasts['d2'].delete()
        frame.delete()

    # 二股コマンドの片一方の出力先にPointを繋げない場合のテストになる
    # mselrowのFIFOの関係で、nm.runs()でフリーズする。
    # だが、そもそもそのようなフローはフローエディタでは作成不可能なので
    # このテストは無効である
    @unittest.skip('無効')
    def test_simple_flow_execute_two_outputs_pcmd_one_side_u(self):
        """
        独自コマンド1個（2つのoutputを持つ）のフロー実行
        uだけ設置
        """
        data = [["顧客", "数量", "金額"],
                ["A", 1, 10],
                ["A", 2, 20],
                ["B", 1, 30],
                ["B", 3, 40],
                ["B", 1, 50]]

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data_a.csv', data)
        update_flow_node_uuid(self.flow_json_outputs_pcmd, 'i', frame.uuid)

        # 出力oを消す
        flow_json = self.flow_json_outputs_pcmd
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                # ⬇️これしたらnm.runs()でフリーズ！
                # node['dsts'] = {'u': 'd3'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd2']

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        self.assertEqual(result_d3, correct['d3'])

        # 後片付け
        lasts['d3'].delete()
        frame.delete()

    def test_same_inputs(self):
        """
        一つのデータソースから二入力して結合する
        """
        flow_json = {
          "label": "mcat", 
          "nodes": [
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": "4392797b-54da-406c-9482-57b572359c27", 
              "label": "testData", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "label": "c1", 
              "commandId": "mcat", 
              "type": "command", 
              "args": {}, 
              "srcs": {
                "*0": "d1", 
                "*1": "d1"
              }, 
              "dsts": {
                "o": "d2"
              }, 
              "srcsOrder": [
                "*0", 
                "*1"
              ]
            },
            {
              "id": "d2", 
              "type": "frame", 
              "uuid": None, 
              "label": "d2", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
          ], 
          "ports": [
            [],
            [
                {
                  "type": "frame", 
                  "label": "d2", 
                  "nodeId": "d2"
                }
            ]
          ],
          "params": [], 
          "creator": "ユーザー管理者", 
          "createdAt": "2021-03-14 08:50:40", 
          "projectId": None, 
          "description": ""
        }

        # 入力データを作成する
        data = [
            ['顧客', '数量', '金額'],
            ["A", 1, 10],
            ["A", 2, 20],
            ["B", 1, 30],
            ["B", 3, 40],
            ["B", 1, 50]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'tst.csv', data)
        
        # フローJSONの入力データにUUIDを設定する
        update_flow_node_uuid(flow_json, 'd1', frame.uuid)

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        # フローを作成する
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d2 = [['顧客', '数量', '金額'], ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'],
                      ['B','1','50'], ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
        result_d2 = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(correct_d2, result_d2)

        # 結果ファイルを削除する
        lasts['d2'].delete()
        # データソースを削除する
        frame.delete()

    def test_same_frame_inputs(self):
        """
        同じフレームを共有する二つのデータソースを結合する
        """
        flow_json = {
          "label": "mcat", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": "4392797b-54da-406c-9482-57b572359c27", 
              "error": {}, 
              "label": "testData", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": "4392797b-54da-406c-9482-57b572359c27", 
              "label": "testData", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "label": "c1", 
              "commandId": "mcat", 
              "type": "command", 
              "args": {}, 
              "srcs": {
                "*0": "d1", 
                "*1": "d"
              }, 
              "dsts": {
                "o": "d2"
              }, 
              "srcsOrder": [
                "*0", 
                "*1"
              ]
            },
            {
              "id": "d2", 
              "type": "frame", 
              "uuid": None, 
              "label": "d2", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
          ], 
          "ports": [
            [],
            [
                {
                  "type": "frame", 
                  "label": "d2", 
                  "nodeId": "d2"
                }
            ]
          ],
          "params": [], 
          "creator": "ユーザー管理者", 
          "createdAt": "2021-03-14 08:50:40", 
          "projectId": None, 
          "description": ""
        }

        # 入力データを作成する
        data = [
            ['顧客', '数量', '金額'],
            ["A", 1, 10],
            ["A", 2, 20],
            ["B", 1, 30],
            ["B", 3, 40],
            ["B", 1, 50]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'tst.csv', data)
        
        # フローJSONの入力データにUUIDを設定する
        update_flow_node_uuid(flow_json, 'd', frame.uuid)
        update_flow_node_uuid(flow_json, 'd1', frame.uuid)

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        # フローを作成する
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d2 = [['顧客', '数量', '金額'], ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50'],
                      ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
        result_d2 = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(correct_d2, result_d2)

        # 結果ファイルを削除する
        lasts['d2'].delete()
        # データソースを削除する
        frame.delete()

    def test_two_outputs_on_onepath(self):
        """
        一つの経路上に二つの出力ポイントがある場合
        """
        flow_json = {
          "label": "mcuta", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": None,
              "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            }, 
            {
              "id": "d2", 
              "type": "frame", 
              "uuid": None, 
              "label": "d2", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c2", 
              "args": {
                "f": "*"
              }, 
              "dsts": {
                "o": "d2"
              }, 
              "srcs": {
                "i": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              },
              {
                "type": "frame", 
                "label": "d2", 
                "nodeId": "d2"
              }
            ]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2019-11-14 11:34:32", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d1'))
        flow_json['nodes'].append(self.create_data_dst_node('d2'))

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(2, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d1 = [['顧客', '数量', '金額'], ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
        result_d1 = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(correct_d1, result_d1)
        result_d2 = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(correct_d1, result_d2)

        # 後片付け
        lasts['d1'].delete()
        lasts['d2'].delete()


    def test_output_on_source_point(self):
        """
        データソースポイントが出力ポイントとなる場合
        """
        flow_json = {
          "label": "q", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": None,
              "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
              "label": "testData", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1",
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "args": {
                "a": "add,add1", 
                "c": "1,2", 
                "precision": 10
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "size": {
                "width": 38, 
                "height": 38
              }, 
              "srcs": {
                "i": "d"
              }, 
              "type": "command", 
              "label": "計算", 
              "commandId": "mcal", 
              "srcsOrder": [
                "i"
              ]
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "testData", 
                "nodeId": "d"
              }
            ]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2019-12-04 13:54:46", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d'))

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d = [['顧客', '数量', '金額'], ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
        result_d = self.get_frame_by_uuid(lasts['d'].uuid)
        self.assertEqual(correct_d, result_d)

        # 後片付け
        lasts['d'].delete()


    def test_output_with_cache(self):
        """
        出力ポイントがキャッシュONの場合
        """
        flow_json = {
          "label": "q", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
                "uuid": None,
                "value": [["顧客", "数量", "金額"],
                          ["A", 1, 10],
                          ["A", 2, 20],
                          ["B", 1, 30],
                          ["B", 3, 40],
                          ["B", 1, 50]],
              "label": "testData", 
              "makeCache": True, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": True, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "args": {
                "a": "add,add1", 
                "c": "1,2", 
                "precision": 10
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "type": "command", 
              "error": {}, 
              "label": "計算", 
              "commandId": "mcal", 
              "srcsOrder": [
                "i"
              ]
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "testData", 
                "nodeId": "d"
              }, 
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              }
            ]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2019-12-04 13:54:46", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d'))
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.save_flow(self.flow_json['label'], flow_json)
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(2, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d = [['顧客', '数量', '金額'], ['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
        result_d = self.get_frame_by_uuid(lasts['d'].uuid)
        self.assertEqual(correct_d, result_d)
        correct_d1 = [['顧客', '数量', '金額', 'add', 'add1'], ['A','1','10','1','2'], ['A','2','20','1','2'], ['B','1','30','1','2'], ['B','3','40','1','2'], ['B','1','50','1','2']]
        result_d1 = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(correct_d1, result_d1)

        # 後片付け
        lasts['d'].delete()
        lasts['d1'].delete()


    def test_one_output_from_branch(self):
        """
        二股出力コマンドのうち一つだけを出力ポイントに指定した場合
        """
        flow_json = {
          "label": "p", 
          "nodes": [
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d4", 
              "size": {
                "width": 38, 
                "height": 38
              }, 
              "type": "frame", 
              "uuid": None, 
              "label": "d4", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c4", 
              "args": {
                "c": "${金額} > 30"
              }, 
              "dsts": {
                "o": "d1", 
                "u": "d4"
              }, 
              "size": {
                "width": 38, 
                "height": 38
              }, 
              "srcs": {
                "i": "d2"
              }, 
              "type": "command", 
              "label": "条件式による行選択", 
              "commandId": "msel", 
              "srcsOrder": [
                "i"
              ]
            }, 
            {
              "id": "d2", 
              "type": "frame", 
              "uuid": None,
              "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
              "label": "testData", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              }
            ]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2019-11-28 10:43:57", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # frameデータは1つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されている
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d1 = [['顧客', '数量', '金額'], ['B','3','40'], ['B','1','50']]
        result_d1 = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result_d1, correct_d1)

        # 後片付け
        lasts['d1'].delete()


    def test_two_vizs_on_onepath(self):
        """
        一つの経路上から二つのvisを取得する場合
        """
        flow_json = {
          "label": "loop", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": None,
              "value": [["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]],
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            }, 
            {
              "id": "d2", 
              "type": "frame", 
              "uuid": None, 
              "label": "d2", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c2", 
              "args": {
                "f": "*"
              }, 
              "dsts": {
                "o": "d2"
              }, 
              "srcs": {
                "i": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              }
            ]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2019-11-14 11:34:32", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 2
            }
          },
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 3
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは2つ生成されているか
        self.assertEqual(2, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20']], 'd2': [['A','1','10'], ['A','2','20'], ['B','1','30']]}
        self.assertDictEqual(lasts, correct)


    def test_vizs_duplicate_column_frame(self):
        """
        同じ列名を持つデータでもプレビューできる
        """
        # テストデータ作成
        data = [
            ['顧客', '顧客', '顧客'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'duplicate.csv', data)

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],[]], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)


    def test_vizs_empty_column_frame(self):
        """
        空列名を持つデータでもプレビューできる
        """
        # テストデータ作成
        data = [
            ['顧客', None, ''],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'empty.csv', data)

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],[]], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_percent_column_frame(self):
        """
        %名を持つデータでもプレビューできる
        """
        # テストデータ作成
        data = [
            ['A%', '%B%', '%C'],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'percent.csv', data)

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],[]], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_jag_csv_file(self):
        """
        ギザギザなCSVファイルもプレビューできる
        """
        # テストデータ作成
        data = [
            ['A', 'B', 'C'],
            ['A', 1, 10],
            ['A', 2],
            ['B'],
            ['B', 3, 40],
            ['B', 1]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'jag.csv', data)

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],[]], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d': [['A','1','10'], ['A','2',''],['B','',''], ['B','3','40'], ['B','1','']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_win_file(self):
        """
        Windows形式ファイルもプレビューできる
        """
        MY_TESTDATA_DIR = './streamcat-engine/streamcat/engine/tests/test_data/'
        frame = self.create_data2(Path(MY_TESTDATA_DIR) / '漢字読み.csv')

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],[]], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d': [['宇宙','そら','B'], ['宇宙','コスモ','A'],['強敵','とも','C'], ['刑事','デカ','C']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_mchkcsv(self):
        """
        mchkcsvによるCSVチェックの結果をプレビューできる
        """
        # テストデータ作成
        data = [
            ['A%', 'A%', None],
            ['A', 1, 10],
            ['A', 2, 20],
            ['B', 1, 30],
            ['B', 3, 40],
            ['B', 1, 50]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'mchkcsv_data.csv', data)

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "diagl": True
              },
              "srcs": {
                "i": "d"
              },
              "dsts": {
                "o": "d1"
              },
              "type": "command", 
              "label": "c1", 
              "commandId": "mchkcsv", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],[]], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], FlowData(flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        # 出力結果が大きいので文字数カウントで確認する
        self.assertEqual(len(lasts['d1']), 103)
        self.assertEqual(lasts['d1'][0][0], '# CSVファイル診断 ')
        self.assertEqual(lasts['d1'][102][0], '#-------------------------------------------------------------')

    def test_vizs_with_cache_on(self):
        """
        キャッシュONのポイントをプレビューできる
        """
        # テストデータ作成
        data = [
            ['A', 'B', 'C'],
            ['A', 1, 10],
            ['B', 2, 20]
        ]
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'tst.csv', data)

        flow_json = {
          "label": "vis", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid,
              "label": "testData.csv", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {
                "f": "*"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "列選択", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              # "uuid": frame.uuid, 
              "uuid": None,
              "label": "d1", 
              "makeCache": True, 
              "dataSource": "csv", 
              # "cacheCreatedAt": "2020-02-07 09:02:00"
              "cacheCreatedAt": None
            }
          ], 
          "ports":[[],
            [{
              "type": "frame", 
              "label": "d1", 
              "nodeId": "d1"
            }]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-01-22 16:11:00", 
          "projectId": None, 
          "description": ""
        }

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        # フローを保存して再取得する
        flow =self.save_flow(self.flow_json['label'], flow_json)
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'],['B','2','20']]}
        self.assertDictEqual(lasts, correct)

    def test_msim_with_params(self):
        """
        msimとmsummaryコマンドは引数にstr list型を持つが、
        フロー変数の置き換え処理でエラーにならないことを検証する
        """
        data = [
            ['A', 'B', 'C'],
            ['A', 1, 10],
            ['B', 2, 20]
        ]

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'tst.csv', data)

        flow_json = {
          "label": "err", 
          "nodes": [
            {
              "id": "d", 
              "type": "frame", 
              "uuid": frame.uuid, 
              "label": "testData", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": False, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }, 
            {
              "id": "c1", 
              "args": {
                "a": "fld1,fld2", 
                "c": [
                  "covar"
                ], 
                "f": "@[new_param1],@[new_param2]", 
                "bufcount": 10
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "type": "command", 
              "label": "二変数間の類似度の計算", 
              "commandId": "msim", 
              "srcsOrder": [
                "i"
              ]
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              }
            ]
          ], 
          "params": [
            {
              "name": "new_param1", 
              "type": "string", 
              "label": "new_param1"
            }, 
            {
              "name": "new_param2", 
              "type": "string", 
              "label": "new_param2"
            }
          ], 
          "creator": "開発用", 
          "createdAt": "2020-03-16 17:15:22", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        args = {'flow_args': {"new_param1":"B", "new_param2":"C"}}
        lasts = execute(FlowCommand(flow), args, {})
        lasts = convert_from_job(lasts)

        # frameデータは1つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されている
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d1 = [['fld1', 'fld2', 'covar'],['B', 'C', '2.5']]
        result_d1 = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result_d1, correct_d1)

        # 後片付け
        lasts['d1'].delete()

    def test_inputs_sort(self):
        """
        コマンドのrun()のinputs引数には
        入力Portのlabel順に入力値が格納されること
        """
        data00 = [['A', 'B', 'C'],
                  ['a', 0, 00],
                  ['b', 1, 10]]
        data01 = [['A', 'B', 'C'],
                  ['c', 2, 20],
                  ['d', 3, 30]]
        data02 = [['A', 'B', 'C'],
                  ['e', 4, 40],
                  ['f', 5, 50]]
        data03 = [['A', 'B', 'C'],
                  ['g', 6, 60],
                  ['h', 7, 70]]

        frame0 = self.create_data(Path(self.TESTDATA_DIR) / 'tst0.csv', data00)
        frame2 = self.create_data(Path(self.TESTDATA_DIR) / 'tst2.csv', data02)

        flow_json = {
          "label": "m2cat", 
          "nodes": [
            {
              "id": "d0",
              "label": "d0",
              "type": "frame",
              "uuid": frame0.uuid
            }, {
              "id": "d1",
              "label": "d1",
              "type": "frame",
              "value": data01
              # "uuid": frame1.uuid
            }, 
            {
              "id": "d2",
              "label": "d2",
              "type": "frame",
              "uuid": frame2.uuid
            }, 
            {
              "id": "d3",
              "label": "d3",
              "type": "frame",
              "value": data03
              # "uuid": frame3.uuid
            }, 
            {
              "id": "c1", 
              "label": "データの併合", 
              "type": "command",  
              "commandId": "mcat",
              "srcs": {
                "*1": "d1",
                "*0": "d0",
                "*3": "d3",
                "*2": "d2",
              }, 
              "dsts": {
                "o": "d9"
              },
              "srcsOrder": [
                "*1","*0","*3","*2"
              ]
            },
            {
              "id": "d9",
              "label": "d9",
              "type": "frame"
            }, 
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d9", 
                "nodeId": "d9"
              }
            ]
          ], 
          "params": [], 
          "creator": "開発用", 
          "createdAt": "2020-03-16 17:15:22", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d9'))

        flow = self.root.create_flow(flow_json['label'], FlowData(flow_json))
        outs = execute(FlowCommand(flow))
        outs = convert_from_job(outs)

        # frameデータは1つ生成されているか
        self.assertEqual(1, len(outs))
        # DBにframeデータが生成されている
        self.assertIsNotNone(self.factory.data.find_by_uuid(outs['d9'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        expected = [['A', 'B',  'C'],
                    ['a', '0',  '0'],
                    ['b', '1', '10'],
                    ['c', '2', '20'],
                    ['d', '3', '30'],
                    ['e', '4', '40'],
                    ['f', '5', '50'],
                    ['g', '6', '60'],
                    ['h', '7', '70']]
        result_d1 = self.get_frame_by_uuid(outs['d9'].uuid, header=True)
        self.assertEqual(result_d1, expected)

    def test_mcmd_error_with_two_outputs(self):
        """
        2出力のフローを実行すると、2つのMCMDErrorが取得できること
        """

        # 2つのMCommandは引数指定が誤っている
        flow_json = {
          "label": "エラーフロー", 
          "nodes": [
            {
              "id": "c", 
              "args": {
                "I": "1", 
                "S": "1", 
                "l": "10"
              }, 
              "dsts": {
                "o": "d"
              }, 
              "srcs": {}, 
              "type": "command", 
              "label": "c", 
              "invalid": {
                "a": [
                  "入力が必須の項目です"
                ]
              }, 
              "commandId": "mnewnumber", 
              "srcsOrder": []
            },
            {
              "id": "d", 
              "type": "frame", 
              "uuid": None, 
              "label": "d", 
              "makeCache": True, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {}, 
              "srcs": {
                "i": "d"
              }, 
              "dsts": {
                "o": "d1"
              }, 
              "type": "command", 
              "label": "c1", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": True, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d", 
                "nodeId": "d"
              }, 
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              }
            ]
          ], 
          "params": [], 
          "creator": "管理者", 
          "createdAt": "2020-09-07 13:47:56", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d'))
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        # フローを作成する
        flow =self.save_flow(self.flow_json['label'], flow_json)
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})

        # 出力ポイントとこれに対応するframeデータを取得する
        results = convert_from_job(lasts)
        # frameデータは作成されていないこと
        self.assertEqual(len(results), 0)

        # 出力ポイントとこれに対応するcacheデータを取得する
        caches = convert_from_job_cache(lasts)
        # キャッシュが作成されていないこと
        # (frameと異なり出力ポイントの要素も返さない)
        self.assertEqual(len(caches), 0)

        # 出力ポイントとこれに対応する例外を取得する
        results = convert_from_job_exs(lasts)
        # 2つの出力ポイントが返されること
        self.assertEqual(len(results), 2)
        self.assertIn('d', results)
        self.assertIn('d1', results)
        # 2つの出力ポイントから例外が出力されること
        self.assertEqual(len(results['d']), 4)
        self.assertEqual(len(results['d1']), 4)
        self.assertIsInstance(results['d'][0], MCMDError)
        self.assertIsInstance(results['d'][1], MCMDError)
        self.assertIsInstance(results['d'][2], MCMDError)
        self.assertIsInstance(results['d'][3], MCMDError)
        self.assertIsInstance(results['d1'][0], MCMDError)
        self.assertIsInstance(results['d1'][1], MCMDError)
        self.assertIsInstance(results['d1'][2], MCMDError)
        self.assertIsInstance(results['d1'][3], MCMDError)

    def test_mcmd_error_with_two_outputs2(self):
        """
        2出力のフローを実行すると、2つのMCMDErrorが取得できること
        """
        
        # 1つのMCommandは引数指定が誤っている
        flow_json = {
          "label": "エラーフロー", 
          "nodes": [
            {
              "id": "c", 
              "args": {
                "a": 'col',
                "I": "1", 
                "S": "1", 
                "l": "10"
              }, 
              "dsts": {
                "o": "d"
              }, 
              "srcs": {}, 
              "type": "command", 
              "label": "c", 
              "invalid": {
                "a": [
                  "入力が必須の項目です"
                ]
              }, 
              "commandId": "mnewnumber", 
              "srcsOrder": []
            },
            {
              "id": "d", 
              "type": "frame", 
              "uuid": None, 
              "label": "d", 
              "makeCache": True, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            },
            {
              "id": "c1", 
              "args": {}, 
              "dsts": {
                "o": "d1"
              }, 
              "srcs": {
                "i": "d"
              }, 
              "type": "command", 
              "label": "c1", 
              "commandId": "mcut", 
              "srcsOrder": [
                "i"
              ]
            },
            {
              "id": "d1", 
              "type": "frame", 
              "uuid": None, 
              "label": "d1", 
              "makeCache": True, 
              "dataSource": "csv", 
              "cacheCreatedAt": None
            }
          ], 
          "ports": [
            [], 
            [
              {
                "type": "frame", 
                "label": "d", 
                "nodeId": "d"
              }, 
              {
                "type": "frame", 
                "label": "d1", 
                "nodeId": "d1"
              }
            ]
          ], 
          "params": [], 
          "creator": "管理者", 
          "createdAt": "2020-09-07 13:47:56", 
          "projectId": None, 
          "description": ""
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d'))
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        # フローを作成する
        flow =self.save_flow(self.flow_json['label'], flow_json)
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})

        # 出力ポイントとこれに対応するframeデータを取得する
        results = convert_from_job(lasts)
        # frameデータは作成されていないこと
        # (1コマンドでもエラーが発生すれば全ての出力はない)
        self.assertEqual(len(results), 0)

        # 出力ポイントとこれに対応するcacheデータを取得する
        caches = convert_from_job_cache(lasts)
        # キャッシュが作成されていないこと
        # (frameと異なり出力ポイントの要素も返さない)
        self.assertEqual(len(caches), 0)

        # 出力ポイントとこれに対応する例外を取得する
        results = convert_from_job_exs(lasts)
        # 2つの出力ポイントが返されること
        self.assertEqual(len(results), 2)
        self.assertIn('d', results)
        self.assertIn('d1', results)
        # 2つの出力ポイントから例外が出力されること
        self.assertEqual(len(results['d']), 2)
        self.assertEqual(len(results['d1']), 2)
        self.assertIsInstance(results['d'][0], MCMDError)
        self.assertIsInstance(results['d1'][0], MCMDError)

    def test_run_error(self):
        """
        Commnad.run()から例外が送出される場合、CommandExceptionが取得できること
        """

        # squareコマンドに文字列を入力してエラーにする
        flow_json = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                [
                  {
                    "type": "frame", 
                    "label": "dd2", 
                    "nodeId": "dd2"
                  }
                ]
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [['Four']],
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
                }
            ]
        }

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('dd2'))

        # フローを作成する
        flow =self.save_flow(self.flow_json['label'], flow_json)
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})

        # 出力ポイントとこれに対応するframeデータを取得する
        results = convert_from_job(lasts)
        # frameデータは作成されていないこと
        self.assertEqual(len(results), 0)

        # 出力ポイントとこれに対応する例外を取得する
        results = convert_from_job_exs(lasts)
        # 2つの出力ポイントが返されること
        self.assertEqual(len(results), 1)
        self.assertIn('dd2', results)
        # 2つの出力ポイントから例外が出力されること
        self.assertEqual(len(results['dd2']), 1)
        self.assertIsInstance(results['dd2'][0], CommandException)

    def test_visz_run_error(self):
        """
        Commnad.run()から例外が送出される場合、CommandExceptionが取得できること
        """

        # squareコマンドに文字列を入力してエラーにする
        flow_json = {
            "description": "メインフロー",
            "label": "メインフロー",
            "params": [],
            "ports": [
                [],
                [
                  {
                    "type": "frame", 
                    "label": "dd2", 
                    "nodeId": "dd2"
                  }
                ]
            ],
            "nodes": [
                {
                    "id": "dd1",
                    "type": "int",
                    "value": [['Four']],
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
                }
            ]
        }

        vis_args = {
          "dd2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを作成する
        flow =self.save_flow(self.flow_json['label'], flow_json)
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})

        # 出力ポイントとこれに対応するvisデータを取得する
        # (対応するvisデータはNoneなので、convert_from_activity_visは使わない)
        results = convert_from_job(lasts)
        # visデータは作成されていないこと

        # 出力ポイントとこれに対応する例外を取得する
        results = convert_from_job_exs(lasts)
        # 2つの出力ポイントが返されること
        self.assertEqual(len(results), 1)
        self.assertIn('dd2', results)
        # 2つの出力ポイントから例外が出力されること
        self.assertEqual(len(results['dd2']), 1)
        self.assertIsInstance(results['dd2'][0], CommandException)

    def test_vizs_flow_with_input(self):
        """
        一つのフローと一つの入力ポイントが配置されている場合に、フローのプレビューができること
        """

        # 一つのフローと一つの入力ポイント
        flow_json = {
            "label": "err",
            "nodes": [
                {
                    "id": "d",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "error": {},
                    "label": "percent",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 119
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "percent",
                    "invalid": {},
                    "position": {
                        "x": 233,
                        "y": 119
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d2",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d2",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 283
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {
                        "f": "*"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d"
                    },
                    "type": "command",
                    "error": {},
                    "label": "c1",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 201
                    },
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                }
            ],
            "ports": [
                [
                    {
                        "type": "frame",
                        "label": "percent",
                        "nodeId": "d1"
                    }
                ],
                []
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2021-02-22 13:48:21",
            "projectId": None,
            "description": ""
        }
    
        vis_args = {
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを作成する
        flow = self.root.create_flow('', FlowData(flow_json))
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d2': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_flow_with_output(self):
        """
        一つのフローと一つの出力ポイントが配置されている場合に、フローのプレビューができること
        """

        # 一つのフローと一つの出力ポイント
        flow_json = {
            "label": "err",
            "nodes": [
                {
                    "id": "d",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "error": {},
                    "label": "percent",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 119
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "percent",
                    "invalid": {},
                    "position": {
                        "x": 233,
                        "y": 119
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d2",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d2",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 283
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {
                        "f": "*"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d"
                    },
                    "type": "command",
                    "error": {},
                    "label": "c1",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 201
                    },
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "percent",
                        "nodeId": "d1"
                    }
                ]
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2021-02-22 13:48:21",
            "projectId": None,
            "description": ""
        }
    
        vis_args = {
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを作成する
        flow = self.root.create_flow('', FlowData(flow_json))
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d2': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_flow_with_inoutput(self):
        """
        一つのフローと一つの入出力ポイントが配置されている場合に、フローのプレビューができること
        """

        # 一つのフローと一つの入出力ポイント
        flow_json = {
            "label": "err",
            "nodes": [
                {
                    "id": "d",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "error": {},
                    "label": "percent",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 119
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "percent",
                    "invalid": {},
                    "position": {
                        "x": 233,
                        "y": 119
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d2",
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "type": "frame",
                    "uuid": None,
                    "error": {},
                    "label": "d2",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 283
                    },
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {
                        "f": "*"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                    "size": {
                        "width": 38,
                        "height": 38
                    },
                    "srcs": {
                        "i": "d"
                    },
                    "type": "command",
                    "error": {},
                    "label": "c1",
                    "invalid": {},
                    "position": {
                        "x": 99,
                        "y": 201
                    },
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                }
            ],
            "ports": [
                [
                    {
                        "type": "frame",
                        "label": "percent",
                        "nodeId": "d1"
                    }
                ],
                [
                    {
                        "type": "frame",
                        "label": "percent",
                        "nodeId": "d1"
                    }
                ]
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2021-02-22 13:48:21",
            "projectId": None,
            "description": ""
        }
    
        vis_args = {
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを作成する
        flow = self.root.create_flow('', FlowData(flow_json))
        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d2': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

    @unittest.skip('メインフローのflowオブジェクトで送出された例外はActivityに渡されない')
    def test_visz_subflow_with_datasource(self):
        """
        入力ポイントとデータソースを配置すフローをプレビューする
        """

        sub_flow_json = {
            "label": "subflow3",
            "nodes": [
                {
                    "id": "d",
                    "type": "frame",
                    "uuid": None,
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {},
                    "srcs": {
                        "*0": "d1",
                        "*1": "d"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                    "type": "command",
                    "label": "c1",
                    "commandId": "mcat",
                    "srcsOrder": [
                        "*0",
                        "*1"
                    ]
                },
                {
                    "id": "d2",
                    "type": "frame",
                    "uuid": None,
                    "label": "d2",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ],
            "ports": [
                [
                    {
                        "type": "frame",
                        "label": "percent",
                        "nodeId": "d"
                    }
                ],
                [
                    {
                        "type": "frame",
                        "label": "d2",
                        "nodeId": "d2"
                    }
                ]
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2021-03-02 12:19:27",
            "projectId": None,
            "description": ""
        }

        # サブフローを作成する
        sub_flow = self.root.create_flow('', FlowData(sub_flow_json))
        sub_flow.save()
        sub_flow = sub_flow.reload()

        vis_args = {
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを実行する
        flow_link = FlowCommand(sub_flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})

        print(lasts)

        # 出力ポイントとこれに対応するvisデータを取得する
        # (対応するvisデータはNoneなので、convert_from_activity_visは使わない)
        results = convert_from_job(lasts)
        # 2つの出力ポイントが返されること
        self.assertEqual(len(results), 1)
        self.assertIn('d2', results)
        # visデータは作成されていないこと
        self.assertIsNone(results['d2'])

        # 出力ポイントとこれに対応する例外を取得する
        results = convert_from_job_exs(lasts)
        # 2つの出力ポイントが返されること
        self.assertEqual(len(results), 1)
        self.assertIn('d2', results)
        # 2つの出力ポイントから例外が出力されること
        self.assertEqual(len(results['d2']), 1)
        self.assertIsInstance(results['d2'][0], CommandException)

    def test_subflow_with_input_on_way1(self):
        """
        フローの途中に入力ポイントを配置するサブフローを呼び出せること
        (フローJSONでのNodeの並び順によって結果が変わらないこと)
        """

        sub_flow_json = {
            "label": "subflow2",
            "nodes": [
                {
                    "id": "d2",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客0", "数量1", "金額2"],
                              ["x", 10, 100],
                              ["x", 20, 200],
                              ["y", 10, 300],
                              ["y", 30, 400],
                              ["y", 10, 500]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d3",
                    "type": "frame",
                    "uuid": None,
                    "label": "d3",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d3"
                    },
                    "dsts": {
                        "o": "d1"
                    },
                    "type": "command",
                    "label": "c1",
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "c2",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d2"
                    },
                    "dsts": {
                        "o": "d3"
                    },
                    "type": "command",
                    "label": "c2",
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "label": "d1",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ],
            "ports": [
                [
                    {
                        "type": "frame",
                        "label": "d3",
                        "nodeId": "d3"
                    }
                ],
                [
                    {
                        "type": "frame",
                        "label": "d1",
                        "nodeId": "d1"
                    }
                ]
            ]
        }

        flow_json = {
            "label": "main2",
            "nodes": [
                {
                    "id": "d",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "label": "d1",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "args": {},
                    "dsts": {
                        "d1": "d1"
                    },
                    "srcs": {
                        "d3": "d"
                    },
                    "type": "flow",
                    "uuid": "5cd94ccf-a1bb-4cae-82ed-d75ddb77c535",
                    "label": "f1",
                    "srcsOrder": [
                        "d3"
                    ]
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "d1",
                        "nodeId": "d1"
                    }
                ]
            ]
        }

        # サブフローを作成する
        sub_flow = self.root.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = '5cd94ccf-a1bb-4cae-82ed-d75ddb77c535'
        sub_flow.save()

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        # フローを作成する
        flow = self.root.create_flow('', FlowData(flow_json))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_subflow_with_input_on_way2(self):
        """
        フローの途中に入力ポイントを配置するサブフローを呼び出せること
        (フローJSONでのNodeの並び順によって結果が変わらないこと)
        """

        sub_flow_json = {
            "label": "subflow2",
            "nodes": [
                {
                    "id": "d2",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客0", "数量1", "金額2"],
                              ["x", 10, 100],
                              ["x", 20, 200],
                              ["y", 10, 300],
                              ["y", 30, 400],
                              ["y", 10, 500]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c2",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d2"
                    },
                    "dsts": {
                        "o": "d3"
                    },
                    "type": "command",
                    "label": "c2",
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d3",
                    "type": "frame",
                    "uuid": None,
                    "label": "d3",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d3"
                    },
                    "dsts": {
                        "o": "d1"
                    },
                    "type": "command",
                    "label": "c1",
                    "commandId": "mcut",
                    "srcsOrder": [
                        "i"
                    ]
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "label": "d1",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ],
            "ports": [
                [
                    {
                        "type": "frame",
                        "label": "d3",
                        "nodeId": "d3"
                    }
                ],
                [
                    {
                        "type": "frame",
                        "label": "d1",
                        "nodeId": "d1"
                    }
                ]
            ]
        }

        flow_json = {
            "label": "main2",
            "nodes": [
                {
                    "id": "d",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "label": "d1",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "args": {},
                    "dsts": {
                        "d1": "d1"
                    },
                    "srcs": {
                        "d3": "d"
                    },
                    "type": "flow",
                    "uuid": "5cd94ccf-a1bb-4cae-82ed-d75ddb77c535",
                    "label": "f1",
                    "srcsOrder": [
                        "d3"
                    ]
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "d1",
                        "nodeId": "d1"
                    }
                ]
            ]
        }

        # サブフローを作成する
        sub_flow = self.root.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = '5cd94ccf-a1bb-4cae-82ed-d75ddb77c535'
        sub_flow.save()

        # データデストを追加する
        flow_json['nodes'].append(self.create_data_dst_node('d1'))

        # フローを作成する
        flow = self.root.create_flow('', FlowData(flow_json))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_subflow_with_datasource(self):
        """
        入力ポイントとデータソースを配置するサブフローを呼び出せること
        """

        sub_flow_json = {
            "label": "subflow3",
            "nodes": [
                {
                    "id": "d",
                    "type": "frame",
                    "uuid": None,
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "args": {},
                    "srcs": {
                        "*0": "d1",
                        "*1": "d"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                    "type": "command",
                    "label": "c1",
                    "commandId": "mcat",
                    "srcsOrder": [
                        "*0",
                        "*1"
                    ]
                },
                {
                    "id": "d2",
                    "type": "frame",
                    "uuid": None,
                    "label": "d2",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ],
            "ports": [
                [
                    {
                        "type": "frame",
                        "label": "percent",
                        "nodeId": "d"
                    }
                ],
                [
                    {
                        "type": "frame",
                        "label": "d2",
                        "nodeId": "d2"
                    }
                ]
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2021-03-02 12:19:27",
            "projectId": None,
            "description": ""
        }
  
        flow_json = {
            "label": "main2",
            "nodes": [
                {
                    "id": "d",
                    "type": "frame",
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                              ["A", 1, 10],
                              ["A", 2, 20],
                              ["B", 1, 30],
                              ["B", 3, 40],
                              ["B", 1, 50]],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "uuid": None,
                    "label": "d1",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "args": {},
                    "srcs": {
                        "percent": "d"
                    },
                    "dsts": {
                        "d2": "d1"
                    },
                    "type": "flow",
                    "uuid": "5cd94ccf-a1bb-4cae-82ed-d75ddb77c535",
                    "label": "f1"
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame",
                        "label": "d1",
                        "nodeId": "d1"
                    }
                ]
            ]
        }

        # サブフローを作成する
        sub_flow = self.root.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = '5cd94ccf-a1bb-4cae-82ed-d75ddb77c535'
        sub_flow.save()

        # フローを作成する
        flow = self.root.create_flow('', FlowData(flow_json))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50'],
                          ['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    # Helpler
    def get_frame_by_uuid(self, uuid, header=True):
        """
        指定したuuidのframeを取得する
        """
        import csv
        result = []
        frame = self.factory.data.find_by_uuid(uuid)
        try:
          with open(frame.path, 'r') as f:
              rows = csv.reader(f)
              if header:
                  header = next(rows)
                  result.append(header)
              for row in rows:
                  result.append(row)
        except Exception as e:
          # import pprint
          # pprint.pprint(f)
          raise e

        return result

    def create_data(self, file_path_obj, data=None):
        """
        テストデータ作成用
        frameが返る
        """
        import io
        # if data is not None:
        #     nm.mread(i=data, o=file_path_obj.as_posix()).run()
        if data is not None:
            with file_path_obj.open('w') as f:
                import csv
                writer = csv.writer(f, lineterminator='\n')
                writer.writerows(data)

        frame = self.root.create_frame(file_path_obj.name, io.BytesIO(b''))
        frame.save(file_path=file_path_obj)
        # save()によりreadable=Noneになるため再取得する
        return frame.reload()

    def create_data2(self, file_path_obj):
        """
        テストデータ作成用
        frameが返る
        """
        with file_path_obj.open('rb') as f:
            frame = self.root.create_frame(file_path_obj.name, f)
            frame.save()
        # save()によりreadable=Noneになるため再取得する
        return frame.reload()

    def save_flow(self, label, flow_json):
        new_flow = self.root.create_flow(label, FlowData(flow_json))
        new_flow.save()
        # save()によりreadable=Noneになるため再取得する
        return new_flow.reload()

    def create_flow(self, flow_id, uuid):
        """
        指定されたidのフローを作成し、そのフローを返す
        """
        from .make_flow_json import test_json
        flow_json = test_json[flow_id]
        flow = self.root.create_flow('test', FlowData(flow_json))
        flow.uuid = uuid
        flow.save()
        # save()によりreadable=Noneになるため再取得する
        return flow.reload()

    def delete_flow(self, uuid):
        try:
            flow = self.factory.data.find_by_uuid(uuid)
            flow.delete()
        except Exception as e:
            print(e)
            return False
        return True

    def delete_caches(self, cache_uuids):
        for cache_uuid in cache_uuids:
          cache = self.factory.data.find_by_uuid(cache_uuid)
          cache.delete()

def update_flow_node_uuid(flow_json, node_id, uuid):
    """
    指定したflow_jsonのnode_idをuuidで更新する
    """
    for node in flow_json['nodes']:
        if node['id'] == node_id:
            node['uuid'] = uuid
            return True
    return False

def convert_from_job(job):
    """
    execute()の戻り値から
    pointのidとframeのDictに置き換える
    """
    from streamcat.store import ApparentOuts
    # Activityを取得して返り値とする
    for point_id, datum in job.join().items():
        if isinstance(datum, ApparentOuts):
            return {out.out_point.id : out.datum for out in datum.outs}

def convert_from_job_vis(job):
    """
    execute()の戻り値から
    pointのidとvisのDictに置き換える
    """
    from streamcat.store import ApparentOuts
    for point_id, datum in job.join().items():
        if isinstance(datum, ApparentOuts):
            return {out.out_point.id : out.datum.result['reader'] for out in datum.outs}

def convert_from_job_cache(job):
    """
    execute()の戻り値から
    pointのidとcacheのDictに置き換える
    """
    from streamcat.store import ApparentOuts
    # Activityを取得して返り値とする
    for point_id, datum in job.join().items():
        if isinstance(datum, ApparentOuts):
            return {cache.out_point.id : cache.datum for cache in datum.caches}

def convert_from_job_exs(job):
    """
    execute()の戻り値から
    pointのidとframeのDictに置き換える
    """
    from streamcat.store import ApparentOuts
    # Activityを取得して返り値とする
    for point_id, datum in job.join().items():
        if isinstance(datum, ApparentOuts):
            return {ex.out_point.id : ex.exs for ex in datum.exs}
