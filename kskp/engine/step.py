from kskp.core import Command

class Step:
    """
    コマンド等の実行可能ノードのインスタンスを表現するクラス
    """
    def __init__(self, id:str, runnable:Command, args:dict={}, o_ports=None, ex_acceptable:bool=False):
        if not isinstance(runnable, Command):
            raise Exception('runnableにFlowCommandまたはCommand以外のオブジェクトが指定されました')

        self.id = id
        self.runnable = runnable
        self.args = args

        # 入力データが例外の場合、コマンドに渡すか否か
        self.ex_acceptable = ex_acceptable
        
        # 可変長Port'*'の展開済みのo_ports
        # make_exception_outputs()でのみ用いる
        self._o_ports = o_ports or runnable.o_ports

    def __repr__(self):
        return self.id

    @property
    def is_flow(self):
        from .flow_command import FlowCommand
        return isinstance(self.runnable, FlowCommand)

    def run(self, inputs):
        """
        コマンドを実行する
        (コマンドの実行で例外が送出されても、最後のコマンドまで実行する)
        """
        from kskp.store import CommandException

        def make_exception_outputs(o_ports, cmd_ex):
            """
            全ての出力ポートに例外を格納する
            """
            outputs = {}
            for o_port in o_ports:
                outputs[o_port.label] = cmd_ex
            return outputs

        try:
            if not self.ex_acceptable:
                # 入力データに1つでも例外があれば、全ての出力ポートに例外を格納する
                for input in inputs.values():
                    if isinstance(input, CommandException):
                        return make_exception_outputs(self._o_ports, cmd_ex=input)
            
            # コマンドを実行する
            return self.runnable.run(self.args, inputs)
        except AttributeError as e:
            raise e
        except Exception as e:
            # 
            # TODO: コマンドからの例外は全てCommandExceptionとしたい
            #

            import traceback
            traceback.print_exc()

            # 出力Portが無ければ、送出(raise)する以外に例外を渡す方法が無い
            # 出力Portが有っても、メインフローは例外を渡す相手がいない
            is_root_flow = self.is_flow and self.runnable.is_main
            if is_root_flow or len(self._o_ports) == 0:
                raise

            # コマンドのrun()から例外が送出された場合、全ての出力Portに例外を格納する
            return make_exception_outputs(self._o_ports, cmd_ex=CommandException(e))

    def dtor(self):
        self.runnable.dtor(self.args)

    def replace_args(self, flow_args):
        """
        自身のargsにフロー変数を使っている箇所があれば、argsの値で置き換える

        FIXME?: フロー変数を書き換えるのはStep以外でもいいが、
        早めに書き換えたかったので、とりあえずStepに記載してある
        """
        
        # TODO: 正規表現やreplace対象を外に出す。
        for param, value in flow_args.items():
            for step_param, step_value in self.args.items():                
                if isinstance(step_value, str):
                    # 文字列の場合は通常通り置換を行う
                    self.replace_arg_internal(self.args, param, value, step_param, step_value)
                elif isinstance(step_value, list):
                    # リストの場合は、リストの要素それぞれに対して置換を行う
                    for list_value in step_value:
                        if isinstance(list_value, dict):
                            # リストの要素がDictの場合
                            for list_value_dict_key, list_value_dict_val in list_value.items():
                                self.replace_arg_internal(list_value, param, value, list_value_dict_key, list_value_dict_val)
                        else:
                            # リストの要素がDict以外の場合(msimとmsummary)
                            for list_value_dict_val in list_value:
                                self.replace_arg_internal(list_value, param, value, step_param, list_value_dict_val)                       

    def replace_arg_internal(self, args, param, value, step_param, step_value):
        """
        特定のargのペア（いわゆるオプションのキー名と値）に
        変数名（e.g. @[variable]）が入っている場合には、
        実際に与えられた値で置き換える

        param/value 親フローに与えられた値、いわば「実引数」
        args/step_param/step_value それぞれのstepに与えられた「仮引数」        
        """
        import re        
        for r in re.finditer(r'@\[(\S*?)\]', step_value):
            if r is None:
                continue

            for g in r.groups():
                if param == g:
                    args[step_param] = args[step_param].replace(f'@[{g}]', value)
