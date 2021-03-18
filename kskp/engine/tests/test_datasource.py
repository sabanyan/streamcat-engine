import copy
import unittest
from kskp.store import FlowData
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowJsonLink
from .test_main import convert_from_activity_vis

class DataSourceTest(TestCaseBase):
    """
    フローの入出力指定の検証
    """

    def test_subflow_with_input_on_way(self):
        """
        フローの途中に入力ポイントを配置するサブフローを呼び出した場合、
        入力ポイントより手前のコマンドは実行されないこと
        """

        sub_flow_json = {
            "label": "test", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": None,
                    "value": [["顧客", "数量", "金額"],
                                ["x", 1, 10],
                                ["x", 2, 20],
                                ["y", 1, 30],
                                ["y", 3, 40],
                                ["z", 1, 50]],
                    "label": "d",
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                }, 
                {
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    # このコマンドが実行されれば無条件に例外を送出する
                    "commandId": "raise", 
                    "args": {},
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcsOrder": [
                        "i"
                    ]
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "uuid": None, 
                    "label": "d1", 
                    "position": {
                        "x": 99, 
                        "y": 283
                    }, 
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                }, 
                {
                    "id": "c2", 
                    "label": "c2", 
                    "type": "command", 
                    "commandId": "mcut", 
                    "args": {
                        "f": "*"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
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
                }
            ], 
            "ports": [
                [
                {
                    "type": "frame", 
                    "label": "d1", 
                    "nodeId": "d1"
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
            "createdAt": "2021-03-17 11:35:39", 
            "projectId": None, 
            "description": ""
        }

        flow_json = {
            "label": "main",
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
                    "id": "f1",
                    "args": {},
                    "srcs": {
                        "d1": "d"
                    },
                    "dsts": {
                        "d2": "d1"
                    },
                    "type": "flow",
                    "uuid": "4be05e2e-cc74-4570-bb6f-e2afe5503462",
                    "label": "f1",
                    "srcsOrder": [
                        "d3"
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

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # サブフローを作成する
        sub_flow = root.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = '4be05e2e-cc74-4570-bb6f-e2afe5503462'
        sub_flow.save()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json))

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
        # (RaiseCommandが実行されないこと)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_mainflow_with_input_on_way(self):
        """
        フローの途中に入力ポイントを配置するフローをメインフローとして実行した場合、
        入力ポイントは無視されること
        """

        flow_json = {
            "label": "test",
            "nodes": [
                {
                "id": "d",
                "label": "testData",
                "type": "frame",
                "uuid": None,
                "value": [["顧客", "数量", "金額"],
                            ["x", 1, 10],
                            ["x", 2, 20],
                            ["y", 1, 30],
                            ["y", 3, 40],
                            ["z", 1, 50]],
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
                },
                {
                "id": "c1",
                "label": "c1",
                "type": "command",
                "commandId": "mcut",
                "args": {
                    "f": "*"
                },
                "srcs": {
                    "i": "d"
                },
                "dsts": {
                    "o": "d1"
                },          
                "srcsOrder": [
                    "i"
                ]
                }, 
                {
                "id": "d1",
                "label": "d1",
                "type": "frame",
                "uuid": None,
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
                },
                {
                "id": "c2",
                "label": "c2",
                "type": "command",
                "commandId": "mcut",
                "args": {
                    "f": "*"
                },
                "srcs": {
                    "i": "d1"
                },
                "dsts": {
                    "o": "d2"
                },
                "srcsOrder": [
                    "i"
                ]
                },
                {
                "id": "d2",
                "label": "d2",
                "type": "frame",
                "uuid": None,
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
                },
                {
                "id": "c3",
                "label": "c3",
                "type": "command",
                "commandId": "mcut",
                "args": {
                    "f": "*"
                },
                "srcs": {
                    "i": "d2"
                },
                "dsts": {
                    "o": "d3"
                },
                "srcsOrder": [
                    "i"
                ]
                },
                {
                "id": "d3",
                "label": "d3",
                "type": "frame",
                "uuid": None,
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
                },
            ],
            "ports": [
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
                },
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
                },
                {
                    "type": "frame",
                    "label": "d2",
                    "nodeId": "d2"
                },
                {
                    "type": "frame",
                    "label": "d3",
                    "nodeId": "d3"
                }
                ]
            ],
            "params": [],
            "creator": "ユーザー管理者",
            "createdAt": "2021-03-17 11:35:39",
            "projectId": None,
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          },
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          },
          "d3": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }

        # フローを実行する
        # (RaiseCommandが実行されないこと)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは3つ生成されているか
        self.assertEqual(3, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']],
                   'd2': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']],
                   'd3': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']]}
        self.assertDictEqual(lasts, correct)
