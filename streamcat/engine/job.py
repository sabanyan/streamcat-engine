from threading import Thread

class Job(Thread):
    """
    Stepを実行する実行単位
    """
    def __init__(self, step, inputs):
        # スレッドIDに紐づくTmpファイルの削除が機能するよう
        # Stepの実行と終了処理を一つのスレッドで実行する
        def run_step(inputs):
            try:
                return step.run(inputs)
            finally:
                # 終了処理をする
                step.dtor()
        # run_step()をスレッド処理に登録する
        super().__init__(target=run_step, name=None, args=[inputs])
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

class AJob():
    """
    Stepを実行する実行単位
    """
    def __init__(self, step, inputs):
        from asyncio import to_thread

        # スレッドIDに紐づくTmpファイルの削除が機能するよう
        # Stepの実行と終了処理を一つのスレッドで実行する
        def run_step(inputs):
            try:
                return step.run(inputs)
            finally:
                # 終了処理をする
                step.dtor()
        # スレッドを新規生成して、そこで同期処理(run_step)を非同期実行する
        # https://qiita.com/smatsumt/items/d8f290e40077a14210f2#async-の処理のなかから一部の処理を別-thread-で処理させる
        self._co = to_thread(run_step, inputs)
        self._step = step
        self._outs = None

    async def run(self):
        """
        Stepの実行を開始する
        """
        try:
            # Stepを非同期に実行する
            # NOTE: Stepが終了する迄の間に他の非同期処理に制御が移る
            self._outs = await self._co
        except BaseException as e:
            raise
        # 結果を返す
        return self._outs
    
    def join(self, timeout=None):
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
