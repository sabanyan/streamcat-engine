"""
外部とのインターフェースを規定している
基本的にはexecute_flow_by_uuidしか使わないはず

TODO: 外部からコマンド実行できるように
"""

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from .core import Step, Job


class DefaultHandler(PatternMatchingEventHandler):
    """
    ファイル監視のイベントハンドラ
    デフォルト実装（何もしない）
    """
    pass

# イベントハンドラ
job_complete_handler = None


def execute(link, args, inputs, job_complete_handler=None):
    """
    全てのentrypointの基本形。
    """

    # 進捗を取得する準備を行う
    prepare_observer(job_complete_handler)

    # exs = []

    try:
        # ここで実行するlinkは一番上の親であることを定義する
        link.is_root = True

        # jobを作成する
        job = make_job(link, args, inputs)

        # jobを開始する
        job.start()

        # 結果を取得する
        lasts = job.step.runnable.lasts

        # 後始末をする
        job.dtor()

        # 結果を返却する
        return lasts

    except Exception as e:
        print('main:', e)
        raise
        # exs.append(exception_manager(e))
        # return exs

def make_job(link, args, inputs):
    # linkからrunnableを生成する
    runnable = link.resolve()

    # runnableからstepを作成する
    step = Step('', runnable, args)

    # port情報から、pointを作成する
    # points = domains(step, inputs)

    # jobを作成する
    job = Job(step, inputs)

    return job

# def domains(step, inputs):
#     """
#     port情報から、pointを作成する
#     1つのportにつき、1つのpointが作られる
#
#     注意：この部分は詳細なロジックを変更したので書換え予定
#     単純に、inputsを取り出せば良い（はず？）
#     """
#
#     # try:
#     #     return [Point(port.name, None, step, inputs[port.name]) for port
#     #                                                             in step.runnable.i_ports]
#     # except KeyError as e:
#     #     # inputsに必要な引数が与えられていない
#     #     raise Exception('inputsに必要な引数が与えられていません') from e
#     port_input = Port('*i*', '*')
#     port_output = Port('*o*', '*')
#     return [Point('input_point', None, None, None, port_input, step),
#             Point('output_point', Step, port_output, None, None, None)]

# def translate_result_lasts(lasts):
#     """
#     帰ってきた結果を変換する(主にdictのkey)
#     """
#     root_points = domains()
#     new_lasts = {: v for k, v in lasts.items()}

class ExceptionManager:
    """
    起こった例外を集めて処理する
    呼出可能オブジェクトであれば他のものに置換可能
    """
    def __call__(self, e):
        """
        eは例外
        このクラスは、もらったexceptionをraiseするだけ
        デフォルトはこっちだろうか（no websocket
        """
        raise e

class ExceptionManagerWebSocket:
    """
    起こった例外を集めて処理する
    WebSocket用（もらった側から順番に返していく
    """
    def __call__(self, e):
        """
        eは例外
        """
        print('ExceptionManagerWebSocket:', e)
        # そのままraiseしてしまうとそこでPython全体が終わってしまうので、
        # 例外を値としてそのまま返す、返してそのまま一つずつ、
        # エラーメッセージの形にしてフロント側に返却してもらう
        return e

exception_manager = ExceptionManagerWebSocket()
# exception_manager = ExceptionManager()

def prepare_observer(job_complete_handler):
    """
    進捗を取得する準備を行う
    """
    # 進捗を取得する準備を行う
    observer = Observer()

    # 監視ディレクトリとハンドラの指定、本来はこの部分を外部から指定可能にしたい
    if job_complete_handler is None:
        job_complete_handler = DefaultHandler()
    # print(job_complete_handler)
    observer.schedule(job_complete_handler, 'kskp/messages/')

    # 監視を開始する
    observer.start()


# ストア
store = None
