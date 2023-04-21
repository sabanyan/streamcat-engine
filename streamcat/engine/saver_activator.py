from .flow_command import FlowCommand
from .step import Step, Steps
from .point import Point
from .flow_port import FlowPort

class SaverActivator:
    """
    実行可能フローの前処理
    """

    class Context():
        """
        Preprocessorを再帰的に下降して呼び出すときに参照する共通の格納場所
        """
        def __init__(self, flow, datum_factory, activity):
            self.datum_factory = datum_factory

            self.flow = flow
            self.flow_uuid = flow.uuid
            self.flow_label = flow.label

            # 処理のAcitivityのUUID
            self.activity = activity

            # 処理の開始時刻を取得する
            self.start_at = activity._start_at

            # ポート名の接尾語(ポート名が被らないようにするため)
            self.port_suffix_num = 0

    def __init__(self, flow, datum_factory=None, activity=None):
        # Context
        self._context = SaverActivator.Context(flow, datum_factory, activity)

    def traverse(self, flow_cmd:FlowCommand, src_point:Point=None):
        # 
        # Rootフローの出力Pointから辿れないコマンドは実行されない
        # その為、SaverCommandはその副作用(出力処理)を実行する為に、そのコマンドの出力Pointをフローの出力Pointに設定する
        # TODO: SaverCommand以外に副作用を持つコマンドも同じ設定をする必要があるだろう
        # 

        # サブフローを縦型探索してSaverCommandの出力Pointを処理する
        for step in flow_cmd.substeps:
            if step.is_flow:
                # step.classificationの設定がないStepにも対応できるよう入出力Portの数で判定する
                is_datadst = len(step.command.i_ports) == 1 and len(step._o_ports) == 0
                if is_datadst:
                    data_dst_src_point = [p for p in flow_cmd.points if p.dst_tubes.have_step(step)][0]
                else:
                    data_dst_src_point = src_point
                self.traverse(step.command, src_point=data_dst_src_point)

        # フロー内の全てのSaverCommandの出力Pointをフロー出力Pointに設定し
        # そのフロー出力ポートを中継ポートに設定する
        self._open_saver_cmd_points(flow_cmd)

        # フロー内の全ての中継ポートを再中継する
        self._relay_o_ports(flow_cmd)

        # SCommandに共通の引数を設定する
        self._set_scmds_args(flow_cmd.substeps, src_point)

        return flow_cmd

    def _open_saver_cmd_points(self, flow_cmd:FlowCommand):
        """
        フロー内の全てのSaverCommandの出力Pointをフロー出力Pointに設定し
        そのフロー出力ポートを中継ポートに設定する
        """
        from streamcat.depo.std.commands.scmd.script import SaverCommand

        for point in flow_cmd.points:
            # 既にフロー出力Pointの場合は中継しない
            if flow_cmd.is_o_port(point):
                continue

            # コマンドの出力Pointでない場合も中継しない
            src_tube = point.src_tubes.find_command_tube()
            if src_tube is None:
                continue

            # SaverCommandとそのサブクラスのコマンドは、その出力ポイントをフローの出力Pointに設定する
            if isinstance(src_tube.step.command, SaverCommand):
                # サブフローにおいては、フロー出力Point以降のSaverCommandは実行しない
                if flow_cmd._is_main or not self._search_out_port_point(flow_cmd, src_tube.step):
                    # フローの出力Pointに設定する
                    o_port = FlowPort(point.id, 'mcmd', point, relayed=True)
                    flow_cmd.open_o_port(o_port)
                    # 中継済みのポートとして記録する
                    flow_cmd.relayed_o_ports.add(o_port)

    def _relay_o_ports(self, flow_cmd:FlowCommand):
        """
        フロー内の全ての中継ポートを再中継する
        """
        for step in flow_cmd.substeps:
            # コマンドにはポートを動的に追加できないため、
            # コマンドがデータデストの場合は、そのコマンドは実行できない
            if not step.is_flow:
                continue

            # フローが中継ポートを持っている場合
            for port in step.command.relayed_o_ports:
                # サブフローにおいては、フロー出力Point以降のSaverCommandは実行しない
                if flow_cmd._is_main or not self._search_out_port_point(flow_cmd, step):
                    # 中継する
                    new_port = self._relay_o_port(flow_cmd, step, port)
                    # 中継済みのポートとして記録する
                    flow_cmd.relayed_o_ports.add(new_port)

    def _search_out_port_point(self, flow_cmd:FlowCommand, step:Step):
        """
        指定されたStepの全ての入力Pointについて、経路を逆に辿るとフロー出力Pointに繋がる場合は、Trueを返す
        ただし、辿る経路の途中にN入力コマンドがある場合は、そのN入力のうちフロー出力Pointに繋がる入力Pointを切断してFalseを返す
        """
        out_points:set[Point] = set()

        # stepの入力Pointを取得する
        prev_points = {p for p in flow_cmd.points if p.dst_tubes.have_step(step)}

        # stepの全ての入力Pointについて、経路を逆に辿ってフロー出力Pointに繋がるか調べる
        for p in prev_points:
            if flow_cmd.is_o_port(p):
                # stepの入力Pointがフロー出力Pointの場合は、そのstepの入力Pointを記録する
                for dst_tube in p.dst_tubes.filter_by_step(step):
                    # フロー出力Point
                    out_points.add(p)
            elif flow_cmd.is_i_port(p):
                # stepの入力Pointがフロー入力Pointの場合は、その経路の探索を終える
                pass
            else:
                # stepの入力Pointがフロー入出力Pointでない場合、その経路を逆に辿る
                for src_tube in p.src_tubes:
                    if src_tube.is_command_tube and self._search_out_port_point(flow_cmd, src_tube.step):
                            # 経路を逆に辿ってフロー出力Pointに繋がる場合は、stepの入力Pointを記録する
                            out_points.add(p)

        # N入力コマンドにおいて、一部の入力Pointがフロー出力Pointに繋がる場合、N入力コマンドとその入力Pointを切断する
        # 全ての入力Pointがフロー出力Pointに繋がる、または全て繋がらない場合は切断しない
        if len(prev_points) > 1 and len(out_points) < len(prev_points):
            for out_point in out_points:
                # N入力コマンドとその入力Pointを切断する
                for dst_tube in out_point.dst_tubes.filter_by_step(step):
                    out_point.dst_tubes.remove(dst_tube)
                # N入力コマンドがフローの場合は空のPointを繋げる
                # (フローの入力Portに入力Pointが繋がれていなければエラーにしているため)
                if step.is_flow:
                    empty_point = Point(f'empty_{out_point.id}', dst_tube=dst_tube)
                    flow_cmd.points.add(empty_point)

        # stepの全ての入力Pointについて、経路を逆に辿るとフロー出力Pointに繋がる場合は、Trueを返す
        return len(out_points) > 0 and len(out_points) == len(prev_points)

    def _relay_o_port(self, flow_cmd:FlowCommand, step:Step, port:FlowPort):
        """
        フローの出力ポートを親フローに中継する
        """
        from streamcat.core import SavableDatum, Port
        from .tube import Tube

        # サブフローから中継された出力Portに紐づくPointを新規作成する
        src_tube = Tube(Port(port.label, 'mcmd'), step)
        new_out_point = Point(f'{step.id}_{port.label}', src_tube)
        flow_cmd.points.add(new_out_point)

        # 親フロー内で出力Portのlabelが重複する場合は、末尾に数字を付加する
        port_label = port.label
        while flow_cmd.has_o_port(port_label):
            port_label = SavableDatum._increment_file_name(port_label)

        # サブフローの出力を親フローに繋げる
        o_port = FlowPort(port_label, 'mcmd', new_out_point, relayed=True)
        flow_cmd.open_o_port(o_port)

        # 作成した親フローの出力Portを返す
        return o_port

    def _set_scmds_args(self, steps:Steps, src_point:Point):
        """
        SCommandに共通の引数を設定する
        """
        from streamcat.depo.std.commands import SCommand

        for step in steps:
            if step.is_flow:
                continue
            if isinstance(step.command, SCommand):
                # SCommand共通引数を作成する
                args = {'flow'         : self._context.flow,
                        'flow_uuid'    : self._context.flow_uuid,
                        'flow_label'   : self._context.flow_label,
                        'result_folder': self._context.flow.find_parent(),
                        # データデストの入力PointのlabelをSaverCommandに渡す
                        'src_point'    : src_point,
                        'datum_factory': self._context.datum_factory,
                        'start_at'     : self._context.start_at,
                        'activity_uuid': self._context.activity.uuid}
                # 引数の設定が重複した場合は、コマンドの個別引数の方を優先する
                args.update(step.args)
                step.args = args
