import copy
import unittest
import shutil
from pathlib import Path

from kskp.core import Datum
from kskp.store import DatabaseConn, FlowData, NysolModule
from kskp.store.lock import lock_manager
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowCommand
from .test_main import convert_from_activity, convert_from_activity_vis, convert_from_activity_cache, convert_from_activity_exs
from .make_flow_json import create_flow_by_flow_id

class CacheTest(TestCaseBase):
    """
    フローのキャッシュ指定の検証
    """
    def test_vis_mainflow_with_use_cache(self):
        """
        use_cache=Trueを指定して実行した場合
        他ユーザにより排他ロック中のメインフローにおいては、キャッシュの作成はしない・参照はする
        """
        flow_json = {
            "label": "cache", 
            "nodes": [ 
                {
                    "id": "c1", 
                    "label": "c1", 
                    "args": {
                        "a": "amount", 
                        "l": "5"
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {}, 
                    "type": "command", 
                    "commandId": "mnewrand"
                },
                {
                    "id": "d1", 
                    "label": "d1", 
                    "type": "frame", 
                    "dataSource": "csv"
                },
                {
                    "id": "c1", 
                    "label": "c1", 
                    "args": {
                        "a": "avg", 
                        "c": "avg(#{amount},${amount})", 
                        "precision": 10
                    },  
                    "srcs": {
                        "i": "d1"
                    },
                    "dsts": {
                        "o": "d2"
                    }, 
                    "type": "command", 
                    "commandId": "mcal"
                }, 
                {
                    "id": "d2", 
                    "label": "d2", 
                    "type": "frame", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "label": "c2", 
                    "args": {
                        "a": "a", 
                        "c": "'a'", 
                        "precision": 10
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "dsts": {
                        "o": "d3"
                    }, 
                    "type": "command", 
                    "commandId": "mcal"
                }, 
                {
                    "id": "d3", 
                    "label": "d3", 
                    "type": "frame", 
                    "dataSource": "csv"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-20 18:01:28", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('TEST')
        project.save()
        project = project.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('cache test 1', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フローを排他ロックしないとキャッシュが作成されない
        lock1 = lock_manager.lock(flow.uuid, self.USER1)

        # プレビューしてd1にキャッシュを作成する
        vis_args = {
          "d3": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 5
            }
          }
        }
        lasts = execute(FlowCommand(flow, lock1.uuid), {'vis':vis_args})
        results1 = convert_from_activity_vis(lasts)
        caches1 = convert_from_activity_cache(lasts)

        # フローの排他ロックを解除する
        lock_manager.unlock_target(flow.uuid)

        # visデータは1つ生成されているか
        self.assertEqual(len(results1), 1)
        # 正しいVisが得られるか
        self.assertEqual(len(results1['d3']), 5)
        # キャッシュが作成されること
        # FIXME: Cache CommandのPort(u)をActivity Commandに繋げてないためcacheを取得できない
        # self.assertEqual(len(caches1), 1, msg='キャッシュが作成できていません')

        # フローを排他ロックする
        lock2 = lock_manager.lock(flow.uuid, self.USER1)

        # 再びプレビューする
        flow = self.factory.data.find_by_uuid(flow.uuid)
        lasts = execute(FlowCommand(flow, lock2.uuid), {'vis':vis_args})
        results2 = convert_from_activity_vis(lasts)

        # キャッシュが参照されていれば値が一致する
        self.assertEqual(len(results2), 1)
        self.assertEqual(len(results2['d3']), 5)
        self.assertDictEqual(results2, results1, msg='キャッシュが参照できていません')

        # フローの排他ロックを解除する
        lock_manager.unlock_target(flow.uuid)

        # フローを削除する
        flow.delete()

    def test_exec_subflow_with_use_cache(self):
        """
        use_cache=Trueを指定して実行した場合
        サブフローにおいては、キャッシュの作成はしない・参照はする
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


    def test_exec_subflow_with_no_cache(self):
        """
        use_cache=Falseを指定して実行した場合
        サブフローにおいては、キャッシュの作成・参照はしない
        """


