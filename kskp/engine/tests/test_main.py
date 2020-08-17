import os
import copy
import uuid
import unittest
import nysol.mcmd as nm

from pathlib import Path

from kskp.store import Command, Port, List, Database, DatabaseConn
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowJsonLink

class ExecuteTestCase(TestCaseBase):
    """
    実際のフロー実行のテスト
    """

    # mコマンド１つのフロー
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

    # mコマンド１つのフロー（csvから読み取り）
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

    # mコマンド１つのフロー（csvから読み取り）
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

    # outputが２つあるフロー
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

    # outputが２つあるフロー（独自コマンド）
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

    # inputとoutputが２つあるフロー
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

    @classmethod
    def setUpClass(cls):
        # 親クラスのsetUpClass()を実行する
        TestCaseBase.setUpClass()
        cls.root = cls.factory.data.load_root()
        cls.TESTDATA_DIR = cls.root.path


    @classmethod
    def tearDownClass(cls):
        # 親クラスのtearDownClass()を実行する
        TestCaseBase.tearDownClass()

    # @unittest.skip
    def test_simple_flow_execute(self):
        """
        mコマンド１個のフロー実行
        """
        json_flow = copy.deepcopy(self.flow_json)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}
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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d2': [['A', '1'], ['A', '2']]}

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

        json_flow = copy.deepcopy(self.flow_json)
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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
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

        json_flow = copy.deepcopy(self.flow_json)
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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'},
                                  {'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d2': [['A', '1'], ['A', '2']], 'd3': [['B', '1'], ['B', '3'], ['B', '1']]}

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

        json_flow = copy.deepcopy(self.flow_json)
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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

    # @unittest.skip
    def test_simple_flow_execute_two_inputs(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        json_flow = copy.deepcopy(self.flow_json_inputs)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d1': [['A', '1', '10', '21'],
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
        mコマンド１個（２つのoutputを持つ）のフロー実行
        """
        json_flow = copy.deepcopy(self.flow_json_outputs)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'},
                                  {'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]
        
        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
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

    # @unittest.skip
    def test_simple_flow_execute_two_outputs_one_side_o(self):
        """
        mコマンド１個（２つのoutputを持つ）のフロー実行
        oだけ設置
        """
        # 出力uを消す
        flow_json = copy.deepcopy(self.flow_json_outputs)
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'o': 'd2'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd3']
        flow_json['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d2': [['A', '1', '10'], ['A', '2', '20']]}

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
        mコマンド１個（２つのoutputを持つ）のフロー実行
        uだけ設置
        """
        # 出力oを消す
        flow_json = copy.deepcopy(self.flow_json_outputs)
        for node in flow_json['nodes']:
            if node['id'] == 'c1':
                node['dsts'] = {'u': 'd3'}
                break
        flow_json['nodes'] = [node for node in flow_json['nodes'] if node['id'] != 'd2']
        flow_json['ports'] = [[],[{'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['B', '1', '30'], ['B', '3', '40'], ['B', '1', '50']]}

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

        flow = self.root.create_flow(self.flow_json_outputs['label'], self.flow_json_outputs)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
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

        flow = self.root.create_flow(self.flow_json_outputs['label'], self.flow_json_outputs)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_datum_2)
        json_flow['ports'] = [[],[{'nodeId':'d3', 'label':'lbl', 'type':'frame'},
                                  {'nodeId':'d4', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

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

        json_flow = copy.deepcopy(self.flow_json)
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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
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

        json_flow = copy.deepcopy(self.flow_json)
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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)
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

        json_flow = copy.deepcopy(self.flow_json_inputs_mnewnumber)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
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
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_simple_flow_execute_use_mnrcommon(self):
        """
        mコマンド１個（2つもinputを持ち、2つのoutputをもつ）のフロー実行
        mnrcommonの実行テスト
        """
        json_flow = copy.deepcopy(self.flow_json_outputs_and_inputs)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'},
                                  {'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d2': [['20080203', '10'], ['20080203', '45']],
                   'd3': [['20080123', '10'], ['20080203', '20'], ['20080410', '50']]}

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
        self.create_flow('sub1', sub_uuid)

        json_mainflow['ports'] = [[],[{'nodeId':'dd3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory), {}, {})
        lasts = convert_from_activity(lasts)
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
        self.create_flow('sub1', sub_uuid)

        json_mainflow['ports'] = [[],[{'nodeId':'dd3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory), {}, {})
        lasts = convert_from_activity(lasts)
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
        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data_z.csv', data)
        update_flow_node_uuid(json_mainflow, 'dd1', frame.uuid)

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

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory, vis_args), {}, {})
        lasts = convert_from_activity_vis(lasts)
        correct = {'dd2': [['256']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

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
        self.create_flow('sub2', sub_uuid)

        json_mainflow['ports'] = [[],[{'nodeId':'dd2', 'label':'lbl', 'type':'frame'},
                                      {'nodeId':'dd3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory), {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

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

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory, vis_args), {}, {})
        lasts = convert_from_activity_vis(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

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

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory, vis_args), {}, {})
        lasts = convert_from_activity_vis(lasts)
        correct = {'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

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
                [
                  {
                    "type": "frame",
                    "label": "ラベル",
                    "nodeId": "dd4"
                  },
                  {
                    "type": "frame",
                    "label": "ラベル",
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
        self.create_flow('sub2', sub_uuid)

        flow = self.root.create_flow(json_flow['label'], json_flow)
        lasts = execute(FlowJsonLink(flow, self.factory), {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}

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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        lasts = execute(FlowJsonLink(flow, self.factory, vis_args), {}, {})
        lasts = convert_from_activity_vis(lasts)
        correct = {'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

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

        flow = self.root.create_flow(json_flow['label'], json_flow)
        lasts = execute(FlowJsonLink(flow, self.factory, vis_args), {}, {})
        lasts = convert_from_activity_vis(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd5': [['1'], ['3'], ['1']]}

        # テスト
        # 正しいVisが得られるか
        self.assertDictEqual(lasts, correct)

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))

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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)
        json_flow['ports'] = [[],[{'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = self.save_flow('test', json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['A', '1']]}

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


        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)
        json_flow['ports'] = [[],[{'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = self.save_flow('test', json_flow)

        # 単純な実行結果のテスト
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['A', '1']]}

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
        json_flow['ports'] = [[],[{'nodeId':'dd4', 'label':'lbl', 'type':'frame'},
                                  {'nodeId':'dd5', 'label':'lbl', 'type':'frame'}]]

        # テスト用のフロー作成
        # キャッシュを生成するテストなので、nodeのuuidが書き換わっているかのテストも行わないといけないため
        flow = self.save_flow('test', json_flow)

        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub2', sub_uuid)

        # 単純なlastsのテスト
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'dd4': [['A'], ['A']], 'dd5': [['1'], ['3'], ['1']]}

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
        self.create_flow('sub3', sub_uuid)

        json_mainflow['ports'] = [[],[{'nodeId':'dd2', 'label':'lbl', 'type':'frame'},
                                      {'nodeId':'dd3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory), {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

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
        self.create_flow('sub4', sub_uuid)

        json_mainflow['ports'] = [[],[{'nodeId':'dd2', 'label':'lbl', 'type':'frame'},
                                      {'nodeId':'dd3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow('メインフロー', json_mainflow)
        lasts = execute(FlowJsonLink(flow, self.factory), {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'dd2': [['A', '1'], ['A', '2']], 'dd3': [['B', '1'], ['B', '3'], ['B', '1']]}

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

        json_flow = copy.deepcopy(self.flow_json_use_by_csv)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'lbl', 'type':'frame'}]]

        flow= self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d1': [['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd_1)
        json_flow['nodes'].append(add_datum_1)
        json_flow['nodes'].append(add_cmd_2)
        json_flow['nodes'].append(add_datum_2)
        json_flow['ports'] = [[],[{'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        # 中間データ作成
        data = [
            ['顧客','数量'],
            ['A',1],
            ['A',2]
        ]

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(json_flow, 'd2', frame.uuid)

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['A', '1']]}

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
        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub2', sub_uuid)

        flow = self.factory.data.find_by_uuid(sub_uuid)
        flow_link = FlowJsonLink(flow, self.factory)

        inputs = {
            'd1': List([["顧客", "数量", "金額"],
                        ["A", 1, 10],
                        ["A", 2, 20],
                        ["B", 1, 30],
                        ["B", 3, 40],
                        ["B", 1, 50]])
        }
        lasts = execute(flow_link, {}, inputs)
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d4'].uuid))
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = self.get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['d3'].delete()
        lasts['d4'].delete()

    # @unittest.skip
    def test_simple_subflow_execute_by_append_inputs_and_args(self):
        """
        1つのサブフローを実行する
        外部からframeを与えて実行する
        args指定する
        """
        # サブフローの作成
        sub_uuid = '62dbe8d6-5f09-450e-a0b8-fab88ecfafd3'
        self.create_flow('sub3', sub_uuid)

        flow = self.factory.data.find_by_uuid(sub_uuid)
        flow_link = FlowJsonLink(flow, self.factory)

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

        lasts = execute(flow_link, args, inputs)
        lasts = convert_from_activity(lasts)
        correct = {'d3': [['A', '1'], ['A', '2']], 'd4': [['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d3'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d4'].uuid))
        result_d3 = self.get_frame_by_uuid(lasts['d3'].uuid)
        result_d4 = self.get_frame_by_uuid(lasts['d4'].uuid)
        self.assertEqual(result_d3, correct['d3'])
        self.assertEqual(result_d4, correct['d4'])

        # 後片付け
        self.assertTrue (self.delete_flow(sub_uuid))
        lasts['d3'].delete()
        lasts['d4'].delete()

    @unittest.skip('もともとskip状態')
    def test_simple_flow_execute_use_mcat(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        mcatの実行テスト
        ※結合順不定なので、失敗することもある。（きちんと結合されてはいる）
        """
        flow = self.root.create_flow(self.flow_json_inputs_mcat['label'], self.flow_json_inputs_mcat)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
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
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d2':[['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        result = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

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

        json_flow = copy.deepcopy(self.flow_json)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d2':[['A', '1'], ['A', '2'], ['B', '1'], ['B', '3'], ['B', '1']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        result = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

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

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_json_use_mchkcsv, 'i', frame.uuid)

        # キャッシュ生成時にjsonを書き換える処理があるため、一旦物理ファイル化
        json_flow = copy.deepcopy(self.flow_json_use_mchkcsv)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'lbl', 'type':'frame'}]]
        flow = self.save_flow('test', json_flow)

        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d1':[['A', '1', '10'],['A', '2', '20'],['B', '1', '30'],['B', '3', '40'],['B', '1', '50']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
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
        lasts['d1'].delete()
        frame.delete()
        self.delete_caches(cache_uuids)

    @unittest.skip('selrow無くなったので、、')
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

        frame = self.create_data(Path(self.TESTDATA_DIR) / 'cache_data.csv', data)
        update_flow_node_uuid(self.flow_json_outputs_pcmd, 'i', frame.uuid)

        json_flow = copy.deepcopy(self.flow_json_outputs_pcmd)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'},
                                  {'nodeId':'d3', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)

        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
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
        独自コマンド１個（２つのoutputを持つ）のフロー実行
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
        flow_json['ports'] = [[],[{'nodeId':'d2', 'label':'lbl', 'type':'frame'}]]

        flow = self.root.create_flow(flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
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
        独自コマンド１個（２つのoutputを持つ）のフロー実行
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

        flow = self.root.create_flow(flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
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


    def test_two_outputs_on_onepath(self):
        """
        一つの経路上に二つの出力ポイントがある場合
        """
        flow_json = {
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(2, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d1 = [['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
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

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d = [['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
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

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.save_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # frameデータは2つ生成されているか
        self.assertEqual(2, len(lasts))
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d = [['A','1','10'], ['A','2','20'], ['B','1','30'], ['B','3','40'], ['B','1','50']]
        result_d = self.get_frame_by_uuid(lasts['d'].uuid)
        self.assertEqual(correct_d, result_d)
        correct_d1 = [['A','1','10','1','2'], ['A','2','20','1','2'], ['B','1','30','1','2'], ['B','3','40','1','2'], ['B','1','50','1','2']]
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

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # frameデータは1つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されている
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d1 = [['B','3','40'], ['B','1','50']]
        result_d1 = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(correct_d1, result_d1)

        # 後片付け
        lasts['d1'].delete()


    def test_two_vizs_on_onepath(self):
        """
        一つの経路上から二つのvisを取得する場合
        """
        flow_json = {
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d': [['A','1','10'], ['A','2',''],['B','',''], ['B','3','40'], ['B','1','']]}
        self.assertDictEqual(lasts, correct)

    def test_vizs_win_file(self):
        """
        Windows形式ファイルもプレビューできる
        """
        MY_TESTDATA_DIR = '../kskp-flow-engine/kskp/engine/tests/test_data/'
        frame = self.create_data2(Path(MY_TESTDATA_DIR) / '漢字読み.csv')

        flow_json = {
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow = self.root.create_flow(self.flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "c5fafc1c-19a3-4be2-809b-10991163a421", 
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
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

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
          "uuid": "f1426e63-4a78-4cd7-8811-09ba89b185ae", 
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
          "description": "", 
          "projectName": "test"
        }

        flow = self.root.create_flow(flow_json['label'], flow_json)
        lasts = execute(FlowJsonLink(flow, self.factory), {"new_param1":"B", "new_param2":"C"}, {})
        lasts = convert_from_activity(lasts)

        # frameデータは1つ生成されているか
        self.assertEqual(1, len(lasts))
        # DBにframeデータが生成されている
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        correct_d1 = [['B', 'C', '2.5']]
        result_d1 = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(correct_d1, result_d1)

        # 後片付け
        lasts['d1'].delete()

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
        frameのuuidが返る
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
        return self.factory.data.find_by_uuid(frame.uuid)

    def create_data2(self, file_path_obj):
        """
        テストデータ作成用
        frameのuuidが返る
        """
        import io
        with file_path_obj.open('rb') as f:
            frame = self.root.create_frame(file_path_obj.name, f)
            frame.save()
        # save()によりreadable=Noneになるため再取得する
        return self.factory.data.find_by_uuid(frame.uuid)

    def save_flow(self, label, flow_json):
        new_flow = self.root.create_flow(label, flow_json)
        new_flow.save()
        # save()によりreadable=Noneになるため再取得する
        return self.factory.data.find_by_uuid(new_flow.uuid)

    def create_flow(self, flow_id, uuid):
        """
        指定されたidのフローを作成し、そのuuidを返す
        """
        from .make_flow_json import test_json
        flow_json = test_json[flow_id]
        flow = self.root.create_flow('test', flow_json)
        flow.uuid = uuid
        flow.save()
        # save()によりreadable=Noneになるため再取得する
        return self.factory.data.find_by_uuid(flow.uuid)

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

@unittest.skip('古いので失敗する。改修予定')
class ExecuteTestCase2(unittest.TestCase):

    # mコマンド１つのフロー
    flow_json = {
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

    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 
      'port'     : 5432, 
      'database' : "kskp", 
      'user_id'  : "kskp", 
      'password' : r'J2-pH|%B'
    }
    database_conn = DatabaseConn(conn_json)

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
        self.create_flow('postgre_src', postgre_src)

        # サブフロー(PostgreSQLデータデスト)の作成
        postgre_dst = 'b3e980d4-8338-4e83-a238-dd4537148c43'
        self.create_flow('postgre_dst', postgre_dst)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = self.root.create_flow(self.flow_json['label'], self.flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # テスト
        # DBにframeデータが生成されているか
        # self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        # result = self.get_frame_by_uuid(lasts['d1'].uuid)
        # self.assertEqual(result, correct['d1'])

        # 後片付け
        self.assertTrue (self.delete_flow(postgre_src))
        self.assertTrue (self.delete_flow(postgre_dst))


def update_flow_node_uuid(flow_json, node_id, uuid):
    """
    指定したflow_jsonのnode_idをuuidで更新する
    """
    for node in flow_json['nodes']:
        if node['id'] == node_id:
            node['uuid'] = uuid
            return True
    return False

def convert_from_activity(lasts):
    """
    execute()の戻り値から
    pointのidとframeのDictに置き換える
    """
    from kskp.store import Activity
    # Activityを取得して返り値とする
    for point_id, datum in lasts.items():
        if isinstance(datum, Activity):
            return {point.id : frame for point, frame in datum.results}

def convert_from_activity_vis(lasts):
    """
    execute()の戻り値から
    pointのidとvisのDictに置き換える
    """
    from kskp.store import Activity
    for point_id, datum in lasts.items():
        if isinstance(datum, Activity):
            return {point.id : vis.result['reader'] for point, vis in datum.results}

