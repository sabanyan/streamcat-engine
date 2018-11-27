"""
外部とのインターフェースを規定している
基本的にはexecute_flow_by_uuidしか使わないはず
"""

from kskp.store import Port

from .core import Step, Job, Arrow

def execute(link, args, inputs):
    """
    全てのentrypointの基本形。
    """

    exs = []
    
    try:        
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
        exs.append(exception_manager(e))
        return exs

def make_job(link, args, inputs):
    # linkからrunnableを生成する
    runnable = link.resolve()

    # runnableからstepを作成する
    step = Step('', runnable, args)

    # port情報から、arrowを作成する
    # arrows = domains(step, inputs)

    # jobを作成する
    job = Job(step, {})

    return job

def domains(step, inputs):
    """
    port情報から、arrowを作成する
    1つのportにつき、1つのarrowが作られる

    注意：この部分は詳細なロジックを変更したので書換え予定
    単純に、inputsを取り出せば良い（はず？）
    """    

    # try:    
    #     return [Arrow(port.name, None, step, inputs[port.name]) for port 
    #                                                             in step.runnable.i_ports]
    # except KeyError as e:
    #     # inputsに必要な引数が与えられていない
    #     raise Exception('inputsに必要な引数が与えられていません') from e
    port_input = Port('*i*', '*')
    port_output = Port('*o*', '*')
    return [Arrow('input_arrow', None, None, None, port_input, step),
            Arrow('output_arrow', Step, port_output, None, None, None)]

# def translate_result_lasts(lasts):
#     """
#     帰ってきた結果を変換する(主にdictのkey)
#     """    
#     root_arrows = domains()
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

# ストア
store = None
