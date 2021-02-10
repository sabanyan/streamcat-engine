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

    # def runs(self):
    #     """
    #     runsを実行する
    #     """
    #     try:
    #         last_modules = []
    #         for point_datum in self.step.runnable.results.values():
    #             last_modules.append(point_datum.content)

    #         module_list = self.step.runnable.get_module_list()
    #         last_modules.extend(module_list)

    #         # import pprint
    #         # pprint.pprint('runs :')  
    #         # pprint.pprint(last_modules)

    #         # 実行
    #         import nysol.mcmd as nm
    #         nm.runs(last_modules, msg='on')
    #     except Exception as e:
    #         self.errors.append(e)
    #         raise

    def dtor(self):
        from kskp.core import Tmp
        from .core import Flow

        # Tmpファイルを削除する
        Tmp.remove_files()

        if isinstance(self.step.runnable, Flow):
            # 今のFlowのdtorは、cacheやlastsを保存しているだけ
            self.step.dtor()

            for point in self.step.runnable.points:
                if point.datum is not None:
                    pass
                    # a.datum.command_to_file().dtor() # command_to_fileは不要になる予定
