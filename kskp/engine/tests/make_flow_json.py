# テストに使うflowのjsonを作成する
# 実ファイルとしてテストデータを持っておくのは色々と面倒なことが起きるので。
# （別のテストの邪魔をしてそっちのテストが通らなかったり）
import json

def create_flow(flow_id, uuid):
    """
    指定されたidのフローを作成し、そのuuidを返す
    """
    flow_json = test_json[flow_id]
    flow_uuid = insert_flow_json(flow_json, uuid)
    return flow_uuid

def insert_flow_json(flow_json, uuid):
    """
    TODO: flowをdbに保存するようになったらそのように変更すること！
    """
    from pathlib import Path
    from kskp.store import FLOW_PATH

    flow_path = Path(FLOW_PATH) / (uuid + '.json')
    flow_path.write_text(json.dumps(flow_json, ensure_ascii=False, indent=2), encoding='utf-8')
    return uuid

def delete_flow(uuid):
    """
    TODO: flowをdbに保存するようになったらそのように変更すること！
    """
    from pathlib import Path
    from kskp.store import FLOW_PATH

    try:
        flow_path = Path(FLOW_PATH) / (uuid + '.json')
        flow_path.unlink()
    except Exception as e:
        print(e)
        return False
    return True

sub1 = {
    "description": "サブフロー",
    "label": "サブフロー",
    "params": [],
    "ports": [
        [{"label": "入力", "nodeId": "d1", "type": "int"}],
        [{"label": "出力", "nodeId": "d3", "type": "int"}]
    ],
    "nodes": [
        {
            "id": "d1",
            "type": "int",
            "uuid": None
        },
        {
            "id": "s1",
            "type": "command",
            "commandId": "square",
            "args": {},
            "srcs": { "i": "d1" },
            "dsts": { "o_sq": "d2" }
        },
        {
            "id": "d2",
            "type": "int",
            "uuid": None
        },
        {
            "id": "s2",
            "type": "command",
            "commandId": "square",
            "args": {},
            "srcs": { "i": "d2" },
            "dsts": { "o_sq": "d3" }
        },
        {
            "id": "d3",
            "type": "int",
            "uuid": None
        }
    ]
}

sub2 = {
    "description": "サブフロー（２つのoutput）",
    "label": "サブフロー",
    "params": [],
    "ports": [
        [{"label": "入力", "nodeId": "d1", "type": "frame"}],
        [{"label": "出力1", "nodeId": "d3", "type": "frame"}, {"label": "出力2", "nodeId": "d4", "type": "frame"}]
    ],
    "nodes": [
        {
            "id": "d1",
            "type": "frame",
            "uuid": None
        },
        {
            "id": "s1",
            "type": "command",
            "commandId": "mcut",
            "args": {
              "f": "0,1",
              "x": True
            },
            "srcs": { "i": "d1" },
            "dsts": { "o": "d2" }
        },
        {
            "id": "d2",
            "type": "int",
            "uuid": None
        },
        {
            "id": "s2",
            "type": "command",
            "commandId": "mselstr",
            "args": {
                "f": "顧客",
                "v": "A"
            },
            "srcs": { "i": "d2" },
            "dsts": { "o": "d3" , "u": "d4"}
        },
        {
            "id": "d3",
            "type": "frame",
            "uuid": None
        },
        {
            "id": "d4",
            "type": "frame",
            "uuid": None
        }
    ]
}

sub3 = {
    "description": "サブフロー（２つのoutput）",
    "label": "サブフロー",
    "params": [
      {
        "name": "sensor",
        "type": "string"
      },
      {
        "name": "customer",
        "type": "string"
      }
    ],
    "ports": [
        [{"label": "入力", "nodeId": "d1", "type": "frame"}],
        [{"label": "出力1", "nodeId": "d3", "type": "frame"}, {"label": "出力2", "nodeId": "d4", "type": "frame"}]
    ],
    "nodes": [
        {
            "id": "d1",
            "type": "frame",
            "uuid": None
        },
        {
            "id": "s1",
            "type": "command",
            "commandId": "mcut",
            "args": {
              "f": "@[sensor]",
              "x": True
            },
            "srcs": { "i": "d1" },
            "dsts": { "o": "d2" }
        },
        {
            "id": "d2",
            "type": "int",
            "uuid": None
        },
        {
            "id": "s2",
            "type": "command",
            "commandId": "mselstr",
            "args": {
                "f": "@[customer]",
                "v": "A"
            },
            "srcs": { "i": "d2" },
            "dsts": { "o": "d3" , "u": "d4"}
        },
        {
            "id": "d3",
            "type": "frame",
            "uuid": None
        },
        {
            "id": "d4",
            "type": "frame",
            "uuid": None
        }
    ]
}

sub4 = {
    "description": "サブフロー（２つのoutput）",
    "label": "サブフロー",
    "params": [
      {
        "name": "sensor1",
        "type": "string"
      },
      {
        "name": "sensor2",
        "type": "string"
      },
      {
        "name": "customer",
        "type": "string"
      }
    ],
    "ports": [
        [{"label": "入力", "nodeId": "d1", "type": "frame"}],
        [{"label": "出力1", "nodeId": "d3", "type": "frame"}, {"label": "出力2", "nodeId": "d4", "type": "frame"}]
    ],
    "nodes": [
        {
            "id": "d1",
            "type": "frame",
            "uuid": None
        },
        {
            "id": "s1",
            "type": "command",
            "commandId": "mcut",
            "args": {
              "f": "@[sensor1],@[sensor2]"
            },
            "srcs": { "i": "d1" },
            "dsts": { "o": "d2" }
        },
        {
            "id": "d2",
            "type": "int",
            "uuid": None
        },
        {
            "id": "s2",
            "type": "command",
            "commandId": "mselstr",
            "args": {
                "f": "@[customer]",
                "v": "A"
            },
            "srcs": { "i": "d2" },
            "dsts": { "o": "d3" , "u": "d4"}
        },
        {
            "id": "d3",
            "type": "frame",
            "uuid": None
        },
        {
            "id": "d4",
            "type": "frame",
            "uuid": None
        }
    ]
}

ni = {
  "projectId": 1,
  "description": "",
  "label": "日本NI様サンプル（改良）2万5千",
  "ports": [
    [],
    []
  ],
  "params": [],
  "creator": "開発用",
  "createdAt": "2018-08-29T03:51:13+09:00",
  "nodes": [
    {
      "position": {
        "x": 351,
        "y": 119
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "i",
      "type": "frame",
      "label": "i",
      "uuid": "2500",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 99,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 425ccf22-a270-46a9-bac3-46012714f308",
      "type": "frame",
      "label": "new 425ccf22-a270-46a9-bac3-46012714f308",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 99,
        "y": 365
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 5fefe394-5817-4e04-9aa7-5b764f7840a7",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "i"
      },
      "dsts": {
        "o": "new 425ccf22-a270-46a9-bac3-46012714f308"
      },
      "args": {
        "f": "0,1,2,3,4",
        "x": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 225,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 44433744-4496-488a-80c0-809d0440b41b",
      "type": "frame",
      "label": "new 44433744-4496-488a-80c0-809d0440b41b",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 225,
        "y": 365
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 5bcff599-6e7f-4f96-b9b7-560b55ea9dcd",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "i"
      },
      "dsts": {
        "o": "new 44433744-4496-488a-80c0-809d0440b41b"
      },
      "args": {
        "f": "0,5,6,7,8",
        "x": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 603,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new a959daef-e8e3-4c2f-96e0-8f51faf58a91",
      "type": "frame",
      "label": "new a959daef-e8e3-4c2f-96e0-8f51faf58a91",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 603,
        "y": 365
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 4b4c1319-b5d3-486c-a081-2d3a8f3b45c3",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "i"
      },
      "dsts": {
        "o": "new a959daef-e8e3-4c2f-96e0-8f51faf58a91"
      },
      "args": {
        "f": "0,9-12",
        "x": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 351,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new df167b23-7e56-40db-b058-f23a7c801a31",
      "type": "frame",
      "label": "new df167b23-7e56-40db-b058-f23a7c801a31",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 365
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new b1155ec8-3a4b-4102-89ef-aa0d5fabebcc",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "i"
      },
      "dsts": {
        "o": "new df167b23-7e56-40db-b058-f23a7c801a31"
      },
      "args": {
        "f": "0,13-16",
        "x": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 477,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new a14c125f-4565-4ec2-a483-a130104b3392",
      "type": "frame",
      "label": "new a14c125f-4565-4ec2-a483-a130104b3392",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 477,
        "y": 365
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 2e017a08-a7e0-418e-87c0-e42ff3370591",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "i"
      },
      "dsts": {
        "o": "new a14c125f-4565-4ec2-a483-a130104b3392"
      },
      "args": {
        "f": "0,17-20",
        "x": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 99,
        "y": 611
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 1d6b725d-b455-4d2e-a9be-e6a0d7759dee",
      "type": "frame",
      "label": "new 1d6b725d-b455-4d2e-a9be-e6a0d7759dee",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 99,
        "y": 529
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 624f4ea5-4964-4ad2-be40-2b5fe079afdd",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new 425ccf22-a270-46a9-bac3-46012714f308"
      },
      "dsts": {
        "o": "new 1d6b725d-b455-4d2e-a9be-e6a0d7759dee"
      },
      "args": {
        "a": "状態",
        "v": "正常"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 225,
        "y": 611
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new e9c09a48-901a-45d7-8bf3-91a323801277",
      "type": "frame",
      "label": "new e9c09a48-901a-45d7-8bf3-91a323801277",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 225,
        "y": 529
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 4c19614f-5711-4e00-91cd-3f8c55631485",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new 44433744-4496-488a-80c0-809d0440b41b"
      },
      "dsts": {
        "o": "new e9c09a48-901a-45d7-8bf3-91a323801277"
      },
      "args": {
        "a": "状態",
        "v": "外輪損傷１"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 603,
        "y": 611
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 5d4d1730-ef78-4d47-a043-344141db3fdc",
      "type": "frame",
      "label": "new 5d4d1730-ef78-4d47-a043-344141db3fdc",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 603,
        "y": 529
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 57a0fb07-e737-427c-ab73-123f32c69d2f",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new a959daef-e8e3-4c2f-96e0-8f51faf58a91"
      },
      "dsts": {
        "o": "new 5d4d1730-ef78-4d47-a043-344141db3fdc"
      },
      "args": {
        "a": "状態",
        "v": "外輪損傷２"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 351,
        "y": 611
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 26cc0bd4-07a0-4bb6-b304-45e65c3f69ff",
      "type": "frame",
      "label": "new 26cc0bd4-07a0-4bb6-b304-45e65c3f69ff",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 529
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new d6713ff7-c457-456b-bbce-549d85f1459b",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new df167b23-7e56-40db-b058-f23a7c801a31"
      },
      "dsts": {
        "o": "new 26cc0bd4-07a0-4bb6-b304-45e65c3f69ff"
      },
      "args": {
        "a": "状態",
        "v": "不釣り合い"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 477,
        "y": 611
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new cbff05f1-f1d8-4275-9ae8-784a36f451b3",
      "type": "frame",
      "label": "new cbff05f1-f1d8-4275-9ae8-784a36f451b3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 477,
        "y": 529
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new e0cba99a-9f20-48a0-85fc-0817aed29ce4",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new a14c125f-4565-4ec2-a483-a130104b3392"
      },
      "dsts": {
        "o": "new cbff05f1-f1d8-4275-9ae8-784a36f451b3"
      },
      "args": {
        "a": "状態",
        "v": "不釣り合い＆軸受部ガタ"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 351,
        "y": 775
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 8d2bc61a-5ba6-4696-a034-48107f5d883d",
      "type": "frame",
      "label": "new 8d2bc61a-5ba6-4696-a034-48107f5d883d",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 693
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new f47c9768-1325-463e-abb0-149fc28aec0a",
      "type": "command",
      "label": "ファイル結合",
      "srcs": {
        "*1": "new 1d6b725d-b455-4d2e-a9be-e6a0d7759dee",
        "*2": "new e9c09a48-901a-45d7-8bf3-91a323801277",
        "*3": "new 26cc0bd4-07a0-4bb6-b304-45e65c3f69ff",
        "*4": "new cbff05f1-f1d8-4275-9ae8-784a36f451b3",
        "*5": "new 5d4d1730-ef78-4d47-a043-344141db3fdc"
      },
      "dsts": {
        "o": "new 8d2bc61a-5ba6-4696-a034-48107f5d883d"
      },
      "args": {},
      "commandId": "mcat"
    },
    {
      "position": {
        "x": 351,
        "y": 939
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 717a8d6f-4d42-4f59-80f4-56bc2532b808",
      "type": "frame",
      "label": "new 717a8d6f-4d42-4f59-80f4-56bc2532b808",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 857
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 2680b83f-0d27-4063-8bcd-88030e69742d",
      "type": "command",
      "label": "ソート",
      "srcs": {
        "i": "new 8d2bc61a-5ba6-4696-a034-48107f5d883d"
      },
      "dsts": {
        "o": "new 717a8d6f-4d42-4f59-80f4-56bc2532b808"
      },
      "args": {
        "f": "状態,Time"
      },
      "commandId": "msortf"
    },
    {
      "position": {
        "x": 288,
        "y": 1595
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 44c5e0ed-0269-4643-bfc1-d9a393db6490",
      "type": "frame",
      "label": "new 44c5e0ed-0269-4643-bfc1-d9a393db6490",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 288,
        "y": 1513
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 2bcb3f41-1c28-433e-a483-62a11dcf2b28",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new 717a8d6f-4d42-4f59-80f4-56bc2532b808"
      },
      "dsts": {
        "o": "new 44c5e0ed-0269-4643-bfc1-d9a393db6490"
      },
      "args": {
        "a": "DATA_SOURCE",
        "v": "51.2kHz"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 414,
        "y": 1103
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 7b5eeac2-bb7d-4f4a-9a70-0662c7a85590",
      "type": "frame",
      "label": "new 7b5eeac2-bb7d-4f4a-9a70-0662c7a85590",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 414,
        "y": 1021
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new b2ae8380-ba3c-4072-aa3b-cf92ab84c45d",
      "type": "command",
      "label": "連番",
      "srcs": {
        "i": "new 717a8d6f-4d42-4f59-80f4-56bc2532b808"
      },
      "dsts": {
        "o": "new 7b5eeac2-bb7d-4f4a-9a70-0662c7a85590"
      },
      "args": {
        "S": "1",
        "a": "TIME_NO",
        "s": "状態,Time"
      },
      "commandId": "mnumber"
    },
    {
      "position": {
        "x": 414,
        "y": 1267
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new d92ffb72-0055-44d6-a0f1-8f86c8565660",
      "type": "frame",
      "label": "new d92ffb72-0055-44d6-a0f1-8f86c8565660",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 414,
        "y": 1185
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 4a10cbd7-4c9e-48f5-a3ad-422deaf33e2f",
      "type": "command",
      "label": "行絞り込み",
      "srcs": {
        "i": "new 7b5eeac2-bb7d-4f4a-9a70-0662c7a85590"
      },
      "dsts": {
        "o": "new d92ffb72-0055-44d6-a0f1-8f86c8565660"
      },
      "args": {
        "c": "${TIME_NO}%2==1"
      },
      "commandId": "msel"
    },
    {
      "position": {
        "x": 414,
        "y": 1431
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 6cdf9512-4901-486b-9e85-98cdf9132442",
      "type": "frame",
      "label": "new 6cdf9512-4901-486b-9e85-98cdf9132442",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 414,
        "y": 1349
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 5e069a2a-790b-4ec5-a4d2-82bcea1cb3ec",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "new d92ffb72-0055-44d6-a0f1-8f86c8565660"
      },
      "dsts": {
        "o": "new 6cdf9512-4901-486b-9e85-98cdf9132442"
      },
      "args": {
        "f": "TIME_NO",
        "r": True,
        "nfni": False,
        "assert_diffSize": False,
        "assert_nullin": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": ""
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 351,
        "y": 1759
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new bda22fae-7eeb-4543-bbd7-2dd2c0c9b186",
      "type": "frame",
      "label": "new bda22fae-7eeb-4543-bbd7-2dd2c0c9b186",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 1677
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 02be9fa0-7033-4518-9b08-3e24d550faee",
      "type": "command",
      "label": "ファイル結合",
      "srcs": {
        "*1": "new 44c5e0ed-0269-4643-bfc1-d9a393db6490",
        "*2": "new c1be2aac-3ae1-4cfa-91f9-8912cc1c49df"
      },
      "dsts": {
        "o": "new bda22fae-7eeb-4543-bbd7-2dd2c0c9b186"
      },
      "args": {},
      "commandId": "mcat"
    },
    {
      "position": {
        "x": 351,
        "y": 1923
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 2940dd07-04ce-4f5f-8771-7397b5ee5c9e",
      "type": "frame",
      "label": "new 2940dd07-04ce-4f5f-8771-7397b5ee5c9e",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 1841
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 95e16aa5-8b26-4133-b667-a4e15dd65c7a",
      "type": "command",
      "label": "連番",
      "srcs": {
        "i": "new bda22fae-7eeb-4543-bbd7-2dd2c0c9b186"
      },
      "dsts": {
        "o": "new 2940dd07-04ce-4f5f-8771-7397b5ee5c9e"
      },
      "args": {
        "S": "1",
        "a": "TIME_NO",
        "k": "DATA_SOURCE,状態",
        "s": "DATA_SOURCE,状態,Time"
      },
      "commandId": "mnumber"
    },
    {
      "position": {
        "x": 351,
        "y": 2087
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 3e043eb7-6998-46a8-828c-b446abb1febc",
      "type": "frame",
      "label": "new 3e043eb7-6998-46a8-828c-b446abb1febc",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2005
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 619dee07-3baf-4b78-a23a-ba106aa76029",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new 2940dd07-04ce-4f5f-8771-7397b5ee5c9e"
      },
      "dsts": {
        "o": "new 3e043eb7-6998-46a8-828c-b446abb1febc"
      },
      "args": {
        "a": "TIME_INTERVAL",
        "c": "${Time} - #{Time}"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 2251
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 626dc350-e6ce-4597-a59f-b0c017a05a15",
      "type": "frame",
      "label": "new 626dc350-e6ce-4597-a59f-b0c017a05a15",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2169
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new eb84d71d-252f-4c34-b704-220056370822",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new 3e043eb7-6998-46a8-828c-b446abb1febc"
      },
      "dsts": {
        "o": "new 626dc350-e6ce-4597-a59f-b0c017a05a15"
      },
      "args": {
        "a": "時分割0.01秒",
        "c": "int(${Time} / 0.01)+1"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 2415
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 10667a6d-ee97-4c74-a400-ae7f91794d9c",
      "type": "frame",
      "label": "new 10667a6d-ee97-4c74-a400-ae7f91794d9c",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2333
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 6bf75890-d0fc-4f99-a682-2819b4a0adc9",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new 626dc350-e6ce-4597-a59f-b0c017a05a15"
      },
      "dsts": {
        "o": "new 10667a6d-ee97-4c74-a400-ae7f91794d9c"
      },
      "args": {
        "a": "時分割0.05秒",
        "c": "int(${Time} / 0.05)+1"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 2579
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 2e3912cc-3f84-430b-aa31-8ea51fb39788",
      "type": "frame",
      "label": "new 2e3912cc-3f84-430b-aa31-8ea51fb39788",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2497
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 3983e19e-65fe-447f-bb80-97b381dac534",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new 10667a6d-ee97-4c74-a400-ae7f91794d9c"
      },
      "dsts": {
        "o": "new 2e3912cc-3f84-430b-aa31-8ea51fb39788"
      },
      "args": {
        "a": "時分割0.1秒",
        "c": "int(${Time} / 0.1 )+1"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 2743
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 57c3838f-f0f4-4034-a7c3-410db1fbcc7a",
      "type": "frame",
      "label": "new 57c3838f-f0f4-4034-a7c3-410db1fbcc7a",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2661
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 55702b2b-de59-4c95-851e-f9185fb56d89",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new 2e3912cc-3f84-430b-aa31-8ea51fb39788"
      },
      "dsts": {
        "o": "new 57c3838f-f0f4-4034-a7c3-410db1fbcc7a"
      },
      "args": {
        "a": "時分割0.5秒",
        "c": "int(${Time} / 0.5 )+1"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 2907
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 9be170f4-f4f4-4af8-90a6-c319d982f78c",
      "type": "frame",
      "label": "new 9be170f4-f4f4-4af8-90a6-c319d982f78c",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2825
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 081a6404-aa72-4fb8-8728-e1b2dc91d8a2",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new 57c3838f-f0f4-4034-a7c3-410db1fbcc7a"
      },
      "dsts": {
        "o": "new 9be170f4-f4f4-4af8-90a6-c319d982f78c"
      },
      "args": {
        "a": "時分割1秒",
        "c": "int(${Time} / 1   )+1"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 3071
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 2c888c29-6338-4c5e-a72b-75c3f0efd351",
      "type": "frame",
      "label": "new 2c888c29-6338-4c5e-a72b-75c3f0efd351",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 2989
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new c4cce70d-1a46-4932-9071-274d7611ca7c",
      "type": "command",
      "label": "1変数の統計量の計算",
      "srcs": {
        "i": "new 9be170f4-f4f4-4af8-90a6-c319d982f78c"
      },
      "dsts": {
        "o": "new 2c888c29-6338-4c5e-a72b-75c3f0efd351"
      },
      "args": {
        "a": "SENSOR",
        "c": "count:Num,min:Min,max:Max,mean:Avg,sd:SD,range:Range,cv:CV",
        "f": "3H,3V,4H,4V",
        "k": "DATA_SOURCE,状態,時分割1秒"
      },
      "commandId": "msummary"
    },
    {
      "position": {
        "x": 414,
        "y": 1595
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new c1be2aac-3ae1-4cfa-91f9-8912cc1c49df",
      "type": "frame",
      "label": "new c1be2aac-3ae1-4cfa-91f9-8912cc1c49df",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 414,
        "y": 1513
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 472d1584-8c31-4be1-aa6a-2a18cdfae709",
      "type": "command",
      "label": "文字列追加",
      "srcs": {
        "i": "new 6cdf9512-4901-486b-9e85-98cdf9132442"
      },
      "dsts": {
        "o": "new c1be2aac-3ae1-4cfa-91f9-8912cc1c49df"
      },
      "args": {
        "a": "DATA_SOURCE",
        "v": "25.6kHz"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 351,
        "y": 3235
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new c70e20df-18a5-4301-b623-c3bb94574000",
      "type": "frame",
      "label": "new c70e20df-18a5-4301-b623-c3bb94574000",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 3153
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new dcc2e95b-daf1-48bc-9281-9292272b39a6",
      "type": "command",
      "label": "1対Nのクロス集計",
      "srcs": {
        "i": "new 2c888c29-6338-4c5e-a72b-75c3f0efd351"
      },
      "dsts": {
        "o": "new c70e20df-18a5-4301-b623-c3bb94574000"
      },
      "args": {
        "a": "変数,値",
        "f": "Num,Min,Max,Avg,SD,Range,CV",
        "k": "DATA_SOURCE,状態,時分割1秒,SENSOR",
        "s": "",
        "v": ""
      },
      "commandId": "m2cross"
    },
    {
      "position": {
        "x": 351,
        "y": 3399
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new b29520eb-65a1-4bca-8fa2-839e7842262c",
      "type": "frame",
      "label": "new b29520eb-65a1-4bca-8fa2-839e7842262c",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 3317
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 3ddbaf72-c4c2-4521-bda0-09cce7639cea",
      "type": "command",
      "label": "計算",
      "srcs": {
        "i": "new c70e20df-18a5-4301-b623-c3bb94574000"
      },
      "dsts": {
        "o": "new b29520eb-65a1-4bca-8fa2-839e7842262c"
      },
      "args": {
        "a": "変数名",
        "c": "cat(\"_\",$s{SENSOR},$s{変数})"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 351,
        "y": 3563
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new bddfbc39-07eb-41ca-9cae-5b257ef124d5",
      "type": "frame",
      "label": "new bddfbc39-07eb-41ca-9cae-5b257ef124d5",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 3481
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 99a8e70f-115e-4a8c-ae66-4f3a0a830500",
      "type": "command",
      "label": "クロス集計",
      "srcs": {
        "i": "new b29520eb-65a1-4bca-8fa2-839e7842262c"
      },
      "dsts": {
        "o": "new bddfbc39-07eb-41ca-9cae-5b257ef124d5"
      },
      "args": {
        "a": "",
        "f": "値",
        "k": "DATA_SOURCE,状態,時分割1秒",
        "s": "変数名",
        "v": ""
      },
      "commandId": "mcross"
    },
    {
      "position": {
        "x": 351,
        "y": 3727
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new 0e332202-efe7-414d-ab46-8bf56c005ea5",
      "type": "frame",
      "label": "new 0e332202-efe7-414d-ab46-8bf56c005ea5",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 351,
        "y": 3645
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "new ee68d450-6a42-4ac9-9236-7bde80a54874",
      "type": "command",
      "label": "列選択",
      "srcs": {
        "i": "new bddfbc39-07eb-41ca-9cae-5b257ef124d5"
      },
      "dsts": {
        "o": "new 0e332202-efe7-414d-ab46-8bf56c005ea5"
      },
      "args": {
        "f": "fld",
        "r": True,
        "nfni": False,
        "assert_diffSize": False,
        "assert_nullin": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": ""
      },
      "commandId": "mcut"
    }
  ]
}

ryudo = {
  "projectId": 12,
  "label": "デモ用フロー",
  "ports": [
    [],
    []
  ],
  "params": [],
  "description": "",
  "creator": "開発用",
  "createdAt": "2019-03-30 21:08:29",
  "nodes": [
    {
      "position": {
        "x": 281,
        "y": 237
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "compdata20190319.csv",
      "type": "frame",
      "label": "測定データ",
      "uuid": "ryudo_demo",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 530,
        "y": 192
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 434,
        "y": 190
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "csvチェック",
      "srcs": {
        "i": "compdata20190319.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "a": "",
        "diag": True,
        "r": False,
        "assert_nullout": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "q": False,
        "tmpPath": ""
      },
      "commandId": "mchkcsv"
    },
    {
      "position": {
        "x": 532,
        "y": 252
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "d2",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 433,
        "y": 249
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "項目確認",
      "srcs": {
        "i": "compdata20190319.csv"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "n": "2",
        "no": False,
        "-nfno": False
      },
      "commandId": "column_list"
    },
    {
      "position": {
        "x": 400,
        "y": 341
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "時刻正規化",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 279,
        "y": 339
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "撮像時間のフォーマット変換",
      "srcs": {
        "i": "compdata20190319.csv"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "c": "%Y-%m-%d %H:%M:%s",
        "f": "撮像時間",
        "A": False,
        "assert_diffSize": False,
        "assert_nullin": False,
        "assert_nullout": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": ""
      },
      "commandId": "mdformat"
    },
    {
      "position": {
        "x": 276,
        "y": 470
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d5",
      "type": "frame",
      "label": "d5",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 278,
        "y": 399
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c5",
      "type": "command",
      "label": "必要列選択",
      "srcs": {
        "i": "d4"
      },
      "dsts": {
        "o": "d5"
      },
      "args": {
        "f": "区切りNo,撮像単位No,撮像時間,粒No,直径,面積,周囲長,長径,短径",
        "r": False,
        "nfni": False,
        "assert_diffSize": False,
        "assert_nullin": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": ""
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 416,
        "y": 731
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d12",
      "type": "frame",
      "label": "d12",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 273,
        "y": 725
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c12",
      "type": "command",
      "label": "【Key付与】1分単位",
      "srcs": {
        "i": "d16"
      },
      "dsts": {
        "o": "d12"
      },
      "args": {
        "a": "撮像時間_min",
        "c": "uxt2t(floor(uxt($t{撮像時間}),60))",
        "assert_diffSize": False,
        "assert_nullout": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": "",
        "precision": ""
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 541,
        "y": 470
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d8",
      "type": "frame",
      "label": "d8",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 430,
        "y": 472
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c8",
      "type": "command",
      "label": "レコード数確認_撮像時間単位",
      "srcs": {
        "i": "d5"
      },
      "dsts": {
        "o": "d8"
      },
      "args": {
        "c": "count",
        "f": "撮像時間",
        "a": "",
        "k": "撮像時間",
        "n": False,
        "assert_diffSize": False,
        "assert_nullkey": False,
        "assert_nullin": False,
        "assert_nullout": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "q": False,
        "tmpPath": "",
        "precision": ""
      },
      "commandId": "msummary"
    },
    {
      "position": {
        "x": 811,
        "y": 1060
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d14",
      "type": "frame",
      "label": "d14",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 811,
        "y": 989
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c14",
      "type": "command",
      "label": "【key付与】5分単位集計key",
      "srcs": {
        "i": "d18"
      },
      "dsts": {
        "o": "d14"
      },
      "args": {
        "a": "撮像時間_5min",
        "c": "uxt2t(floor(uxt($t{撮像時間}),5*60))"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 276,
        "y": 866
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d18",
      "type": "frame",
      "label": "d18",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 276,
        "y": 791
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c18",
      "type": "command",
      "label": "【Key付与】1時間単位",
      "srcs": {
        "i": "d12"
      },
      "dsts": {
        "o": "d18"
      },
      "args": {
        "a": "撮像時間_hr",
        "c": "uxt2t(floor(uxt($t{撮像時間}),60*60))",
        "precision": ""
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 229,
        "y": 615.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n11",
      "type": "note",
      "label": "n11",
      "title": "集計キー付与",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 184,
        "y": 1197
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d20",
      "type": "frame",
      "label": "d20",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 106,
        "y": 1201
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c9",
      "type": "command",
      "label": "時刻指定選択",
      "srcs": {
        "i": "d7"
      },
      "dsts": {
        "o": "d20"
      },
      "args": {
        "c": "regexs($s{撮像時間},\"^[0-9]{8,8}[01][802]00{2,2}\")"
      },
      "commandId": "msel"
    },
    {
      "position": {
        "x": 107,
        "y": 1499
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d21",
      "type": "frame",
      "label": "【グラフ用データ】ヒストグラム",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 105,
        "y": 1269
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c13",
      "type": "command",
      "label": "必要列選択",
      "srcs": {
        "i": "d20"
      },
      "dsts": {
        "o": "d21"
      },
      "args": {
        "f": "撮像時間_min,直径"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 458,
        "y": 1204
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "【グラフ用データ】1分単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 456,
        "y": 1134
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f5",
      "type": "flow",
      "label": "1分単位集計",
      "srcs": {
        "ダミー.csv": "d18"
      },
      "dsts": {
        "d7": "d3"
      },
      "args": {
        "時系列集計key": "撮像時間_min"
      },
      "uuid": "ryudo_sub1_demo1"
    },
    {
      "position": {
        "x": 814,
        "y": 1205
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d6",
      "type": "frame",
      "label": "【グラフ用データ】5分単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 812,
        "y": 1134
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f1",
      "type": "flow",
      "label": "5分単位集計",
      "srcs": {
        "ダミー.csv": "d14"
      },
      "dsts": {
        "d7": "d6"
      },
      "args": {
        "時系列集計key": "撮像時間_5min"
      },
      "uuid": "ryudo_sub1_demo1"
    },
    {
      "position": {
        "x": 498,
        "y": 1567.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n3",
      "type": "note",
      "label": "n3",
      "title": "粒度分布推移（時系列グラフ）",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 186,
        "y": 1138
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d7",
      "type": "frame",
      "label": "d7",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 107,
        "y": 1138
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f2",
      "type": "flow",
      "label": "粒度特徴量追加",
      "srcs": {
        "ダミー.csv": "d18"
      },
      "dsts": {
        "d6": "d7"
      },
      "args": {
        "時系列集計key": "撮像時間_min"
      },
      "uuid": "ryudo_sub2_demo1"
    },
    {
      "position": {
        "x": 45,
        "y": 1570.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n4",
      "type": "note",
      "label": "n4",
      "title": "粒度分布（ヒストグラム）",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 734,
        "y": 588.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n2",
      "type": "note",
      "label": "n2",
      "title": "【特長】計算機能",
      "content": "数値演算\n　論理演算、比較演算、三角関数、乱数など\n\n統計量計算\n　構成比計算\n　基準化（標準偏差、範囲）\n　移動平均\n　ウインドウ関数\n　\n日付時刻演算\n　経過時間、曜日など\n　　\n文字列操作\n　条件マッチ\n　ワイルドカード\n　正規表現\n　文字列併合、切り出し\n\n参照指定\n　同行指定、前後行指定、起点行指定\n　全行指定（キー項目指定可能）"
    },
    {
      "position": {
        "x": 602,
        "y": 1206
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d9",
      "type": "frame",
      "label": "【グラフ用データ】1時間単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 601,
        "y": 1132
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f3",
      "type": "flow",
      "label": "1時間単位集計",
      "srcs": {
        "ダミー.csv": "d18"
      },
      "dsts": {
        "d7": "d9"
      },
      "args": {
        "時系列集計key": "撮像時間_hr"
      },
      "uuid": "ryudo_sub1_demo1"
    },
    {
      "position": {
        "x": 330.5,
        "y": 988.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n5",
      "type": "note",
      "label": "n5",
      "title": "適切な集約時間単位の検討",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 462,
        "y": 1502
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d10",
      "type": "frame",
      "label": "【グラフ用データ】1分単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 458,
        "y": 1275
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "必要列選択",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d10"
      },
      "args": {
        "f": "総体積,総粒子数",
        "r": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 602,
        "y": 1499
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d11",
      "type": "frame",
      "label": "【グラフ用データ】1時間単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 601,
        "y": 1274
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c6",
      "type": "command",
      "label": "必要列選択",
      "srcs": {
        "i": "d9"
      },
      "dsts": {
        "o": "d11"
      },
      "args": {
        "f": "総体積,総粒子数",
        "r": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 814,
        "y": 1502
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d13",
      "type": "frame",
      "label": "【グラフ用データ】5分単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 812,
        "y": 1274
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c7",
      "type": "command",
      "label": "必要列選択",
      "srcs": {
        "i": "d6"
      },
      "dsts": {
        "o": "d13"
      },
      "args": {
        "f": "総体積,総粒子数",
        "r": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 416,
        "y": 658
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d16",
      "type": "frame",
      "label": "d16",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 274,
        "y": 657
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c10",
      "type": "command",
      "label": "【Key付与】1秒単位",
      "srcs": {
        "i": "d5"
      },
      "dsts": {
        "o": "d16"
      },
      "args": {
        "a": "撮像時間_sec",
        "c": "uxt2t(floor(uxt($t{撮像時間}),1))",
        "precision": ""
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 325,
        "y": 1206
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d17",
      "type": "frame",
      "label": "【グラフ用データ】1秒単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 326,
        "y": 1136
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f6",
      "type": "flow",
      "label": "1秒単位集計",
      "srcs": {
        "ダミー.csv": "d18"
      },
      "dsts": {
        "d7": "d17"
      },
      "args": {
        "時系列集計key": "撮像時間_sec"
      },
      "uuid": "ryudo_sub1_demo1"
    },
    {
      "position": {
        "x": 327,
        "y": 1504
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d15",
      "type": "frame",
      "label": "【グラフ用データ】1秒単位",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 325,
        "y": 1281
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c11",
      "type": "command",
      "label": "必要列選択",
      "srcs": {
        "i": "d17"
      },
      "dsts": {
        "o": "d15"
      },
      "args": {
        "f": "総体積,総粒子数",
        "r": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 40.5,
        "y": 98.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n1",
      "type": "note",
      "label": "n1",
      "title": "【目的】特徴把握に適切な集約単位を知る",
      "content": "・「集団」の特徴を「時系列」で把握する\n・ノイズが大きいため測定1回単位（0.25秒単位）で見ても特徴はわからない。\n\n・集約期間を変えて可視化し、特徴を見る"
    },
    {
      "position": {
        "x": 54.5,
        "y": 208.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n6",
      "type": "note",
      "label": "n6",
      "title": "データの特徴",
      "content": "粒度分布計測定結果\n・1回の測定で複数の粒子の直径を測定\n　測定間隔：0.25秒、期間:　07:55~14:00\n\n・重要な特徴量の追加が必要\n　　体積分率（粒子体積／粒子体積合計）\n　　個数分率（粒子個数／粒子数合計）\n・体積分率、個数分率の計算には、集約単位ごとに体積、粒子それぞれの合計を求める必要がある。\n\n"
    }
  ]
}

ryudo_sub1 = {
  "projectId": 12,
  "label": "関数　特徴量追加＆GroupBy",
  "ports": [
    [
      {
        "label": "ダミー",
        "nodeId": "ダミー.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d7",
        "nodeId": "d7",
        "type": "frame"
      }
    ]
  ],
  "params": [
    {
      "name": "時系列集計key",
      "type": "string"
    }
  ],
  "description": "粒度分布計に対応した処理\n時系列集計keyをKeyとして特徴量を算出\n特徴量　体積分率、総体積、個数分率、総粒子数\n直径ラベル（Small,Medium,Large）を付与",
  "creator": "開発用",
  "createdAt": "2019-03-29 20:57:20",
  "nodes": [
    {
      "position": {
        "x": 660,
        "y": 126.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "ダミー.csv",
      "type": "frame",
      "label": "input",
      "uuid": "691b816a-cfb3-4a07-b1f7-6355db6d440a",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 798,
        "y": 554.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "付与：体積",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 668,
        "y": 553.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "c2",
      "srcs": {
        "i": "d9"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "a": "体積",
        "c": "4/3*pi()*power(${直径}/2,3)"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 669,
        "y": 674.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "付与：体積分率",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 667,
        "y": 611.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "c3",
      "srcs": {
        "i": "d2"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "f": "体積:体積分率",
        "k": "@[時系列集計key]"
      },
      "commandId": "mshare"
    },
    {
      "position": {
        "x": 400,
        "y": 571
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n1",
      "type": "note",
      "label": "n1",
      "title": "特徴量：粒子体積関係",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 674,
        "y": 1022.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d6",
      "type": "frame",
      "label": "付与：直径ラベル",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 674,
        "y": 951.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c6",
      "type": "command",
      "label": "c6",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d6"
      },
      "args": {
        "f": "直径:label_直径",
        "R": "MIN,30,50,MAX",
        "v": "Small,Medium,Large",
        "A": True
      },
      "commandId": "mchgnum"
    },
    {
      "position": {
        "x": 742,
        "y": 268.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d8",
      "type": "frame",
      "label": "d8",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 661,
        "y": 268.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c8",
      "type": "command",
      "label": "c8",
      "srcs": {
        "i": "ダミー.csv"
      },
      "dsts": {
        "o": "d8"
      },
      "args": {
        "v": "1",
        "a": "個数"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 664,
        "y": 397.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d9",
      "type": "frame",
      "label": "d9",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 663,
        "y": 327.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c9",
      "type": "command",
      "label": "c9",
      "srcs": {
        "i": "d8"
      },
      "dsts": {
        "o": "d9"
      },
      "args": {
        "f": "個数:個数分率",
        "k": "@[時系列集計key]"
      },
      "commandId": "mshare"
    },
    {
      "position": {
        "x": 676,
        "y": 1336.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 676,
        "y": 1280.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "c1",
      "srcs": {
        "i": "d6"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "k": "@[時系列集計key],label_直径",
        "f": "体積,体積分率,個数分率",
        "c": "count,sum"
      },
      "commandId": "groupby"
    },
    {
      "position": {
        "x": 418,
        "y": 283.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n2",
      "type": "note",
      "label": "n2",
      "title": "個数分率",
      "content": "GroupByで個数分率を出すために\n"
    },
    {
      "position": {
        "x": 742,
        "y": 1611.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "d4",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 678,
        "y": 1614.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "c4",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "f": "体積分率_count,個数分率_count",
        "r": True
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 678,
        "y": 1794.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d7",
      "type": "frame",
      "label": "d7",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 677,
        "y": 1672.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c7",
      "type": "command",
      "label": "c7",
      "srcs": {
        "i": "d4"
      },
      "dsts": {
        "o": "d7"
      },
      "args": {
        "f": "体積分率_sum:体積分率,体積_count:総粒子数,体積_sum:総体積,個数分率_sum:個数分率"
      },
      "commandId": "mfldname"
    }
  ]
}

ryudo_sub2 = {
  "projectId": 12,
  "label": "関数　特徴量追加",
  "ports": [
    [
      {
        "label": "ダミー",
        "nodeId": "ダミー.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "ダミー",
        "nodeId": "d6",
        "type": "frame"
      }
    ]
  ],
  "params": [
    {
      "name": "時系列集計key",
      "type": "string"
    }
  ],
  "description": "粒度分布計に対応した処理\n・特徴量\n　・体積分率、総体積\n　・個数分率、総粒子数\n\n・フロー変数（必須）\n　・時系列key",
  "creator": "開発用",
  "createdAt": "2019-03-30 19:52:51",
  "nodes": [
    {
      "position": {
        "x": 660,
        "y": 126.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "ダミー.csv",
      "type": "frame",
      "label": "input",
      "uuid": "691b816a-cfb3-4a07-b1f7-6355db6d440a",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 798,
        "y": 554.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "付与：体積",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 669,
        "y": 553.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "c2",
      "srcs": {
        "i": "d9"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "a": "体積",
        "c": "4/3*pi()*power(${直径}/2,3)"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 669,
        "y": 674.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "付与：体積分率",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 667,
        "y": 611.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "c3",
      "srcs": {
        "i": "d2"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "f": "体積:体積分率",
        "k": "@[時系列集計key]"
      },
      "commandId": "mshare"
    },
    {
      "position": {
        "x": 400,
        "y": 571
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n1",
      "type": "note",
      "label": "n1",
      "title": "特徴量：粒子体積関係",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 817,
        "y": 891.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d5",
      "type": "frame",
      "label": "付与：体積ラベル",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 672,
        "y": 894.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c5",
      "type": "command",
      "label": "c5",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d5"
      },
      "args": {
        "f": "体積:label_体積",
        "R": "MIN,300,3000,MAX",
        "v": "Small,Medium,Large",
        "A": True
      },
      "commandId": "mchgnum"
    },
    {
      "position": {
        "x": 674,
        "y": 1022.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d6",
      "type": "frame",
      "label": "付与：直径ラベル",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 674,
        "y": 951.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c6",
      "type": "command",
      "label": "c6",
      "srcs": {
        "i": "d5"
      },
      "dsts": {
        "o": "d6"
      },
      "args": {
        "f": "直径:label_直径",
        "R": "MIN,30,50,MAX",
        "v": "Small,Medium,Large",
        "A": True
      },
      "commandId": "mchgnum"
    },
    {
      "position": {
        "x": 742,
        "y": 268.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d8",
      "type": "frame",
      "label": "d8",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 661,
        "y": 268.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c8",
      "type": "command",
      "label": "c8",
      "srcs": {
        "i": "ダミー.csv"
      },
      "dsts": {
        "o": "d8"
      },
      "args": {
        "v": "1",
        "a": "個数"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 664,
        "y": 397.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d9",
      "type": "frame",
      "label": "d9",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 664,
        "y": 327.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c9",
      "type": "command",
      "label": "c9",
      "srcs": {
        "i": "d8"
      },
      "dsts": {
        "o": "d9"
      },
      "args": {
        "f": "個数:個数分率",
        "k": "@[時系列集計key]"
      },
      "commandId": "mshare"
    },
    {
      "position": {
        "x": 418,
        "y": 283.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n2",
      "type": "note",
      "label": "n2",
      "title": "個数分率",
      "content": "GroupByで個数分率を出すために\n"
    },
    {
      "position": {
        "x": 397,
        "y": 906.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "type": "note",
      "id": "n3",
      "label": "n3",
      "title": "スケールラベルを追加",
      "content": "新しいメモ"
    }
  ]
}

shindo = {
  "projectId": 13,
  "label": "振動データデモ",
  "ports": [
    [],
    []
  ],
  "params": [],
  "description": "●モータへ、4箇所 加速度計 設置\n●正常、故障モード4種類 を観測\n   25.6万件\n\n【課題設定 例】\n●5つの状態の 分類モデルを作成する\n●比較ケースを設定しデータセットを作成\n    目的1：観測間隔の適正化\n    目的2：診断時間の適正化\n",
  "creator": "開発用",
  "createdAt": "2019-03-30 17:10:43",
  "nodes": [
    {
      "position": {
        "x": 351,
        "y": 192
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "180127_1535_4sensor_5sec.csv",
      "type": "frame",
      "label": "4sensor_5sec.csv",
      "uuid": "2500",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 352.8333333333333,
        "y": 369
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "【取込】振動データ",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 352,
        "y": 254
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "CSV検査",
      "srcs": {
        "i": "180127_1535_4sensor_5sec.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "diag": False,
        "a": ""
      },
      "commandId": "mchkcsv"
    },
    {
      "position": {
        "x": 58.5,
        "y": 717
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n1",
      "type": "note",
      "label": "n1",
      "title": "【集約】データ形式を正規化",
      "content": "5つの状態（正常、異常モード）が、\n列方向へ並ぶ形式から、\n行方向へと変換"
    },
    {
      "position": {
        "x": 729.6666666666666,
        "y": 624.8333333333333
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "列数行数",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 567.1666666666666,
        "y": 622.6666666666666
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f1",
      "type": "flow",
      "label": "列数行数",
      "srcs": {
        "sample.csv": "d3"
      },
      "dsts": {
        "d3": "d2"
      },
      "args": {},
      "uuid": "shindo_sub1_demo1"
    },
    {
      "position": {
        "x": 352.8333333333333,
        "y": 559
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "d3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 144.83333333333331,
        "y": 560
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "行抽出",
      "srcs": {
        "i": "d4"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "c": "1 == 1",
        "x": False
      },
      "commandId": "msel"
    },
    {
      "position": {
        "x": 34,
        "y": 522
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n2",
      "type": "note",
      "label": "n2",
      "title": "【設定】対象データ限定",
      "content": "行抽出 の絞り込み条件\n\n■ 本番用（全件   25万件）\n     1  == 1\n\n■動作テスト用 （Top 指定件数）\n      line() < 100\n\n"
    },
    {
      "position": {
        "x": 352.8333333333333,
        "y": 495
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "d4",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 353.83333333333326,
        "y": 434
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "列名ユニーク化",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "d": "_"
      },
      "commandId": "column_unique_name"
    },
    {
      "position": {
        "x": 731,
        "y": 195
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d5",
      "type": "frame",
      "label": "検査結果",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 569,
        "y": 193
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "CSV検査",
      "srcs": {
        "i": "180127_1535_4sensor_5sec.csv"
      },
      "dsts": {
        "o": "d5"
      },
      "args": {
        "diag": True
      },
      "commandId": "mchkcsv"
    },
    {
      "position": {
        "x": 728.8333333333333,
        "y": 564
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d6",
      "type": "frame",
      "label": "列名リスト",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 566.8333333333333,
        "y": 561
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c5",
      "type": "command",
      "label": "列名リスト",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d6"
      },
      "args": {
        "n": "2",
        "no": True
      },
      "commandId": "column_list"
    },
    {
      "position": {
        "x": 352.8333333333333,
        "y": 909
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d7",
      "type": "frame",
      "label": "【集約】データ",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "2019-04-19 14:40:27",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 353.8333333333333,
        "y": 743
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f2",
      "type": "flow",
      "label": "列を行へ展開",
      "srcs": {
        "d.csv": "d3"
      },
      "dsts": {
        "d11": "d7"
      },
      "args": {},
      "uuid": "shindo_sub2_demo1"
    },
    {
      "position": {
        "x": 53,
        "y": 986.75
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n3",
      "type": "note",
      "label": "n3",
      "title": "【集約】観測間隔 ケース作成",
      "content": "元の観測データに対して、\n間引きによる 異なる観測データを作成し、\n行方向に連結する"
    },
    {
      "position": {
        "x": 354.8333333333333,
        "y": 1092
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d8",
      "type": "frame",
      "label": "元間隔",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 352.8333333333333,
        "y": 1027
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c6",
      "type": "command",
      "label": "列追加",
      "srcs": {
        "i": "d7"
      },
      "dsts": {
        "o": "d8"
      },
      "args": {
        "v": "51.2kHz",
        "a": "DATA_SOURCE"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 505.83333333333326,
        "y": 1089
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d9",
      "type": "frame",
      "label": "d9",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 504.83333333333326,
        "y": 1025
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f3",
      "type": "flow",
      "label": "【間引き】1/2",
      "srcs": {
        "d.csv": "d7"
      },
      "dsts": {
        "d4": "d9"
      },
      "args": {
        "num": "2",
        "name": "DATA_SOURCE",
        "value": "25.6kHz"
      },
      "uuid": "shindo_sub3_demo1"
    },
    {
      "position": {
        "x": 655.8333333333333,
        "y": 1095
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d10",
      "type": "frame",
      "label": "d10",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 656.8333333333333,
        "y": 1030
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f4",
      "type": "flow",
      "label": "【間引き】1/3",
      "srcs": {
        "d.csv": "d7"
      },
      "dsts": {
        "d4": "d10"
      },
      "args": {
        "num": "3",
        "name": "DATA_SOURCE",
        "value": "17.1kHz"
      },
      "uuid": "shindo_sub3_demo1"
    },
    {
      "position": {
        "x": 352.8333333333333,
        "y": 1262
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d11",
      "type": "frame",
      "label": "観測間隔別データ",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 352.83333333333326,
        "y": 1188
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c7",
      "type": "command",
      "label": "行の連結",
      "srcs": {
        "*1": "d8",
        "*2": "d9",
        "*3": "d10"
      },
      "dsts": {
        "o": "d11"
      },
      "args": {},
      "commandId": "mcat"
    },
    {
      "position": {
        "x": 59,
        "y": 1349.75
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n4",
      "type": "note",
      "label": "n4",
      "title": "【集約】診断時間ケース作成",
      "content": "■ ID列 の追加\n波形を 診断時間 の間隔ごとに、\nグループ分けするために、\n診断時間 間隔ごとに、連番を付与する\n\n\n"
    },
    {
      "position": {
        "x": 351.8333333333333,
        "y": 1454
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d12",
      "type": "frame",
      "label": "診断時間ID付与済データ",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "2019-04-19 14:40:27",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 350.8333333333333,
        "y": 1382
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f5",
      "type": "flow",
      "label": "診断時間ケース設定",
      "srcs": {
        "d.csv": "d11"
      },
      "dsts": {
        "d4": "d12"
      },
      "args": {},
      "uuid": "shindo_sub4_demo1"
    },
    {
      "position": {
        "x": 743.8333333333333,
        "y": 1498
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d13",
      "type": "frame",
      "label": "行数列数",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 584.8333333333333,
        "y": 1499
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f6",
      "type": "flow",
      "label": "行数列数確認",
      "srcs": {
        "sample.csv": "d12"
      },
      "dsts": {
        "d3": "d13"
      },
      "args": {},
      "uuid": "shindo_sub1_demo1"
    },
    {
      "position": {
        "x": 743.8333333333333,
        "y": 1441
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d14",
      "type": "frame",
      "label": "列名リスト",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 584.8333333333333,
        "y": 1439
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c8",
      "type": "command",
      "label": "列名リスト",
      "srcs": {
        "i": "d12"
      },
      "dsts": {
        "o": "d14"
      },
      "args": {
        "n": "2",
        "no": True
      },
      "commandId": "column_list"
    },
    {
      "position": {
        "x": 254,
        "y": 1892.5
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n5",
      "type": "note",
      "label": "n5",
      "title": "【統合】機械学習用データセット",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 30,
        "y": 1548.25
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n6",
      "type": "note",
      "label": "n6",
      "title": "【変形】特徴量の作成",
      "content": "観測間隔のケース設定      別、\n診断時間のケース設定      別、\n特徴量算出対象のセンサ  別、\n特徴量とする定量化方法  別 \nの値を計算する\n\n\n■ 指定可能な統計量\ncount          件数\nucount        種類数\nsum             合計\nmin              最小値\nmax             最大値\nmean           算術平均\nmedian        中央値\nmode           最頻値\n\nvar               分散（標本分散   1/n）\nuvar             分散（不偏分散   1/(n-1) ）\nsd                標準偏差\nusd              標準偏差（不偏推定値）\ndevsq          偏差平方和\ncv                変動係数\n\nrange           範囲\nqrange         四分位範囲\nqtile1            第1四分位点\nqtile3           第3四分位点\n\nskew            歪度\nuskew          歪度（不偏推定値）\nkurt              尖度\nukurt            尖度（不偏推定値）\n"
    },
    {
      "position": {
        "x": 727.8333333333333,
        "y": 466
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d15",
      "type": "frame",
      "label": "列数行数",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 567.8333333333333,
        "y": 467
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f7",
      "type": "flow",
      "label": "列数行数",
      "srcs": {
        "sample.csv": "d4"
      },
      "dsts": {
        "d3": "d15"
      },
      "args": {},
      "uuid": "shindo_sub1_demo1"
    },
    {
      "position": {
        "x": 348.8333333333333,
        "y": 1596
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d16",
      "type": "frame",
      "label": "d16",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 148.83333333333326,
        "y": 1593
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f8",
      "type": "flow",
      "label": "【列＆行追加】特徴量",
      "srcs": {
        "d.csv": "d12"
      },
      "dsts": {
        "d7": "d16"
      },
      "args": {
        "key_list": "DATA_SOURCE,状態",
        "sensor_list": "3H,3V,4H,4V",
        "feature_list": "count:件数,min:最小,max:最大,mean:平均,sd:標準偏差,range:値域,cv:変動係数"
      },
      "uuid": "shindo_sub5_demo1"
    },
    {
      "position": {
        "x": 345.8333333333333,
        "y": 1834
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d17",
      "type": "frame",
      "label": "分類学習用データ",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 348.8333333333333,
        "y": 1655
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c9",
      "type": "command",
      "label": "列順変更",
      "srcs": {
        "i": "d16"
      },
      "dsts": {
        "o": "d17"
      },
      "args": {
        "f": "DATA_SOURCE,状態,波形間隔,波形ID,*"
      },
      "commandId": "column_name"
    },
    {
      "position": {
        "x": 740.8333333333333,
        "y": 1801
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d18",
      "type": "frame",
      "label": "列名リスト",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 573.8333333333333,
        "y": 1801
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c10",
      "type": "command",
      "label": "列名リスト",
      "srcs": {
        "i": "d17"
      },
      "dsts": {
        "o": "d18"
      },
      "args": {
        "n": "2",
        "no": True
      },
      "commandId": "column_list"
    },
    {
      "position": {
        "x": 741.8333333333333,
        "y": 1859
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d19",
      "type": "frame",
      "label": "行数列数",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 574.8333333333333,
        "y": 1858
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f9",
      "type": "flow",
      "label": "行数列数確認",
      "srcs": {
        "sample.csv": "d17"
      },
      "dsts": {
        "d3": "d19"
      },
      "args": {},
      "uuid": "shindo_sub1_demo1"
    },
    {
      "position": {
        "x": 30,
        "y": 1999
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n7",
      "type": "note",
      "label": "n7",
      "title": "【学習】機械学習モデル",
      "content": "＜現在、機械学習機能は、封印＞"
    },
    {
      "position": {
        "x": 726.8333333333333,
        "y": 825
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d21",
      "type": "frame",
      "label": "行数列数",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 567.8333333333333,
        "y": 826
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f10",
      "type": "flow",
      "label": "行数列数",
      "srcs": {
        "sample.csv": "d7"
      },
      "dsts": {
        "d3": "d21"
      },
      "args": {},
      "uuid": "shindo_sub1_demo1"
    },
    {
      "position": {
        "x": 725.8333333333333,
        "y": 763
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d20",
      "type": "frame",
      "label": "列名リスト",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 565.8333333333333,
        "y": 761
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c11",
      "type": "command",
      "label": "列名リスト",
      "srcs": {
        "i": "d7"
      },
      "dsts": {
        "o": "d20"
      },
      "args": {
        "n": "2",
        "no": True
      },
      "commandId": "column_list"
    },
    {
      "position": {
        "x": 344.8333333333333,
        "y": 2116
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d23",
      "type": "frame",
      "label": "d23",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "2019-04-19 14:40:28",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 343.8333333333333,
        "y": 2029
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "f11",
      "type": "flow",
      "label": "機械学習",
      "srcs": {
        "d.csv": "d17"
      },
      "dsts": {
        "d1": "d23"
      },
      "args": {},
      "uuid": "shindo_sub6_demo1"
    },
    {
      "position": {
        "x": 40,
        "y": 184
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n8",
      "type": "note",
      "label": "n8",
      "title": "【取込】ロード",
      "content": "CSVフォーマット異常あるため、\n形式を修正する\n\n[異常なポイント]\n ● 列名に重複あり\n \n"
    }
  ]
}

shindo_sub1 = {
  "projectId": 13,
  "label": "【サブフロー】列数行数の確認",
  "ports": [
    [
      {
        "label": "sample",
        "nodeId": "sample.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d3",
        "nodeId": "d3",
        "type": "frame"
      }
    ]
  ],
  "params": [],
  "description": "",
  "creator": "開発用",
  "createdAt": "2019-03-24 23:28:05",
  "nodes": [
    {
      "position": {
        "x": 596,
        "y": 216
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "sample.csv",
      "type": "frame",
      "label": "sample.csv",
      "uuid": "fc5765a8-d778-4d50-bfac-7b267a635709",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 697,
        "y": 311
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 596,
        "y": 311
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "行数",
      "srcs": {
        "i": "sample.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "a": "行数",
        "k": "",
        "assert_diffSize": False,
        "assert_nullkey": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "q": False,
        "tmpPath": ""
      },
      "commandId": "mcount"
    },
    {
      "position": {
        "x": 695,
        "y": 400
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "d2",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 597,
        "y": 398
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "列数",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "a": "列数",
        "c": "fldsize() - 1",
        "assert_diffSize": False,
        "assert_nullout": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": "",
        "precision": ""
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 596,
        "y": 586
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "d3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 594,
        "y": 482
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "srcs": {
        "i": "d2"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "f": "列数,行数",
        "r": False,
        "nfni": False,
        "assert_diffSize": False,
        "assert_nullin": False,
        "nfn": False,
        "nfno": False,
        "x": False,
        "tmpPath": ""
      },
      "commandId": "mcut"
    }
  ]
}

shindo_sub2 = {
  "projectId": 13,
  "label": "【サブルーチン】列を行へ展開",
  "ports": [
    [
      {
        "label": "d",
        "nodeId": "d.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d11",
        "nodeId": "d11",
        "type": "frame"
      }
    ]
  ],
  "params": [],
  "description": "",
  "creator": "開発用",
  "createdAt": "2019-03-30 20:22:13",
  "nodes": [
    {
      "position": {
        "x": 367,
        "y": 119
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d.csv",
      "type": "frame",
      "label": "d.csv",
      "uuid": "eda5b6e7-576a-4573-aae6-e507f86ad8fe",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 99,
        "y": 283
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 99,
        "y": 201.71428571428572
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "状態1",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "f": "Time,3H_1,3V_1,4H_1,4V_1"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 233,
        "y": 283
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "d2",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 233,
        "y": 201
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "状態2",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "f": "Time,3H_2,3V_2,4H_2,4V_2"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 367,
        "y": 283
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "d3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 367,
        "y": 201
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "状態3",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "f": "Time,3H_3,3V_3,4H_3,4V_3"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 501,
        "y": 283
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "d4",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 501,
        "y": 201
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "状態4",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "f": "Time,3H_4,3V_4,4H_4,4V_4"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 99,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d5",
      "type": "frame",
      "label": "d5",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 49.833333333333314,
        "y": 369.1666666666667
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c5",
      "type": "command",
      "label": "列追加",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d5"
      },
      "args": {
        "v": "正常",
        "a": "状態"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 231.57142857142858,
        "y": 448.42857142857144
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d6",
      "type": "frame",
      "label": "d6",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 182.1666666666666,
        "y": 365
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c6",
      "type": "command",
      "label": "列追加",
      "srcs": {
        "i": "d2"
      },
      "dsts": {
        "o": "d6"
      },
      "args": {
        "v": "外輪損傷1",
        "a": "状態"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 367,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d7",
      "type": "frame",
      "label": "d7",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 316.1666666666668,
        "y": 368.3333333333333
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c7",
      "type": "command",
      "label": "列追加",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d7"
      },
      "args": {
        "v": "外輪損傷2",
        "a": "状態"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 501,
        "y": 447
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d8",
      "type": "frame",
      "label": "d8",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 453.5000000000001,
        "y": 367.49999999999994
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c8",
      "type": "command",
      "label": "列追加",
      "srcs": {
        "i": "d4"
      },
      "dsts": {
        "o": "d8"
      },
      "args": {
        "v": "不釣合い",
        "a": "状態"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 635,
        "y": 284.66666666666663
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d9",
      "type": "frame",
      "label": "d9",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 634.2857142857143,
        "y": 201
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c9",
      "type": "command",
      "label": "状態5",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d9"
      },
      "args": {
        "f": "Time,3H_5,3V_5,4H_5,4V_5"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 635.7142857142857,
        "y": 446.14285714285705
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d10",
      "type": "frame",
      "label": "d10",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 587.3809523809523,
        "y": 368.5476190476188
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c10",
      "type": "command",
      "label": "列追加",
      "srcs": {
        "i": "d9"
      },
      "dsts": {
        "o": "d10"
      },
      "args": {
        "v": "不釣合い＆軸受部ガタ",
        "a": "状態"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 365.7857142857141,
        "y": 813.7142857142859
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d11",
      "type": "frame",
      "label": "d11",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 366.14285714285705,
        "y": 728.3809523809533
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c11",
      "type": "command",
      "label": "行連結",
      "srcs": {
        "*1": "d12",
        "*2": "d13",
        "*3": "d14",
        "*4": "d15",
        "*5": "d16"
      },
      "dsts": {
        "o": "d11"
      },
      "args": {
        "x": False,
        "f": "Time,3H,3V,4H,4V,状態",
        "nfn": False
      },
      "commandId": "mcat"
    },
    {
      "position": {
        "x": 99,
        "y": 623
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d12",
      "type": "frame",
      "label": "d12",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 99,
        "y": 541
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c12",
      "type": "command",
      "label": "列名変更",
      "srcs": {
        "i": "d5"
      },
      "dsts": {
        "o": "d12"
      },
      "args": {
        "f": "",
        "n": "Time,3H,3V,4H,4V,状態"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 231.57142857142858,
        "y": 624.4285714285714
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d13",
      "type": "frame",
      "label": "d13",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 231.57142857142858,
        "y": 542.4285714285714
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c13",
      "type": "command",
      "label": "列名変更",
      "srcs": {
        "i": "d6"
      },
      "dsts": {
        "o": "d13"
      },
      "args": {
        "n": "Time,3H,3V,4H,4V,状態"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 367,
        "y": 623
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d14",
      "type": "frame",
      "label": "d14",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 367,
        "y": 541
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c14",
      "type": "command",
      "label": "列名変更",
      "srcs": {
        "i": "d7"
      },
      "dsts": {
        "o": "d14"
      },
      "args": {
        "n": "Time,3H,3V,4H,4V,状態"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 501,
        "y": 623
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d15",
      "type": "frame",
      "label": "d15",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 501,
        "y": 541
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c15",
      "type": "command",
      "label": "列名変更",
      "srcs": {
        "i": "d8"
      },
      "dsts": {
        "o": "d15"
      },
      "args": {
        "n": "Time,3H,3V,4H,4V,状態"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 635.7142857142857,
        "y": 622.1428571428571
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d16",
      "type": "frame",
      "label": "d16",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 636.5476190476192,
        "y": 542.6428571428571
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c16",
      "type": "command",
      "label": "列名変更",
      "srcs": {
        "i": "d10"
      },
      "dsts": {
        "o": "d16"
      },
      "args": {
        "n": "Time,3H,3V,4H,4V,状態"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 715.8333333333336,
        "y": 383.58333333333326
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "type": "note",
      "id": "n1",
      "label": "n1",
      "title": "【列追加】正常・異常モードの設定",
      "content": ""
    }
  ]
}

shindo_sub3 = {
  "projectId": 13,
  "label": "【関数】間引き",
  "ports": [
    [
      {
        "label": "d",
        "nodeId": "d.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d4",
        "nodeId": "d4",
        "type": "frame"
      }
    ]
  ],
  "params": [
    {
      "name": "num",
      "type": "string"
    },
    {
      "name": "name",
      "type": "string"
    },
    {
      "name": "value",
      "type": "string"
    }
  ],
  "description": "フロー変数\nnum   間引きをする間隔\n          num個につき1個を抽出\nname  追加する列名\nvalue   追加列にセットする値",
  "creator": "開発用",
  "createdAt": "2019-03-30 21:41:50",
  "nodes": [
    {
      "position": {
        "x": 475,
        "y": 192.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d.csv",
      "type": "frame",
      "label": "d.csv",
      "uuid": "63e84617-b659-41a2-a530-96c2e7ea0b4d",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 612,
        "y": 331.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 475,
        "y": 331.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "【列追加】連番",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "k": "状態",
        "s": "状態,Time",
        "S": "1",
        "a": "TIME_NO"
      },
      "commandId": "mnumber"
    },
    {
      "position": {
        "x": 612,
        "y": 393.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "d2",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 476,
        "y": 396.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "【列抽出】間引き",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "c": "${TIME_NO} % @[num] == 1"
      },
      "commandId": "msel"
    },
    {
      "position": {
        "x": 611,
        "y": 457.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "d3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 475,
        "y": 458.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "【列削除】",
      "srcs": {
        "i": "d2"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "r": True,
        "f": "TIME_NO"
      },
      "commandId": "mcut"
    },
    {
      "position": {
        "x": 476,
        "y": 641.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "d4",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 475,
        "y": 521.5
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "【列追加】間引き名",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "a": "@[name]",
        "v": "@[value]"
      },
      "commandId": "msetstr"
    }
  ]
}

shindo_sub4 = {
  "projectId": 13,
  "label": "【サブルーチン】区間化",
  "ports": [
    [
      {
        "label": "d",
        "nodeId": "d.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d2",
        "nodeId": "d2",
        "type": "frame"
      },
      {
        "label": "d4",
        "nodeId": "d4",
        "type": "frame"
      }
    ]
  ],
  "params": [],
  "description": "",
  "creator": "開発用",
  "createdAt": "2019-03-30 22:32:53",
  "nodes": [
    {
      "position": {
        "x": 342.50000000000006,
        "y": 330.1666666666667
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d.csv",
      "type": "frame",
      "label": "d.csv",
      "uuid": "4d990874-ed64-41f1-ad9a-d58bc65bc3dc",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 457.0000000000001,
        "y": 488.0000000000001
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d3",
      "type": "frame",
      "label": "d3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 345.0000000000001,
        "y": 485.0000000000001
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c3",
      "type": "command",
      "label": "【列追加】ケース：時分割0.01秒",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "c": "int(${Time} /0.01)+1",
        "a": "時分割0.01秒"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 457.0000000000001,
        "y": 625.0000000000001
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "d4",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 342.0000000000001,
        "y": 628.0000000000001
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "【列追加】ケース：時分割0.1秒",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "c": "int(${Time} /0.1)+1",
        "a": "時分割0.1秒"
      },
      "commandId": "mcal"
    },
    {
      "position": {
        "x": 79,
        "y": 444
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n1",
      "type": "note",
      "label": "n1",
      "title": "ケースの作成",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 456.0000000000001,
        "y": 555.0000000000001
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 345.0000000000001,
        "y": 558.0000000000001
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "【列追加】ケース：時分割0.05秒",
      "srcs": {
        "i": "d3"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "c": "int(${Time} /0.05)+1",
        "a": "時分割0.05秒"
      },
      "commandId": "mcal"
    }
  ]
}

shindo_sub5 = {
  "projectId": 13,
  "label": "【サブルーチン】特徴量作成",
  "ports": [
    [
      {
        "label": "d",
        "nodeId": "d.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d7",
        "nodeId": "d7",
        "type": "frame"
      }
    ]
  ],
  "params": [
    {
      "name": "key_list",
      "type": "string"
    },
    {
      "name": "sensor_list",
      "type": "string"
    },
    {
      "name": "feature_list",
      "type": "string"
    }
  ],
  "description": "",
  "creator": "開発用",
  "createdAt": "2019-03-30 23:58:12",
  "nodes": [
    {
      "position": {
        "x": 253,
        "y": 227
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d.csv",
      "type": "frame",
      "label": "d.csv",
      "uuid": "a1c363e4-0caa-4d48-9843-02f1cde61dc1",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 315,
        "y": 381
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 253,
        "y": 379
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "GroupBy",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "k": "@[key_list],時分割0.01秒",
        "f": "@[sensor_list]",
        "c": "@[feature_list]"
      },
      "commandId": "groupby"
    },
    {
      "position": {
        "x": 317,
        "y": 443
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d2",
      "type": "frame",
      "label": "d2",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 253,
        "y": 442
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c2",
      "type": "command",
      "label": "【列追加】波形分割",
      "srcs": {
        "i": "d1"
      },
      "dsts": {
        "o": "d2"
      },
      "args": {
        "v": "時分割0.01秒",
        "a": "波形間隔"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 150,
        "y": 338
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n1",
      "type": "note",
      "label": "n1",
      "title": "【時分割0.01秒】",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 604,
        "y": 383
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d4",
      "type": "frame",
      "label": "d4",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 532,
        "y": 381
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c4",
      "type": "command",
      "label": "GroupBy",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d4"
      },
      "args": {
        "k": "@[key_list],時分割0.05秒",
        "f": "@[sensor_list]",
        "c": "@[feature_list]"
      },
      "commandId": "groupby"
    },
    {
      "position": {
        "x": 605,
        "y": 444
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d5",
      "type": "frame",
      "label": "d5",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 533,
        "y": 442
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c5",
      "type": "command",
      "label": "【列追加】波形分割",
      "srcs": {
        "i": "d4"
      },
      "dsts": {
        "o": "d5"
      },
      "args": {
        "v": "時分割0.05秒",
        "a": "波形間隔"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 481,
        "y": 338
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n2",
      "type": "note",
      "label": "n2",
      "title": "【時分割0.05秒】",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 253,
        "y": 906
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d7",
      "type": "frame",
      "label": "d7",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 254,
        "y": 761
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c7",
      "type": "command",
      "label": "【行追加】連結",
      "srcs": {
        "*1": "d11",
        "*2": "d3",
        "*3": "d6"
      },
      "dsts": {
        "o": "d7"
      },
      "args": {},
      "commandId": "mcat"
    },
    {
      "position": {
        "x": 807,
        "y": 336.03333282470703
      },
      "size": {
        "width": 215,
        "height": 25
      },
      "invalid": {},
      "error": {},
      "id": "n3",
      "type": "note",
      "label": "n3",
      "title": "【時分割0.1秒】",
      "content": "新しいメモ"
    },
    {
      "position": {
        "x": 925,
        "y": 374
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d8",
      "type": "frame",
      "label": "d8",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 842,
        "y": 375
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c8",
      "type": "command",
      "label": "GroupBy",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d8"
      },
      "args": {
        "k": "@[key_list],時分割0.1秒",
        "f": "@[sensor_list]",
        "c": "@[feature_list]"
      },
      "commandId": "groupby"
    },
    {
      "position": {
        "x": 926,
        "y": 433
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d9",
      "type": "frame",
      "label": "d9",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 843,
        "y": 435
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c9",
      "type": "command",
      "label": "【列追加】波形分割",
      "srcs": {
        "i": "d8"
      },
      "dsts": {
        "o": "d9"
      },
      "args": {
        "v": "時分割0.1秒",
        "a": "波形間隔"
      },
      "commandId": "msetstr"
    },
    {
      "position": {
        "x": 254,
        "y": 646
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "type": "frame",
      "id": "d11",
      "label": "d11",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 253,
        "y": 503
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "type": "command",
      "id": "c11",
      "label": "c11",
      "srcs": {
        "i": "d2"
      },
      "dsts": {
        "o": "d11"
      },
      "args": {
        "f": "時分割0.01秒:波形ID"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 534,
        "y": 632
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "type": "frame",
      "id": "d3",
      "label": "d3",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 533,
        "y": 504
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "type": "command",
      "id": "c3",
      "label": "c3",
      "srcs": {
        "i": "d5"
      },
      "dsts": {
        "o": "d3"
      },
      "args": {
        "f": "時分割0.05秒:波形ID"
      },
      "commandId": "mfldname"
    },
    {
      "position": {
        "x": 841,
        "y": 626
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "type": "frame",
      "id": "d6",
      "label": "d6",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 841,
        "y": 497
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "type": "command",
      "id": "c6",
      "label": "c6",
      "srcs": {
        "i": "d9"
      },
      "dsts": {
        "o": "d6"
      },
      "args": {
        "f": "時分割0.1秒:波形ID"
      },
      "commandId": "mfldname"
    }
  ]
}

shindo_sub6 = {
  "projectId": 13,
  "label": "【サブルーチン】分類モデル学習",
  "ports": [
    [
      {
        "label": "d",
        "nodeId": "d.csv",
        "type": "frame"
      }
    ],
    [
      {
        "label": "d1",
        "nodeId": "d1",
        "type": "frame"
      }
    ]
  ],
  "params": [],
  "description": "",
  "creator": "開発用",
  "createdAt": "2019-03-31 14:02:34",
  "nodes": [
    {
      "position": {
        "x": 494,
        "y": 198
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d.csv",
      "type": "frame",
      "label": "d.csv",
      "uuid": "f82feb99-e5f5-48cb-89f2-68148b2ba19c",
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 491,
        "y": 417
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "d1",
      "type": "frame",
      "label": "d1",
      "uuid": None,
      "makeCache": False,
      "cacheCreatedAt": "",
      "dataSource": "csv"
    },
    {
      "position": {
        "x": 493,
        "y": 304
      },
      "size": {
        "width": 38,
        "height": 38
      },
      "invalid": {},
      "error": {},
      "id": "c1",
      "type": "command",
      "label": "c1",
      "srcs": {
        "i": "d.csv"
      },
      "dsts": {
        "o": "d1"
      },
      "args": {
        "target_list": "状態",
        "k": "DATA_SOURCE,波形間隔",
        "command_list": "'python3 modeling/classification/kdt.py,python3 modeling/classification/ksvm.py,python3 modeling/classification/kab.py,python3 modeling/classification/kbag.py,python3 modeling/classification/kgaussian_nb.py,python3 modeling/classification/klogreg.py,python3 modeling/classification/krf.py,python3 modeling/classification/knearest_neighbors.py'",
        "classification": True,
        "feature_list": "3H_平均,3V_平均,4H_平均,4V_平均"
      },
      "commandId": "sml_modeling"
    }
  ]
}

test_json = {
    'sub1': sub1,
    'sub2': sub2,
    'sub3': sub3,
    'sub4': sub4,
    'ni': ni,
    'ryudo': ryudo,
    'ryudo_sub1': ryudo_sub1,
    'ryudo_sub2': ryudo_sub2,
    'shindo': shindo,
    'shindo_sub1': shindo_sub1,
    'shindo_sub2': shindo_sub2,
    'shindo_sub3': shindo_sub3,
    'shindo_sub4': shindo_sub4,
    'shindo_sub5': shindo_sub5,
    'shindo_sub6': shindo_sub6,
}
