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
    
    def test_cannot_save_cache_to_locked_flow(self):
        """
        use_cache=Trueを指定して実行した場合
        他ユーザにより排他ロック中のメインフローにおいては、キャッシュの作成はしないこと
        """
        flow_json = {
            "label": "メインフロー", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "value": [["顧客","数量","金額"],
                              ["x", 1, 10],
                              ["x", 2, 20],
                              ["y", 1, 30],
                              ["y", 3, 40],
                              ["z", 1, 50]],
                    "label": "testData", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "a": "rand", 
                        "l": "4"
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {}, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mnewrand"
                },
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "makeCache": True, 
                    "dataSource": "csv"
                },
                {
                    "id": "c2", 
                    "args": {
                        "bufcount": "10"
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
                    "srcs": {
                        "i": "d", 
                        "m": "d1"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mproduct"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c3", 
                    "args": {
                        "c": "[,0.5)", 
                        "f": "rand", 
                        "bufcount": 10
                    }, 
                    "dsts": {
                        "o": "d3", 
                        "u": "d4"
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "type": "command", 
                    "label": "c3", 
                    "commandId": "mselnum"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d4", 
                    "type": "frame", 
                    "label": "d4", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-21 10:33:12", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('TEST')
        project.save()
        project = project.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('cache test 0', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フロー実行前のキャッシュファイル数を数えておく
        cache_folder = self.factory0.data.load_cache_folder()
        len_caches1 = len(cache_folder.find_children())

        # 他ユーザによるフローの排他ロック
        lock1 = lock_manager.lock(flow.uuid, self.USER1)

        # 排他ロックされたフローをプレビューしてもキャッシュは作成されないこと
        vis_args = {
          "d3": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 32
            }
          },
          "d4": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 32
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args})
        results1 = convert_from_activity_vis(lasts)

        # 正しいVisが得られるか
        self.assertEqual(len(results1), 2)
        self.assertIn('d3', results1)
        self.assertIn('d4', results1)

        # キャッシュフォルダにキャッシュが作成されていないこと
        cache_folder = self.factory.data.load_cache_folder()
        len_caches2 = len(cache_folder.find_children())
        self.assertEqual(len_caches2, len_caches1, msg='キャッシュファイルが作成されました')

        # フローの排他ロックを解除する
        lock_manager.unlock(lock1.uuid)

        # フローを削除する
        flow.delete()

        # プロジェクトを削除する
        project.delete()


    def test_load_cache_to_locked_flow(self):
        """
        use_cache=Trueを指定して実行した場合
        他ユーザにより排他ロック中のメインフローにおいては、キャッシュの参照はできること
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
        lock_manager.unlock(lock1.uuid)

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
        lasts = execute(FlowCommand(flow), {'vis':vis_args})
        results2 = convert_from_activity_vis(lasts)

        # キャッシュが参照されていれば値が一致する
        self.assertEqual(len(results2), 1)
        self.assertEqual(len(results2['d3']), 5)
        self.assertDictEqual(results2, results1, msg='キャッシュが参照できていません')

        # フローの排他ロックを解除する
        lock_manager.unlock(lock2.uuid)

        # フローを削除する
        flow.delete()

        # プロジェクトを削除する
        project.delete()


    def test_cannot_save_cache_to_subflow(self):
        """
        use_cache=Trueを指定して実行した場合
        サブフローにおいては、キャッシュの作成はしないこと
        """
        sub_flow_json = {
            "label": "sub", 
            "nodes": [
                {
                    "id": "c", 
                    "args": {
                        "a": "rand", 
                        "l": "10"
                    }, 
                    "dsts": {
                        "o": "d"
                    }, 
                    "srcs": {}, 
                    "type": "command", 
                    "label": "c", 
                    "commandId": "mnewrand"
                }, 
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "d", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "f": "*", 
                        "nfno": True, 
                        "bufcount": "10"
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
                    "commandId": "mdelnull"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "I": "1", 
                        "S": "1", 
                        "a": "seq", 
                        "e": "seq", 
                        "q": True
                    }, 
                    "dsts": {
                        "o": "d3"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mnumber"
                },
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "makeCache": True, 
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
                        "label": "d3", 
                        "nodeId": "d3"
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
            "createdAt": "2021-04-21 17:20:25", 
            "description": ""
        }

        flow_json = {
            "label": "main", 
            "nodes": [
                {
                    "id": "c", 
                    "args": {
                        "a": "rand", 
                        "l": "10"
                    }, 
                    "dsts": {
                        "o": "d"
                    }, 
                    "srcs": {}, 
                    "type": "command", 
                    "label": "c", 
                    "commandId": "mnewrand"
                }, 
                {
                    "id": "d", 
                    "type": "frame", 
                    "label": "d", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d2": "d2", 
                        "d3": "d1"
                    }, 
                    "srcs": {
                        "d": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "a469bdd3-5236-4be3-a9f6-25ec9780f735", 
                    "label": "f1"
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
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-21 17:28:13", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('TEST')
        project.save()
        project = project.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('cache test 2', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # サブフローを作成する
        sub_flow = project.create_flow('i am sub flow', FlowData(sub_flow_json))
        sub_flow.uuid = 'a469bdd3-5236-4be3-a9f6-25ec9780f735'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フロー実行前のキャッシュファイル数を数えておく
        cache_folder = self.factory0.data.load_cache_folder()
        len_caches1 = len(cache_folder.find_children())

        # フローを排他ロックしないとキャッシュが作成されない
        lock1 = lock_manager.lock(flow.uuid, self.USER1)

        # プレビューしてもサブフロー内でキャッシュは作成されないこと
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
              "limit": 1192
            }
          }
        }
        lasts = execute(FlowCommand(flow, lock1.uuid), {'vis':vis_args})
        results = convert_from_activity_vis(lasts)

        # 正しいVisが得られるか
        self.assertEqual(len(results), 2)
        self.assertIn('d1', results)
        self.assertIn('d2', results)

        # キャッシュフォルダにキャッシュが作成されていないこと
        cache_folder = self.factory.data.load_cache_folder()
        len_caches2 = len(cache_folder.find_children())
        self.assertEqual(len_caches2, len_caches1, msg='キャッシュファイルが作成されました')

        # フローの排他ロックを解除する
        lock_manager.unlock(lock1.uuid)

        # フローを削除する
        flow.delete()
        sub_flow.delete()

        # プロジェクトを削除する
        project.delete()

    def test_load_cache_to_subflow(self):
        """
        use_cache=Trueを指定して実行した場合
        サブフローにおいては、キャッシュの参照はできること
        """
        sub_flow_json = {
            "label": "sub1", 
            "nodes": [
                {
                    "id": "d1", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "s": "date", 
                        "type": "exp", 
                        "fatlist": [
                        {
                            "a": "avg", 
                            "f": "amount", 
                            "t": "2"
                        }
                        ], 
                        "precision": 10
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "multi_mvavg"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {}, 
                    "dsts": {
                        "o": "d3"
                    }, 
                    "srcs": {
                        "*0": "d2", 
                        "*1": "d4"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mcat"
                }, 
                {
                    "id": "d4", 
                    "type": "frame", 
                    "label": "d4", 
                    "makeCache": True, 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c3", 
                    "args": {
                        "a": "avg", 
                        "c": "${amount}", 
                        "precision": 10
                    }, 
                    "dsts": {
                        "o": "d4"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "type": "command", 
                    "label": "c3", 
                    "commandId": "mcal"
                }
            ], 
            "ports": [
                [
                    {
                        "type": "frame", 
                        "label": "testData", 
                        "nodeId": "d1"
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
            "createdAt": "2021-04-21 17:20:25", 
            "description": ""
        }

        flow_json =  {
            "label": "main1", 
            "nodes": [
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d3": "d1"
                    }, 
                    "srcs": {
                        "d1": "d3"
                    }, 
                    "type": "flow", 
                    "uuid": "171d415d-eae5-4249-9601-fc8f19e5fec6", 
                    "label": "f1"
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
                        "a": "amount", 
                        "l": "10", 
                        "int": True, 
                        "max": "1000", 
                        "min": "10"
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
                    "srcs": {}, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mnewrand"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "a": "date", 
                        "c": "today() + randi(31, 0)", 
                        "precision": 10
                    }, 
                    "dsts": {
                        "o": "d3"
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mcal"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-21 17:56:50", 
            "description": ""
        }


    def test_exec_subflow_with_no_cache(self):
        """
        use_cache=Falseを指定して実行した場合
        サブフローにおいては、キャッシュの作成・参照はしない
        """


