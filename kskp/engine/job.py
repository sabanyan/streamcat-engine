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
        # Stepの終了処理
        self.step.dtor()
