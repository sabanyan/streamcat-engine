import copy
import unittest
import shutil
from pathlib import Path
from unittest import result

from kskp.core import Datum
from kskp.store import DatabaseConn, FlowData, NysolModule
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowCommand
from .test_main import convert_from_activity, convert_from_activity_vis, convert_from_activity_exs
from .make_flow_json import create_flow_by_flow_id

class DataSourceTest(TestCaseBase):
    """
    フローの入出力指定の検証
    """

    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "db", 
      'port'     : 5432, 
      'database' : "kskp", 
      'user_id'  : "kskp", 
      'password' : 'ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz'
    }
    database_conn = DatabaseConn(conn_json)

    def test_subflow_has_input_on_way(self):
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_mainflow_has_input_on_way(self):
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは3つ生成されているか
        self.assertEqual(3, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']],
                   'd2': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']],
                   'd3': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']]}
        self.assertDictEqual(lasts, correct)

    def test_subflow_has_inout_on_way(self):
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
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
    def test_subflow_has_outin_on_way(self):
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','20180101','5200'], ['B','20180112','4300'],['A','20180105','2000'], ['B','20180107','4000']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    def test_mainflow_has_in_and_datasource(self):
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
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

    def test_subflow_has_in_and_out_point(self):
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
                    "uuid": "2c797dce-6573-43b6-ad37-b77768adaf76", 
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

        # 入力データを作成する
        data = [
            ['顧客', '数量', '金額'],
            ["A", 1, 10],
            ["A", 2, 20],
            ["B", 1, 30],
            ["B", 3, 40],
            ["B", 1, 50]
        ]
        import io
        frame = root.create_frame('インプットデータ', io.BytesIO(str(data).encode('utf-8')))
        frame.uuid = "2c797dce-6573-43b6-ad37-b77768adaf76"
        frame.save()
        frame = frame.reload()

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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
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
        frame.delete()

    def test_subflow_has_datasource(self):
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
        flow_link = FlowCommand(flow)
        args = {'vis':vis_args, 'params': {'frame_uuid':in_frame.uuid}}
        lasts = execute(flow_link, args, {})
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

    def test_subflow_has_datadest(self):
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
                    "label": "この世界で君に会えた日から輝き始めてる",
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('この世界で君に会えた日から輝き始めてる'))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_has_datadest2(self):
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
                    "label": "ひとつひとつ叶えて行けるかな　そばにいて",
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
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)
        
        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        self.assertIsNotNone(lasts['f0_d3'], 'SaverCommandは結果(f0_d3)を出力しませんでした')
        # 一つ目の出力結果が出力されていること
        out_frame1 = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame1.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame1.label.startswith('ひとつひとつ叶えて行けるかな　そばにいて'))
        self.assertTrue(out_frame1.file_exists)
        # 二つ目の出力結果が出力されていること
        out_frame2 = lasts['f0_d3']
        self.assertTrue(self.factory.data.exists(out_frame2.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame2.label.startswith('ひとつひとつ叶えて行けるかな　そばにいて'))
        self.assertTrue(out_frame2.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_has_datasource_and_dest(self):
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
                    "label": "どこにいても見えない　未来なんてもっと退屈な光",
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

        # サブフローを実行する
        flow_link = FlowCommand(sub_flow)
        args = {'params': {'frame_uuid':in_frame.uuid}}
        lasts = execute(flow_link, args, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(f1_d2)を出力しませんでした')
        out_frame = lasts['f1_d2']
        self.assertTrue(self.factory.data.exists(out_frame.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('どこにいても見えない　未来なんてもっと退屈な光'))
        self.assertTrue(out_frame.file_exists)

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, args, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('どこにいても見えない　未来なんてもっと退屈な光'))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()
        folder_src.throw_away()
        in_folder.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_has_datedst_and_out_point(self):
        """
        サブフローがデータデストとフロー出力Pointをもつ場合、
        実行・プレビューすると、その入出力も実行されること
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-25 19:55:00",
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
                [
                    {
                        "type": "frame", 
                        "label": "d1", 
                        "nodeId": "d1"
                    }
                ]
            ],
            "nodes": [
                {
                    "id": "d",
                    "label": "とっておきの場所で一緒に隠れた　陽射し揺れて",
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
                    "uuid": "683cfa29-b431-495f-b617-078123a6518c",
                    "args": {},
                    "srcs": {
                        "d1": "d"
                    },
                    "dsts": {}
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
                        "s": "金額"
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
                    "label": "あと少しの距離を待ち望んでいるの？",
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
            "params": [],
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
                    "uuid": "dcf3c775-b504-4b06-bd7b-7ee9738f3b2f",
                    "args": {},
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    },
                    "srcsOrder": []
                },
                {
                    "id": "d1",
                    "label": "d1",
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

        # サブフロー(フォルダデータデスト)の作成
        from .make_flow_json import folder_dst_json
        folder_dst = root.create_flow('folder_dst', FlowData(folder_dst_json))
        folder_dst.uuid = '683cfa29-b431-495f-b617-078123a6518c'
        folder_dst.save()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'dcf3c775-b504-4b06-bd7b-7ee9738f3b2f'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        # 
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame1 = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame1.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame1.label.startswith('とっておきの場所で一緒に隠れた　陽射し揺れて'))
        self.assertTrue(out_frame1.file_exists)
        # 
        self.assertIsNotNone(lasts['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame2 = lasts['d1']
        self.assertTrue(self.factory.data.exists(out_frame2.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame2.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_hasnot_in_and_out_point(self):
        """
        入出力Portの無いサブフローであっても、SaverCommandは実行されること
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-26 06:43:00",
            "projectId": None,
            "description": "",
            "params": [],
            "ports": [[],[]],
            "nodes": [
                {
                    "id": "d",
                    "label": "いつだってもどかしいよ　離れないで",
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
                    "id": "f1",
                    "label": "Folderデータデスト",
                    "type": "flow",
                    "uuid": "d6c92ed6-a8d0-403a-af1e-c0d32cde2146",
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
                    "id": "f0",
                    "label": "f0",
                    "type": "flow",
                    "uuid": "2aae0735-aeb7-4000-b9ff-393aae5802ae",
                    "args": {},
                    "srcs": {},
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
        folder_dst.uuid = 'd6c92ed6-a8d0-403a-af1e-c0d32cde2146'
        folder_dst.save()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '2aae0735-aeb7-4000-b9ff-393aae5802ae'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.factory.data.exists(out_frame.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('いつだってもどかしいよ　離れないで'))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_subflow_hasnot_in_and_out_point2(self):
        """
        入出力Portが無いサブフローで、かつSaverCommandも含まれていない場合、
        そのサブフローは実行されないこと
        """

        sub_flow_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2021-3-26 08:58:00",
            "projectId": None,
            "description": "",
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
                    "id": "c2",
                    "commandId": "mrand",
                    "type": "command",
                    "label": "c2",
                    "args": {
                        "a": "乱数"
                    },
                    "srcs": {
                        "i": "d"
                    },
                    "dsts": {
                        "o": "d2"
                    }
                },
                {
                    "id": "d1",
                    "label": "d1",
                    "type": "frame",
                    "dataSource": "csv"
                }
            ]
        }

        flow_json = {
            "label": "main",
            "params": [],
            "ports": [[],[]],
            "nodes": [
                {
                    "id": "f0",
                    "label": "f0",
                    "type": "flow",
                    "uuid": "df5dc139-17fe-4843-9aaa-6dc1306d0e9d",
                    "args": {},
                    "srcs": {},
                    "dsts": {},
                    "srcsOrder": []
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'df5dc139-17fe-4843-9aaa-6dc1306d0e9d'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})

        # 出力結果は0件であること
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されないこと
        self.assertIsNone(lasts)

        # ほかす
        sub_flow.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_run_flow_cmd(self):
        """
        Flow Commandを直接runしても結果が得られること
        """

        flow_json = {
            "label": "Yoshinoya", 
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
            "nodes": [
                {
                "id": "c1", 
                "label": "c1", 
                "type": "command", 
                "commandId": "mnewstr",
                "args": {
                    "a": "static", 
                    "l": "13", 
                    "v": "𠮷野家"
                }, 
                "srcs": {}, 
                "dsts": {
                    "o": "d1"
                }
                },
                {
                "id": "d1", 
                "label": "d1", 
                "type": "frame", 
                "makeCache": False, 
                "dataSource": "csv", 
                "cacheCreatedAt": None
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_cmd = FlowCommand(flow)
        lasts = flow_cmd.run()
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        # 
        self.assertIsNotNone(lasts['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame1 = lasts['d1']
        self.assertTrue(self.factory.data.exists(out_frame1.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame1.file_exists)

    def test_run_cmd(self):
        """
        Commandを直接runしても結果が得られること
        """
        # コマンドを作成する
        import nysol.mcmd as nm 
        from kskp.depo.std.commands import CommandLink
        cmd = CommandLink('ts_axis_0in_generator').resolve()

        # コマンド引数
        args = {
            'a'        : 'TIME',
            'time_type': 'date',
            'start'    : '19140801',
            'num'      : '16',
            'interval' : '30'
        }

        # コマンドを実行する
        lasts = cmd.run(args=args, inputs={})

        # 実行結果はNYSOLコマンドであること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['o'], 'Commandは結果(o)を出力しませんでした')
        self.assertIsInstance(lasts['o'], NysolModule)

        # NYSOLを実行する
        nysol_cmd = lasts['o'].content
        nysol_cmd <<= nm.writelist()
        result = nysol_cmd.run()

        # 期待する結果が得られること
        expected = [
            ['19140801'],
            ['19140831'],
            ['19140930'],
            ['19141030'],
            ['19141129'],
            ['19141229'],
            ['19150128'],
            ['19150227'],
            ['19150329'],
            ['19150428'],
            ['19150528'],
            ['19150627'],
            ['19150727'],
            ['19150826'],
            ['19150925'],
            ['19151025']
        ]
        self.assertListEqual(result, expected)

    def test_vis_optimization(self):
        """
        プレビューの結果データの作成に関係しないコマンドは実行しないこと
        """

        flow_json ={
            "label": "raiseとmnewnumber",
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
            "params": [],
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "raise",
                    "args": {
                        "message": "d1のプレビューでこのRaiseコマンドは実行しません"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d"
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
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1",
                        "S": "1",
                        "a": "b",
                        "l": "20"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d1"
                    }
                },
                {
                    "id": "d1",
                    "label": "d1",
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

        # フローを作成する
        flow = root.create_flow('vis test', FlowData(flow_json))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }

        # フローを実行する
        # (RaiseCommandが実行されないこと)
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10'],
                          ['11'], ['12'], ['13'], ['14'], ['15'], ['16'], ['17'], ['18'], ['19'], ['20']]}
        self.assertDictEqual(lasts, correct)

    def test_vis_optimization_with_make_cache(self):
        """
        キャッシュ作成=ONのPointが存在しても
        プレビューの結果データの作成に関係しないコマンドは実行しないこと
        """

        flow_json ={
            "label": "raiseとmnewnumber",
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
            "params": [],
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "raise",
                    "args": {
                        "message": "d1のプレビューでこのRaiseコマンドは実行しません"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d"
                    }
                },
                {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": True,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1",
                        "S": "1",
                        "a": "b",
                        "l": "20"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d1"
                    }
                },
                {
                    "id": "d1",
                    "label": "d1",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": True,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                }
            ]
        }
    
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('vis test', FlowData(flow_json))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }

        # フローを実行する
        # (RaiseCommandが実行されないこと)
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})

        print(lasts)

        lasts = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10'],
                          ['11'], ['12'], ['13'], ['14'], ['15'], ['16'], ['17'], ['18'], ['19'], ['20']]}
        self.assertDictEqual(lasts, correct)

    def test_vis_deep_subflow_call(self):
        """
        十分に深い呼出関係のサブフローをプレビューできること
        """

        sub_flow4 = {
            "label": "subflow4", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "c": "[10000,]", 
                        "f": "amount", 
                        "bufcount": 10
                    }, 
                    "dsts": {
                        "o": "d1", 
                        "u": "d2"
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mselnum"
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
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-13 09:13:10", 
            "description": ""
        }

        sub_flow3 = {
            "label": "subflow3", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d1": "d1", 
                        "d2": "d2"
                    }, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "7da92d9d-256a-4172-8587-c593ba72ebd9", 
                    "label": "f1"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {}, 
                    "dsts": {
                        "o": "d3"
                    }, 
                    "srcs": {
                        "*0": "d1", 
                        "*1": "d2"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mcat"
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
                [
                    {
                        "type": "frame", 
                        "label": "d3", 
                        "nodeId": "d3"
                    }
                ]
            ], 
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-13 09:25:31", 
            "description": ""
        }

        sub_flow2 = {
            "label": "subflow2", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d3": "d2"
                    }, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "99f81446-d805-481c-9329-b555a4b1a240", 
                    "label": "f1"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f2", 
                    "args": {}, 
                    "dsts": {
                        "d3": "d3"
                    }, 
                    "srcs": {
                        "d": "d1"
                    }, 
                    "type": "flow", 
                    "uuid": "99f81446-d805-481c-9329-b555a4b1a240", 
                    "label": "f2"
                }, 
                {
                    "id": "d4", 
                    "type": "frame", 
                    "label": "d4", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "k": "0,1", 
                        "x": True
                    }, 
                    "dsts": {
                        "o": "d4"
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "muniq"
                }, 
                {
                    "id": "d5", 
                    "type": "frame", 
                    "label": "d5", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "k": "customer,date"
                    }, 
                    "dsts": {
                        "o": "d5"
                    }, 
                    "srcs": {
                        "i": "d3"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "muniq"
                }
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "testData", 
                        "nodeId": "d1"
                    }, 
                    {
                        "type": "frame", 
                        "label": "testData", 
                        "nodeId": "d"
                    }
                ], 
                [
                    {
                        "type": "frame", 
                        "label": "d4", 
                        "nodeId": "d4"
                    }, 
                    {
                        "type": "frame", 
                        "label": "d5", 
                        "nodeId": "d5"
                    }
                ]
            ], 
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-13 09:46:20",
            "description": ""
        }

        sub_flow1 = {
            "label": "subflow1", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d4": "d2", 
                        "d5": "d3"
                    }, 
                    "srcs": {
                        "d": "d", 
                        "d1": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "0ea4d275-9526-498e-98c6-35b92aebc12d", 
                    "label": "f1"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "verbose": True
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {
                        "i": "d3", 
                        "m": "d2"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "assert"
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
                [
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
            "createdAt": "2021-04-13 09:52:04", 
            "description": ""
        }

        main_flow = {
            "label": "main", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]],
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d2": "d1", 
                        "d3": "d2"
                    }, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "9d406060-7920-4c0e-b4d9-e5db432103dd", 
                    "label": "f1"
                }
            ], 
            "ports": [
                [], 
                []
            ], 
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-13 11:06:14", 
            "description": ""
        } 

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # サブフロー4を作成する
        sub_flow4 = root.create_flow('Sub', FlowData(sub_flow4))
        sub_flow4.uuid = '7da92d9d-256a-4172-8587-c593ba72ebd9'
        sub_flow4.save()
        sub_flow4 = sub_flow4.reload()

        # サブフロー3を作成する
        sub_flow3 = root.create_flow('Sub', FlowData(sub_flow3))
        sub_flow3.uuid = '99f81446-d805-481c-9329-b555a4b1a240'
        sub_flow3.save()
        sub_flow3 = sub_flow3.reload()

        # サブフロー2を作成する
        sub_flow2 = root.create_flow('Sub', FlowData(sub_flow2))
        sub_flow2.uuid = '0ea4d275-9526-498e-98c6-35b92aebc12d'
        sub_flow2.save()
        sub_flow2 = sub_flow2.reload()

        # サブフロー1を作成する
        sub_flow1 = root.create_flow('Sub', FlowData(sub_flow1))
        sub_flow1.uuid = '9d406060-7920-4c0e-b4d9-e5db432103dd'
        sub_flow1.save()
        sub_flow1 = sub_flow1.reload()

        # フローを作成する
        flow = root.create_flow('deep subflow test', FlowData(main_flow))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          },
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_activity_vis(lasts)

        # visデータは2つ生成されているか
        self.assertEqual(len(lasts), 2)

        # 正しいVisが得られるか
        correct = {'d1': [['A','20180101','5200'],['A','20180105','2000'],['B','20180101','800'],['B','20180107','4000'],['B','20180112','3500']],
                   'd2': [['A','20180101','5200'],['A','20180105','2000'],['B','20180101','800'],['B','20180107','4000'],['B','20180112','3500']]}
        self.assertDictEqual(lasts, correct)

        # ほかす
        sub_flow1.throw_away()
        sub_flow2.throw_away()
        sub_flow3.throw_away()
        sub_flow4.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_deep_datadest_call(self):
        """
        十分に深い呼出関係のデータデストを実行できること
        """
        datadest4 = {
            "label": "datadest4", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "この世界に君が居てくれる道は　不思議と好きになる", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f", 
                    "args": {}, 
                    "dsts": {
                        "d1": "d"
                    }, 
                    "srcs": {}, 
                    "type": "flow", 
                    "uuid": "f3f0000c-6525-4b7d-9843-fe89e692bc17", 
                    "label": "f"
                }, 
                {
                    "id": "f1", 
                    "args": {
                        "Table": "@[table]", 
                        "Schema": "@[schema]"
                    }, 
                    "dsts": {}, 
                    "srcs": {
                        "d1": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "4b1fb10d-8417-4c7f-b15d-7eb2775d2c76", 
                    "label": "f1"
                }
            ], 
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
            "params": [
                {
                    "name": "schema", 
                    "type": "string", 
                    "label": "schema"
                }, 
                {
                    "name": "table", 
                    "type": "string", 
                    "label": "table"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-18 07:18:07", 
            "description": ""
        }

        datadest3 = {
            "label": "datadest3", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "d", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f", 
                    "args": {}, 
                    "dsts": {
                        "d1": "d"
                    }, 
                    "srcs": {}, 
                    "type": "flow", 
                    "uuid": "f3f0000c-6525-4b7d-9843-fe89e692bc17", 
                    "label": "f"
                }, 
                {
                    "id": "f1", 
                    "args": {
                        "table": "@[table]", 
                        "schema": "@[schema]"
                    }, 
                    "dsts": {}, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "f57eed6b-f24d-4dc0-ad45-29d45f756b4e", 
                    "label": "f1"
                }
            ], 
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
            "params": [
                {
                    "name": "schema", 
                    "type": "string", 
                    "label": "schema"
                }, 
                {
                    "name": "table", 
                    "type": "string",  
                    "label": "table"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-18 07:23:59", 
            "description": ""
        }

        datadest2 = {
            "label": "datadest2", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "d", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f", 
                    "args": {}, 
                    "dsts": {
                        "d1": "d"
                    }, 
                    "srcs": {}, 
                    "type": "flow", 
                    "uuid": "f3f0000c-6525-4b7d-9843-fe89e692bc17", 
                    "label": "f"
                }, 
                {
                    "id": "f1", 
                    "args": {
                        "table": "@[table]", 
                        "schema": "@[schema]"
                    }, 
                    "dsts": {}, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "f33e5138-e508-4b2a-8596-6811dcc3eccf", 
                    "label": "f1"
                }, 
                {
                    "id": "f2", 
                    "args": {
                        "table": "@[table]", 
                        "schema": "@[schema]"
                    }, 
                    "dsts": {}, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "f33e5138-e508-4b2a-8596-6811dcc3eccf", 
                    "label": "f2"
                }
            ], 
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
            "params": [
                {
                    "name": "schema", 
                    "type": "string", 
                    "label": "schema"
                }, 
                {
                    "name": "table", 
                    "type": "string", 
                    "label": "table"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-18 07:29:54", 
            "description": ""
        }

        datadest1 = {
            "label": "datadest1", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "d", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f", 
                    "args": {}, 
                    "dsts": {
                        "d1": "d"
                    }, 
                    "srcs": {}, 
                    "type": "flow", 
                    "uuid": "f3f0000c-6525-4b7d-9843-fe89e692bc17", 
                    "label": "f"
                }, 
                {
                    "id": "f1", 
                    "args": {
                        "table": "@[table]", 
                        "schema": "@[schema]"
                    }, 
                    "dsts": {}, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "31883bdd-fb0c-4057-b73e-c6dba6e28c27", 
                    "label": "f1"
                }
            ], 
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
            "params": [
                {
                    "name": "schema", 
                    "type": "string", 
                    "label": "schema"
                }, 
                {
                    "name": "table", 
                    "type": "string", 
                    "label": "table"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-18 07:31:17", 
            "description": ""
        }

        main_flow = {
            "label": "main", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]],
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {
                        "table": "test_tbl", 
                        "schema": "schema_005e59"
                    }, 
                    "dsts": {}, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "20ce7318-66a1-48e0-8f56-3741d35629db", 
                    "label": "f1"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-18 07:33:03", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # DBストアの作成
        db = root.create_database('postgresql', self.database_conn)
        db.uuid = 'c410cd16-2529-498d-8e7f-490ffa58dc95'
        db.save()

        # サブフロー(PostgreSQLデータソース)の作成
        postgre_src_uuid = 'f3f0000c-6525-4b7d-9843-fe89e692bc17'
        postgre_src = create_flow_by_flow_id(root,'postgre_src', postgre_src_uuid)

        # サブフロー(PostgreSQLデータデスト)の作成
        postgre_dst_uuid = '4b1fb10d-8417-4c7f-b15d-7eb2775d2c76'
        postgre_dst = create_flow_by_flow_id(root, 'postgre_dst', postgre_dst_uuid)

        # サブフロー4を作成する
        sub_flow4 = root.create_flow('Sub', FlowData(datadest4))
        sub_flow4.uuid = 'f57eed6b-f24d-4dc0-ad45-29d45f756b4e'
        sub_flow4.save()
        sub_flow4 = sub_flow4.reload()

        # サブフロー3を作成する
        sub_flow3 = root.create_flow('Sub', FlowData(datadest3))
        sub_flow3.uuid = 'f33e5138-e508-4b2a-8596-6811dcc3eccf'
        sub_flow3.save()
        sub_flow3 = sub_flow3.reload()

        # サブフロー2を作成する
        sub_flow2 = root.create_flow('Sub', FlowData(datadest2))
        sub_flow2.uuid = '31883bdd-fb0c-4057-b73e-c6dba6e28c27'
        sub_flow2.save()
        sub_flow2 = sub_flow2.reload()

        # サブフロー1を作成する
        sub_flow1 = root.create_flow('Sub', FlowData(datadest1))
        sub_flow1.uuid = '20ce7318-66a1-48e0-8f56-3741d35629db'
        sub_flow1.save()
        sub_flow1 = sub_flow1.reload()

        # フローを作成する
        flow = root.create_flow('deep datadest test', FlowData(main_flow))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(f1_d2)を出力しませんでした')
        self.assertIsNotNone(lasts['f1_d2_1'], 'SaverCommandは結果(f1_d2_1)を出力しませんでした')
        out_frame1 = lasts['f1_d2']
        out_frame2 = lasts['f1_d2_1']
        self.assertTrue(self.factory.data.exists(out_frame1.uuid, type=Datum.FLOW_TYPE))
        self.assertTrue(self.factory.data.exists(out_frame2.uuid, type=Datum.FLOW_TYPE))
        self.assertTrue(out_frame1.label.startswith('この世界に君が居てくれる道は　不思議と好きになる'))
        self.assertTrue(out_frame2.label.startswith('この世界に君が居てくれる道は　不思議と好きになる'))

        # ほかす
        sub_flow1.throw_away()
        sub_flow2.throw_away()
        sub_flow3.throw_away()
        sub_flow4.throw_away()
        postgre_src.throw_away()
        postgre_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    @unittest.skip('テストケースの実行ログが溢れるのでテストしない')
    def test_vis_circular_subflow_call(self):
        """
        循環参照する場合は実行・プレビュー時に例外を送出すること
        """
        main_flow = {
            "label": "circle", 
            "nodes": [
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "a": "b", 
                        "c": "0", 
                        "precision": 10
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mcal"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "a": "a", 
                        "c": "1", 
                        "precision": 10
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mcal"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-18 16:15:39", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('loop', FlowData(main_flow))

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }

        # フローを実行しようとすると例外を送出すること
        flow_link = FlowCommand(flow)
        with self.assertRaises(RecursionError):
            execute(flow_link, {'vis':vis_args}, {})

    def test_subflow_has_no_data_out_point(self):
        """
        データを返さない出力Pointを持つサブフローを呼び出すとエラーになること
        """
        # フロー出力Pointが一つだけ
        sub_flow_json = {
            "label": "err2", 
            "nodes": [
                {
                    "id": "d", 
                    "label": "d", 
                    "type": "frame", 
                    "dataSource": "csv"
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
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 07:57:44", 
            "description": ""
        }

        flow_json = {
            "label": "main", 
            "nodes": [
                {
                    "id": "f", 
                    "label": "f",
                    "type": "flow", 
                    "uuid": "490a22fe-0cd1-4801-b052-c899e80c2547", 
                    "args": {},
                    "srcs": {},
                    "dsts": {
                        "d": "d"
                    } 
                },
                {
                    "id": "d", 
                    "label": "d", 
                    "type": "frame", 
                    "dataSource": "csv"
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
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 07:59:16",
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '490a22fe-0cd1-4801-b052-c899e80c2547'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # プレビューしても結果は得られない
        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_activity_vis(lasts)
        self.assertIsNone(results)

        # 実行しても結果は得られない
        lasts = execute(FlowCommand(flow), {}, {})
        results = convert_from_activity(lasts)
        self.assertIsNone(results)

        # ほかす
        sub_flow.throw_away()

        # ゴミ箱を空にする
        trash = self.factory.data.load_trash_folder()
        trash.trash_all()

    def test_inner_subflow(self):
        """
        Flowリテラルが実行できること
        """
        flow_json =  {
            "label": "Flowのリテラル表記のテスト",
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
            "nodes": [
                {
                    "id": "d", 
                    "label": "testData", 
                    "type": "frame", 
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]],
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1", 
                    "type": "flow",
                    "flow": {
                        "label": "リテラル表記のフロー", 
                        "description": "",
                        "projectId": None, 
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
                        "params": [], 
                        "nodes": [
                            {
                                "id": "d", 
                                "label": "testData", 
                                "type": "frame", 
                                "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "c1", 
                                "label": "c1", 
                                "type": "command", 
                                "commandId": "mcombi",
                                "args": {
                                    "a": "date_combi", 
                                    "f": "date", 
                                    "n": "1", 
                                    "s": "date"
                                }, 
                                "srcs": {
                                    "i": "d"
                                }, 
                                "dsts": {
                                    "o": "d1"
                                }
                            },
                            {
                                "id": "d1", 
                                "label": "d1", 
                                "type": "frame", 
                                "dataSource": "csv"
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2021-04-23 14:14:22", 
                    },
                    "args": {}, 
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    }
                },
                {
                    "id": "d1", 
                    "label": "d1", 
                    "type": "frame", 
                    "dataSource": "csv"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 14:16:55"
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('inner subflow test', FlowData(flow_json))

        # フローをプレビューする
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(len(results), 1)

        # 正しいVisが得られるか
        correct = {'d1': [['B', '20180112', '3500', '20180101'],
                        ['B', '20180112', '3500', '20180101'],
                        ['B', '20180112', '3500', '20180105'],
                        ['B', '20180112', '3500', '20180107'],
                        ['B', '20180112', '3500', '20180112']]}
        self.assertDictEqual(results, correct)

        # フローを実行する
        lasts = execute(FlowCommand(flow), {}, {})
        results = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(results['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame2 = results['d1']
        self.assertTrue(self.factory.data.exists(out_frame2.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame2.file_exists)

    def test_inner_subflow_has_makecache(self):
        """
        キャッシュ出力指定のPointを持つFlowリテラルが実行できること
        (Flowリテラルはサブフローなので、キャッシュは出力されない仕様である)
        """

        flow_json =  {
            "label": "キャッシュ出力指定を持つFlowのリテラル",
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
            "nodes": [
                {
                    "id": "d", 
                    "label": "testData", 
                    "type": "frame", 
                    "value":[["customer", "date", "amount"],
                             ["A", "20180101", "5200"],
                             ["B", "20180101", "800"],
                             ["B", "20180112", "3500"],
                             ["A", "20180105", "2000"],
                             ["B", "20180107", "4000"]],
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1", 
                    "type": "flow",
                    "flow": {
                        "label": "リテラル表記のフロー", 
                        "description": "",
                        "projectId": None, 
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
                        "params": [], 
                        "nodes": [
                            {
                                "id": "d", 
                                "label": "testData", 
                                "type": "frame", 
                                "makeCache": True,
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "c1", 
                                "label": "c1", 
                                "type": "command", 
                                "commandId": "mcombi",
                                "args": {
                                    "a": "date_combi", 
                                    "f": "date", 
                                    "n": "1", 
                                    "s": "date"
                                }, 
                                "srcs": {
                                    "i": "d"
                                }, 
                                "dsts": {
                                    "o": "d1"
                                }
                            },
                            {
                                "id": "d1", 
                                "label": "d1", 
                                "type": "frame", 
                                "makeCache": True,
                                "dataSource": "csv"
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2021-04-23 14:14:22", 
                    },
                    "args": {}, 
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {
                        "d1": "d1"
                    }
                },
                {
                    "id": "d1", 
                    "label": "d1", 
                    "type": "frame", 
                    "dataSource": "csv"
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 14:16:55"
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # フローを作成する
        flow = root.create_flow('inner make cache subflow test', FlowData(flow_json))

        # フローをプレビューする
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_activity_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(len(results), 1)

        # 正しいVisが得られるか
        correct = {'d1': [['B', '20180112', '3500', '20180101'],
                        ['B', '20180112', '3500', '20180101'],
                        ['B', '20180112', '3500', '20180105'],
                        ['B', '20180112', '3500', '20180107'],
                        ['B', '20180112', '3500', '20180112']]}
        self.assertDictEqual(results, correct)

        # フローを実行する
        lasts = execute(FlowCommand(flow), {}, {})
        results = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(results['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame2 = results['d1']
        self.assertTrue(self.factory.data.exists(out_frame2.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame2.file_exists)

    def test_runt_flow_cmd_reentrant(self):
        """
        Flow Commandのrun()を再実行できること
        """

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        flow_json ={
            "label": "flow", 
            "nodes": [
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewrand",
                    "args": {
                        "a": "a", 
                        "l": "10"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d"
                    }
                },
                {
                    "id": "d", 
                    "label": "d", 
                    "type": "frame", 
                    "dataSource": "csv"
                },
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {},
                    "srcs": {
                        "d": "d"
                    },
                    "dsts": {}, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                            {
                                "id": "d", 
                                "label": "d", 
                                "type": "frame", 
                                "dataSource": "csv"
                            }, 
                            {
                                "id": "s", 
                                "label": "ライブラリ",
                                "type": "store", 
                                "uuid": root.uuid
                            }, 
                            {
                                "id": "c1", 
                                "label": "c1", 
                                "type": "command", 
                                "commandId": "saver",
                                "args": {}, 
                                "srcs": {
                                    "i": "d", 
                                    "folder": "s"
                                }, 
                                "dsts": {
                                    "o": "d1"
                                }
                            }, 
                            {
                                "id": "d1", 
                                "label": "d1", 
                                "type": "frame", 
                                "dataSource": "csv"
                            }
                        ], 
                        "ports": [
                            [
                                {
                                    "type": "frame", 
                                    "label": "i", 
                                    "nodeId": "d"
                                }
                            ], 
                            []
                        ], 
                        "params": []
                    }
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
            "params": []
        }


        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_cmd = FlowCommand(flow)
        lasts = flow_cmd.run()
        lasts = convert_from_activity(lasts)

        # 同じFlowCommandオブジェクトを用いて
        # 再度フローを実行する
        import time
        time.sleep(3)
        lasts = flow_cmd.run()
        lasts = convert_from_activity(lasts)
        
        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        # 
        self.assertIsNotNone(lasts['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame1 = lasts['d1']
        self.assertTrue(self.factory.data.exists(out_frame1.uuid, type=Datum.FRAME_TYPE))
        self.assertTrue(out_frame1.file_exists)
