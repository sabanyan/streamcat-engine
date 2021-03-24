import copy
import unittest
import shutil
from pathlib import Path

from kskp.core import Datum
from kskp.store import FlowData
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowJsonLink
from .test_main import convert_from_activity, convert_from_activity_vis

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

    def test_subflow_with_inout_on_way(self):
        """
        フローの途中に入力と出力ポイントを配置するサブフローを呼び出した場合、
        入力ポイントより手前のコマンドは実行されないこと
        出力ポイントより後ろのコマンドは実行されないこと
        """

        sub_flow_json = {
            "label": "test1", 
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
                    "commandId": "mnumber", 
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "no", 
                        "e": "seq", 
                        "s": "amount%n"
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
                    "commandId": "msum", 
                    "args": {
                        "f": "amount:sum", 
                        "k": "customer", 
                        "q": True, 
                        "precision": 10
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
                        "f": "*", 
                        "assert_diffSize": True
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "dsts": {
                        "o": "d3"
                    },          "srcsOrder": [
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
            "createdAt": "2021-03-18 17:09:32", 
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
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]
                    ],
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
                    "uuid": "2b221505-6f99-4cc8-8342-fd83bf357354",
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
        sub_flow.uuid = '2b221505-6f99-4cc8-8342-fd83bf357354'
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
        correct = {'d1': [['A','20180101','5200'], ['B','20180112','4300'],['A','20180105','2000'], ['B','20180107','4000']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    # 入力ポイントより前のコマンドの実行を許可するか否か、仕様が未定
    # そのため、エラーになる
    def test_subflow_with_outin_on_way(self):
        """
        フローの途中に出力と入力ポイントの順に配置するサブフローを呼び出した場合、
        出力ポイントより後ろのコマンドは実行されないこと
        """

        sub_flow_json = {
            "label": "test1", 
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
                    "commandId": "mnumber", 
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "no", 
                        "e": "seq", 
                        "s": "amount%n"
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
                    "commandId": "msum", 
                    "args": {
                        "f": "amount:sum", 
                        "k": "customer", 
                        "q": True, 
                        "precision": 10
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
                        "f": "*", 
                        "assert_diffSize": True
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "dsts": {
                        "o": "d3"
                    },          "srcsOrder": [
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
                }
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "d2", 
                        "nodeId": "d2"
                    }
                ], 
                [
                    {
                        "type": "frame", 
                        "label": "d1", 
                        "nodeId": "d1"
                    }
                ]
            ], 
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-03-18 17:09:32", 
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
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]
                    ],
                    "label": "percent",
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "args": {},
                    "srcs": {
                        "d2": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    },
                    "type": "flow",
                    "uuid": "2b221505-6f99-4cc8-8342-fd83bf357354",
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
        sub_flow.uuid = '2b221505-6f99-4cc8-8342-fd83bf357354'
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
        correct = {'d1': [['A','20180101','5200'], ['B','20180112','4300'],['A','20180105','2000'], ['B','20180107','4000']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_mainflow_with_in_and_datasource(self):
        """
        入力ポイントかつデータソースのポイントは、
        メインフローとして実行する場合は、データソースとして扱われること
        """

        flow_json = {
            "label": "test1 のコピー", 
            "nodes": [
                {
                    "id": "d", 
                    "label": "testData", 
                    "type": "frame", 
                    "uuid": None,
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]
                    ],
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                }, 
                {
                    "id": "c2", 
                    "label": "c2", 
                    "type": "command", 
                    "commandId": "mduprec", 
                    "args": {
                        "n": "2"
                    }, 
                    "srcs": {
                        "i": "d"
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
                }
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "testData", 
                        "nodeId": "d"
                    }
                ], 
                []
            ], 
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-03-18 17:09:32", 
            "projectId": None, 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json))

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
        # (RaiseCommandが実行されないこと)
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは3つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d2':[["A","20180101","5200"],
                         ["A","20180101","5200"],
                         ["B","20180101","800"],
                         ["B","20180101","800"],
                         ["B","20180112","3500"],
                         ["B","20180112","3500"],
                         ["A","20180105","2000"],
                         ["A","20180105","2000"],
                         ["B","20180107","4000"],
                         ["B","20180107","4000"]]}

        self.assertDictEqual(lasts, correct)

    def test_subflow_output_on_way(self):
        """
        フローの途中に出力ポイントを配置するサブフローを呼び出した場合、
        出力ポイントより後ろのコマンドは実行されないこと
        """

        sub_flow_json = {
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "testData", 
                    "uuid": "4392797b-54da-406c-9482-57b572359c27", 
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                }, 
                {
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    "commandId": "msetstr", 
                    "args": {
                        "a": "str", 
                        "v": "文字列です"
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
                    "commandId": "raise", 
                    "args": {}, 
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
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "testData", 
                        "nodeId": "d"
                    }
                ], 
                [
                    {
                        "type": "frame", 
                        "label": "d1", 
                        "nodeId": "d1"
                    }
                ]
            ], 
            "params": []
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
                        "d": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    },
                    "type": "flow",
                    "uuid": "ebb8d60e-fcb6-44c1-8db0-1c3330c83dbc",
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
        sub_flow.uuid = 'ebb8d60e-fcb6-44c1-8db0-1c3330c83dbc'
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
        correct = {'d1': [['A','1','10','文字列です'],
                          ['A','2','20','文字列です'],
                          ['B','1','30','文字列です'],
                          ['B','3','40','文字列です'],
                          ['B','1','50','文字列です']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_subflow_with_in_and_out_point(self):
        """
        フローの途中に入力かつ出力ポイントを配置するサブフローを呼び出した場合、
        入力ポイントより手前のコマンドは実行されないこと
        出力ポイントより後ろのコマンドは実行されないこと
        """

        sub_flow_json = {
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "testData", 
                    "uuid": "4392797b-54da-406c-9482-57b572359c27", 
                    "makeCache": False, 
                    "dataSource": "csv", 
                    "cacheCreatedAt": None
                }, 
                {
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    "commandId": "raise", 
                    "args": {
                        "message": "Here we go! ⚡️"
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
                    "commandId": "raise", 
                    "args": {
                        "message": "Hoho! ⚡️"
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
                        "label": "d1", 
                        "nodeId": "d1"
                    }
                ]
            ], 
            "params": []
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
                        "d1": "d1"
                    },
                    "type": "flow",
                    "uuid": "deb9a201-02aa-4afc-9502-4fafb5104ea4",
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
        sub_flow.uuid = 'deb9a201-02aa-4afc-9502-4fafb5104ea4'
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
        correct = {'d1': [['A','1','10'],
                          ['A','2','20'],
                          ['B','1','30'],
                          ['B','3','40'],
                          ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_subflow_with_datasource(self):
        """
        データソースを持つサブフローを実行・プレビューすると、その入力も実行されること
        (プレビューであってもデータデストを実行して出力を実行する)
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-21 10:51:00",
            "projectId": None,
            "description": "",
            "params": [
                {
                    "name" : "frame_uuid",
                    "label": "入力ファイルのUUID",
                    "type" : "frame"
                }
            ],
            "ports": [
                [],
                [
                    {
                        "type": "frame", 
                        "label": "d", 
                        "nodeId": "d"
                    }
                ]
            ],
            "nodes": [
                {
                    "id": "f",
                    "label": "Folderデータソース",
                    "type": "flow",
                    "uuid": "6f1cf477-9ce8-41cc-be74-0c3fe6068d8f",
                    "args": {
                        "frame_uuid": "@[frame_uuid]"
                    },
                    "srcs": {},
                    "dsts": {
                        "d1": "d"
                    }
                },
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ]
        }

        flow_json = {
            "label": "main",
            "params": [
                {
                    "name" : "frame_uuid",
                    "label": "入力ファイルのUUID",
                    "type" : "frame"
                }
            ],
            "ports": [[],[]],
            "nodes": [
                {
                    "id": "f0",
                    "label": "f0",
                    "type": "flow",
                    "uuid": "8b21e5fa-98a8-489c-b341-4a5836c3132a",
                    "args": {
                        "frame_uuid": "@[frame_uuid]"
                    },
                    "srcs": {},
                    "dsts": {
                        "d": "d"
                    },
                    "srcsOrder": []
                },
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # 入力フォルダを作成する
        in_folder = root.create_folder('入力フォルダ')
        in_folder.uuid = '4062d99c-54e8-477c-8c3b-b08958e0d2f3'
        in_folder.save()
        in_folder = in_folder.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = Path('../kskp-flow-engine/kskp/engine/tests/test_data/')
        in_file_path = in_folder.path / '2500.csv'
        shutil.copyfile(MY_TESTDATA_DIR / '2500.csv', in_file_path)

        # 入力CSVフレームを作成する
        in_frame = in_folder.create_frame('2500.csv', None)
        in_frame.save(file_path=in_file_path)

        # サブフロー(フォルダデータソース)の作成
        from .make_flow_json import folder_src_json
        folder_src = root.create_flow('folder_src', FlowData(folder_src_json))
        folder_src.uuid = '6f1cf477-9ce8-41cc-be74-0c3fe6068d8f'
        folder_src.save()
        folder_src = folder_src.reload()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '8b21e5fa-98a8-489c-b341-4a5836c3132a'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 108
            }
          }
        }
        flow_link = FlowJsonLink(flow, self.factory, vis_args)
        lasts = execute(flow_link, {'frame_uuid':in_frame.uuid}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['d'], 'Point"d"のプレビュー結果が得られませんでした')

        # 正しいVisが得られるか
        correct = [ '0.00191406997683585',
                    '-0.132273064191617',
                    '-0.0147741509760956',
                    '0.259594465851272',
                    '-0.148865534552684',
                    '-0.0980084224351297',
                    '-0.0808126083466136',
                    '-0.0391955180039139',
                    '0.182718539741551',
                    '-0.0563577925748503',
                    '0.00560793908366534',
                    '-0.0391716076320939',
                    '0.338283323489066',
                    '0.234739185309381',
                    '0.0760165884860558',
                    '0.114321024266145',
                    '-0.0182433456461233',
                    '-0.177497756007984',
                    '-0.184204068167331',
                    '-0.0326978744618395',
                    '0.0315082338369781']
        self.assertEqual(lasts['d'][0], correct)

        # ほかす
        sub_flow.throw_away()
        folder_src.throw_away()
        in_folder.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_with_datadest(self):
        """
        データデストを持つサブフローを実行・プレビューすると、その出力も実行されること
        (プレビューであってもデータデストを実行して出力を実行する)
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-21 11:41:00",
            "projectId": None,
            "description": "",
            "params": [],
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "d", 
                        "nodeId": "d"
                    }
                ],
                []
            ],
            "nodes": [
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "label": "Folderデータデスト",
                    "type": "flow",
                    "uuid": "b724993c-12cc-4ae3-b5e6-7b893f89346a",
                    "args": {},
                    "srcs": {
                        "d1": "d"
                    },
                    "dsts": {}
                }
            ]
        }

        flow_json = {
            "label": "main",
            "params": [],
            "ports": [[],[]],
            "nodes": [
                {
                    "id": "d",
                    "label": "d",
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
                    "id": "f0",
                    "label": "f0",
                    "type": "flow",
                    "uuid": "beefe9ba-7ccb-4536-9642-54207bcbddc7",
                    "args": {},
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {},
                    "srcsOrder": []
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # サブフロー(フォルダデータデスト)の作成
        from .make_flow_json import folder_dst_json
        folder_dst = root.create_flow('folder_dst', FlowData(folder_dst_json))
        folder_dst.uuid = 'b724993c-12cc-4ae3-b5e6-7b893f89346a'
        folder_dst.save()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'beefe9ba-7ccb-4536-9642-54207bcbddc7'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_with_datadest2(self):
        """
        2つのSaverコマンドを持つデータデストを持つサブフローを
        実行・プレビューすると、その出力も実行されること
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-23 19:02:00",
            "projectId": None,
            "description": "",
            "params": [],
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "d", 
                        "nodeId": "d"
                    }
                ],
                []
            ],
            "nodes": [
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "label": "2出力Folderデータデスト",
                    "type": "flow",
                    "uuid": "40a496a2-6cc2-4203-b945-0e57478191a0",
                    "args": {},
                    "srcs": {
                        "d1": "d"
                    },
                    "dsts": {}
                }
            ]
        }

        flow_json = {
            "label": "main",
            "params": [],
            "ports": [[],[]],
            "nodes": [
                {
                    "id": "d",
                    "label": "d",
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
                    "id": "f0",
                    "label": "f0",
                    "type": "flow",
                    "uuid": "52e7ca28-dbc2-422e-bf74-601bec042d43",
                    "args": {},
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {},
                    "srcsOrder": []
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # サブフロー(フォルダデータデスト)の作成
        from .make_flow_json import two_savers_folder_dst_json
        folder_dst = root.create_flow('folder_dst', FlowData(two_savers_folder_dst_json))
        folder_dst.uuid = '40a496a2-6cc2-4203-b945-0e57478191a0'
        folder_dst.save()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '52e7ca28-dbc2-422e-bf74-601bec042d43'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        
        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        self.assertIsNotNone(lasts['f0_d3'], 'SaverCommandは結果(f0_d3)を出力しませんでした')
        # 一つ目の出力結果が出力されていること
        out_frame1 = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame1.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame1.file_exists)
        # 二つ目の出力結果が出力されていること
        out_frame2 = lasts['f0_d3']
        self.assertTrue(self.factory.data.exists(out_frame2.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame2.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_with_datasource_and_dest(self):
        """
        データソースとデストを持つサブフローを実行・プレビューすると、その入出力も実行されること
        (プレビューであってもデータデストを実行して出力を実行する)
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-20 09:39:00",
            "projectId": None,
            "description": "",
            "params": [
                {
                    "name" : "frame_uuid",
                    "label": "入力ファイルのUUID",
                    "type" : "frame"
                }
            ],
            "ports": [
                [],
                []
            ],
            "nodes": [
                {
                    "id": "f",
                    "label": "Folderデータソース",
                    "type": "flow",
                    "uuid": "5befab77-d9e8-4bba-b581-cbaf2537f3de",
                    "args": {
                        "frame_uuid": "@[frame_uuid]"
                    },
                    "srcs": {},
                    "dsts": {
                        "d1": "d"
                    }
                },
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "f1",
                    "label": "Folderデータデスト",
                    "type": "flow",
                    "uuid": "7ed12207-e7fe-416d-b97c-682020ffa797",
                    "args": {},
                    "srcs": {
                        "d1": "d"
                    },
                    "dsts": {}
                }
            ]
        }

        flow_json = {
            "label": "main",
            "params": [
                {
                    "name" : "frame_uuid",
                    "label": "入力ファイルのUUID",
                    "type" : "frame"
                }
            ],
            "ports": [[],[]],
            "nodes": [
                {
                    "id": "f0",
                    "label": "f0",
                    "type": "flow",
                    "uuid": "de29a88c-f1f4-4e00-b9ff-1f1083a2f4c4",
                    "args": {
                        "frame_uuid": "@[frame_uuid]"
                    },
                    "srcs": {},
                    "dsts": {},
                    "srcsOrder": []
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # 入力フォルダを作成する
        in_folder = root.create_folder('入力フォルダ')
        in_folder.uuid = '4062d99c-54e8-477c-8c3b-b08958e0d2f3'
        in_folder.save()
        in_folder = in_folder.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = Path('../kskp-flow-engine/kskp/engine/tests/test_data/')
        in_file_path = in_folder.path / '2500.csv'
        shutil.copyfile(MY_TESTDATA_DIR / '2500.csv', in_file_path)

        # 入力CSVフレームを作成する
        in_frame = in_folder.create_frame('2500.csv', None)
        in_frame.save(file_path=in_file_path)

        # サブフロー(フォルダデータソース)の作成
        from .make_flow_json import folder_src_json
        folder_src = root.create_flow('folder_src', FlowData(folder_src_json))
        folder_src.uuid = '5befab77-d9e8-4bba-b581-cbaf2537f3de'
        folder_src.save()
        folder_src = folder_src.reload()

        # サブフロー(フォルダデータデスト)の作成
        from .make_flow_json import folder_dst_json
        folder_dst = root.create_flow('folder_dst', FlowData(folder_dst_json))
        folder_dst.uuid = '7ed12207-e7fe-416d-b97c-682020ffa797'
        folder_dst.save()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'de29a88c-f1f4-4e00-b9ff-1f1083a2f4c4'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {'frame_uuid':in_frame.uuid}, {})
        # 0入力0出力のフローは実行されないため結果は0件になる
        self.assertEqual(len(lasts), 0)

        # サブフローを実行する
        flow_link = FlowJsonLink(sub_flow, self.factory)
        lasts = execute(flow_link, {'frame_uuid':in_frame.uuid}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(f1_d2)を出力しませんでした')
        out_frame = lasts['f1_d2']
        self.assertTrue(self.factory.data.exists(out_frame.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()
        folder_src.throw_away()
        in_folder.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()
