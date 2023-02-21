from threading import Thread

class Job(Thread):
    def __init__(self, step, inputs):
        super().__init__(target=step.run, name=None, args=[inputs])
        self._step = step
        self._ex = None
        self._outs = None

    def run(self):
        """
        Thread.run()をオーバーライドしてJob.start()を実装する
        """
        try:
            self._outs = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self._ex = e
            raise

    def join(self, timeout=None):
        # 処理の終了を待つ
        super().join(timeout)
        # NOTE: スレッド実行中に送出された例外はキャッチできない
        if self._ex:
            raise self._ex
        # 終了処理をする
        self.dtor()
        # 結果を返す
        return self._outs

    @property
    def activity_uuid(self):
        # NOTE: ApparentOutsはjoin()が返すoutsと、Activityに含まれている
        # ApparentOutsをどちらから取得するか混乱しないようActivityオブジェクトを返さずそのUUIDを返すことにする
        if self._step.is_flow:
            return self._step.command.activity.uuid
        else:
            # FlowCommandでない場合はActivityが無い
            return None

    def dtor(self):
        # Stepの終了処理
        self._step.dtor()
