import copy
import unittest
import pprint

from kskp.store import FlowData, RemoteFolderConn
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowJsonLink
from .test_main import convert_from_activity

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
          "uuid": "8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5",
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
          "uuid": "78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e",
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
          "uuid": "8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5",
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
          "uuid": "8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5",
          "error": {},
          "label": "PostgreSQLデータデスト2",
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

        # サブフロー(リモートフォルダデータソース)の作成
        windows_src_uuid = '78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e'
        windows_src = self.create_flow_by_flow_id(root,'windows_src', windows_src_uuid)

        # サブフロー(リモートフォルダデータデスト)の作成
        windows_dst_uuid = '8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5'
        windows_dst = self.create_flow_by_flow_id(root, 'windows_dst', windows_dst_uuid)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = root.create_flow(self.flow_json0['label'], FlowData(self.flow_json0))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 1)
        self.assertIsNotNone(lasts['f1'], 'SaverCommandは結果(Datasource)を出力しませんでした')
        datasource_f1 = lasts['f1']
        self.assertTrue(self.factory.data.exists(datasource_f1.uuid))

        # 後片付け
        windows_src.delete()
        windows_dst.delete()
        datasource_f1.delete()
        rfolder.delete()

    @unittest.skip
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

        # サブフロー(リモートフォルダデータソース)の作成
        windows_src_uuid = '78b407a7-e0a6-4fd6-b1ae-67a6a96dbb5e'
        windows_src = self.create_flow_by_flow_id(root,'windows_src', windows_src_uuid)

        # サブフロー(リモートフォルダデータデスト)の作成
        windows_dst_uuid = '8f8bf3eb-73aa-4400-b53d-5a2cbd325bc5'
        windows_dst = self.create_flow_by_flow_id(root, 'windows_dst', windows_dst_uuid)

        # runfuncの中で例外が送出されてもここまで上がってこない(T_T)
        flow = root.create_flow(self.flow_json['label'], FlowData(self.flow_json))
        flow_link = FlowJsonLink(flow, self.factory)
        lasts = execute(flow_link, {}, {})
        lasts = convert_from_activity(lasts)

        # ライブラリにデータソースが出力されていること
        self.assertEqual(len(lasts), 2)
        self.assertIsNotNone(lasts['f1'], 'SaverCommandは結果(Datasource)を出力しませんでした')
        self.assertIsNotNone(lasts['f2'], 'SaverCommandは結果(Datasource)を出力しませんでした')
        datasource_f1 = lasts['f1']
        datasource_f2 = lasts['f2']
        self.assertTrue(self.factory.data.exists(datasource_f1.uuid))
        self.assertTrue(self.factory.data.exists(datasource_f2.uuid))

        # 後片付け
        windows_src.delete()
        windows_dst.delete()
        datasource_f1.delete()
        datasource_f2.delete()
        rfolder.delete()

    def create_flow_by_flow_id(self, parent, flow_id, uuid):
        """
        指定されたidのフローを作成し、そのフローを返す
        """
        from .make_flow_json import test_json
        flow_json = test_json[flow_id]
        flow = parent.create_flow('test', FlowData(flow_json))
        flow.uuid = uuid
        flow.save()
        # save()によりreadable=Noneになるため再取得する
        return flow.reload()