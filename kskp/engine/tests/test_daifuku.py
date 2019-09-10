import os
import copy
import json
import uuid
import unittest
import nysol.mcmd as nm

from pathlib import Path

from kskp.engine import execute, FlowJsonLink, FlowUuidLink
from kskp.store import Library, FLOW_PATH, Frame, Command, Port, Datum, STORE_DIR

class DaifukuLoaderTestCase(unittest.TestCase):
    # mコマンド１つのフロー
    flow_data = {
      "label": "テストフロ",
      "params": [],
      "description": "",
      "ports": [
        [],
        []
      ],
      "nodes": [
        {
          "id": "i",
          "type": "frame",
          "label": "テストデータ",
          "value": [["顧客", "数量", "金額"],
              ["A", 1, 10],
              ["A", 2, 20],
              ["B", 1, 30],
              ["B", 3, 40],
              ["B", 1, 50]],
          "dataSource": "csv"
        },
        {
          "type": "frame",
          "id": "d1",
          "label": "d1",
          "uuid": None,
          "dataSource": "csv"
        },
        {
          "type": "command",
          "id": "c1",
          "label": "c1",
          "srcs": {
            "i": "i"
          },
          "dsts": {
            "o": "d1"
          },
          "args": {
            "f": "0,1",
            "x": True
          },
          "commandId": "mcut"
        }
      ]
    }

    # @unittest.skip
    def test_simple_flow_two_commands_execute(self):
        """
        mコマンド２個のフロー実行
        """
        add_cmd = {
          "type": "command",
          "id": "c2",
          "label": "c2",
          "srcs": {
            "i": "d1"
          },
          "dsts": {
            "o": "d2"
          },
          "args": {
            "f": "顧客",
            "v": "A"
          },
          "commandId": "mselstr"
        }

        add_datum = {
          "type": "frame",
          "id": "d2",
          "label": "d2",
          "uuid": None,
          "dataSource": "csv"
        }

        json_flow = copy.deepcopy(self.flow_data)
        json_flow['nodes'].append(add_cmd)
        json_flow['nodes'].append(add_datum)

        flow_link = FlowJsonLink(json.dumps(json_flow))
        lasts = execute(flow_link, {}, {})
        correct = {'d2': [['A', '1'], ['A', '2']]}

        # テスト
        # DBにframeデータが生成されているか
        self.assertIsNotNone(Library.load_frame(lasts['d2'].uuid))
        # 実ファイルが指定ディレクトリに存在するか
        result = get_frame_by_uuid(lasts['d2'].uuid)
        self.assertEqual(result, correct['d2'])

        # 後片付け
        Library.delete_frame(lasts['d2'].uuid)

# Helpler
def get_frame_by_uuid(uuid, header=True):
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
