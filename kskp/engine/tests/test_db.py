import copy
import unittest
import pprint

from kskp.store import FlowData, DatabaseConn
from kskp.depo.std.commands.scmd.mcmd_error_info import MCMDError
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowCommand
from .test_main import convert_from_activity, convert_from_activity_exs
from .make_flow_json import create_flow_by_flow_id

class DbTest(TestCaseBase):

    flow_json0 = {
      "label": "test用",
      "creator": "開発用",
      "createdAt": "2019-10-28 15:06:35",
      "projectId": None,
      "description": "",
      "ports": [
        [],
        []
      ],
      "params": [],
      "nodes": [
        {
          "id": "f",
          "args": {},
          "dsts": {
            "d1": "d"
          },
          "srcs": {},
          "type": "flow",
          "uuid": "8cfbce33-f2f9-4f52-a97d-ce170f70f6e3",
          "label": "PostgreSQLデータソース",
        },
        {
          "id": "d",
          "type": "frame",
          "uuid": None,
          "label": "d",
          "makeCache": False,
          "dataSource": "csv",
          "cacheCreatedAt": None
        },
        {
          "id": "f1",
          "args": {},
          "dsts": {},
          "srcs": {
            "d1": "d"
          },
          "type": "flow",
          "uuid": "b3e980d4-8338-4e83-a238-dd4537148c43",
          "label": "PostgreSQLデータデスト1"
        }
      ]
    }

    flow_json = {
      "label": "test用",
      "creator": "開発用",
      "createdAt": "2019-10-28 15:06:35",
      "projectId": None,
      "description": "",
      "ports": [
        [],
        []
      ],
      "params": [],
      "nodes": [
        {
          "id": "f",
          "args": {},
          "dsts": {
            "d1": "d"
          },
          "srcs": {},
          "type": "flow",
          "uuid": "8cfbce33-f2f9-4f52-a97d-ce170f70f6e3",
          "error": {},
          "label": "PostgreSQLデータソース",
          "invalid": {},
          "srcsOrder": []
        },
        {
          "id": "d",
          "type": "frame",
          "uuid": None,
          "error": {},
          "label": "d",
          "invalid": {},
          "makeCache": False,
          "dataSource": "csv",
          "cacheCreatedAt": None
        },
        {
          "id": "f1",
          "args": {},
          "dsts": {},
          "srcs": {
            "d1": "d"
          },
          "type": "flow",
          "uuid": "b3e980d4-8338-4e83-a238-dd4537148c43",
          "error": {},
          "label": "PostgreSQLデータデスト1",
          "invalid": {},
          "srcsOrder": [
            "d1"
          ]
        },
        {
          "id": "f2",
          "args": {},
          "dsts": {},
          "srcs": {
            "d1": "d"
          },
          "type": "flow",
          "uuid": "b3e980d4-8338-4e83-a238-dd4537148c43",
          "error": {},
          "label": "PostgreSQLデータデスト2",
          "invalid": {},
          "srcsOrder": [
            "d1"
          ]
        }
      ]
    }

    # conn_json = {
    #   'dbms'     : "postgresql",
    #   'hostname' : "kskp.cr4gfi5zl5xm.ap-northeast-1.rds.amazonaws.com", 
    #   'port'     : 5432, 
    #   'database' : "kskp", 
    #   'user_id'  : "kskp", 
    #   'password' : r'J2-pH|%B'
    # }
    conn_json = {
      'dbms'     : "postgresql",
      'hostname' : "db", 
      'port'     : 5432, 
      'database' : "kskp", 
      'user_id'  : "kskp", 
      'password' : 'ZQZtVgL6G32Vy6p6WJtG3C3K84yuJ4zz'
    }
    database_conn = DatabaseConn(conn_json)

    # @unittest.skip
    def test_simple_flow(self):
        """
        1つのDBデータソースの出力を1つのDBデータデストに繋げて実行する
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # DBストアの作成
        db = root.create_database('postgresql', self.database_conn)
        db.uuid = 'c410cd16-2529-498d-8e7f-490ffa58dc95'
        db.save()

        # サブフロー(PostgreSQLデータソース)の作成
        postgre_src_uuid = '8cfbce33-f2f9-4f52-a97d-ce170f70f6e3'
        postgre_src = create_flow_by_flow_id(root,'postgre_src', postgre_src_uuid)

        # サブフロー(PostgreSQLデータデスト)の作成
        postgre_dst_uuid = 'b3e980d4-8338-4e83-a238-dd4537148c43'
        postgre_dst = create_flow_by_flow_id(root, 'postgre_dst', postgre_dst_uuid)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = root.create_flow(self.flow_json0['label'], FlowData(self.flow_json0))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        datasource_f1 = lasts['f1_d2']
        self.assertTrue(self.factory.data.exists(datasource_f1.uuid))

        # 後片付け
        postgre_src.delete()
        postgre_dst.delete()
        datasource_f1.delete()
        db.delete()

    # @unittest.skip
    def test_two_datadest(self):
        """
        1つのDBデータソースの出力を2つのDBデータデストに繋げて実行する
        TODO: 2つのDBデータソースの出力先テーブルは同じテーブル名なので、排他制御が必要になる
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # DBストアの作成
        db = root.create_database('postgresql', self.database_conn)
        db.uuid = 'c410cd16-2529-498d-8e7f-490ffa58dc95'
        db.save()

        # サブフロー(PostgreSQLデータソース)の作成
        postgre_src_uuid = '8cfbce33-f2f9-4f52-a97d-ce170f70f6e3'
        postgre_src = create_flow_by_flow_id(root, 'postgre_src', postgre_src_uuid)

        # サブフロー(PostgreSQLデータデスト)の作成
        postgre_dst_uuid = 'b3e980d4-8338-4e83-a238-dd4537148c43'
        postgre_dst = create_flow_by_flow_id(root, 'postgre_dst', postgre_dst_uuid)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = root.create_flow(self.flow_json['label'], FlowData(self.flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        datasource_f1 = lasts['f1_d2']
        datasource_f2 = lasts['f2_d2']
        self.assertTrue(self.factory.data.exists(datasource_f1.uuid))
        self.assertTrue(self.factory.data.exists(datasource_f2.uuid))

        # 後片付け
        postgre_src.delete()
        postgre_dst.delete()
        datasource_f1.delete()
        datasource_f2.delete()
        db.delete()

    def test_error(self):
        """
        DBデータソースに存在しないテーブル名を指定すると例外が送出されること
        """
        main_json = {
            "label": "test用",
            "creator": "開発用",
            "createdAt": "2019-10-28 15:06:35",
            "projectId": None,
            "description": "",
            "ports": [
              [],
              []
            ],
            "params": [],
            "nodes": [
              {
                "id": "f",
                "args": {},
                "dsts": {
                  "d1": "d"
                },
                "srcs": {},
                "type": "flow",
                "uuid": "42af44db-872a-408b-b5d6-ff082f5bb3e2",
                "label": "PostgreSQLデータソース",
              },
              {
                "id": "d",
                "type": "frame",
                "uuid": None,
                "label": "d",
                "makeCache": False,
                "dataSource": "csv",
                "cacheCreatedAt": None
              }
            ]
        }

        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # DBストアの作成
        db = root.create_database('postgresql', self.database_conn)
        db.uuid = 'c410cd16-2529-498d-8e7f-490ffa58dc95'
        db.save()

        # サブフロー(PostgreSQLデータソース)の作成
        postgre_err_src_uuid = '42af44db-872a-408b-b5d6-ff082f5bb3e2'
        postgre_err_src = create_flow_by_flow_id(root,'postgre_err_src', postgre_err_src_uuid)

        # フローを作成する
        flow = root.create_flow(self.flow_json['label'], FlowData(main_json))

        # プレビューする
        vis_args = {
          "d": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 20
            }
          }
        }
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {'vis':vis_args}, {})

        # 出力ポイントとこれに対応するframeデータを取得する
        results = convert_from_activity(lasts)
        # 1つの出力ポイントが返されること
        self.assertEqual(len(results), 1)
        self.assertIn('d', results)
        # frameデータは作成されていないこと
        self.assertIsNone(results['d'])

        # 出力ポイントとこれに対応する例外を取得する
        results = convert_from_activity_exs(lasts)
        # 1つの出力ポイントが返されること
        self.assertEqual(len(results), 1)
        self.assertIn('d', results)
        # 1つの出力ポイントから例外が出力されること
        self.assertEqual(len(results['d']), 2)
        self.assertIsInstance(results['d'][0], MCMDError)
        self.assertIsInstance(results['d'][1], MCMDError)

        # 後片付け
        postgre_err_src.delete()
        db.delete()
