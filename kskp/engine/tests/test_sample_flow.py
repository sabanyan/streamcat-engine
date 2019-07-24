import os
import json
import uuid
import unittest
import nysol.mcmd as nm

from pathlib import Path

from .make_flow_json import create_flow, delete_flow

from kskp.engine import execute, FlowJsonLink, FlowUuidLink
from kskp.store import Library, FLOW_PATH, Frame, Command, Port, Datum, STORE_DIR

root = Library.load_root()

class ExecuteSampleFlowTestCase(unittest.TestCase):
    """
    実際のフローを実行するテスト
    βにあったflowを実行する
    """
    import json

    TESTDATA_DIR = 'kskp/engine/tests/test_data/'

    @classmethod
    def tearDownClass(cls):
        """
        rootFolderを削除する
        """
        root.delete()

    # @unittest.skip
    def test_ni_flow_execute(self):
        """
        NI様のフローの実行テスト
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        import uuid
        # フローの作成
        main_uuid = str(uuid.uuid4())
        flow = create_flow('ni', main_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid)
        lasts = execute(flow_link, {}, {})
        uuid = [value for value in lasts.values()][0].uuid

        # テスト
        # DBにframeデータが生成されているか
        frame = Library.load_frame(uuid)
        self.assertIsNotNone(frame)
        self.assertTrue(Path(frame.path).exists())

        # 後片付け
        delete_flow(flow.uuid)
        Library.delete_frame(uuid)
        Library.load_frame(frame_uuid).remove_reference_only()

    # @unittest.skip
    def test_ni_flow_preview(self):
        """
        NI様のフローのプレビュー実行テスト
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        import uuid
        # フローの作成
        main_uuid = str(uuid.uuid4())
        flow = create_flow('ni', main_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid, ['new e9c09a48-901a-45d7-8bf3-91a323801277'])
        lasts = execute(flow_link, {}, {})
        uuid = [value for value in lasts.values()][0].uuid

        # テスト
        # DBにframeデータが生成されているか
        frame = Library.load_frame(uuid)
        self.assertIsNotNone(frame)
        self.assertTrue(Path(frame.path).exists())

        # 後片付け
        delete_flow(main_uuid)
        Library.delete_frame(uuid)
        Library.load_frame(frame_uuid).remove_reference_only()

    # @unittest.skip
    def test_ni_flow_execute_generate_four_caches(self):
        """
        NI様のフローの実行テスト
        とりあえず全部キャッシュを作成する
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        import uuid
        # フローの作成
        main_uuid = str(uuid.uuid4())
        flow = create_flow('ni', main_uuid)

        # キャッシュを設定する
        flow_json = json.loads(json.loads(flow.data)['flow'])
        for node in flow_json['nodes']:
            if node['type'] == 'frame':
                if node['uuid'] is None:
                    node['makeCache'] = True
                    node['cacheCreatedAt'] = ""
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid)
        lasts = execute(flow_link, {}, {})
        uuid = [value for value in lasts.values()][0].uuid

        # テスト
        # DBにframeデータが生成されているか
        frame = Library.load_frame(uuid)
        self.assertIsNotNone(frame)
        self.assertTrue(Path(frame.path).exists())

        cache_uuids = []
        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = json.loads(json.loads(flow.data)['flow'])
        cache_nodes = [node for node in result_json['nodes'] if node['type'] == 'frame' and node['uuid'] != frame_uuid]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            self.assertIsNotNone(node['cacheCreatedAt'])
            cache_uuids.append(node['uuid'])

        # 後片付け
        delete_flow(main_uuid)
        Library.delete_frame(uuid)
        Library.load_frame(frame_uuid).remove_reference_only()
        for uuid in cache_uuids:
            Library.delete_frame(uuid)

    # @unittest.skip
    def test_ryudo_flow_execute(self):
        """
        デモ用のフロー実行（粒度分布計）
        lastsは8個ある
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'ryudo_demo.csv')

        # フローの作成
        main_uuid = str(uuid.uuid4())
        sub1_uuid = 'bd87d38d-060e-4304-8610-63d93629a676'
        sub2_uuid = 'bd27d38d-060e-4304-8610-63d93629a676'
        flow = create_flow('ryudo', main_uuid)
        create_flow('ryudo_sub1', sub1_uuid)
        create_flow('ryudo_sub2', sub2_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        result_uuids = []
        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid)
        lasts = execute(flow_link, {}, {})
        for datum in lasts.values():
            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(datum.uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())
            result_uuids.append(datum.uuid)

        delete_flow(flow.uuid)
        self.assertTrue(delete_flow(sub1_uuid))
        self.assertTrue(delete_flow(sub2_uuid))
        Library.load_frame(frame_uuid).remove_reference_only()
        for result in result_uuids:
            Library.delete_frame(result)

    # @unittest.skip
    def test_ryudo_flow_cache(self):
        """
        デモ用のフロー実行（粒度分布計）
        キャッシュをとりあえず全部作成する
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'ryudo_demo.csv')

        # フローの作成
        main_uuid = str(uuid.uuid4())
        sub1_uuid = 'bd87d38d-060e-4304-8610-63d93629a676'
        sub2_uuid = 'bd27d38d-060e-4304-8610-63d93629a676'
        flow = create_flow('ryudo', main_uuid)
        create_flow('ryudo_sub1', sub1_uuid)
        create_flow('ryudo_sub2', sub2_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        # キャッシュを設定する
        for node in flow_json['nodes']:
            if node['type'] == 'frame':
                if node['uuid'] is None:
                    node['makeCache'] = True
                    node['cacheCreatedAt'] = ""
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        result_uuids = []
        cache_uuids = []
        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid)
        lasts = execute(flow_link, {}, {})
        for datum in lasts.values():
            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(datum.uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())
            # 後片付け
            result_uuids.append(datum.uuid)

        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = json.loads(json.loads(flow.data)['flow'])
        cache_nodes = [node for node in result_json['nodes'] if node['type'] == 'frame' and node['uuid'] != frame_uuid]
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            self.assertIsNotNone(node['cacheCreatedAt'])
            cache_uuids.append(node['uuid'])

        self.assertTrue(delete_flow(main_uuid))
        self.assertTrue(delete_flow(sub1_uuid))
        self.assertTrue(delete_flow(sub2_uuid))
        Library.load_frame(frame_uuid).remove_reference_only()
        for result in result_uuids:
            Library.delete_frame(result)
        for cache in cache_uuids:
            Library.delete_frame(cache)

    # @unittest.skip
    def test_ryudo_flow_preview(self):
        """
        デモ用のフロープレビュー（粒度分布計）
        プレビューデータは適当
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / 'ryudo_demo.csv')

        # フローの作成
        main_uuid = str(uuid.uuid4())
        sub1_uuid = 'bd87d38d-060e-4304-8610-63d93629a676'
        sub2_uuid = 'bd27d38d-060e-4304-8610-63d93629a676'
        flow = create_flow('ryudo', main_uuid)
        create_flow('ryudo_sub1', sub1_uuid)
        create_flow('ryudo_sub2', sub2_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid, ['d14'])
        lasts = execute(flow_link, {}, {})
        self.assertIsNotNone(lasts['d14'])
        frame = Library.load_frame(lasts['d14'].uuid)
        self.assertIsNotNone(frame)
        self.assertTrue(Path(frame.path).exists())

        delete_flow(flow.uuid)
        self.assertTrue(delete_flow(sub1_uuid))
        self.assertTrue(delete_flow(sub2_uuid))
        Library.load_frame(frame_uuid).remove_reference_only()
        Library.delete_frame(frame.uuid)

    # @unittest.skip
    def test_shindo_flow_execute(self):
        """
        デモ用のフロー実行（振動データ）
        lasts11個ある
        """
        # 単純な実行結果のテスト
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = str(uuid.uuid4())
        sub1_uuid = 'ad87d38d-060e-4304-8610-63d93629a676'
        sub2_uuid = 'bd87d38d-060e-4304-8610-63d93629a676'
        sub3_uuid = 'cd87d38d-060e-4304-8610-63d93629a676'
        sub4_uuid = 'dd87d38d-060e-4304-8610-63d93629a676'
        sub5_uuid = 'ed87d38d-060e-4304-8610-63d93629a676'
        sub6_uuid = 'fd87d38d-060e-4304-8610-63d93629a676'
        flow = create_flow('shindo', main_uuid)
        create_flow('shindo_sub1', sub1_uuid)
        create_flow('shindo_sub2', sub2_uuid)
        create_flow('shindo_sub3', sub3_uuid)
        create_flow('shindo_sub4', sub4_uuid)
        create_flow('shindo_sub5', sub5_uuid)
        create_flow('shindo_sub6', sub6_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        result_uuids = []
        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid)
        lasts = execute(flow_link, {}, {})
        for datum in lasts.values():
            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(datum.uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())
            # 後片付け
            result_uuids.append(datum.uuid)

        self.assertTrue(delete_flow(main_uuid))
        self.assertTrue(delete_flow(sub1_uuid))
        self.assertTrue(delete_flow(sub2_uuid))
        self.assertTrue(delete_flow(sub3_uuid))
        self.assertTrue(delete_flow(sub4_uuid))
        self.assertTrue(delete_flow(sub5_uuid))
        self.assertTrue(delete_flow(sub6_uuid))
        Library.load_frame(frame_uuid).remove_reference_only()
        for result in result_uuids:
            Library.delete_frame(result)

    # @unittest.skip
    def test_shindo_flow_cache(self):
        """
        デモ用のフロー実行（振動データ）
        キャッシュをとりあえず全部作成する
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = str(uuid.uuid4())
        sub1_uuid = 'ad87d38d-060e-4304-8610-63d93629a676'
        sub2_uuid = 'bd87d38d-060e-4304-8610-63d93629a676'
        sub3_uuid = 'cd87d38d-060e-4304-8610-63d93629a676'
        sub4_uuid = 'dd87d38d-060e-4304-8610-63d93629a676'
        sub5_uuid = 'ed87d38d-060e-4304-8610-63d93629a676'
        sub6_uuid = 'fd87d38d-060e-4304-8610-63d93629a676'
        flow = create_flow('shindo', main_uuid)
        create_flow('shindo_sub1', sub1_uuid)
        create_flow('shindo_sub2', sub2_uuid)
        create_flow('shindo_sub3', sub3_uuid)
        create_flow('shindo_sub4', sub4_uuid)
        create_flow('shindo_sub5', sub5_uuid)
        create_flow('shindo_sub6', sub6_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        # キャッシュを設定する
        for node in flow_json['nodes']:
            if node['type'] == 'frame':
                if node['uuid'] is None and not node['id'] == 'd1':
                    node['makeCache'] = True
                    node['cacheCreatedAt'] = ""
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        result_uuids = []
        cache_uuids = []
        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid)
        lasts = execute(flow_link, {}, {})
        for datum in lasts.values():
            # テスト
            # DBにframeデータが生成されているか
            frame = Library.load_frame(datum.uuid)
            self.assertIsNotNone(frame)
            self.assertTrue(Path(frame.path).exists())
            # 後片付け
            result_uuids.append(datum.uuid)

        # uuidが書き換わっているかのテスト
        flow = Library.load_flow(flow.uuid)
        result_json = json.loads(json.loads(flow.data)['flow'])
        cache_nodes = [node for node in result_json['nodes'] if node['type'] == 'frame' and node['uuid'] != frame_uuid and node['id'] != 'd1']
        for node in cache_nodes:
            self.assertIsNotNone(node['uuid'])
            self.assertIsNotNone(Library.load_frame(node['uuid']))
            self.assertIsNotNone(node['cacheCreatedAt'])
            cache_uuids.append(node['uuid'])

        self.assertTrue(delete_flow(main_uuid))
        self.assertTrue(delete_flow(sub1_uuid))
        self.assertTrue(delete_flow(sub2_uuid))
        self.assertTrue(delete_flow(sub3_uuid))
        self.assertTrue(delete_flow(sub4_uuid))
        self.assertTrue(delete_flow(sub5_uuid))
        self.assertTrue(delete_flow(sub6_uuid))
        Library.load_frame(frame_uuid).remove_reference_only()
        for result in result_uuids:
            Library.delete_frame(result)
        for cache in cache_uuids:
            Library.delete_frame(cache)

    # @unittest.skip
    def test_shindo_flow_preview(self):
        """
        デモ用のフロープレビュー（振動データ）
        プレビューデータは適当
        """
        flow_json = None
        # テストデータ登録
        frame_uuid = create_data(Path(self.TESTDATA_DIR) / '2500.csv')

        # フローの作成
        main_uuid = str(uuid.uuid4())
        sub1_uuid = 'ad87d38d-060e-4304-8610-63d93629a676'
        sub2_uuid = 'bd87d38d-060e-4304-8610-63d93629a676'
        sub3_uuid = 'cd87d38d-060e-4304-8610-63d93629a676'
        sub4_uuid = 'dd87d38d-060e-4304-8610-63d93629a676'
        sub5_uuid = 'ed87d38d-060e-4304-8610-63d93629a676'
        sub6_uuid = 'fd87d38d-060e-4304-8610-63d93629a676'
        flow = create_flow('shindo', main_uuid)
        create_flow('shindo_sub1', sub1_uuid)
        create_flow('shindo_sub2', sub2_uuid)
        create_flow('shindo_sub3', sub3_uuid)
        create_flow('shindo_sub4', sub4_uuid)
        create_flow('shindo_sub5', sub5_uuid)
        create_flow('shindo_sub6', sub6_uuid)

        flow_json = json.loads(json.loads(flow.data)['flow'])
        update_flow_node_uuid(flow_json, 'i', frame_uuid)

        # uuidを更新する
        from kskp.store import Flow
        Flow.update_data(flow.uuid, 'test', json.dumps(flow_json), '1')
        flow = Library.load_flow(flow.uuid)

        # 単純な実行結果のテスト
        flow_link = FlowUuidLink(flow.uuid, ['d12'])
        lasts = execute(flow_link, {}, {})
        self.assertIsNotNone(lasts['d12'])
        frame = Library.load_frame(lasts['d12'].uuid)
        self.assertIsNotNone(frame)
        self.assertTrue(Path(frame.path).exists())

        self.assertTrue(delete_flow(main_uuid))
        self.assertTrue(delete_flow(sub1_uuid))
        self.assertTrue(delete_flow(sub2_uuid))
        self.assertTrue(delete_flow(sub3_uuid))
        self.assertTrue(delete_flow(sub4_uuid))
        self.assertTrue(delete_flow(sub5_uuid))
        self.assertTrue(delete_flow(sub6_uuid))
        Library.load_frame(frame_uuid).remove_reference_only()
        Library.delete_frame(frame.uuid)


# Helpler
def get_frame_by_uuid(uuid, dir_path, header=True):
    """
    指定したuuidのframeを取得する
    """
    import csv
    result = []
    frame = Library.load_frame(uuid)
    with open(frame.path, 'r') as f:
        rows = csv.reader(f)
        if header:
            header = next(rows)
        for row in rows:
            result.append(row)

    return result

def write_data_to_json(path, data):
    """
    データをJSONとしてファイルに書き込むヘルパー
    """
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def create_data(file_path_obj, data=None):
    """
    テストデータ作成用
    frameのuuidが返る
    """
    if data is not None:
        nm.mread(i=data, o=file_path_obj.as_posix()).run()
    frame = Library.save_frame(root.uuid, str(uuid.uuid4()), file_path_obj)
    return frame.uuid

def update_flow_node_uuid(flow_json, node_id, uuid):
    """
    指定したflow_jsonのnode_idをuuidで更新する
    """
    for node in flow_json['nodes']:
        if node['id'] == node_id:
            node['uuid'] = uuid
            return True
    return False
