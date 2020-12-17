import os
import copy
import uuid
import datetime
import unittest
import nysol.mcmd as nm

from pathlib import Path

from kskp.store import FlowData, Command, Port, List, Database, DatabaseConn
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
            "value": [['顧客','数量','金額'],
                ['A',1,10],
                ['A',2,20],
                ['B',1,30],
                ['B',3,40],
                ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['A',2,20],
                    ['B',1,30],
                    ['B',3,40],
                    ['B',1,50]],
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
                "value": [['顧客','数量','金額'],
                    ['A',1,10],
                    ['B',1,30]],
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
          raise e

        return result

    # @unittest.skip
    def test_simple_assert_command(self):
        """
        内容が違う２つの入力に対して、assert_commandを一つ配置したフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.simple_assert_json)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d1': [
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','3','A,2,20','B,1,30'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','4','B,1,30',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','5','B,3,40',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','6','B,1,50','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d1'].delete()

    # @unittest.skip
    def test_same_execute(self):
        """
        内容が同じ２つの入力に対して、assert_commandを一つ配置したフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.flow_json_same)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d1': [
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','True','False','','','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d1'].delete()


    # @unittest.skip
    def test_case_sequential_assert(self):
        """
        assert_commandが２連続で実行されるフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.sequential_assert_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','1','顧客,数量,金額','flow_label,flow_uuid,flow_path,date,point_id,is_true,raise_exs,diff_row_number,i_port_diff,m_port_diff'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','2','A,1,10','テストフロ,00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,0000-00-00 00:00:00.000000+00:00,d1,False,False,3,"A,2,20",""'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','3','A,2,20','テストフロ,00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,0000-00-00 00:00:00.000000+00:00,d1,False,False,4,"B,1,30",""'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','4','B,1,30','テストフロ,00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,0000-00-00 00:00:00.000000+00:00,d1,False,False,5,"B,3,40",""'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','5','B,3,40','テストフロ,00000000-0000-0000-0000-000000000000,/ライブラリ/テストフロ,0000-00-00 00:00:00.000000+00:00,d1,False,False,6,"B,1,50",""'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','6','B,1,50','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        # 比較するデータ内にタイムスタンプがあるので、文字列を置き換え。
        # コマンドの動作自体は別のコマンドがしてくれているので、ここではerrorが発生しないことを確認
        for s in results:
            s[9]= "Replacement of output information"
        for s in corrects['d2']:
            s[9]= "Replacement of output information"

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d2'].delete()

    # @unittest.skip
    def test_case_two_assert(self):
        """
        assert_commandが並列で2つの島にあるフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.double_assert_json)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'},{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {
        'd1':[
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','3','A,2,20','B,1,30'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','4','B,1,30',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','5','B,3,40',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','False','6','B,1,50','']
        ],
        'd2': [
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','3','A,2,20','B,1,30'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','4','B,1,30',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','5','B,3,40',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','False','6','B,1,50','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)
        results2 = self.get_frame_by_uuid(lasts['d2'].uuid)


        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results2, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d1'].delete()
        lasts['d2'].delete()


    # @unittest.skip
    def test_one_side_error_assert(self):
        """
        assert_commandの入力の一方がエラーのフローを実行、出力結果をテストする
        エラーはnysol_pythonのモジュールから発せられるものを使用する
        """
        json_flow = copy.deepcopy(self.one_side_error_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','1','顧客,数量,金額','MCMDError:#ERROR# parameter a= is mandatory (kgNewnumber); kgNewnumber;  OUT=0; 2020/09/13 16:54:32; 2020/09/13 16:54:32'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','2','A,1,10',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','3','A,2,20',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','4','B,1,30',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','5','B,3,40',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','6','B,1,50','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d2'].delete()


    # @unittest.skip
    def test_same_both_error_assert(self):
        """
        assert_commandの入力の両方がエラーのフローを実行、出力結果をテストする
        エラー内容はどちらも同じ
        エラーはnysol_pythonのモジュールから発せられるものを使用する
        """
        json_flow = copy.deepcopy(self.both_same_error_json)
        json_flow['ports'] = [[],[{'nodeId':'d2', 'label':'d2', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {
            'd2': [
                ['テストフロ','fa95ec62-5141-44fb-b4b0-f680139b4adc','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','True','True','','','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)


        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))
            
            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

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

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {'d2': [
            ['テストフロ','cb4cf7ad-44de-4df9-a7b7-a4d5a4201d81','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d2','False','True','None','MCMDError:#ERROR# parameter a= is mandatory (kgNewnumber); kgNewnumber;  OUT=0; 2020/09/12 11:24:50; 2020/09/12 11:24:50','MCMDError:#ERROR# parameter a= is mandatory (kgnewrand); kgnewrand;  OUT=0; 2020/09/12 11:24:50; 2020/09/12 11:24:50']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d2'].uuid)

        results, corrects['d2'] = self.check_equal(results, corrects['d2'])

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d2']))
        for result,correct in zip(results, corrects['d2']):
            self.assertEqual(len(result), len(correct))

            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d2'].delete()

    @unittest.skip
    def test_error_groupby2(self):
        """
        特徴量コマンドにてエラーが発生するフローを実行、出力結果をテストする
        """
        json_flow = copy.deepcopy(self.error_groupby2_json)
        json_flow['ports'] = [[],[{'nodeId':'d1', 'label':'d1', 'type':'frame'}]]

        flow = self.root.create_flow(json_flow['label'], FlowData(json_flow))
        flow.save()
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        # 正解データ内のuuid, タイムスタンプはダミー、テスト実行時には、毎回変動するので、出力がされているかどうかのみ確認する
        corrects = {
            'd1': [['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','True','1','顧客,数量,金額','【コマンド：特徴量の計算】【オプション欄：f】指定した項目名は存在しません。random1'],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','True','2','A,1,10',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','True','3','A,2,20',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','True','4','B,1,30',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','True','5','B,3,40',''],
            ['テストフロ','00000000-0000-0000-0000-000000000000','/ライブラリ/テストフロ','0000-00-00 00:00:00.000000+00:00','d1','False','True','6','B,1,50','']
        ]}
        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(self.factory.data.exists(lasts['d1'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        results = self.get_frame_by_uuid(lasts['d1'].uuid)

        # 出力の一致を確認
        self.assertEqual(len(results), len(corrects['d1']))
        for result,correct in zip(results, corrects['d1']):
            self.assertEqual(len(result), len(correct))

            self.assertEqual(result[0], correct[0])
            self.assertIsNotNone(result[1])
            self.assertEqual(result[2], correct[2])
            self.assertIsNotNone(result[3])
            self.assertEqual(result[4], correct[4])
            self.assertEqual(result[5], correct[5])
            self.assertEqual(result[6], correct[6])
            self.assertEqual(result[7], correct[7])
            self.assertEqual(result[8], correct[8])
            self.assertEqual(result[9], correct[9])

        # 後片付け
        lasts['d1'].delete()


    def check_equal(self, result, correct):
        """
        MCommandが出すエラーにあるタイムスタンプ部位を取り除く
        """
        # TODO:
        # mcmd_error_infoのMCMDErrorにタイムスタンプを取り除く処理を描こうとしたが、
        # mコマンドにもエラーメッセージでタイムスタンプが出ないものがあり対応に時間が取られるため、後回し


        for row in result:
            if row[8].find('MCMDError') != -1:
                row[8] = row[8][:-42]

            if row[9].find('MCMDError') != -1:
                row[9] = row[9][:-42]

        for row in correct:
            if row[8].find('MCMDError') != -1:
                row[8] = row[8][:-42]

            if row[9].find('MCMDError') != -1:
                row[9] = row[9][:-42]

        return result, correct


def convert_from_activity(lasts):
    """
    execute()の戻り値から
    pointのidとframeのDictに置き換える
    """
    from kskp.store import Activity
    # Activityを取得して返り値とする
    for point_id, datum in lasts.items():
        if isinstance(datum, Activity):
            return {point.id : frame for point, frame in datum.lasts}

            