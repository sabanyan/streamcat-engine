from streamcat.store import ProjectFolder, FlowData
from streamcat.store.lock import lock_manager
from streamcat.store.auth import NotAuthorizedException
from streamcat.store.tests.test_case_base import TestCaseBase
from streamcat.engine import execute, FlowCommand
from .test_main import convert_from_job_vis, convert_from_job_cache

class CacheTest(TestCaseBase):
    """
    フローのキャッシュ指定の検証
    """

    def test_cannot_save_cache_to_unauth_flow(self):
        """
        更新権限の無いメインフローを、
        use_cache=Trueでプレビューしてもキャッシュの作成はしないこと
        """
        flow_json = {
            "label": "rand", 
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
                        "f": "rand", 
                        "q": True, 
                        "t": 1
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mslide"
                },
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                },
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-22 11:35:53", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('沈黙が横たわる真昼に')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)
        
        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('主張する二つの鼓動', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フロー実行前のキャッシュファイル数を数えておく
        cache_folder = self.factory2.data.load_cache_folder()
        len_caches1 = len(cache_folder.find_children())

        # 作成を確定する
        self.factory2.end()

        # USER3は、更新権限の無いフローをプレビューしてもキャッシュは作成されないこと
        readonly_flow = self.factory3.data.find_by_uuid(flow.uuid)
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 32
            }
          }
        }
        lasts = execute(FlowCommand(readonly_flow), {'vis':vis_args,'use_cache':True})
        results1 = convert_from_job_vis(lasts)

        # 正しいVisが得られるか
        self.assertEqual(len(results1), 1)
        self.assertIn('d1', results1)

        # キャッシュフォルダにキャッシュが作成されていないこと
        cache_folder = self.factory3.data.load_cache_folder()
        len_caches2 = len(cache_folder.find_children())
        self.assertEqual(len_caches2, len_caches1, msg='キャッシュファイルが作成されました')

        # USER3は、同じフローを再度プレビューする
        lasts = execute(FlowCommand(readonly_flow), {'vis':vis_args,'use_cache':True})
        results2 = convert_from_job_vis(lasts)

        # キャッシュが作成されていないので、再度プレビューすると異なる値が得られること
        self.assertNotEqual(results2['d1'][0][1], results1['d1'][0][1])

        # フローを削除する
        flow.delete()

        # プロジェクトを削除する
        project.delete()

    def test_cannot_save_cache_to_locked_flow(self):
        """
        他ユーザにより排他ロック中のメインフローを、
        use_cache=Trueでプレビューしてもキャッシュの作成はしないこと
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
        project = root.create_project_folder('いつだって私の方が駆け足で')
        project.save()
        project = project.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('散らかった思考が火につけて', FlowData(flow_json))
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
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
        results1 = convert_from_job_vis(lasts)

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
        他ユーザにより排他ロック中のメインフローを、
        use_cache=Trueでプレビューすると、キャッシュの参照はできること
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
                    "id": "c2", 
                    "label": "c2", 
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
                    "id": "c3", 
                    "label": "c3", 
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
        project = root.create_project_folder('煌めいた')
        project.save()
        project = project.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('気づいていますか？', FlowData(flow_json))
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
        lasts = execute(FlowCommand(flow, lock1.uuid), {'vis':vis_args,'use_cache':True})
        results1 = convert_from_job_vis(lasts)
        caches1 = convert_from_job_cache(lasts)

        # フローの排他ロックを解除する
        lock_manager.unlock(lock1.uuid)

        # キャッシュの作成を確定する
        self.factory0.end()

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
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
        results2 = convert_from_job_vis(lasts)

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
        use_cache=Trueでプレビューしても、
        サブフロー内ではキャッシュの作成はしないこと
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
        project = root.create_project_folder('近くて遠い　二人名前はまだいらない')
        project.save()
        project = project.reload()

        # サブフローを作成する
        sub_flow = project.create_flow('響きよくある明日の前に', FlowData(sub_flow_json))
        sub_flow.uuid = 'a469bdd3-5236-4be3-a9f6-25ec9780f735'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('見つけあった今日が　愛おしいとか', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

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
        lasts = execute(FlowCommand(flow, lock1.uuid), {'vis':vis_args,'use_cache':True})
        results = convert_from_job_vis(lasts)

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
        use_cache=Trueでプレビューすると、
        サブフロー内でもキャッシュの参照はできること
        """
        sub_flow_json = {
            "label": "sub1", 
            "nodes": [
                {
                    "id": "d1", 
                    "type": "frame", 
                    "value" : [['customer','date','amount'],
                                ['A',20180101,5200],
                                ['B',20180101,800],
                                ['B',20180112,3500],
                                ['A',20180105,2000],
                                ['B',20180107,4000]],
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
                        "f": "amount", 
                        "s": "date", 
                        "t": "2", 
                        "exp": True, 
                        "precision": "10"
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mmvavg"
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
                    "id": "c1", 
                    "args": {
                        "a": "amount", 
                        "l": "10", 
                        "int": True, 
                        "max": "1000", 
                        "min": "10"
                    }, 
                    "srcs": {}, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mnewrand"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "a": "date", 
                        "c": "today() + randi(31, 0)", 
                        "precision": 10
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "dsts": {
                        "o": "d2"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mcal"
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
                    "srcs": {
                        "testData": "d2"
                    }, 
                    "dsts": {
                        "d3": "d3"
                    }, 
                    "type": "flow", 
                    "uuid": "171d415d-eae5-4249-9601-fc8f19e5fec6", 
                    "label": "f1"
                },
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-21 17:56:50", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('どうして　笑えない？')
        project.save()
        project = project.reload()

        # サブフローを作成する
        sub_flow = project.create_flow('あと何十回、何千時間一緒にいれば', FlowData(sub_flow_json))
        sub_flow.uuid = '171d415d-eae5-4249-9601-fc8f19e5fec6'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('cache test 3', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フロー実行前のキャッシュファイル数を数えておく
        cache_folder = self.factory0.data.load_cache_folder()
        len_caches1 = len(cache_folder.find_children())

        # サブフローをプレビューして、サブフローにキャッシュを作成する
        vis_args = {
          "d3": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 64
            }
          }
        }
        lasts = execute(FlowCommand(sub_flow), {'vis':vis_args,'use_cache':True})
        results = convert_from_job_vis(lasts)

        # 作成とキャッシュの作成を確定する
        self.factory0.end()

        # 正しいVisが得られるか
        expect = {'d3': [['A','20180101','5200'],
                        ['B','20180101','2266.666667'],
                        ['A','20180105','2088.888889'],
                        ['B','20180107','3362.962963'],
                        ['B','20180112','3454.320988'],
                        ['A','20180101','5200'], 
                        ['B','20180101','800'],
                        ['B','20180112','3500'],
                        ['A','20180105','2000'],
                        ['B','20180107','4000']]}
        self.assertEqual(len(results), 1)
        self.assertIn('d3', results)
        self.assertDictEqual(results, expect)

        # キャッシュフォルダにキャッシュが作成されていること
        cache_folder = self.factory.data.load_cache_folder()
        len_caches2 = len(cache_folder.find_children())
        self.assertGreater(len_caches2, len_caches1, msg='キャッシュファイルが作成されませんでした')

        # メインフローをプレビューする
        vis_args = {
          "d3": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 128
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
        results2 = convert_from_job_vis(lasts)

        # 正しいVisが得られるか
        self.assertEqual(len(results2), 1)
        self.assertIn('d3', results2)

        # もう一度、メインフローをプレビューする
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
        results3 = convert_from_job_vis(lasts)

        # 乱数をデータソースとするメインフローをプレビューしても
        # サブフロー内のキャッシュが参照されるので、同じ結果が得られること
        self.assertDictEqual(results3, results2)

        # フローを削除する
        flow.delete()
        sub_flow.delete()

        # プロジェクトを削除する
        project.delete()

    def test_exec_subflow_with_no_cache(self):
        """
        use_cache=Falseでプレビューすると、
        サブフロー内でもキャッシュの参照はしないこと
        """
        sub_flow_json = {
            "label": "sub", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "value" : [['customer','date','amount'],
                                ['A',20280101,3201],
                                ['B',20280101,8600],
                                ['B',20280112,33500],
                                ['A',20280105,2023],
                                ['B',20280107,4642]],
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "E": "2", 
                        "S": "0", 
                        "f": "date%d"
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mpadding"
                }, 
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv",
                    "makeCache": True
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "f": "amount:sum", 
                        "s": "date", 
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
                    "commandId": "maccum"
                },
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
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
                    }
                ]
            ], 
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-22 06:00:06", 
            "description": ""
        }
  
        flow_json = {
            "label": "main", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "value" : [['customer','date','amount'],
                                ['A',20180101,5200],
                                ['B',20180101,800],
                                ['B',20180112,3500],
                                ['A',20180105,2000],
                                ['B',20180107,4000]],
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
                    "id": "f1", 
                    "args": {}, 
                    "dsts": {
                        "d2": "d1"
                    }, 
                    "srcs": {
                        "testData": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "cc928f40-721b-4bb3-b4b0-e376e3ab9299", 
                    "label": "f1"
                }, 
                {
                    "id": "d2", 
                    "type": "frame", 
                    "label": "d2", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f2", 
                    "args": {}, 
                    "dsts": {
                        "d2": "d2"
                    }, 
                    "srcs": {
                        "testData": "d"
                    }, 
                    "type": "flow", 
                    "uuid": "cc928f40-721b-4bb3-b4b0-e376e3ab9299", 
                    "label": "f2"
                }, 
                {
                    "id": "d3", 
                    "type": "frame", 
                    "label": "d3", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f3", 
                    "args": {}, 
                    "dsts": {
                        "d2": "d3"
                    }, 
                    "srcs": {
                        "testData": "d6"
                    }, 
                    "type": "flow", 
                    "uuid": "cc928f40-721b-4bb3-b4b0-e376e3ab9299", 
                    "label": "f3"
                }, 
                {
                    "id": "d4", 
                    "type": "frame", 
                    "label": "d4", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "f4", 
                    "args": {}, 
                    "dsts": {
                        "d2": "d4"
                    }, 
                    "srcs": {
                        "testData": "d7"
                    }, 
                    "type": "flow", 
                    "uuid": "cc928f40-721b-4bb3-b4b0-e376e3ab9299", 
                    "label": "f4"
                }, 
                {
                    "id": "d5", 
                    "type": "frame", 
                    "label": "d5", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {}, 
                    "dsts": {
                        "o": "d5"
                    }, 
                    "srcs": {
                        "*0": "d4", 
                        "*1": "d3"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mcat"
                }, 
                {
                    "id": "d6", 
                    "type": "frame", 
                    "label": "d6", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c2", 
                    "args": {
                        "f": "sum:sum0"
                    }, 
                    "dsts": {
                        "o": "d6"
                    }, 
                    "srcs": {
                        "i": "d2"
                    }, 
                    "type": "command", 
                    "label": "c2", 
                    "commandId": "mfldname"
                }, 
                {
                    "id": "d7", 
                    "type": "frame", 
                    "label": "d7", 
                    "dataSource": "csv"
                    }, 
                    {
                    "id": "c3", 
                    "args": {
                        "f": "sum:sum0"
                    }, 
                    "dsts": {
                        "o": "d7"
                    }, 
                    "srcs": {
                        "i": "d1"
                    }, 
                    "type": "command", 
                    "label": "d7", 
                    "commandId": "mfldname"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-22 06:08:59", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory0.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('“いつも通り”と呼べるようになれるかな')
        project.save()
        project = project.reload()

        # サブフローを作成する
        sub_flow = project.create_flow('恐慌不振な感情は時に自分さえ裏切って', FlowData(sub_flow_json))
        sub_flow.uuid = 'cc928f40-721b-4bb3-b4b0-e376e3ab9299'
        sub_flow.save()
        sub_flow = sub_flow.reload()

        # フローを作成する
        flow = project.create_flow('cache test 4', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フロー実行前のキャッシュファイル数を数えておく
        cache_folder = self.factory0.data.load_cache_folder()
        len_caches1 = len(cache_folder.find_children())

        # サブフローをプレビューして、サブフローにキャッシュを作成する
        vis_args = {
          "d2": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 794
            }
          }
        }
        lasts = execute(FlowCommand(sub_flow), {'vis':vis_args,'use_cache':True})
        results1 = convert_from_job_vis(lasts)

        # 作成とキャッシュの作成を確定する
        self.factory0.end()

        # 正しいVisが得られるか
        expect = {'d2': [['A', '20280101', '3201', '3201'],
                        ['B', '20280101', '8600', '11801'],
                        ['B', '20280102', '8600', '20401'],
                        ['B', '20280103', '8600', '29001'],
                        ['B', '20280104', '8600', '37601'],
                        ['A', '20280105', '2023', '39624'],
                        ['A', '20280106', '2023', '41647'],
                        ['B', '20280107', '4642', '46289'],
                        ['B', '20280108', '4642', '50931'],
                        ['B', '20280109', '4642', '55573'],
                        ['B', '20280110', '4642', '60215'],
                        ['B', '20280111', '4642', '64857'],
                        ['B', '20280112', '33500', '98357']]}
        self.assertEqual(len(results1), 1)
        self.assertIn('d2', results1)
        self.assertDictEqual(results1, expect)

        # キャッシュフォルダにキャッシュが作成されていること
        cache_folder = self.factory.data.load_cache_folder()
        len_caches2 = len(cache_folder.find_children())
        self.assertGreater(len_caches2, len_caches1, msg='キャッシュファイルが作成されませんでした')

        # use_cache=Falseを指定して、メインフローをプレビューする
        vis_args = {
          "d5": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 128
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':False})
        results2 = convert_from_job_vis(lasts)

        # サブフローのキャッシュが参照されないこと
        expect = {'d5': [['A', '20180101', '5200', '5200', '5200'],
                        ['B', '20180101', '800', '6000', '6000'], 
                        ['B', '20180102', '800', '6800', '6800'], 
                        ['B', '20180103', '800', '7600', '7600'], 
                        ['B', '20180104', '800', '8400', '8400'],
                        ['A', '20180105', '2000', '10400', '10400'],
                        ['A', '20180106', '2000', '12400', '12400'], 
                        ['B', '20180107', '4000', '16400', '16400'], 
                        ['B', '20180108', '4000', '20400', '20400'], 
                        ['B', '20180109', '4000', '24400', '24400'], 
                        ['B', '20180110', '4000', '28400', '28400'], 
                        ['B', '20180111', '4000', '32400', '32400'], 
                        ['B', '20180112', '3500', '35900', '35900'], 
                        ['A', '20180101', '5200', '5200', '5200'],
                        ['B', '20180101', '800', '6000', '6000'], 
                        ['B', '20180102', '800', '6800', '6800'], 
                        ['B', '20180103', '800', '7600', '7600'], 
                        ['B', '20180104', '800', '8400', '8400'], 
                        ['A', '20180105', '2000', '10400', '10400'], 
                        ['A', '20180106', '2000', '12400', '12400'], 
                        ['B', '20180107', '4000', '16400', '16400'], 
                        ['B', '20180108', '4000', '20400', '20400'], 
                        ['B', '20180109', '4000', '24400', '24400'], 
                        ['B', '20180110', '4000', '28400', '28400'], 
                        ['B', '20180111', '4000', '32400', '32400'], 
                        ['B', '20180112', '3500', '35900', '35900']]}
        self.assertEqual(len(results2), 1)
        self.assertIn('d5', results2)
        self.assertDictEqual(results2, expect)

        # フローを削除する
        flow.delete()
        sub_flow.delete()

        # プロジェクトを削除する
        project.delete()

    def test_skip_unauth_cache(self):
        """
        キャッシュの参照権限が無い場合でも、キャッシュを無視してプレビューができること
        """
        flow_json = {
            "label": "rand", 
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
                        "f": "rand", 
                        "q": True, 
                        "t": 1
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "mslide"
                },
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                },
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-22 11:35:53", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('振りかざす純情じゃ　泣いてるみたいだ')
        project.save()
        project = project.reload()
        
        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('いつも通りの復習させて', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # フロー実行前のキャッシュファイル数を数えておく
        cache_folder = self.factory.data.load_cache_folder()
        len_caches1 = len(cache_folder.find_children())

        # プレビューしてd1にキャッシュを作成する
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 32
            }
          }
        }
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
        results1 = convert_from_job_vis(lasts)

        # 正しいVisが得られるか
        self.assertEqual(len(results1), 1)
        self.assertIn('d1', results1)

        # キャッシュフォルダにキャッシュが作成されていること
        cache_folder = self.factory.data.load_cache_folder()
        len_caches2 = len(cache_folder.find_children())
        self.assertGreater(len_caches2, len_caches1, msg='キャッシュファイルが作成できませんでした')

        # キャッシュフォルダの権限を削除して参照不可にする
        cache_folder = self.factory.data.load_cache_folder()
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.clear_authz(cache_folder.id)

        # 再びプレビューする
        flow = self.factory.data.find_by_uuid(flow.uuid)
        lasts = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
        results2 = convert_from_job_vis(lasts)

        # キャッシュが参照できないので、再度プレビューすると異なる値が得られること
        self.assertNotEqual(results2['d1'][0][1], results1['d1'][0][1])

        # フローを削除する
        flow.delete()

        # プロジェクトを削除する
        project.delete()

    def test_cannot_unauth_datasource(self):
        """
        データソースの参照権限が無い場合は、プレビューすると例外が送出されること
        """
        flow_json = {
            "label": "rand", 
            "nodes": [
                {
                    "id": "d", 
                    "type": "frame", 
                    "uuid": "30576973-0dc9-42e1-8fd6-aba699517043", 
                    "label": "testData", 
                    "dataSource": "csv"
                }, 
                {
                    "id": "c1", 
                    "args": {
                        "f": "amount,date", 
                        "pways": 32, 
                        "blocks": 10, 
                        "maxlines": 500000, 
                        "threadCnt": 8
                    }, 
                    "dsts": {
                        "o": "d1"
                    }, 
                    "srcs": {
                        "i": "d"
                    }, 
                    "type": "command", 
                    "label": "c1", 
                    "commandId": "msortf"
                },
                {
                    "id": "d1", 
                    "type": "frame", 
                    "label": "d1", 
                    "dataSource": "csv"
                }
            ], 
            "ports": [[],[]],
            "params": [], 
            "creator": "ユーザー管理者", 
            "createdAt": "2021-04-22 11:35:53", 
            "description": ""
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('お母にゃん')
        project.save()
        project = project.reload()

        # プロジェクトの下にフレームを作成する
        import io
        frame = project.create_frame('たびにゃん', io.BytesIO(b'date,amount\n20100101,2300'))
        frame.uuid = '30576973-0dc9-42e1-8fd6-aba699517043'
        frame.save()

        # フローを作成する
        flow = project.create_flow('あににゃん', FlowData(flow_json))
        flow.save()
        flow = flow.reload()

        # データソースファイルの権限を削除して参照不可にする
        everyone_role = self.factory.role.load_everyone_role()
        everyone_role.clear_authz(frame.id)

        # プレビューすると例外が送出されること
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 32
            }
          }
        }
        with self.assertRaises(NotAuthorizedException):
            job = execute(FlowCommand(flow), {'vis':vis_args,'use_cache':True})
            convert_from_job_vis(job)

        # フローを削除する
        flow.delete()

        # フレームを削除する
        everyone_role.init_authz(frame.id, read=False, write=True)
        frame.delete()

        # プロジェクトを削除する
        project.delete()
