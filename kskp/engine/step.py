from kskp.core import Command

class Step:
    """
    コマンド等の実行可能ノードのインスタンスを表現するクラス
    """
    def __init__(self, id:str, command:Command, args:dict={}, o_ports=None, classification:str=None, ex_acceptable:bool=False):
        if not isinstance(command, Command):
            raise Exception('commandにFlowCommandまたはCommand以外のオブジェクトが指定されました')

        self.id = id
        self.command = command
        self.args = args

        # classificationはサブフローノードで定義される
        self.classification = classification

        # 入力データが例外の場合、コマンドに渡すか否か
        self.ex_acceptable = ex_acceptable
        
        # 可変長Port'*'の展開済みのo_ports
        # make_exception_outs()でのみ用いる
        self._o_ports = o_ports or command.o_ports

    def __repr__(self):
        return self.id

    @property
    def is_flow(self):
        from .flow_command import FlowCommand
        return isinstance(self.command, FlowCommand)

    @property
    def is_datadst(self):
        """
        データデストの場合はTrueを返す
        """
        # return len(self.command.i_ports) == 1 and len(self._o_ports) == 0
        return self.classification == 'data_dest'

    def run(self, inputs):
        """
        コマンドを実行する
        (コマンドの実行で例外が送出されても、最後のコマンドまで実行する)
        """
        from kskp.store import CommandException

        def make_exception_outs(o_ports, cmd_ex):
            """
            全ての出力ポートに例外を格納する
            """
            outs = {}
            for o_port in o_ports:
                outs[o_port.label] = cmd_ex
            return outs

        try:
            if not self.ex_acceptable:
                # 入力データに1つでも例外があれば、全ての出力ポートに例外を格納する
                for input in inputs.values():
                    if isinstance(input, CommandException):
                        return make_exception_outs(self._o_ports, cmd_ex=input)
            
            # コマンドを実行する
            return self.command.run(self.args, inputs)
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
            is_root_flow = self.is_flow and self.command.is_main
            if is_root_flow or len(self._o_ports) == 0:
                raise e

            # コマンドのrun()から例外が送出された場合、全ての出力Portに例外を格納する
            return make_exception_outs(self._o_ports, cmd_ex=CommandException(e))

    def dtor(self):
        self.command.dtor(self.args)

    def replace_args(self, flow_args):
        """
        自身のargsにフロー変数を使っている箇所があれば、argsの値で置き換える

        FIXME?: フロー変数を書き換えるのはStep以外でもいいが、
        早めに書き換えたかったので、とりあえずStepに記載してある
        """
        # フロー変数が存在する場合は、フロー変数を置き換え対象にする
        if 'flow_args' in self.args and isinstance(self.args['flow_args'], dict):
            # フロー変数は'flow_args'の下に格納されている
            args = self.args.get('flow_args') or {}
        else:
            args = self.args

        # TODO: 正規表現やreplace対象を外に出す
        for arg, value in flow_args.items():
            for step_param, step_value in args.items():
                if isinstance(step_value, str):
                    # 文字列の場合は通常通り置換を行う
                    self._replace_arg_internal(args, arg, value, step_param, step_value)
                elif isinstance(step_value, list):
                    # リストの場合は、リストの要素それぞれに対して置換を行う
                    for list_value in step_value:
                        if isinstance(list_value, dict):
                            # リストの要素がDictの場合
                            for list_value_dict_key, list_value_dict_val in list_value.items():
                                self._replace_arg_internal(list_value, arg, value, list_value_dict_key, list_value_dict_val)
                        else:
                            # リストの要素がDict以外の場合(msimとmsummary)
                            for list_value_dict_val in list_value:
                                self._replace_arg_internal(list_value, arg, value, step_param, list_value_dict_val)

    def _replace_arg_internal(self, args, param, value, step_param, step_value):
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
