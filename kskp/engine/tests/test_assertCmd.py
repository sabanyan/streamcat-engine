import os
import copy
import uuid
import datetime
import unittest
import nysol.mcmd as nm

from pathlib import Path

from kskp.store import Command, Port, List, Database, DatabaseConn
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowJsonLink

class ExecuteAssertCmdFlow(TestCaseBase):
    """
    AssertCommandの動作を確認するテストプログラム
    """
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
                "id": "c1", 
                "args": {
                "dlimit": "1"
                }, 
                "dsts": {
                "o": "d1"
                }, 
                "size": {
                "width": 38, 
                "height": 38
                }, 
                "srcs": {
                "i": "d1", 
                "m": "d"
                }, 
                "type": "command", 
                "error": {}, 
                "label": "c1", 
                "invalid": {}, 
                "position": {
                "x": 276.5, 
                "y": 254
                }, 
                "commandId": "assert", 
                "srcsOrder": [
                "i", 
                "m"
                ]
            }
        ]
    }

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
                "id": "c1", 
                "args": {
                "dlimit": "10"
                }, 
                "dsts": {
                "o": "d1"
                }, 
                "srcs": {
                "i": "i", 
                "m": "i2"
                }, 
                "type": "command", 
                "error": {}, 
                "label": "c1", 
                "commandId": "assert"
            }
        ]
    }

    # test　コマンドへの、両者の入力が同じデータの場合

    flow_json_inputs2 = {
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
                "value": [["ant","sas"],
                    [39,30],
                    [18,30],
                    [11,30],
                    [25,30],
                    [2,30],
                    [14,30],
                    [20,30],
                    [44,30],
                    [10,30],
                    [10,30]],
                "dataSource": "csv"
            },
            {
                "id": "c1", 
                "args": {
                "dlimit": "10"
                }, 
                "dsts": {
                "o": "d1"
                }, 
                "srcs": {
                "i": "i", 
                "m": "i2"
                }, 
                "type": "command", 
                "error": {}, 
                "label": "c1", 
                "commandId": "assert"
            }
        ]
    }

    raal_flow_data = {
        "label": "test_ftlow",
        "nodes": [
            {
                "id": "d",
                "size": {
                    "width": 38,
                    "height": 38
                },
                "type": "frame",
                "uuid": None,
                "error": {},
                "label": "d",
                "invalid": {},
                "position": {
                    "x": 111,
                    "y": 256
                },
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "c",
                "args": {
                    "S": "10",
                    "a": "ランダム生成した数",
                    "l": "20",
                    "int": True,
                    "max": "10",
                    "min": "0"
                },
                "dsts": {
                    "o": "d"
                },
                "size": {
                    "width": 38,
                    "height": 38
                },
                "srcs": {},
                "type": "command",
                "error": {},
                "label": "c",
                "invalid": {},
                "position": {
                    "x": 104,
                    "y": 145
                },
                "commandId": "mnewrand",
                "srcsOrder": []
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
                "label": "d1",
                "invalid": {},
                "position": {
                    "x": 429.5,
                    "y": 430
                },
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "c1",
                "args": {
                    "S": "10",
                    "a": "ランダム生成した数",
                    "l": "20",
                    "int": True,
                    "max": "10",
                    "min": "0"
                },
                "dsts": {
                    "o": "d1"
                },
                "size": {
                    "width": 38,
                    "height": 38
                },
                "srcs": {},
                "type": "command",
                "error": {},
                "label": "c1",
                "invalid": {},
                "position": {
                    "x": 420.5,
                    "y": 131
                },
                "commandId": "mnewrand",
                "srcsOrder": []
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
                    "x": 62,
                    "y": 431
                },
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "d3",
                "size": {
                    "width": 38,
                    "height": 38
                },
                "type": "frame",
                "uuid": None,
                "error": {},
                "label": "d3",
                "invalid": {},
                "position": {
                    "x": 197,
                    "y": 432
                },
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "c2",
                "args": {
                    "s": "ランダム生成した数",
                    "to": "10",
                    "from": "0"
                },
                "dsts": {
                    "o": "d2",
                    "u": "d3"
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
                "label": "c2",
                "invalid": {},
                "position": {
                    "x": 111,
                    "y": 350
                },
                "commandId": "mbest",
                "srcsOrder": [
                    "i"
                ]
            },
            {
                "id": "d4",
                "size": {
                    "width": 38,
                    "height": 38
                },
                "type": "frame",
                "uuid": None,
                "error": {},
                "label": "d4",
                "invalid": {},
                "position": {
                    "x": 318.25,
                    "y": 604
                },
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
            },
            {
                "id": "c3",
                "args": {
                    "dlimit": "50"
                },
                "dsts": {
                    "o": "d4"
                },
                "size": {
                    "width": 38,
                    "height": 38
                },
                "srcs": {
                    "i": "d2",
                    "m": "d1"
                },
                "type": "command",
                "error": {},
                "label": "c3",
                "invalid": {},
                "position": {
                    "x": 312.25,
                    "y": 525
                },
                "commandId": "assert",
                "srcsOrder": [
                    "i",
                    "m"
                ]
            }
        ],
        "ports": [
            [],
            [
                {
                    "type": "frame",
                    "label": "d4",
                    "nodeId": "d4"
                }
            ]
        ],
        "params": [],
        "creator": "管理者",
        "createdAt": "2020-07-30 15:33:14",
        "projectId": None,
        "description": ""
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

    @unittest.skip
    def test_flow_execute(self):
        """
        testFlowを実行
        """
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



        # json = copy.deepcopy(flow_json)
        # json['ports'] = [[], [{"type": "frame", "label": "d2", "nodeId": "d2"}]]


        # flow = self.root.create_flow(json['label'], flow_json)
        flow = self.root.create_flow(flow_json['label'], flow_json)
        flow_link = FlowJsonLink(flow, self.factory)
        # print(flow_link)
        lasts = execute(flow_link, {}, {})
        
        from pprint import pprint
        pprint(flow_link)
        pprint(lasts)

        lasts = convert_from_activity(lasts)
        print(lasts)
        nowtime = str(datetime.date.today())
        
        # 想定出力結果
        correct = {
            "d2" : [
                ["flow_UUID","parent_project_UUID", "date", "T/F", "diff"],
                ["53e38e82-7966-4c00-a631-f4815f8f9455", "",nowtime, "True", ""]
            ]
        }
        # テスト
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)
        self.assetEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()


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

    @unittest.skip
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

    @unittest.skip
    def test_simple_flow_execute_two_inputs(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        json_flow = copy.deepcopy(self.flow_json_inputs)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        print(lasts)
        lasts = convert_from_activity(lasts)
        correct = {'d1': [['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}
        correct = {'d1': [["A", "1", "10"],
                    ["A", "2", "20"],
                    ["B", "1", "30"],
                    ["B", "3", "40"],
                    ["B", "1", "50"],
                    []]}
        print(lasts)
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_simple_flow_execute_two_inputs2(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        json_flow = copy.deepcopy(self.flow_json_inputs2)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        print(lasts)
        lasts = convert_from_activity(lasts)
        correct = {'d1': [['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}
        correct = {'d1': [["A", "1", "10"],
                    ["A", "2", "20"],
                    ["B", "1", "30"],
                    ["B", "3", "40"],
                    ["B", "1", "50"],
                    []]}
        print(lasts)
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()


    @unittest.skip
    def test_real_flow_execute(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        json_flow = copy.deepcopy(self.raal_flow_data)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        print(lasts)
        lasts = convert_from_activity(lasts)
        correct = {'d1': [['A', '1', '10', '21'],
                          ['A', '2', '20', '21'],
                          ['B', '1', '30', '31'],
                          ['B', '3', '40', '31'],
                          ['B', '1', '50', '31']]}
        correct = {'d1': [["A", "1", "10"],
                    ["A", "2", "20"],
                    ["B", "1", "30"],
                    ["B", "3", "40"],
                    ["B", "1", "50"],
                    []]}
        print(lasts)
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()


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

            