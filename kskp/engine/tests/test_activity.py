from sqlalchemy.orm.exc import NoResultFound
from kskp.core.datum import Datum
from kskp.store import ProjectFolder, FlowData
from kskp.store.tests.test_case_base import TestCaseBase
from kskp.engine import execute, FlowCommand
from .test_main import convert_from_activity, convert_from_activity_vis

class ActivityTest(TestCaseBase):
    """
    アクティビティの検証
    """

    def setUp(self):
        import copy

        # 乱数をデータソースとするフロー
        self.flow_json0 = {
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

        # 二つの結果をライブラリに出力するフロー
        self.flow_json = copy.deepcopy(self.flow_json0)
        # データデストを付加する
        self.flow_json['nodes'].append(self.create_data_dst_node('d'))
        self.flow_json['nodes'].append(self.create_data_dst_node('d1'))

    def test_save_activity_by_execute(self):
        """
        フロー実行後にアクティビティが出力されること
        """
        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('上様・・お手向かい致しますぞ')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)
        
        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('もはやこれまで。切れ！切り捨てい！', FlowData(self.flow_json))
        flow.save()
        flow = flow.reload()

        # USER2は、フローを実行する
        readonly_flow = self.factory2.data.find_by_uuid(flow.uuid)
        outs = execute(FlowCommand(readonly_flow))
        activity = self._get_activity(outs)
        results1 = convert_from_activity(outs)

        # 正しい結果が得られるか
        self.assertEqual(len(results1), 2)
        self.assertIn('d',  results1)
        self.assertIn('d1', results1)

        # アクティビティフォルダにアクティビティが作成されていること
        activity_folder = self.factory2.data.load_activity_folder()
        activity_folder.find_child_by_uuid(activity.uuid)

        # アクティビティの保持する値を取得する
        activity_json = activity.to_json()

        # Datumのメタ情報が正しいこと
        self.assertIsNotNone(activity_json['uuid'])
        self.assertEqual(activity_json['type'], Datum.ACTIVITY_TYPE)
        self.assertEqual(activity_json['label'], flow.label)
        self.assertEqual(activity_json['folderPath'], '/ライブラリ/' + Datum.ACTIVITY_FOLDER_LABEL)
        self.assertEqual(activity_json['folderUuid'], Datum.ACTIVITY_FOLDER_UUID)
        self.assertIsNone(activity_json['prevFolderPath'])
        self.assertEqual(activity_json['creator'], self.USER2.name)
        self.assertIsNotNone(activity_json['createdAt'])
        # アクティビティの保持する値が正しいこと
        self.assertEqual(activity_json['flow_uuid'], flow.uuid)
        self.assertIsNotNone(activity_json['start_time'])
        self.assertIsNotNone(activity_json['end_time'])
        # 結果Datumの値が正しいこと
        self.assertEqual(len(activity_json['outs']), 2)
        self.assertEqual(activity_json['outs'][0]['id'], 'd')
        self.assertEqual(activity_json['outs'][0]['label'], 'd')
        self.assertIsNotNone(activity_json['outs'][0]['datum'])
        self.assertEqual(activity_json['outs'][1]['id'], 'd1')
        self.assertEqual(activity_json['outs'][1]['label'], 'd1')
        self.assertIsNotNone(activity_json['outs'][1]['datum'])
        # Point(d)からキャッシュが出力されるが、
        # Cache CommandのPort(u)をActivity Commandに繋げてないためcacheを取得できない
        self.assertEqual(len(activity_json['caches']), 0)
        # 例外は0件であること
        self.assertEqual(len(activity_json['exs']), 0)

        # プロジェクトをほかして、ゴミ箱を空にする
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

    def test_save_activity_if_error(self):
        """
        フロー実行で例外が発生してもアクティビティが出力されること
        """
        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('上さまを騙る不届き者！叩き切れ！')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)
        
        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('かようなところに上様が来られるはずがない！', FlowData(self.flow_json))
        flow.save()
        flow = flow.reload()

        # USER3は、フローを実行する
        # USER3は、プロジェクトの閲覧者メンバなので、実行結果の出力で例外が送出される
        readonly_flow = self.factory3.data.find_by_uuid(flow.uuid)
        outs = execute(FlowCommand(readonly_flow))
        activity = self._get_activity(outs)
        results1 = convert_from_activity(outs)

        # 正しい結果が得られるか
        self.assertEqual(len(results1), 2)
        self.assertIn('d',  results1)
        self.assertIn('d1', results1)

        # アクティビティフォルダにアクティビティが作成されていること
        activity_folder = self.factory3.data.load_activity_folder()
        activity_folder.find_child_by_uuid(activity.uuid)

        # アクティビティの保持する値を取得する
        activity_json = activity.to_json()

        # Datumのメタ情報が正しいこと
        self.assertIsNotNone(activity_json['uuid'])
        self.assertEqual(activity_json['type'], Datum.ACTIVITY_TYPE)
        self.assertEqual(activity_json['label'], flow.label)
        self.assertEqual(activity_json['folderPath'], '/ライブラリ/' + Datum.ACTIVITY_FOLDER_LABEL)
        self.assertEqual(activity_json['folderUuid'], Datum.ACTIVITY_FOLDER_UUID)
        self.assertIsNone(activity_json['prevFolderPath'])
        self.assertEqual(activity_json['creator'], self.USER3.name)
        self.assertIsNotNone(activity_json['createdAt'])
        # アクティビティの保持する値が正しいこと
        self.assertEqual(activity_json['flow_uuid'], flow.uuid)
        self.assertIsNotNone(activity_json['start_time'])
        self.assertIsNotNone(activity_json['end_time'])
        # 結果Datumは0件であること
        self.assertEqual(len(activity_json['outs']), 0)
        # キャッシュは0件であること
        self.assertEqual(len(activity_json['caches']), 0)
        # 例外の値は正しいこと
        self.assertEqual(len(activity_json['exs']), 2)
        self.assertEqual(activity_json['exs'][0]['id'], 'd')
        self.assertEqual(activity_json['exs'][0]['label'], 'd')
        self.assertIsNotNone(activity_json['exs'][0]['message'])
        self.assertEqual(activity_json['exs'][1]['id'], 'd1')
        self.assertEqual(activity_json['exs'][1]['label'], 'd1')
        self.assertIsNotNone(activity_json['exs'][1]['message'])

        # プロジェクトをほかして、ゴミ箱を空にする
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

    def test_save_activity_if_empty(self):
        """
        フロー実行の結果がない場合でもアクティビティが出力されること
        """
        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('もはやこれまで、お命頂戴つかまつる')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)
        
        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('お許し頂けぬのなら是非もない、この場で死んでもらいましょう', FlowData(self.flow_json0))
        flow.save()
        flow = flow.reload()

        # USER2は、フローを実行する
        readonly_flow = self.factory2.data.find_by_uuid(flow.uuid)
        outs = execute(FlowCommand(readonly_flow), {'use_cache':True})
        activity = self._get_activity(outs)
        results1 = convert_from_activity(outs)

        # 結果は出力されないこと
        self.assertEqual(len(results1), 0)

        # アクティビティフォルダにアクティビティが作成されていること
        activity_folder = self.factory2.data.load_activity_folder()
        activity_folder.find_child_by_uuid(activity.uuid)

        # アクティビティの保持する値を取得する
        activity_json = activity.to_json()

        # Datumのメタ情報が正しいこと
        self.assertIsNotNone(activity_json['uuid'])
        self.assertEqual(activity_json['type'], Datum.ACTIVITY_TYPE)
        self.assertEqual(activity_json['label'], flow.label)
        self.assertEqual(activity_json['folderPath'], '/ライブラリ/' + Datum.ACTIVITY_FOLDER_LABEL)
        self.assertEqual(activity_json['folderUuid'], Datum.ACTIVITY_FOLDER_UUID)
        self.assertIsNone(activity_json['prevFolderPath'])
        self.assertEqual(activity_json['creator'], self.USER2.name)
        self.assertIsNotNone(activity_json['createdAt'])
        # アクティビティの保持する値が正しいこと
        self.assertEqual(activity_json['flow_uuid'], flow.uuid)
        self.assertIsNotNone(activity_json['start_time'])
        self.assertIsNotNone(activity_json['end_time'])
        # 結果Datumは0件であること
        self.assertEqual(len(activity_json['outs']), 0)
        # Point(d)からキャッシュが出力されるが、
        # Cache CommandのPort(u)をActivity Commandに繋げてないためcacheを取得できない
        self.assertEqual(len(activity_json['caches']), 0)
        # 例外は0件であること
        self.assertEqual(len(activity_json['exs']), 0)

        # プロジェクトをほかして、ゴミ箱を空にする
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

    def test_no_activity_by_preview(self):
        """
        プレビュー実行ではアクティビティが出力されないこと
        """
        # ルートデータストアを取得する
        root = self.factory2.data.load_root()

        # プロジェクトを作成する
        project = root.create_project_folder('えーい、何が上様じゃ！出会え！出会え！！')
        project.save()
        project = project.reload()

        # メンバを設定する
        member1 = ProjectFolder.Member(self.USER2, ProjectFolder.OWNER_MEMBER_TYPE)
        member2 = ProjectFolder.Member(self.USER3, ProjectFolder.READER_MEMBER_TYPE)
        project.init_members([member1, member2], last_modified_at=project.modified_at)
        
        # 乱数をデータソースとするフローを作成する
        flow = project.create_flow('えーい、上様とて構わぬ！出会え！出会え！！', FlowData(self.flow_json))
        flow.save()
        flow = flow.reload()

        # USER2は、フローをプレビューする
        readonly_flow = self.factory2.data.find_by_uuid(flow.uuid)
        vis_args = {
          "d1": {
            "args": {
              "visualizer": "csvtohtmltable",
              "offset": 0,
              "limit": 32
            }
          }
        }
        outs = execute(FlowCommand(readonly_flow), {'vis':vis_args})
        activity = self._get_activity(outs)
        results1 = convert_from_activity_vis(outs)

        # 正しいVisが得られるか
        self.assertEqual(len(results1), 1)
        self.assertIn('d1', results1)

        # アクティビティフォルダにアクティビティが作成されないこと
        activity_folder = self.factory2.data.load_activity_folder()
        with self.assertRaises(NoResultFound):
            activity_folder.find_child_by_uuid(activity.uuid)

        # プロジェクトをほかして、ゴミ箱を空にする
        project.throw_away()
        self.factory.data.find_trashcan().trash_all()

    def _get_activity(self, outs:dict):
        """
        execute()の戻り値から
        pointのidとframeのDictに置き換える
        """
        from kskp.store import Activity
        # Activityを取得して返り値とする
        for point_id, datum in outs.items():
            if isinstance(datum, Activity):
                return datum
        return 
