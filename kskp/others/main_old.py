"""
外部とのインターフェースを規定している
基本的にはexecute_flowしか使わないはず
"""

import json2job

def execute_flow(flow_uuid, arguments={}, inputs=None):
    """
    指定したフローを実行する

    json内の記法が原因で、flowやframeのパスがないと、外部のflowやframeが呼べなくなっている。
    だから、環境変数が存在することは仕方ないようにも思える。そこを変更してもコストの割にメリットがない。一貫性があるだけだ。
    そういう意味では、「flowインスタンスは、uuidで一意に特定されることを前提としている」と言って差し支えない。

    「デフォルトでは」uuidに沿って読み出すファイルのパスが決まっている。
    いざとなればディレクトリや詳しいパスを指定できるようにオプションを追加予定。
    もしくは、直接中身のJSONを書けるようにしてもいいかもね。
    それぞれexecute_json/execute_json_file/execute_flowに対応するという感じで。

    execute_json(obj)
    execute_json_file(path)
    execute_flow(flow_uuid)
    """

def execute_json_file(path, arguments={}, inputs=None):
    flow = make_flow(flow_uuid, json_obj)
    pass

def execute_flow(flow_obj, args={}, inputs=None):
    flow = make_flow(None, json_obj)
    job = json2job.make_job(obj, flow, args, {}, {}, inputs)
    job.execute() # job.execute(step_paths=step_paths)
    job.dtor()

    return job.lasts