import io
import unittest
import shutil
from pathlib import Path

from streamcat.core import SavableDatum
from streamcat.store import DatabaseConn, FlowData, NysolModule, CommandException
from streamcat.store.tests.test_case_base import TestCaseBase
from streamcat.engine import aexecute, FlowCommand
from .test_main import convert_from_job, convert_from_job_exs, convert_from_job_vis
from .make_flow_json import create_flow_by_flow_id

class DataSourceTest(TestCaseBase, unittest.IsolatedAsyncioTestCase):
    """
    フローの入出力指定の検証
    """

    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "db", 
      'port'     : 5432, 
      'database' : "streamcat", 
      'userId'  : "streamcat", 
      'password' : 'ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz'
    }
    database_conn = DatabaseConn(conn_json)

    async def test_subflow_has_input_on_way(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','1','10'], ['A','2','20'],['B','1','30'], ['B','3','40'], ['B','1','50']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    async def test_mainflow_has_input_on_way(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは3つ生成されているか
        self.assertEqual(3, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']],
                   'd2': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']],
                   'd3': [['x','1','10'], ['x','2','20'],['y','1','30'], ['y','3','40'], ['z','1','50']]}
        self.assertDictEqual(lasts, correct)

    async def test_subflow_has_inout_on_way(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['A','20180101','5200'], ['B','20180112','4300'],['A','20180105','2000'], ['B','20180107','4000']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    async def test_subflow_has_outin_on_way(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['x','1','10','1'], ['x','2','20','2'], ['y','1','30','3'], ['y','3','40','4'], ['z','1','50','5']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    async def test_mainflow_has_in_and_datasource(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

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

    async def test_subflow_has_output_on_way1(self):
        """
        フローの途中に出力ポイントを配置するサブフローを呼び出した場合、
        出力ポイントより後ろのコマンドは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # 参照先フレームを作成する
        frame1 = root.create_frame('CSV1', io.BytesIO(b''))
        frame1.save()

        sub_flow_json = {
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "testData", 
                    "uuid": frame1.uuid, 
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
                        "testData": "d"
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

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

    async def test_subflow_has_output_on_way2(self):
        """
        一つの経路に二つの出力ポイントを配置したサブフロー呼び出す場合、
        経路途中の出力ポイントより後ろの出力ポイントをプレビューできること
        """  
        # mnewnumber -> mcut -> mcut -> mcut
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
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
                    }
                }, 
                {
                    "id": "d1",
                    "label": "d1",
                    "type": "frame",
                    "dataSource": "csv"
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
                    }
                }, 
                {
                    "id": "d2",
                    "label": "d2",
                    "type": "frame",
                    "dataSource": "csv"
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
                    }
                },
                {
                    "id": "d3",
                    "label": "d3",
                    "type": "frame",
                    "dataSource": "csv"
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
                [
                    {
                        "type": "frame",
                        "label": "d1",
                        "nodeId": "d1"
                    },
                    {
                        "type": "frame",
                        "label": "d3", 
                        "nodeId": "d3"
                    }
                ]
            ], 
            "params": []
        }

        # mnewnumber -> f1
        flow_json = {
            "nodes": [
                {
                    "id": "C",
                    "label": "C",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "a", 
                        "l": "10"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "D"
                    }
                }, 
                {
                    "id": "D",
                    "label": "D",
                    "type": "frame",
                    "dataSource": "csv"
                }, 
                {
                    "id": "F1",
                    "label": "F1",
                    "type": "flow",
                    "uuid": "3acb80c6-6f62-4785-95bf-d2e032d4aeed",
                    "args": {},
                    "srcs": {
                        "d": "D"
                    },
                    "dsts": {
                        "d1": "D1", 
                        "d3": "D2"
                    }
                },
                {
                    "id": "D1",
                    "label": "D1",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "D2",
                    "label": "D2",
                    "type": "frame",
                    "dataSource": "csv"
                }, 
            ], 
            "ports": [[],[]], 
            "params": []
        }

        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # サブフローを作成する
        sub_flow = root.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = '3acb80c6-6f62-4785-95bf-d2e032d4aeed'
        sub_flow.save()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json)) 

        # 経路途中の出力ポイント(D1)より後ろの出力ポイント(D2)をプレビューする
        vis_args = {
          "D2": {
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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'D2': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10']]}
        self.assertDictEqual(lasts, correct)

        # フローを削除する
        sub_flow.delete()

    async def test_subflow_has_in_and_out_point(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

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

    async def test_subflow_has_datasource(self):
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
        root = self.finder.data.load_root()

        # 入力フォルダを作成する
        in_folder = root.create_folder('入力フォルダ')
        in_folder.uuid = '4062d99c-54e8-477c-8c3b-b08958e0d2f3'
        in_folder.save()
        in_folder = in_folder.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = Path('./streamcat-engine/streamcat/engine/tests/test_data/')
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
        args = {'vis':vis_args, 'flow_args': {'frame_uuid':in_frame.uuid}}
        lasts = await aexecute(flow_link, args, {})
        lasts = convert_from_job_vis(lasts)

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
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datadest(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.finder.data.exists(out_frame.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('この世界で君に会えた日から輝き始めてる'))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datadest2(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {}, {})
        lasts = convert_from_job(lasts)
        
        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        self.assertIsNotNone(lasts['f0_d3'], 'SaverCommandは結果(f0_d3)を出力しませんでした')
        # 一つ目の出力結果が出力されていること
        out_frame1 = lasts['f0_d2']
        self.assertTrue(self.finder.data.exists(out_frame1.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame1.label.startswith('ひとつひとつ叶えて行けるかな　そばにいて'))
        self.assertTrue(out_frame1.file_exists)
        # 二つ目の出力結果が出力されていること
        out_frame2 = lasts['f0_d3']
        self.assertTrue(self.finder.data.exists(out_frame2.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame2.label.startswith('ひとつひとつ叶えて行けるかな　そばにいて'))
        self.assertTrue(out_frame2.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datasource_and_dest(self):
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
        root = self.finder.data.load_root()

        # 入力フォルダを作成する
        in_folder = root.create_folder('入力フォルダ')
        in_folder.uuid = '4062d99c-54e8-477c-8c3b-b08958e0d2f3'
        in_folder.save()
        in_folder = in_folder.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = Path('./streamcat-engine/streamcat/engine/tests/test_data/')
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
        args = {'flow_args': {'frame_uuid':in_frame.uuid}}
        lasts = await aexecute(flow_link, args, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(f1_d2)を出力しませんでした')
        out_frame = lasts['f1_d2']
        self.assertTrue(self.finder.data.exists(out_frame.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('どこにいても見えない　未来なんてもっと退屈な光'))
        self.assertTrue(out_frame.file_exists)

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = await aexecute(flow_link, args, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.finder.data.exists(out_frame.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('どこにいても見えない　未来なんてもっと退屈な光'))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()
        folder_src.throw_away()
        in_folder.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datedst_and_out_point(self):
        """
        サブフローがデータデストとフロー出力Pointをもつ場合、
        実行・プレビューすると、その入出力も実行されること
        """

        # (in_point) -> data_dest
        #         \_--> mnumber -> (out_point)
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
                        "label": "D1", 
                        "nodeId": "D1"
                    }
                ]
            ],
            "nodes": [
                {
                    "id": "D",
                    "label": "D",
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
                        "d": "D"
                    },
                    "dsts": {
                        "d1": "D1"
                    },
                    "srcsOrder": []
                },
                {
                    "id": "D1",
                    "label": "D1",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "srcs": {
                        "i": 'D1'
                    },
                    "dsts": {}, 
                    "uuid": self.data_dst.uuid
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        # 
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame1 = lasts['f0_d2']
        self.assertTrue(self.finder.data.exists(out_frame1.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame1.label.startswith('とっておきの場所で一緒に隠れた　陽射し揺れて'))
        self.assertTrue(out_frame1.file_exists)
        # 
        self.assertIsNotNone(lasts['D1'], 'SaverCommandは結果(D1)を出力しませんでした')
        out_frame2 = lasts['D1']
        self.assertTrue(self.finder.data.exists(out_frame2.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame2.label.startswith('D1'))
        self.assertTrue(out_frame2.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datedst_and_out_point2(self):
        """
        サブフローがデータデストとフロー出力Pointをもつ場合、
        実行・プレビューすると、その入出力も実行されること
        """

        # (in_point) -> mnumber -> (out_point) -> data_dst
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
                },
                {
                    "id": "f1",
                    "label": "Folderデータデスト",
                    "type": "flow",
                    "uuid": "683cfa29-b431-495f-b617-078123a6518c",
                    "args": {},
                    "srcs": {
                        "d1": "d1"
                    },
                    "dsts": {}
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
                        "label": "D1", 
                        "nodeId": "D1"
                    }
                ]
            ],
            "nodes": [
                {
                    "id": "D",
                    "label": "D",
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
                        "d": "D"
                    },
                    "dsts": {
                        "d1": "D1"
                    },
                    "srcsOrder": []
                },
                {
                    "id": "D1",
                    "label": "D1",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "srcs": {
                        "i": 'D1'
                    },
                    "dsts": {}, 
                    "uuid": self.data_dst.uuid
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        # 
        self.assertIsNotNone(lasts['D1'], 'SaverCommandは結果(D1)を出力しませんでした')
        out_frame2 = lasts['D1']
        self.assertTrue(self.finder.data.exists(out_frame2.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame2.label.startswith('D1'))
        self.assertTrue(out_frame2.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_hasnot_in_and_out_point(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f0_d2'], 'SaverCommandは結果(f0_d2)を出力しませんでした')
        out_frame = lasts['f0_d2']
        self.assertTrue(self.finder.data.exists(out_frame.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame.label.startswith('いつだってもどかしいよ　離れないで'))
        self.assertTrue(out_frame.file_exists)

        # ほかす
        sub_flow.throw_away()
        folder_dst.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_hasnot_in_and_out_point2(self):
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
        root = self.finder.data.load_root()

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'df5dc139-17fe-4843-9aaa-6dc1306d0e9d'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        lasts = await aexecute(flow_link, {}, {})

        # 出力結果は0件であること
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されないこと
        self.assertEqual(len(lasts), 0)

        # ほかす
        sub_flow.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datadst_after_outs(self):
        """
        サブフロー内において、データデストの前にフロー出力Pointがある経路とない経路が混在する場合、
        ある経路の場合はそこで処理が打ち切られ、ない経路の場合はデータデストまで処理が行われること
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = Path('./streamcat-engine/streamcat/engine/tests/test_data/')
        in_file_path = project.path / '2500.csv'
        shutil.copyfile(MY_TESTDATA_DIR / '2500.csv', in_file_path)

        # 入力CSVフレームを作成する
        in_frame = project.create_frame('2500.csv', None)
        in_frame.save(file_path=in_file_path)

        # mnewnumber -> mcut -> mcat -> data_dest
        # mnewrand   -> mcut __/ /
        # mnewstr    -> mcut ___/
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "col", 
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
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    "commandId": "mnewrand",
                    "args": {
                        "a": "col", 
                        "l": "10"
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
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "label": "c2", 
                    "type": "command", 
                    "commandId": "mnewstr",
                    "args": {
                        "a": "col", 
                        "l": "10", 
                        "v": "1"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d2"
                    }
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c3", 
                    "label": "c3", 
                    "type": "command", 
                    "commandId": "mcut",
                    "args": {
                        "f": "0,1",
                        "nfni": True
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {
                        "o": "d3"
                    }
                }, 
                {
                    "id": "d3", 
                    "label": "d3", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c4", 
                    "label": "c4", 
                    "type": "command", 
                    "commandId": "mcut",
                    "args": {
                        "f": "0,1",
                        "nfni": True
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "dsts": {
                        "o": "d4"
                    }
                }, 
                {
                    "id": "d4", 
                    "label": "d4", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c5", 
                    "label": "c5", 
                    "type": "command", 
                    "commandId": "mcut",
                    "args": {
                        "f": "2,3",
                        "nfni": True
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "dsts": {
                        "o": "d5"
                    }
                }, 
                {
                    "id": "d5", 
                    "label": "d5", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c6", 
                    "label": "c6", 
                    "type": "command", 
                    "commandId": "mcat",
                    "args": {}, 
                    "srcs": {
                        "*0": "d3", 
                        "*1": "d4", 
                        "*2": "d5"
                    }, 
                    "dsts": {
                        "o": "d6"
                    }
                }, 
                {
                    "id": "d6", 
                    "label": "d6", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 18:58:06", 
                        "projectId": None, 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "d6"
                    },
                    "dsts": {}
                }
            ], 
            "ports": [
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
                    }, 
                    {
                        "type": "frame", 
                        "label": "d2", 
                        "nodeId": "d2"
                    }
                ], 
                [
                    {
                        "type": "frame", 
                        "label": "d5", 
                        "nodeId": "d5"
                    }
                ]
            ], 
            "params": []
        }

        # data_source -> sub_flow -> data_dest
        # data_source ___/ /
        # data_source ____/
        flow_json = {
            "nodes": [
                {
                    "id": "i", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame.uuid
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                        {
                            "id": "s", 
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
                        }, 
                        {
                            "id": "c1", 
                            "label": "c1", 
                            "type": "command", 
                            "commandId": "loader",
                            "args": {
                            "uuid": "@[uuid]"
                            }, 
                            "srcs": {
                                "folder": "s"
                            }, 
                            "dsts": {
                                "o": "d"
                            }, 
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
                                "label": "o", 
                                "nodeId": "d"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid", 
                                "type": "frame", 
                                "label": "ファイルを指定する", 
                                "optional": False
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:03:53", 
                        "description": ""
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
                    "id": "i1", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame.uuid
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                        {
                            "id": "s", 
                            "label": "ライブラリ",
                            "type": "store", 
                            "uuid": root.uuid, 
                        }, 
                        {
                            "id": "c1", 
                            "label": "c1", 
                            "type": "command", 
                            "commandId": "loader",
                            "args": {
                            "uuid": "@[uuid]"
                            }, 
                            "srcs": {
                                "folder": "s"
                            }, 
                            "dsts": {
                                "o": "d"
                            }, 
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
                                    "label": "o", 
                                    "nodeId": "d"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid", 
                                "type": "frame", 
                                "label": "ファイルを指定する", 
                                "optional": False
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:03:53", 
                        "description": ""
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
                    "dataSource": "csv"
                }, 
                {
                    "id": "i2", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame.uuid
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                        {
                            "id": "s", 
                            "label": "ライブラリ",
                            "type": "store", 
                            "uuid": root.uuid, 
                        }, 
                        {
                            "id": "c1", 
                            "label": "c1", 
                            "type": "command", 
                            "commandId": "loader",
                            "args": {
                            "uuid": "@[uuid]"
                            }, 
                            "srcs": {
                                "folder": "s"
                            }, 
                            "dsts": {
                                "o": "d"
                            }, 
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
                                    "label": "o", 
                                    "nodeId": "d"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid", 
                                "type": "frame", 
                                "label": "ファイルを指定する", 
                                "optional": False
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:03:53", 
                        "description": ""
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d2"
                    }
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1",
                    "type": "flow", 
                    "uuid": "e0e06e11-1bf6-420a-aa33-f92466fdc3c5",
                    "args": {}, 
                    "srcs": {
                        "d": "d1", 
                        "d1": "d2", 
                        "d2": "d"
                    },
                    "dsts": {
                        "d5": "d3"
                    }
                }, 
                {
                    "id": "d3", 
                    "label": "d3", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
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
                            }, 
                        }, 
                        {
                            "id": "d1", 
                            "type": "frame", 
                            "label": "d1", 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:12:22", 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "d3"
                    }, 
                    "dsts": {}
                }
            ], 
            "ports": [[],[]],
            "params": []
        }

        # サブフローを作成する
        sub_flow = project.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = 'e0e06e11-1bf6-420a-aa33-f92466fdc3c5'
        sub_flow.save()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json)) 

        # フローを実行する
        flow_link = FlowCommand(flow)
        outs = await aexecute(flow_link, {}, {})
        outs = convert_from_job(outs)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(outs), 2)
        self.assertIsNotNone(outs['d3'])
        self.assertIsNotNone(outs['d6'])

        # 
        # 実行結果ファイルをプレビューして、その結果を検証する
        # 
        from streamcat.depo.std.commands import LoaderCommand

        d3_frame = outs['d3']
        d6_frame = outs['d6']

        vis_args = {
            'vis': {'d': 
                {
                    'command_id':'csvtohtmltable',
                    'args':{
                        'offset': 0,
                        'limit' : 2
                    }
                }
            }
        }

        # 
        # d3_frame
        # 
        datasource = root.create_datasource('tmp_source1', d3_frame.find_parent(), LoaderCommand(), {'uuid':d3_frame.uuid})
        outs = await aexecute(FlowCommand(datasource), args=vis_args)
        outs = convert_from_job_vis(outs)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))
        # 正しいVisが得られるか
        correct = {'d':[['3V','4H'],['-0.0147741509760956','0.259594465851272']]}
        self.assertDictEqual(outs, correct)

        # 
        # d6_frame
        # 
        datasource = root.create_datasource('tmp_source2', d6_frame.find_parent(), LoaderCommand(), {'uuid':d6_frame.uuid})
        outs = await aexecute(FlowCommand(datasource), args=vis_args)
        outs = convert_from_job_vis(outs)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))
        # 正しいVisが得られるか
        correct = {'d': [['Time', '3H'],['0.00191406997683585', '-0.132273064191617']]}
        self.assertDictEqual(outs, correct)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datadst_after_outs2(self):
        """
        サブフロー内において、データデストの前にフロー出力Pointがある経路とない経路が混在する場合、
        ある経路の場合はそこで処理が打ち切られ、ない経路の場合はデータデストまで処理が行われること
        (サブサブフローの直前にフロー出力Pointを設定する)
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = Path('./streamcat-engine/streamcat/engine/tests/test_data/')
        in_file_path = project.path / '2500.csv'
        shutil.copyfile(MY_TESTDATA_DIR / '2500.csv', in_file_path)

        # 入力CSVフレームを作成する
        in_frame = project.create_frame('2500.csv', None)
        in_frame.save(file_path=in_file_path)

        # -> mcut ->
        sub_sub_flow_json = {
            "nodes": [
                {
                    "id": "d00", 
                    "label": "d00", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c00", 
                    "label": "c00", 
                    "type": "command", 
                    "commandId": "mcut",
                    "args": {
                        "f": "0,1",
                        "nfni": True
                    }, 
                    "srcs": {
                        "i": "d00"
                    }, 
                    "dsts": {
                        "o": "d01"
                    }
                }, 
                {
                    "id": "d01", 
                    "label": "d01", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
            ],
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "d00", 
                        "nodeId": "d00"
                    }
                ], 
                [
                    {
                        "type": "frame", 
                        "label": "d01", 
                        "nodeId": "d01"
                    }
                ]
            ], 
            "params": []
        }

        # mnewnumber -> sub_sub_flow -> mcat -> data_dest
        # mnewrand   -> mcut __________/ /
        # mnewstr    -> mcut ___________/
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "col", 
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
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    "commandId": "mnewrand",
                    "args": {
                        "a": "col", 
                        "l": "10"
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
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "label": "c2", 
                    "type": "command", 
                    "commandId": "mnewstr",
                    "args": {
                        "a": "col", 
                        "l": "10", 
                        "v": "1"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d2"
                    }
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c3", 
                    "label": "c3", 
                    "type": "command", 
                    "commandId": "mcut",
                    "args": {
                        "f": "0,1",
                        "nfni": True
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {
                        "o": "d3"
                    }
                }, 
                {
                    "id": "d3", 
                    "label": "d3", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c4", 
                    "label": "c4", 
                    "type": "command", 
                    "commandId": "mcut",
                    "args": {
                        "f": "0,1",
                        "nfni": True
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "dsts": {
                        "o": "d4"
                    }
                }, 
                {
                    "id": "d4", 
                    "label": "d4", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "subf1", 
                    "label": "subf1",
                    "type": "flow", 
                    "uuid": "e7d0fed4-4be6-42a0-b565-34434ed661ad",
                    "args": {}, 
                    "srcs": {
                        "d00": "d2"
                    },
                    "dsts": {
                        "d01": "d5"
                    }
                }, 
                {
                    "id": "d5", 
                    "label": "d5", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c6", 
                    "label": "c6", 
                    "type": "command", 
                    "commandId": "mcat",
                    "args": {}, 
                    "srcs": {
                        "*0": "d3", 
                        "*1": "d4", 
                        "*2": "d5"
                    }, 
                    "dsts": {
                        "o": "d6"
                    }
                }, 
                {
                    "id": "d6", 
                    "label": "d6", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 18:58:06", 
                        "projectId": None, 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "d6"
                    },
                    "dsts": {}
                }
            ], 
            "ports": [
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
                    }, 
                    {
                        "type": "frame", 
                        "label": "d2", 
                        "nodeId": "d2"
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
            "params": []
        }

        # data_source -> sub_flow -> data_dest
        # data_source ___/ /
        # data_source ____/
        flow_json = {
            "nodes": [
                {
                    "id": "i", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame.uuid
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                        {
                            "id": "s", 
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
                        }, 
                        {
                            "id": "c1", 
                            "label": "c1", 
                            "type": "command", 
                            "commandId": "loader",
                            "args": {
                            "uuid": "@[uuid]"
                            }, 
                            "srcs": {
                                "folder": "s"
                            }, 
                            "dsts": {
                                "o": "d"
                            }, 
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
                                "label": "o", 
                                "nodeId": "d"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid", 
                                "type": "frame", 
                                "label": "ファイルを指定する", 
                                "optional": False
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:03:53", 
                        "description": ""
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
                    "id": "i1", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame.uuid
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                        {
                            "id": "s", 
                            "label": "ライブラリ",
                            "type": "store", 
                            "uuid": root.uuid, 
                        }, 
                        {
                            "id": "c1", 
                            "label": "c1", 
                            "type": "command", 
                            "commandId": "loader",
                            "args": {
                            "uuid": "@[uuid]"
                            }, 
                            "srcs": {
                                "folder": "s"
                            }, 
                            "dsts": {
                                "o": "d"
                            }, 
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
                                    "label": "o", 
                                    "nodeId": "d"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid", 
                                "type": "frame", 
                                "label": "ファイルを指定する", 
                                "optional": False
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:03:53", 
                        "description": ""
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
                    "dataSource": "csv"
                }, 
                {
                    "id": "i2", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_source",
                    "args": {
                        "uuid": in_frame.uuid
                    }, 
                    "flow": {
                        "label": "ライブラリ", 
                        "nodes": [
                        {
                            "id": "s", 
                            "label": "ライブラリ",
                            "type": "store", 
                            "uuid": root.uuid, 
                        }, 
                        {
                            "id": "c1", 
                            "label": "c1", 
                            "type": "command", 
                            "commandId": "loader",
                            "args": {
                            "uuid": "@[uuid]"
                            }, 
                            "srcs": {
                                "folder": "s"
                            }, 
                            "dsts": {
                                "o": "d"
                            }, 
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
                                    "label": "o", 
                                    "nodeId": "d"
                                }
                            ]
                        ], 
                        "params": [
                            {
                                "name": "uuid", 
                                "type": "frame", 
                                "label": "ファイルを指定する", 
                                "optional": False
                            }
                        ], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:03:53", 
                        "description": ""
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d2"
                    }
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1",
                    "type": "flow", 
                    "uuid": "e0e06e11-1bf6-420a-aa33-f92466fdc3c5",
                    "args": {}, 
                    "srcs": {
                        "d": "d1", 
                        "d1": "d2", 
                        "d2": "d"
                    },
                    "dsts": {
                        "d2": "d3"
                    }
                }, 
                {
                    "id": "d3", 
                    "label": "d3", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
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
                            }, 
                        }, 
                        {
                            "id": "d1", 
                            "type": "frame", 
                            "label": "d1", 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:12:22", 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "d3"
                    }, 
                    "dsts": {}
                }
            ], 
            "ports": [[],[]],
            "params": []
        }
 
        # サブサブフローを作成する
        sub_sub_flow = project.create_flow('sub_sub', FlowData(sub_sub_flow_json))
        sub_sub_flow.uuid = 'e7d0fed4-4be6-42a0-b565-34434ed661ad'
        sub_sub_flow.save()

        # サブフローを作成する
        sub_flow = project.create_flow('sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'e0e06e11-1bf6-420a-aa33-f92466fdc3c5'
        sub_flow.save()

        # フローを作成する
        flow = root.create_flow('main', FlowData(flow_json)) 

        # フローを実行する
        flow_link = FlowCommand(flow)
        outs = await aexecute(flow_link, {}, {})
        outs = convert_from_job(outs)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(outs), 2)
        self.assertIsNotNone(outs['d3'])
        self.assertIsNotNone(outs['d6'])

        # 
        # 実行結果ファイルをプレビューして、その結果を検証する
        # 
        from streamcat.depo.std.commands import LoaderCommand

        d3_frame = outs['d3']
        d6_frame = outs['d6']

        vis_args = {
            'vis': {'d': 
                {
                    'command_id':'csvtohtmltable',
                    'args':{
                        'offset': 0,
                        'limit' : 2
                    }
                }
            }
        }

        # 
        # d3_frame
        # 
        datasource = root.create_datasource('tmp_source1', d3_frame.find_parent(), LoaderCommand(), {'uuid':d3_frame.uuid})
        outs = await aexecute(FlowCommand(datasource), args=vis_args)
        outs = convert_from_job_vis(outs)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))
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
        self.assertEqual(outs['d'][0], correct)

        # 
        # d6_frame
        # 
        datasource = root.create_datasource('tmp_source2', d6_frame.find_parent(), LoaderCommand(), {'uuid':d6_frame.uuid})
        outs = await aexecute(FlowCommand(datasource), args=vis_args)
        outs = convert_from_job_vis(outs)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))
        # 正しいVisが得られるか
        correct = ['Time', '3H']
        self.assertEqual(outs['d'][0], correct)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_saver_after_outs(self):
        """
        サブフロー内において、Saverコマンドの前にフロー出力Pointがある場合、
        そのSaverコマンドは例外を送出し、フローは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewnumber -> saver
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "col", 
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

        # sub_flow -> data_dest
        flow_json = {
            "nodes": [
                {
                    "id": "f1", 
                    "label": "f1",
                    "type": "flow", 
                    "uuid": "bbed0fbe-e0ca-4e30-b816-5a35b490615d",
                    "args": {}, 
                    "srcs": {},
                    "dsts": {
                        "d": "D"
                    }
                }, 
                {
                    "id": "D", 
                    "label": "D", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
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
                            }, 
                        }, 
                        {
                            "id": "d1", 
                            "type": "frame", 
                            "label": "d1", 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:12:22", 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "D"
                    }, 
                    "dsts": {}
                }
            ], 
            "ports": [[],[]],
            "params": []
        }

        # サブフローを作成する
        sub_flow = project.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = 'bbed0fbe-e0ca-4e30-b816-5a35b490615d'
        sub_flow.save()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json)) 

        # フローを実行する
        flow_cmd = FlowCommand(flow)
        outs = await aexecute(flow_cmd, {}, {})
        outs = convert_from_job_exs(outs)

        # 例外が出力されること
        self.assertEqual(len(outs), 1)
        self.assertIsInstance(outs['f1_d1'][0], CommandException)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_out_point_between_savers(self):
        """
        サブフロー内において、2つのSaverコマンドの間ににフロー出力Pointがある場合、
        そのフロー出力Pointより後のSaverコマンドは例外を送出し、フローは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewnumber -> saver -> saver
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "col", 
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
                },
                {
                    "id": "s1",
                    "label": "ライブラリ",
                    "type": "store", 
                    "uuid": root.uuid
                }, 
                {
                    "id": "c2", 
                    "label": "c2", 
                    "type": "command", 
                    "commandId": "saver",
                    "args": {}, 
                    "srcs": {
                        "i": "d1", 
                        "folder": "s1"
                    }, 
                    "dsts": {
                        "o": "d2"
                    }
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "dataSource": "csv"
                },
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
            "params": []
        }

        # sub_flow -> data_dest
        flow_json = {
            "nodes": [
                {
                    "id": "f1", 
                    "label": "f1",
                    "type": "flow", 
                    "uuid": "a2f34a4d-6d34-489c-8c1e-3e103bf42383",
                    "args": {}, 
                    "srcs": {},
                    "dsts": {
                        "d1": "D"
                    }
                }, 
                {
                    "id": "D", 
                    "label": "D", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
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
                            }, 
                        }, 
                        {
                            "id": "d1", 
                            "type": "frame", 
                            "label": "d1", 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:12:22", 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "D"
                    }, 
                    "dsts": {}
                }
            ], 
            "ports": [[],[]],
            "params": []
        }

        # サブフローを作成する
        sub_flow = project.create_flow('', FlowData(sub_flow_json))
        sub_flow.uuid = 'a2f34a4d-6d34-489c-8c1e-3e103bf42383'
        sub_flow.save()

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json)) 

        # フローを実行する
        flow_cmd = FlowCommand(flow)
        outs = await aexecute(flow_cmd, {}, {})
        outs = convert_from_job_exs(outs)

        # 例外が出力されること
        self.assertEqual(len(outs), 1)
        self.assertIsInstance(outs['f1_d2'][0], CommandException)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_run_flow_cmd(self):
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
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "srcs": {
                        "i": 'd1'
                    },
                    "dsts": {}, 
                    "uuid": self.data_dst.uuid
                }
            ]
        }

        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # フローを作成する
        flow = root.create_flow('Main', FlowData(flow_json))

        # フローを実行する
        flow_cmd = FlowCommand(flow)
        outs = flow_cmd.run()

        # FlowCommandはoutsを出力すること
        # d1とo0_d1_runs_activity_0(データデストが開いたPort)の2つ
        self.assertEqual(len(outs), 2)
        self.assertIsNotNone(outs['d1'], 'FlowCommandは結果(d1)を出力しませんでした')
        self.assertIsNotNone(outs['o0_d1_runs_activity_0'], 'FlowCommandは結果(o0_d1_runs_activity_0)を出力しませんでした')
        # apparentOutsはapparentOutを一つ持っていること
        apparentOuts = outs['o0_d1_runs_activity_0']
        self.assertEqual(len(apparentOuts.outs), 1)
        self.assertEqual(apparentOuts.outs[0].out_point.id, 'd1')
        # apparentOutは出力frameを持っていること
        out_frame1 = apparentOuts.outs[0].datum
        self.assertTrue(self.finder.data.exists(out_frame1.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame1.file_exists)

    async def test_run_cmd(self):
        """
        Commandを直接runしても結果が得られること
        """
        # コマンドを作成する
        import nysol.mcmd as nm 
        from streamcat.depo.std.commands import CommandLink
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

    async def test_remove_tmp_files_after_run(self):
        """
        フロー実行後にTmpファイルが削除されること
        """
        from streamcat.core import Tmp

        # ルートデータストアを取得する
        root = self.finder3.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewnumber -> tmp
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "a": "num",
                        "I": "1",
                        "S": "1",
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
                    "id": "c1",
                    "label": "Tmpファイルコマンド",
                    "type": "command",
                    "commandId": "tmp",
                    "args": {},
                    "srcs": {
                        "i": "d"
                    },
                    "dsts": {
                        "o": "d1"
                    },
                },
                {
                    "id": "d1",
                    "label": "d1",
                    "type": "frame",
                    "dataSource": "csv"
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

        # subflowを呼び出す
        flow_json = {
            "nodes": [
                {
                    "id": "f",
                    "label": "f",
                    "type": "flow",
                    "uuid": "48d4e950-c41b-4b4f-a170-42599d6088d6",
                    "args": {},
                    "srcs": {},
                    "dsts": {
                        "d1": "D"
                    },
                },
                {
                    "id": "D",
                    "label": "モナリザ",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "uuid": self.data_dst.uuid,
                    "srcs": {
                        "i": 'D'
                    },
                    "dsts": {},
                }
            ],
            "ports": [[],[]]
        }

        # サブフローを作成する
        sub_flow = project.create_flow('Tmpファイルを作成するサブフロー', FlowData(sub_flow_json))
        sub_flow.uuid = '48d4e950-c41b-4b4f-a170-42599d6088d6'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('Mainフロー', FlowData(flow_json)) 
        flow.save()
        flow = flow.reload()

        # フロー実行前に全てのTmpファイルを削除する
        tmp_files = [f for f in Tmp._get_tmp_directory().glob(f'__SCATTMP_*')]
        for f in tmp_files:
            f.unlink(missing_ok=True)

        # フローを実行する
        flow_cmd = FlowCommand(flow)
        outs = await aexecute(flow_cmd, {}, {})
        outs = convert_from_job(outs)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(outs), 1)

        # D
        self.assertIsNotNone(outs['D'], 'SaverCommandは結果(D)を出力しませんでした')
        out_frame1 = outs['D']
        self.assertTrue(self.finder3.data.exists(out_frame1.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame1.label.startswith('モナリザ'))
        self.assertTrue(out_frame1.file_exists)

        # TmpディレクトリからTMPファイルを取得する
        tmp_files = [f for f in Tmp._get_tmp_directory().glob(f'__SCATTMP_*')]
        # フロー実行後はTmpファイルは削除されていること
        self.assertEqual(len(tmp_files), 0, msg=f'{len(tmp_files)}つのTmpファイルが残っています')

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder3.data.load_trash_folder()
        trash.trash_all()

    async def test_vis_optimization(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10'],
                          ['11'], ['12'], ['13'], ['14'], ['15'], ['16'], ['17'], ['18'], ['19'], ['20']]}
        self.assertDictEqual(lasts, correct)

    async def test_vis_optimization_with_make_cache(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})

        print(lasts)

        lasts = convert_from_job_vis(lasts)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(lasts))

        # 正しいVisが得られるか
        correct = {'d1': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10'],
                          ['11'], ['12'], ['13'], ['14'], ['15'], ['16'], ['17'], ['18'], ['19'], ['20']]}
        self.assertDictEqual(lasts, correct)

    async def test_vis_deep_subflow_call(self):
        """
        十分に深い呼出関係のサブフローをプレビューできること
        """

        # ルートデータストアを取得する
        root = self.finder.data.load_root()
        # 参照先フレームを作成する
        frame1 = root.create_frame('CSV1', io.BytesIO(b''))
        frame1.save()
        # 参照先サブフローを作成する
        sub_flow1 = root.create_flow('サブフロー1', FlowData({}))
        sub_flow1.save()

        sub_flow4 = {
            "label": "subflow4", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": frame1.uuid, 
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
                    "uuid": frame1.uuid, 
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
                        "testData": "d"
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
                    "uuid": frame1.uuid, 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "uuid": frame1.uuid, 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1",
                    "args": {}, 
                    "srcs": {
                        "testData": "d"
                    }, 
                    "dsts": {
                        "d3": "d2"
                    }, 
                    "type": "flow", 
                    "uuid": "99f81446-d805-481c-9329-b555a4b1a240"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f2", 
                    "label": "f2",
                    "args": {}, 
                    "srcs": {
                        "testData": "d1"
                    }, 
                    "dsts": {
                        "d3": "d3"
                    }, 
                    "type": "flow", 
                    "uuid": "99f81446-d805-481c-9329-b555a4b1a240"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "k": "0,1", 
                        "x": True
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "dsts": {
                        "o": "d4"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "muniq"
                }, 
                {
                    "id": "d4", 
                    "type": "frame", 
                    "label": "d4", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "k": "customer,date"
                    }, 
                    "srcs": {
                        "i": "d3"
                    }, 
                    "dsts": {
                        "o": "d5"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "muniq"
                },
                {
                    "id": "d5", 
                    "type": "frame", 
                    "label": "d5", 
                    "dataSource": "csv"
                }
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "testData1", 
                        "nodeId": "d1"
                    }, 
                    {
                        "type": "frame", 
                        "label": "testData2", 
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
                    "uuid": frame1.uuid, 
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
                        "testData1": "d", 
                        "testData2": "d"
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
                        "testData": "d"
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {'vis':vis_args}, {})
        lasts = convert_from_job_vis(lasts)

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
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_deep_datadest_call(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(flow_link, {}, {})
        lasts = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(f1_d2)を出力しませんでした')
        self.assertIsNotNone(lasts['f1_d2_1'], 'SaverCommandは結果(f1_d2_1)を出力しませんでした')
        out_frame1 = lasts['f1_d2']
        out_frame2 = lasts['f1_d2_1']
        self.assertTrue(self.finder.data.exists(out_frame1.uuid, type=SavableDatum.FLOW_TYPE))
        self.assertTrue(self.finder.data.exists(out_frame2.uuid, type=SavableDatum.FLOW_TYPE))
        print(out_frame1.label)
        self.assertTrue(out_frame1.label.startswith('この世界に君が居てくれる道は　不思議と好きになる'))
        self.assertTrue(out_frame2.label.startswith('この世界に君が居てくれる道は　不思議と好きになる'))

        # ほかす
        out_frame1.throw_away()
        out_frame2.throw_away()
        sub_flow1.throw_away()
        sub_flow2.throw_away()
        sub_flow3.throw_away()
        sub_flow4.throw_away()
        postgre_src.throw_away()
        postgre_dst.throw_away()
        db.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    @unittest.skip('テストケースの実行ログが溢れるのでテストしない')
    async def test_vis_circular_subflow_call(self):
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
        root = self.finder.data.load_root()

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
            await aexecute(flow_link, {'vis':vis_args}, {})

    async def test_subflow_has_no_data_out_point(self):
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
        root = self.finder.data.load_root()

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
        lasts = await aexecute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_job_vis(lasts)
        self.assertIsNone(results)

        # 実行しても結果は得られない
        lasts = await aexecute(FlowCommand(flow), {}, {})
        results = convert_from_job(lasts)
        self.assertIsNone(results)

        # ほかす
        sub_flow.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_inner_subflow(self):
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
                        "testData": "d"
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
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "srcs": {
                        "i": 'd1'
                    },
                    "dsts": {}, 
                    "uuid": self.data_dst.uuid
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 14:16:55"
        }

        # ルートデータストアを取得する
        root = self.finder.data.load_root()

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
        lasts = await aexecute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_job_vis(lasts)

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
        lasts = await aexecute(FlowCommand(flow), {}, {})
        results = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(results['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame2 = results['d1']
        self.assertTrue(self.finder.data.exists(out_frame2.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame2.file_exists)

    async def test_inner_subflow_has_makecache(self):
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
                        "testData": "d"
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
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "srcs": {
                        "i": 'd1'
                    },
                    "dsts": {}, 
                    "uuid": self.data_dst.uuid
                }
            ], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-23 14:16:55"
        }

        # ルートデータストアを取得する
        root = self.finder.data.load_root()

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
        lasts = await aexecute(FlowCommand(flow), {'vis':vis_args}, {})
        results = convert_from_job_vis(lasts)

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
        lasts = await aexecute(FlowCommand(flow), {}, {})
        results = convert_from_job(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(results['d1'], 'SaverCommandは結果(d1)を出力しませんでした')
        out_frame2 = results['d1']
        self.assertTrue(self.finder.data.exists(out_frame2.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame2.file_exists)

    async def test_run_flow_cmd_reentrant(self):
        """
        Flow Commandのrun()を再実行できること
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

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
                        "i": "d"
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
        outs1 = flow_cmd.run()

        # FlowCommandはoutsを出力すること
        # dとo_d1_runs_activity_0(データデストが開いたPort)の2つ
        self.assertEqual(len(outs1), 2)
        self.assertIsNotNone(outs1['d'], 'FlowCommandは結果(d)を出力しませんでした')
        self.assertIsNotNone(outs1['o_d1_runs_activity_0'], 'FlowCommandは結果(o_d1_runs_activity_0)を出力しませんでした')
        # apparentOutsはapparentOutを一つ持っていること
        apparentOuts = outs1['o_d1_runs_activity_0']
        self.assertEqual(len(apparentOuts.outs), 1)
        self.assertEqual(apparentOuts.outs[0].out_point.id, 'd')
        # apparentOutは出力frameを持っていること
        out_frame1 = apparentOuts.outs[0].datum
        self.assertTrue(self.finder.data.exists(out_frame1.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame1.file_exists)

        # 同じFlowCommandオブジェクトを用いて
        # 再度フローを実行する
        outs2 = flow_cmd.run()

        # FlowCommandはoutsを出力すること
        # dとo_d1_runs_activity_0(データデストが開いたPort)の2つ
        self.assertEqual(len(outs2), 2)
        self.assertIsNotNone(outs2['d'], 'FlowCommandは結果(d)を出力しませんでした')
        self.assertIsNotNone(outs2['o_d1_runs_activity_0'], 'FlowCommandは結果(o_d1_runs_activity_0)を出力しませんでした')
        # apparentOutsはapparentOutを一つ持っていること
        apparentOuts = outs2['o_d1_runs_activity_0']
        self.assertEqual(len(apparentOuts.outs), 1)
        self.assertEqual(apparentOuts.outs[0].out_point.id, 'd')
        # apparentOutは出力frameを持っていること
        out_frame2 = apparentOuts.outs[0].datum
        self.assertTrue(self.finder.data.exists(out_frame1.uuid, type=SavableDatum.FRAME_TYPE))
        self.assertTrue(out_frame1.file_exists)

        # 初回と再実行はそれぞれ異なる出力結果を出力すること
        self.assertNotEqual(out_frame1.uuid, out_frame2.uuid)

    async def test_run_datedest_after_empty_point(self):
        """
        空のPointを入力とするデータデストを実行しても
        実行結果は出力されないこと
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # -> data_dest
        flow_json = {
            "nodes": [
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
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
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
                            }, 
                        }, 
                        {
                            "id": "d1", 
                            "type": "frame", 
                            "label": "d1", 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:12:22", 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {}
                }
            ], 
            "ports": [[],[]],
            "params": []
        }

        # フローを作成する
        flow = root.create_flow('', FlowData(flow_json)) 

        # フローを実行する
        flow_link = FlowCommand(flow)
        outs = await aexecute(flow_link, {}, {})
        outs = convert_from_job(outs)

        # 結果は出力されないこと
        self.assertIsNone(outs)
    
        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_datedest_after_empty_point(self):
        """
        サブフローが空のPointを入力とするデータデストを持つ場合
        実行結果は出力されないこと
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # -> data_dest
        sub_flow_json = {
            "nodes": [
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
                            "type": "store", 
                            "uuid": root.uuid, 
                            "label": "ライブラリ"
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
                            }, 
                        }, 
                        {
                            "id": "d1", 
                            "type": "frame", 
                            "label": "d1", 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-04 19:12:22", 
                        "description": ""
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {}
                }
            ], 
            "ports": [[],[]],
            "params": []
        }

        # -> sub_flow
        flow_json = {
            "label": "main",
            "params": [],
            "ports": [
                [],
                [
                    {
                        "type": "frame", 
                        "label": "D1", 
                        "nodeId": "D1"
                    }
                ]
            ],
            "nodes": [
                {
                    "id": "D",
                    "label": "D",
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
                    "uuid": "6f10cdaf-f28f-4a8b-bc8e-67cd5562e47e",
                    "args": {},
                    "srcs": {},
                    "dsts": {},
                    "srcsOrder": []
                },
                {
                    "id": "D1",
                    "label": "D1",
                    "type": "frame",
                    "uuid": None,
                    "makeCache": False,
                    "dataSource": "csv",
                    "cacheCreatedAt": None
                },
                {
                    "id": 'o0', 
                    "label": "ライブラリ出力🖨", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "srcs": {
                        "i": 'D1'
                    },
                    "dsts": {}, 
                    "uuid": self.data_dst.uuid
                }
            ]
        }

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '6f10cdaf-f28f-4a8b-bc8e-67cd5562e47e'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('sub', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        outs = await aexecute(flow_link, {}, {})
        outs = convert_from_job(outs)

        # 結果は出力されないこと
        self.assertIsNone(outs)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_forked_branch_after_out(self):
        """
        サブフローにフロー出力Pointの後に分岐がある場合、
        分岐の後のデータデストとフロー出力Pointが機能すること
        """
        # ルートデータストアを取得する
        root = self.finder.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        #     mnewnumber -> mcat -> data_dest
        # mnewrand -> mcut __/
        #     \_ mcal    \_ mcal -> data_dest
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    "commandId": "mnewrand",
                    "args": {
                        "a": "col", 
                        "l": "10"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d1"
                    }, 
                }, 
                {
                    "id": "d1", 
                    "label": "d1", 
                    "type": "frame", 
                    "dataSource": "csv"
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
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c3", 
                    "label": "c3", 
                    "type": "command", 
                    "commandId": "mcat",
                    "args": {}, 
                    "srcs": {
                        "*0": "d", 
                        "*1": "d2"
                    }, 
                    "dsts": {
                        "o": "d3"
                    }, 
                }, 
                {
                    "id": "d3", 
                    "label": "d3", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
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
                                "uuid": root.uuid, 
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
                                }, 
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
                    }, 
                    "args": {}, 
                    "srcs": {
                        "i": "d3"
                    }, 
                    "dsts": {}, 
                }, 
                # 
                # mnewnumbewr -> mcat ->
                # 
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "col", 
                        "l": "10"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d"
                    }, 
                }, 
                {
                    "id": "d", 
                    "label": "d", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                # 
                # -> mcal -> data_dest
                # 
                {
                    "id": "c5", 
                    "label": "c5", 
                    "type": "command", 
                    "commandId": "mcal",
                    "args": {
                        "a": "col2", 
                        "c": "2", 
                        "precision": 10
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "dsts": {
                        "o": "d5"
                    }, 
                }, 
                {
                    "id": "d5", 
                    "label": "d5", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o1", 
                    "label": "ライブラリ",
                    "type": "flow",  
                    "classification": "data_dest",
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
                                "uuid": root.uuid, 
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
                                }, 
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
                    }, 
                    "args": {}, 
                    "srcs": {
                        "i": "d5"
                    }, 
                    "dsts": {}, 
                },

                # 
                # -> mcal
                # 
                {
                    "id": "c4", 
                    "label": "c4", 
                    "type": "command", 
                    "commandId": "mcal",
                    "args": {
                        "a": "col1", 
                        "c": "1", 
                        "precision": 10
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "dsts": {
                        "o": "d4"
                    }, 
                }, 
                {
                    "id": "d4", 
                    "label": "d4", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
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
                        "label": "d4", 
                        "nodeId": "d4"
                    }
                ]
            ] 
        }

        # sub_flow => mcat -> data_dest
        flow_json = {
            "nodes": [
                {
                    "id": "f", 
                    "label": "f",
                    "type": "flow", 
                    "uuid": "68956134-154d-4bc4-a99c-1e41c6a89c35", 
                    "args": {}, 
                    "srcs": {}, 
                    "dsts": {
                        "d1": "D", 
                        "d4": "D1"
                    }, 
                }, 
                {
                    "id": "D", 
                    "label": "D", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "D1", 
                    "label": "D1", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "label": "c1", 
                    "type": "command", 
                    "commandId": "mnjoin",
                    "args": {
                        "k": "col", 
                        "bufcount": "10"
                    }, 
                    "srcs": {
                        "i": "D", 
                        "m": "D1"
                    }, 
                    "dsts": {
                        "o": "D2"
                    }, 
                }, 
                {
                    "id": "D2", 
                    "label": "D2", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
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
                            "uuid": root.uuid, 
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
                            }, 
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
                    }, 
                    "args": {}, 
                    "srcs": {
                        "i": "D2"
                    }, 
                    "dsts": {}, 
                }
            ], 
            "ports": [[],[]],
        }

        # サブフローを作成する
        sub_flow = root.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '68956134-154d-4bc4-a99c-1e41c6a89c35'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = root.create_flow('main', FlowData(flow_json))

        # フローを実行する
        flow_link = FlowCommand(flow)
        outs = await aexecute(flow_link, {}, {})
        outs = convert_from_job(outs)

        # ライブラリに結果データが出力されていること
        self.assertEqual(len(outs), 2)
        # D2
        self.assertIsNotNone(outs['D2'])
        self.assertEqual(outs['D2'].type, 'frame')
        self.assertGreater(outs['D2'].file_size, 0)
        # d3
        self.assertIsNotNone(outs['d3'])
        self.assertEqual(outs['d3'].type, 'frame')
        self.assertGreater(outs['d3'].file_size, 0)

        # プロジェクトをほかす
        project.throw_away()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_subflow_has_inout_at_same_point(self):
        """
        サブフロー内において、フロー入出力Pointの後にデータデストがある場合
        そららのデータデストは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewnumber -> in/out -> data_dest
        #                \  \_--> data_dest
        #                 \_----> data_dest
        sub_flow_json = {
            "nodes": [
                {
                    "id": "n1", 
                    "label": "n1", 
                    "type": "note", 
                    "title": "新しいメモ", 
                    "content": "aa", 
                    "color": "green", 
                    "fontSize": 16
                }, 
                {
                    "id": "c", 
                    "label": "c", 
                    "type": "command", 
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "a", 
                        "l": "1000"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d"
                    }, 
                }, 
                {
                    "id": "d", 
                    "label": "out-of-subflow", 
                    "type": "frame",  
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                                "uuid": project.uuid, 
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
                                }, 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-12 23:32:42", 
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {}, 
                }, 
                {
                    "id": "o1", 
                    "label": "ライブラリ",
                    "type": "flow",  
                    "classification": "data_dest",
                    "args": {}, 
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
                                "uuid": project.uuid, 
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
                                }, 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-13 07:45:07", 
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {}, 
                }, 
                {
                    "id": "o2",
                    "label": "ライブラリ", 
                    "type": "flow",  
                    "classification": "data_dest",
                    "args": {}, 
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
                                "uuid": project.uuid, 
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
                                }, 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-13 07:45:07", 
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "dsts": {}, 
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
                [
                    {
                        "type": "frame", 
                        "label": "d", 
                        "nodeId": "d"
                    }
                ]
            ], 
            "params": [
                {
                    "name": "new_param1", 
                    "type": "string", 
                    "label": "new_param1"
                }
            ], 
        }

        # data_source -> sub_flow -> data_dest
        flow_json = {
            "nodes": [
                {
                    "id": "D", 
                    "label": "testData", 
                    "type": "frame", 
                    "value": [["顧客","数量","金額"],
                              ["x", 1, 10],
                              ["x", 2, 20],
                              ["y", 1, 30],
                              ["y", 3, 40],
                              ["z", 1, 50]],
                    "makeCache" : True,
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "label": "f1",
                    "type": "flow", 
                    "uuid": "97a8df8d-6b40-49d5-ab73-0ed1110386bf", 
                    "args": {
                        "new_param1": "999"
                    }, 
                    "srcs": {
                        "d": "D"
                    }, 
                    "dsts": {
                        "d": "D1"
                    }, 
                }, 
                {
                    "id": "D1", 
                    "label": "out-of-flow", 
                    "type": "frame", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "o", 
                    "label": "ライブラリ1", 
                    "type": "flow", 
                    "classification": "data_dest",
                    "args": {}, 
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
                                "uuid": project.uuid, 
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
                                }, 
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
                        "params": [], 
                        "creator": "ユーザー管理者", 
                        "createdAt": "2022-06-13 07:49:26", 
                    }, 
                    "srcs": {
                        "i": "D1"
                    }, 
                    "dsts": {}, 
                }
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "o", 
                        "nodeId": "D"
                    }
                ], 
                [
                    {
                        "type": "frame", 
                        "label": "i", 
                        "nodeId": "D"
                    }
                ]
            ]
        }

        # サブフローを作成する
        sub_flow = project.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '97a8df8d-6b40-49d5-ab73-0ed1110386bf'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('main', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フローを実行して、キャッシュを作成する
        # (サブフロー内ではキャッシュは作成しない)
        flow_cmd = FlowCommand(flow)
        outs = await aexecute(flow_cmd, {'use_cache':True}, {})
        outs = convert_from_job(outs)

        # ライブラリに結果データが出力されていること
        self.assertEqual(len(outs), 1)
        # out-of-flow
        self.assertIsNotNone(outs['D1'])
        self.assertEqual(outs['D1'].type, 'frame')
        self.assertGreater(outs['D1'].file_size, 0)

        # 再度、フローを実行する
        # (入力にはキャッシュが使用される)
        flow_cmd = FlowCommand(flow)
        outs = await aexecute(flow_cmd, {'use_cache':True}, {})
        outs = convert_from_job(outs)

        # ライブラリに結果データが出力されていること
        self.assertEqual(len(outs), 1)
        # out-of-flow
        self.assertIsNotNone(outs['D1'])
        self.assertEqual(outs['D1'].type, 'frame')
        self.assertGreater(outs['D1'].file_size, 0)

        # プロジェクトをほかす
        project.throw_away()

        # 作成と変更を確定する
        self.finder2.end()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_vis_outside_subflow(self):
        """
        メインフロー内において、プレビューの経路にないコマンド(サブフロー)は実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewnumber -> raise -> data_dest
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1",
                        "S": "1",
                        "a": "num",
                        "l": "7"
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
                    "id": "c1",
                    "label": "例外を送出",
                    "type": "command",
                    # このコマンドが実行されれば無条件に例外を送出する
                    "commandId": "raise",
                    "args": {
                        "immediately": True
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
                },
                {
                    "id": "o",
                    "label": "ライブラリ",
                    "type": "flow",
                    "classification": "data_dest",
                    "args": {},
                    "srcs": {
                        "i": "d1"
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
                                "uuid": project.uuid, 
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
                                "label": "i",
                                "types": [
                                    "mcmd"
                                ],
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
                    "label": "d1",
                    "nodeId": "d1"
                }
                ]
            ],
            "params": []
        }

        # mnewstr, sub_flow
        flow_json = {
            "nodes": [
                {
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": "mnewstr",
                    "args": {
                        "a": "str",
                        "l": "5",
                        "v": "ABC"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d"
                    }
                },     {
                    "id": "d",
                    "label": "d",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "f",
                    "label": "f",
                    "type": "flow",
                    "uuid": "6d459fed-2be3-423e-9cca-a2bc5f090e11",
                    "args": {},
                    "srcs": {},
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
            "ports": [
                [],
                []
            ],
            "params": []
        }

        # サブフローを作成する
        sub_flow = project.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '6d459fed-2be3-423e-9cca-a2bc5f090e11'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('main', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 10
            }
          }
        }

        # フローをプレビューする
        # (RaiseCommandが実行されないこと)
        flow_link = FlowCommand(flow)
        job = await aexecute(flow_link, {'vis':vis_args}, {})
        outs = convert_from_job_vis(job)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))

        # 正しいVisが得られるか
        correct = {'d': [['ABC'],['ABC'],['ABC'],['ABC'],['ABC']]}
        self.assertDictEqual(outs, correct)

        # プロジェクトをほかす
        project.throw_away()

        # 作成と変更を確定する
        self.finder2.end()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_vis_subflow_has_outside_datadst(self):
        """
        サブフロー内において、プレビュー実行の経路にないデータデストは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewnumber -> raise -> data_dst
        # mnewnumber
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1",
                        "S": "10",
                        "a": "num",
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
                    "id": "c1",
                    "label": "例外を送出",
                    "type": "command",
                    # このコマンドが実行されれば無条件に例外を送出する
                    "commandId": "raise",
                    "args": {
                        "immediately": True
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
                },
                {
                    "id": "o",
                    "label": "ライブラリ",
                    "type": "flow",
                    "classification": "data_dest",
                    "args": {},
                    "srcs": {
                        "i": "d1"
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
                                "uuid": project.uuid
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
                                    "label": "i",
                                    "types": [
                                        "mcmd"
                                    ],
                                    "nodeId": "d"
                                }
                            ],
                            []
                        ],
                        "params": [],
                    }
                },
                {
                    "id": "c2",
                    "args": {
                        "I": "1",
                        "S": "1",
                        "a": "num",
                        "l": "10"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                    "srcs": {},
                    "type": "command",
                    "label": "c2",
                    "commandId": "mnewnumber"
                },
                {
                    "id": "d2",
                    "type": "frame",
                    "label": "d2",
                    "dataSource": "csv"
                }
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
            "params": []
        }

        #
        flow_json = {
            "nodes": [
                {
                    "id": "f",
                    "label": "f",
                    "type": "flow",
                    "uuid": "5e1610cb-29fe-48f1-a1d5-abc2ebe53535",
                    "args": {},
                    "srcs": {},
                    "dsts": {
                        "d2": "d1"
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
                [],
                []
            ],
            "params": []
        }

        # サブフローを作成する
        sub_flow = project.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '5e1610cb-29fe-48f1-a1d5-abc2ebe53535'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('main', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 10
            }
          }
        }

        # フローをプレビューする
        # (RaiseCommandが実行されないこと)
        flow_link = FlowCommand(flow)
        job = await aexecute(flow_link, {'vis':vis_args}, {})
        outs = convert_from_job_vis(job)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))

        # 正しいVisが得られるか
        correct = {'d1': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10']]}
        self.assertDictEqual(outs, correct)

        # プロジェクトをほかす
        project.throw_away()

        # 作成と変更を確定する
        self.finder2.end()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_vis_subflow_has_outside_path(self):
        """
        サブフロー内において、プレビュー実行の経路にないコマンドは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewrand -> mcut
        # mnewrand -> raise
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "type": "command",
                    "commandId": "mnewrand",
                    "args": {
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
                    "id": "c2",
                    "label": "c2",
                    "type": "command",
                    "commandId": "mcut",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d"
                    },
                    "dsts": {
                        "o": "d2"
                    },
                },
                {
                    "id": "d2",
                    "label": "d2",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": "mnewrand",
                    "args": {
                        "l": "10"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d1"
                    },
                },
                {
                    "id": "d1",
                    "label": "d1",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "c3",
                    "label": "c3",
                    "type": "command",
                    "commandId": "raise",
                    "args": {
                        "immediately": True
                    },
                    "srcs": {
                        "i": "d1"
                    },
                    "dsts": {
                        "o": "d3"
                    },
                },
                {
                    "id": "d3",
                    "label": "d3",
                    "type": "frame",
                    "dataSource": "csv"
                }
            ],
            "ports": [
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
            "params": []
        }

        # 
        flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "type": "command",
                    "label": "c",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1",
                        "S": "20",
                        "a": "num",
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
                    "id": "c1",
                    "label": "c1",
                    "type": "command",
                    "commandId": "mnewnumber",
                    "args": {
                        "I": "1",
                        "S": "30",
                        "a": "num",
                        "l": "10"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "d1"
                    },
                },
                {
                    "id": "d1",
                    "type": "frame",
                    "label": "d1",
                    "dataSource": "csv"
                },
                {
                    "id": "f1",
                    "label": "f1",
                    "type": "flow",
                    "uuid": "14ed7cd5-7ee0-4927-af1a-5ff015453887",
                    "args": {},
                    "srcs": {
                        "d": "d1",
                        "d1": "d"
                    },
                    "dsts": {
                        "d2": "d2",
                        "d3": "d3"
                    },
                },
                {
                    "id": "d2",
                    "label": "d2",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "d3",
                    "label": "d3",
                    "type": "frame",
                    "dataSource": "csv"
                }
            ],
            "ports": [
                [],
                []
            ],
            "params": []
        }

        # サブフローを作成する
        sub_flow = project.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = '14ed7cd5-7ee0-4927-af1a-5ff015453887'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('main', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        vis_args = {
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 10
            }
          }
        }

        # フローをプレビューする
        # (RaiseCommandが実行されないこと)
        flow_link = FlowCommand(flow)
        job = await aexecute(flow_link, {'vis':vis_args}, {})
        outs = convert_from_job_vis(job)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))

        # 正しいVisが得られるか
        correct = {'d2': [['30'], ['31'], ['32'], ['33'], ['34'], ['35'], ['36'], ['37'], ['38'], ['39']]}
        self.assertDictEqual(outs, correct)

        # プロジェクトをほかす
        project.throw_away()

        # 作成と変更を確定する
        self.finder2.end()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()

    async def test_vis_mainflow_has_outside_path(self):
        """
        メインフロー内において、プレビュー実行の経路にないコマンドは実行されないこと
        """
        # ルートデータストアを取得する
        root = self.finder2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('プロジェクト')
        project.save()
        project = project.reload()

        # mnewstr -> mcut
        # mnewstr -> mcut
        sub_flow_json = {
            "nodes": [
                {
                    "id": "c",
                    "label": "c",
                    "commandId": "mnewstr",
                    "type": "command",
                    "args": {
                        "a": "a",
                        "l": "10",
                        "v": "abc"
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
                    "id": "c2_",
                    "label": "c2_",
                    "commandId": "mcut",
                    "type": "command",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d"
                    },
                    "dsts": {
                        "o": "d2"
                    }
                },
                {
                    "id": "d2",
                    "label": "d2",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "c1",
                    "label": "c1",
                    "commandId": "mnewstr",
                    "type": "command",
                    "args": {
                        "a": "b",
                        "l": "10",
                        "v": "def"
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
                    "dataSource": "csv"
                },
                {
                    "id": "c3_",
                    "label": "c3_",
                    "commandId": "mcut",
                    "type": "command",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "d1"
                    },
                    "dsts": {
                        "o": "d3"
                    }
                },
                {
                    "id": "d3",
                    "label": "d3",
                    "type": "frame",
                    "dataSource": "csv"
                }
            ],
            "ports": [
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
            ]
        }

        # mnewnumber -> mcut -> subflow
        # mnewnumber -> mcut __/
        flow_json = {
            "nodes": [
                {
                    "id": "C",
                    "label": "C",
                    "commandId": "raise",
                    "type": "command",
                    "commandId": "raise",
                    "args": {
                        "immediately": True
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "D"
                    },
                },
                {
                    "id": "D",
                    "label": "D",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "C2",
                    "label": "C2",
                    "commandId": "mcut",
                    "type": "command",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "D"
                    },
                    "dsts": {
                        "o": "D2"
                    },
                },
                {
                    "id": "D2",
                    "label": "D2",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "C1",
                    "label": "C1",
                    "commandId": "mnewnumber",
                    "type": "command",
                    "args": {
                        "I": "1",
                        "S": "1",
                        "a": "num1",
                        "l": "10"
                    },
                    "srcs": {},
                    "dsts": {
                        "o": "D1"
                    },
                },
                {
                    "id": "D1",
                    "label": "D1",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "C3",
                    "label": "C3",
                    "commandId": "mcut",
                    "type": "command",
                    "args": {
                        "f": "*"
                    },
                    "srcs": {
                        "i": "D1"
                    },
                    "dsts": {
                        "o": "D3"
                    },
                },
                {
                    "id": "D3",
                    "label": "D3",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "f1",
                    "label": "f1",
                    "type": "flow",
                    "uuid": "e7314fee-0bfb-48c1-a362-53c60d4612ca",
                    "args": {},
                    "srcs": {
                        "d": "D2",
                        "d1": "D3"
                    },
                    "dsts": {
                        "d2": "D4",
                        "d3": "D5"
                    },
                },
                {
                    "id": "D4",
                    "label": "D4",
                    "type": "frame",
                    "dataSource": "csv"
                },
                {
                    "id": "D5",
                    "label": "D5",
                    "type": "frame",
                    "dataSource": "csv"
                },
            ],
            "ports": [[],[]]
        }

        # サブフローを作成する
        sub_flow = project.create_flow('Sub', FlowData(sub_flow_json))
        sub_flow.uuid = 'e7314fee-0bfb-48c1-a362-53c60d4612ca'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('main', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        vis_args = {
          "D5": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 10
            }
          }
        }

        # フローをプレビューする
        # (RaiseCommandが実行されないこと)
        flow_link = FlowCommand(flow)
        job = await aexecute(flow_link, {'vis':vis_args}, {})
        outs = convert_from_job_vis(job)

        # visデータは1つ生成されているか
        self.assertEqual(1, len(outs))

        # 正しいVisが得られるか
        correct = {'D5': [['1'], ['2'], ['3'], ['4'], ['5'], ['6'], ['7'], ['8'], ['9'], ['10']]}
        self.assertDictEqual(outs, correct)

        # プロジェクトをほかす
        project.throw_away()

        # 作成と変更を確定する
        self.finder2.end()

        # ゴミ箱を空にする
        trash = self.finder.data.load_trash_folder()
        trash.trash_all()
