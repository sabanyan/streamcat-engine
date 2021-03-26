class Job:
    def __init__(self, step, inputs):
        self.step = step
        self.inputs = inputs

        self.errors = []

    def start(self):
        try:
            return self.step.run(self.inputs)
        except Exception as e:
            self.errors.append(e)
            raise

    def dtor(self):
        from kskp.core import Tmp
        from .flow_command import FlowCommand

        # Tmpファイルを削除する
        Tmp.remove_files()

        if isinstance(self.step.runnable, FlowCommand):
            # 今のFlowのdtorは、cacheやlastsを保存しているだけ
            self.step.dtor()

            for point in self.step.runnable.points:
                if point.datum is not None:
                    pass
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定
