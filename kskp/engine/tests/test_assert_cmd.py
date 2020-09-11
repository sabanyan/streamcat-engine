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

    maxDiff = None
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
            "value": [["顧客","数量","金額"],
                ["A",1,10],
                ["A",2,20],
                ["B",1,30],
                ["B",3,40],
                ["B",1,50]],
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

    simple_assert_json = {
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["B",1,30]],
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

    flow_json_same = {
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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

    sequential_assert_json = {
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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
                "type": "frame",
                "id": "d2",
                "label": "d2",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "type": "frame",
                "label": "テストデータ2",
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["B",1,30]],
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
            },
            {
                "id": "c2",
                "args": {
                "dlimit": "10"
                },
                "dsts": {
                "o": "d2"
                },
                "srcs": {
                "i": "i",
                "m": "d1"
                },
                "type": "command",
                "error": {},
                "label": "c2",
                "commandId": "assert"
            }
        ]
    }

    double_assert_json = {
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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
                "type": "frame",
                "id": "d2",
                "label": "d2",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "i2",
                "type": "frame",
                "label": "テストデータ2",
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["B",1,30]],
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
            },
            {
                "id": "c2",
                "args": {
                "dlimit": "10"
                },
                "dsts": {
                "o": "d2"
                },
                "srcs": {
                "i": "i",
                "m": "i2"
                },
                "type": "command",
                "error": {},
                "label": "c2",
                "commandId": "assert"
            }
        ]
    }

    one_side_error_json = {
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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
                "id": "c2",
                "type": "command",
                "label": "c2",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d1"
                },
                "error": {}
            },
            {
                "type": "frame",
                "id": "d2",
                "label": "d2",
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
                "id": "c1",
                "args": {
                "dlimit": "10"
                },
                "dsts": {
                "o": "d2"
                },
                "srcs": {
                "i": "i",
                "m": "d1"
                },
                "type": "command",
                "error": {},
                "label": "c1",
                "commandId": "assert"
            }
        ]
    }

    both_same_error_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [
            [],
            []
        ],
        "nodes": [
            {
                "id": "c3",
                "type": "command",
                "label": "c3",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d3"
                },
                "error": {}
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
                "id": "d1",
                "label": "d1",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "type": "command",
                "label": "c2",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d1"
                },
                "error": {}
            },
            {
                "type": "frame",
                "id": "d1",
                "label": "d1",
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
                "id": "c1",
                "args": {
                "dlimit": "10"
                },
                "dsts": {
                "o": "d2"
                },
                "srcs": {
                "i": "d3",
                "m": "d1"
                },
                "type": "command",
                "error": {},
                "label": "c1",
                "commandId": "assert"
            }
        ]
    }

    both_error_json = {
        "label": "テストフロ",
        "params": [],
        "description": "",
        "ports": [
            [],
            []
        ],
        "nodes": [
            {
                "id": "c3",
                "type": "command",
                "label": "c3",
                "commandId": "mnewnumber",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d3"
                },
                "error": {}
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
                "id": "d1",
                "label": "d1",
                "uuid": None,
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "type": "command",
                "label": "c2",
                "commandId": "mnewrand",
                "args": {},
                "srcs": {},
                "dsts": {
                    "o": "d1"
                },
                "error": {}
            },
            {
                "type": "frame",
                "id": "d1",
                "label": "d1",
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
                "id": "c1",
                "args": {
                "dlimit": "10"
                },
                "dsts": {
                "o": "d2"
                },
                "srcs": {
                "i": "d3",
                "m": "d1"
                },
                "type": "command",
                "error": {},
                "label": "c1",
                "commandId": "assert"
            }
        ]
    }

    error_groupby2_json = {
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["A",2,20],
                    ["B",1,30],
                    ["B",3,40],
                    ["B",1,50]],
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
                "value": [["顧客","数量","金額"],
                    ["A",1,10],
                    ["B",1,30]],
                "dataSource": "csv"
            },
            {
                "id": "c2",
                "type": "command",
                "label": "c2",
                "commandId": "groupby2",
                "args": {
                    "clist":[
                        {
                            "c": "",
                            "fld": ""
                        }
                    ],
                    "fclist": [
                        {
                            "c": "sum",
                            "f": "random1"
                        },
                        {
                            "c": "max",
                            "f": "random2"
                        },
                        {
                            "c": "min",
                            "f": "random3"
                        }
                    ],
                    "format": "&_%",
                    "nfclist": [
                        {
                            "c": "",
                            "f": "",
                            "n": ""
                        }
                    ],
                    "xfclist": [
                        {
                            "c": "",
                            "f": "",
                            "x": ""
                        }
                    ],
                    "xfcnlist": [
                        {
                            "c": "",
                            "f": "",
                            "n": "",
                            "x": ""
                        }
                    ],
                    "precision": "10",
                    "dataformat": "date"
                },
                "srcs": {
                    "i": "i2"
                },
                "dsts": {
                    "o": "d3"
                },
                "error": {}
            },
            {
                "type": "frame",
                "id": "d3",
                "label": "d3",
                "uuid": None,
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
                "m": "d3"
                },
                "type": "command",
                "error": {},
                "label": "c1",
                "commandId": "assert"
            }
        ]
    }

    @classmethod
    def setUpClass(cls):
        # 親クラスのsetUpClass()を実行する
        TestCaseBase.setUpClass()
        cls.root = cls.factory.data.load_root()
        cls.TESTDATA_DIR = cls.root.path
        maxDiff = None

    @classmethod
    def tearDownClass(cls):
        # 親クラスのtearDownClass()を実行する
        TestCaseBase.tearDownClass()

    # @unittest.skip
    def test_flow_execute(self):
        """
        本プログラムが正しく動作するか、確認するためのフロー
        本来のテスト対象であるassertコマンドをここでは動かさない
        """
        json = copy.deepcopy(self.flow_json)
        json['ports'] = [[], [{"type": "frame", "label": "d1", "nodeId": "d1"}]]

        flow = self.root.create_flow(json['label'], json)
        flow_link = FlowJsonLink(flow, self.factory)
        
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        
        # 想定出力結果
        correct = {
            "d1" : [
                ['A', '1'],
                ['A', '2'],
                ['B', '1'],
                ['B', '3'],
                ['B', '1']
            ]
        }
        # テスト
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        self.assertEqual(result, correct['d1'])

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

    # @unittest.skip
    def test_simple_assert_command(self):
        """
        mコマンド１個（２つのinputを持つ）のフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.simple_assert_json)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d1': [
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','1','A,2,20','B,1,30'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','2','B,1,30','null'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','3','B,3,40','null'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','4','B,1,50','null']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d1']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_same_execute(self):
        """
        mコマンド１個（２つのinputを持つ）のフロー実行
        """
        json_flow = copy.deepcopy(self.flow_json_same)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        correct = {'d1': [['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 08:31:17.329527+00:00','d1','True','False','nothing','nothing','nothing']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d1']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d1'])

        # 後片付け
        lasts['d1'].delete()


    # @unittest.skip
    def test_case_sequential_assert(self):
        """
        assert_commandが２連続で実行されるフローを実行、出力結果をテストする
        # 現状必ずエラーが発生する
        """
        

        json_flow = copy.deepcopy(self.sequential_assert_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        correct = {'d2': [['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 08:42:17.489747+00:00','d2','False','False','0','A,1,10','flow_label,flow_uuid,flow_path,parent_uuid,parent_label,date,point_id,is_true,raise_exs,diff_row_number,diff_result,diff_answer'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 08:42:17.489747+00:00','d2','False','False','1','A,2,20','テストフロ,0b70cdad-3901-4f2c-a47a-3b2507f5a91b,/ライブラリ/テストフロ,テストフロ,テストフロ,2020-09-10 08:42:17.489747+00:00,d1,False,False,1,"A,2,20","B,1,30"'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 08:42:17.489747+00:00','d2','False','False','2','B,1,30','テストフロ,0b70cdad-3901-4f2c-a47a-3b2507f5a91b,/ライブラリ/テストフロ,テストフロ,テストフロ,2020-09-10 08:42:17.489747+00:00,d1,False,False,2,"B,1,30","null"'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 08:42:17.489747+00:00','d2','False','False','3','B,3,40','テストフロ,0b70cdad-3901-4f2c-a47a-3b2507f5a91b,/ライブラリ/テストフロ,テストフロ,テストフロ,2020-09-10 08:42:17.489747+00:00,d1,False,False,3,"B,3,40","null"'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 08:42:17.489747+00:00','d2','False','False','4','B,1,50','テストフロ,0b70cdad-3901-4f2c-a47a-3b2507f5a91b,/ライブラリ/テストフロ,テストフロ,テストフロ,2020-09-10 08:42:17.489747+00:00,d1,False,False,4,"B,1,50","null"']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d2']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_case_two_assert(self):
        """
        assert_commandが並列で2つの島にあるフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.double_assert_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'},{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        correct = {'d2': [['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d2','False','False','1','A,2,20','B,1,30'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d2','False','False','2','B,1,30','null'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d2','False','False','3','B,3,40','null'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d2','False','False','4','B,1,50','null']],
        'd1':[
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','1','A,2,20','B,1,30'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','2','B,1,30','null'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','3','B,3,40','null'],
        ['テストフロ','0b70cdad-3901-4f2c-a47a-3b2507f5a91b','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-10 07:43:16.397353+00:00','d1','False','False','4','B,1,50','null']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d1'].uuid))
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)
        result2 = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d1']:
                ans[number] = result[0][number]
        for number in [1,5]:
            for ans in correct['d2']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d1'])
        self.assertEqual(result2, correct['d2'])

        # 後片付け
        lasts['d1'].delete()
        lasts['d2'].delete()


    @unittest.skip
    def test_one_side_error_assert(self):
        """
        assert_commandの入力の一方がエラーのフローを実行、出力結果をテストする
        エラーはnysol_pythonのモジュールから発せられるものを使用する
        # テスト出力のエラー文章内にタイムスタンプがあるため、正確に比較ができない。
        """
        json_flow = copy.deepcopy(self.one_side_error_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        correct = {'d2': [
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 01:39:48.810760+00:00','d2','False','True','0','A,1,10','MCMDError: no data found : /dev/stdin (kgload)'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 01:39:48.810760+00:00','d2','False','True','1','A,2,20','MCMDError:#ERROR# parameter a= is mandatory (kgNewnumber); kgNewnumber;  OUT=0; 2020/09/11 10:39:48; 2020/09/11 10:39:48'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 01:39:48.810760+00:00','d2','False','True','2','B,1,30','null'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 01:39:48.810760+00:00','d2','False','True','3','B,3,40','null'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 01:39:48.810760+00:00','d2','False','True','4','B,1,50','null']
            ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d2']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()


    # @unittest.skip
    def test_same_both_error_assert(self):
        """
        assert_commandの入力の両方がエラーのフローを実行、出力結果をテストする
        エラー内容はどちらも同じ
        エラーはnysol_pythonのモジュールから発せられるものを使用する
        # 実行のたびに出力内容が変わって、テストの成否が変わる。不安定
        """
        json_flow = copy.deepcopy(self.both_same_error_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        correct = {'d2': [['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 01:45:38.666279+00:00','d2','True','True','nothing','nothing','nothing']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d2']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()
    
    # @unittest.skip
    def test_both_error_assert(self):
        """
        assert_commandの入力の両方がエラーのフローを実行、出力結果をテストする
        エラー内容は左右で違うものを用意
        エラーはnysol_pythonのモジュールから発せられるものを使用する
        """
        json_flow = copy.deepcopy(self.both_error_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        correct = {'d2': [
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 02:08:32.453742+00:00','d2','False','True','None','MCMDError:#ERROR# parameter a= is mandatory (kgNewnumber); kgNewnumber;  OUT=0; 2020/09/11 11:08:32; 2020/09/11 11:08:32','MCMDError:#ERROR# parameter a= is mandatory (kgnewrand); kgnewrand;  OUT=0; 2020/09/11 11:08:32; 2020/09/11 11:08:32']]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.find_by_uuid(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d2']:
                ans[number] = result[0][number]

        self.assertEqual(result, correct['d2'])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_error_groupby2(self):
        """
        特徴量コマンドにてエラーが発生するフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.error_groupby2_json)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], json_flow)
        flow.save()
        # print(flow)
        # print(json_flow)
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        # print("executed")
        # print(lasts)
        lasts = convert_from_activity(lasts)
        # print(lasts)
        correct = {'d1': [
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 02:19:19.212191+00:00','d1','False','True','0','A,1,10','【コマンド：特徴量の計算】【オプション欄：f】指定した項目名は存在しません。random1'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 02:19:19.212191+00:00','d1','False','True','1','A,2,20','null'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 02:19:19.212191+00:00','d1','False','True','2','B,1,30','null'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 02:19:19.212191+00:00','d1','False','True','3','B,3,40','null'],
            ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','テストフロ','テストフロ','2020-09-11 02:19:19.212191+00:00','d1','False','True','4','B,1,50','null']
        ]}
        # print(lasts)
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 実行した日時、uuidがテスト実行毎に変動するので、正解データに実行結果の日時、uuidを実行結果から取得する(実行毎に変わるのではテストにできない)
        for number in [1,5]:
            for ans in correct['d1']:
                ans[number] = result[0][number]
        
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

            