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
        # print(e)
        # exception_manager()
        # return {}
        raise e

def make_job(link, args, inputs):
    # linkからrunnableを生成する
    runnable = link.resolve()

    # runnableからstepを作成する
    step = Step('', runnable, args)

    # port情報から、arrowを作成する
    arrows = domains(step, inputs)

    # jobを作成する
    job = Job(step, arrows)

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

class NotificationCenter:
    """
    起こった例外を集めて処理する
    呼出可能オブジェクトであれば他のものに置換可能
    """
    def __call__(self):
        pass

exception_manager = NotificationCenter()

# ストア
store = None
