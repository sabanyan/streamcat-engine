import unittest
import pprint
import shutil
from pathlib import Path

from kskp.core import Datum
from kskp.store import FlowData, RemoteFolderConn
from kskp.depo.std.commands.scmd.mcmd_error_info import MCMDError
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowCommand
from .test_main import convert_from_activity, convert_from_activity_exs
from .make_flow_json import create_flow_by_flow_id

class RemoteFolderTest(TestCaseBase):

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
          "uuid": "78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e",
          "label": "Windowsデータソース",
        },
        {
          "id": "d",
          "label": "(=^ェ^=)",
          "type": "frame",
          "uuid": None,
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
          "uuid": "8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5",
          "label": "Windowsデータデスト1"
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
          "uuid": "78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e",
          "error": {},
          "label": "Windowsデータソース",
          "invalid": {},
          "srcsOrder": []
        },
        {
          "id": "d",
          "label": "(=^x^=)",
          "type": "frame",
          "uuid": None,
          "error": {},
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
          "uuid": "8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5",
          "error": {},
          "label": "Windowsデータデスト1",
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
          "uuid": "8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5",
          "error": {},
          "label": "Windowsデータデスト2",
          "invalid": {},
          "srcsOrder": [
            "d1"
          ]
        }
      ]
    }

    conn_json = {
        'protocol' : 'smb',
        'hostname' : "18.178.64.116",
        'domain'   : "WORKGROUP",
        'directory': "share",
        'user_id'  : "samba",
        'password' : "kskanalytics"
    }
    remote_folder_conn = RemoteFolderConn(conn_json)

    # @unittest.skip
    def test_simple_flow(self):
        """
        1つのデータソースの出力を1つのデータデストに繋げて実行する
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # リモートフォルダストアの作成
        rfolder = root.create_remote_folder('windows', self.remote_folder_conn)
        rfolder.uuid = '8557c193-9bf9-4ce8-8dbb-d1d09864e4a8'
        rfolder.save()
        rfolder = rfolder.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = '../kskp-flow-engine/kskp/engine/tests/test_data/'
        shutil.copyfile(Path(MY_TESTDATA_DIR) / '漢字読み.csv', rfolder.path / 'testData.csv')

        # サブフロー(リモートフォルダデータソース)の作成
        windows_src_uuid = '78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e'
        windows_src = create_flow_by_flow_id(root,'windows_src', windows_src_uuid)

        # サブフロー(リモートフォルダデータデスト)の作成
        windows_dst_uuid = '8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5'
        windows_dst = create_flow_by_flow_id(root, 'windows_dst', windows_dst_uuid)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = root.create_flow(self.flow_json0['label'], FlowData(self.flow_json0))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(Datasource)を出力しませんでした')
        datasource_f1 = lasts['f1_d2']
        self.assertTrue(self.factory.data.exists(datasource_f1.uuid, type=Datum.FLOW_TYPE))
        self.assertTrue(datasource_f1.label.startswith('(=^ェ^=)'))

        # 後片付け
        windows_src.delete()
        windows_dst.delete()
        datasource_f1.delete()
        rfolder.delete()

    # @unittest.skip
    def test_two_datadest(self):
        """
        1つのデータソースの出力を2つのデータデストに繋げて実行する
        2つのデータソースの出力先は同じファイルなので、排他制御が必要になる
        """
        # ルートデータストアを取得する
        root = self.factory.data.load_root()

        # リモートフォルダストアの作成
        rfolder = root.create_remote_folder('windows', self.remote_folder_conn)
        rfolder.uuid = '8557c193-9bf9-4ce8-8dbb-d1d09864e4a8'
        rfolder.save()
        rfolder = rfolder.reload()

        # 入力CSVファイルを作成する
        MY_TESTDATA_DIR = '../kskp-flow-engine/kskp/engine/tests/test_data/'
        shutil.copyfile(Path(MY_TESTDATA_DIR) / '漢字読み.csv', rfolder.path / 'testData.csv')

        # サブフロー(リモートフォルダデータソース)の作成
        windows_src_uuid = '78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e'
        windows_src = create_flow_by_flow_id(root,'windows_src', windows_src_uuid)

        # サブフロー(リモートフォルダデータデスト)の作成
        windows_dst_uuid = '8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5'
        windows_dst = create_flow_by_flow_id(root, 'windows_dst', windows_dst_uuid)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = root.create_flow(self.flow_json['label'], FlowData(self.flow_json))
        flow_link = FlowCommand(flow)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f1_d2'], 'SaverCommandは結果(Datasource)を出力しませんでした')
        self.assertIsNotNone(lasts['f2_d2'], 'SaverCommandは結果(Datasource)を出力しませんでした')
        datasource_f1 = lasts['f1_d2']
        datasource_f2 = lasts['f2_d2']
        self.assertTrue(self.factory.data.exists(datasource_f1.uuid, type=Datum.FLOW_TYPE))
        self.assertTrue(self.factory.data.exists(datasource_f2.uuid, type=Datum.FLOW_TYPE))
        self.assertTrue(datasource_f1.label.startswith('(=^x^=)'))
        self.assertTrue(datasource_f1.label.startswith('(=^x^=)'))

        # 後片付け
        windows_src.delete()
        windows_dst.delete()
        datasource_f1.delete()
        datasource_f2.delete()
        rfolder.delete()

    def test_error(self):
        """
        リモートフォルダデータソースに存在しないファイル名を指定すると例外が送出されること
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
                "uuid": "f2bb010f-791e-4bf4-bd3c-666d0a0922c4",
                "label": "リモートフォルダデータソース",
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

        # リモートフォルダストアの作成
        rfolder = root.create_remote_folder('windows', self.remote_folder_conn)
        rfolder.uuid = '8557c193-9bf9-4ce8-8dbb-d1d09864e4a8'
        rfolder.save()
        rfolder = rfolder.reload()

        # サブフロー(リモートフォルダデータソース)の作成
        windows_err_src_uuid = 'f2bb010f-791e-4bf4-bd3c-666d0a0922c4'
        windows_err_src = create_flow_by_flow_id(root,'windows_err_src', windows_err_src_uuid)

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
        self.assertEqual(len(results['d']), 1)
        self.assertIsInstance(results['d'][0], MCMDError)

        # 後片付け
        windows_err_src.delete()
        rfolder.delete()
