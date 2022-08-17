from .flow_command import FlowCommand
from .flow_port import FlowPort
from .point import Points, Point

class Preprocessor:
    """
    実行可能フローの前処理
    """

    class Context():
        """
        Preprocessorを再帰的に下降して呼び出すときに参照する共通の格納場所
        """
        def __init__(self, datum_factory, flow, activity_uuid):
            self.datum_factory = datum_factory

            self.flow = flow
            self.flow_uuid = flow.uuid
            self.flow_label = flow.label

            # 処理のAcitivityのUUID
            self.activity_uuid = activity_uuid

            # 処理の開始時刻を取得する
            from datetime import datetime, timezone
            self.start_at = datetime.utcnow().replace(tzinfo=timezone.utc)

            # ポート名の接尾語(ポート名が被らないようにするため)
            self.port_suffix_num = 0

    def __init__(self, flow, datum_factory=None, lock_uuid=None):
        from .appenders import (
            CacheDataDestAppender,
            VisDataDestAppender,
            ActivityDataDestAppender,
            RunsCommandAppender
        )

        # Appenders
        self._runs_command_appender = RunsCommandAppender()
        self._activity_data_dest_appender = ActivityDataDestAppender(datum_factory, flow)

        # Context
        self._context = Preprocessor.Context(datum_factory, flow, self._activity_data_dest_appender.activity_uuid)

        # Appenders
        self._cache_data_dest_appender = CacheDataDestAppender(flow, datum_factory, lock_uuid, self._context.start_at)
        self._vis_data_dest_appender = VisDataDestAppender()

        # flow_datumのLockのUUID
        self._lock_uuid = lock_uuid

    def init(self, args:dict):
        """
        初期状態に戻す
        """
        from .appenders import RunsCommandAppender, ActivityDataDestAppender
        self._runs_command_appender = RunsCommandAppender()
        self._activity_data_dest_appender = ActivityDataDestAppender(self._context.datum_factory,
                                                                     self._context.flow,
                                                                     args)
        self._context = Preprocessor.Context(self._context.datum_factory,
                                             self._context.flow,
                                             self._activity_data_dest_appender.activity_uuid)

    def execute(self, flow_cmd:FlowCommand, vis_args:dict, use_cache:bool=False, src_point:Point=None):
        # 
        # Rootフローの出力Pointから辿れないコマンドは実行されない
        # その為、SaverCommandはその副作用(出力処理)を実行する為に、そのコマンドの出力Pointをフローの出力Pointに設定する
        # TODO: SaverCommand以外に副作用を持つコマンドも同じ設定をする必要があるだろう
        # 

        # フロー内の全てのSaverCommandの出力Pointをフロー出力Pointに設定し
        # そのフロー出力ポートを中継ポートに設定する
        self._open_saver_cmd_points(flow_cmd)

        # フロー内の全ての中継ポートを再中継する
        self._relay_o_ports(flow_cmd)

        # SCommandに共通の引数を設定する
        self._set_scmds_args(flow_cmd.substeps, src_point)

        # サブフローの場合、フロー出力PointへのSaverコマンド等の付加をしない
        # また、キャッシュの出力処理もしない
        if flow_cmd.is_main:
            # プレビューを取得するPoint
            vis_ids = vis_args.keys()
            is_vis = len(vis_ids) > 0

            # outs出力処理
            if is_vis:
                # Vis出力PointにVisコマンド、RunsコマンドとActivityコマンドを付加する
                self._terminate_for_vizs(flow_cmd, vis_args, vis_ids)
            else:
                # フロー出力PointにRunsコマンドとActivityコマンドを付加する
                self._terminate_for_exec(flow_cmd)

            # キャッシュを利用する指定がされていれば、キャッシュデータデストを付加する
            if use_cache:
                # キャッシュ出力=ONのPointにキャッシュデータデストを付加する
                # ・サブフロー内ではキャッシュは作成しない
                # ・is_outかつis_cacheなPointにも対応できるよう
                #   データデストを付加した後にキャッシュデータデストを付加すること
                self._append_cache_saver_cmds(flow_cmd)

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
                if flow_cmd.is_main or not self._search_out_port_point(flow_cmd, src_tube.step):
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
                if flow_cmd.is_main or not self._search_out_port_point(flow_cmd, step):
                    # 中継する
                    new_port = self._relay_o_port(flow_cmd, step, port)
                    # 中継済みのポートとして記録する
                    flow_cmd.relayed_o_ports.add(new_port)

    def _search_out_port_point(self, flow_cmd:FlowCommand, step):
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

    def _relay_o_port(self, flow_cmd:FlowCommand, step, port):
        """
        フローの出力ポートを親フローに中継する
        """
        from streamcat.core import Datum, Port
        from .tube import Tube

        # サブフローから中継された出力Portに紐づくPointを新規作成する
        src_tube = Tube(Port(port.label, 'mcmd'), step)
        new_out_point = Point(f'{step.id}_{port.label}', src_tube)
        flow_cmd.points.add(new_out_point)

        # 親フロー内で出力Portのlabelが重複する場合は、末尾に数字を付加する
        port_label = port.label
        while flow_cmd.has_o_port(port_label):
            port_label = Datum._increment_file_name(port_label)

        # サブフローの出力を親フローに繋げる
        o_port = FlowPort(port_label, 'mcmd', new_out_point, relayed=True)
        flow_cmd.open_o_port(o_port)

        # 作成した親フローの出力Portを返す
        return o_port

    def _set_scmds_args(self, steps:list, src_point:Point):
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
                        'activity_uuid': self._context.activity_uuid}
                # 引数の設定が重複した場合は、コマンドの個別引数の方を優先する
                args.update(step.args)
                step.args = args

    def _terminate_for_vizs(self, flow_cmd:FlowCommand, vis_args:dict, vis_ids:list[str]):
        """
        Vis出力PointにVisコマンド、RunsコマンドとActivityコマンドを付加する
        """
        # プレビューの結果を得るのに不要なコマンドをStepointsでrun()させない為
        # メインフローの全ての出力Portを閉じる
        # (_search_invokable_steps()では出力Portを起点に実行すべきコマンドを探す)
        flow_cmd.close_all_o_ports()

        # プレビュー実行の場合、実行結果情報を保存しない
        self._activity_data_dest_appender.set_is_vis()

        for original_out_point in [flow_cmd.points[pid] for pid in vis_ids]:
            # Visualizerコマンドのための前処理コマンドを付加する
            o_point, u_point = self._vis_data_dest_appender.do_append(flow_cmd, original_out_point, vis_args)
            # Runsコマンドを付加する
            o_point, u_point = self._runs_command_appender.do_append(flow_cmd, o_point, u_point)
            # Visualizeコマンドを付加する
            vis_arg = vis_args.get(original_out_point.id)
            out_point = self._vis_data_dest_appender.do_append_after_runs(flow_cmd, o_point, u_point, vis_arg)
            # Activity Stepを付加する
            out_point = self._activity_data_dest_appender.do_append(flow_cmd, out_point, original_out_point)
            # Activity_pointを出力Pointに設定する
            out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'activity', out_point))

    def _terminate_for_exec(self, flow_cmd:FlowCommand):
        """
        フロー出力PointにRunsコマンドとActivityコマンドを付加する
        """
        # SaverCommandとそのサブクラスのコマンドの出力Pointに、Runs StepとActivity Stepを付加する
        for original_out_point in [p.point for p in flow_cmd.relayed_o_ports]:
            # データデストの入力Pointを取得する、取得できない場合はSaverCommandの出力Pointを用いる
            src_point_of_data_dst = self._get_src_point_of_data_dst(flow_cmd.points, original_out_point) or original_out_point
            # Runs Stepを付加する
            out_point, none_point = self._runs_command_appender.do_append(flow_cmd, original_out_point)
            # Activity Stepを付加する
            out_point = self._activity_data_dest_appender.do_append(flow_cmd, out_point, src_point_of_data_dst)
            # 出力Point設定を元のPointからActivity_pointに変更する
            flow_cmd.close_o_port_by_point(original_out_point)
            out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'activity', out_point))

        # SaverCommandとそのサブクラスのコマンドが存在しない場合でも、Activity Stepを付加する
        if len(flow_cmd.o_ports) == 0:
            out_point = self._activity_data_dest_appender.make_activity_point(flow_cmd, 'activity_0')
            flow_cmd.open_o_port(FlowPort(out_point.id, 'activity', out_point))

    def _append_cache_saver_cmds(self, flow_cmd:FlowCommand):
        """
        キャッシュ出力=ONのPointにキャッシュデータデストを付加する
        """
        for cache_point in [p for p in flow_cmd.points if p.makeCache]:
            # Cache Stepを挿入する
            out_point, frame_point = self._cache_data_dest_appender.do_append(flow_cmd, cache_point)

            # 
            # TODO: エラー発生時にdtor()でCacheフレームを削除する為、CacheSaverのPort(u)をActivityコマンドに繋げたが
            # そうすると、プレビュー実行に関係のないコマンドのrun()が実行されてしまう
            # 解決方法は、やはりNysolModule.contextにCacheフレームを格納してActivityコマンドにまで渡すことだろう
            # 全てのコマンドでNysolModuleインスタンスを使い回すための修正が必要になる
            # 
            # # Activity Stepを付加する
            # out_point = self._activity_data_dest_appender.do_append(flow_cmd, frame_point, cache_point)
            # # Activity_pointを出力Pointに設定する
            # out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'activity', out_point))

    def _get_src_point_of_data_dst(self, flow_points:Points, dst_point_of_data_dst:Point) -> Point:
        """
        データデストの入力Pointを取得する、取得できない場合はNoneを返す
        """
        # 出力PointからCommandに紐づくTubeを取得する
        src_tube = dst_point_of_data_dst.src_tubes.find_command_tube()
        if src_tube is None:
            return None

        if src_tube.step.is_datadst:
            # 出力Pointに紐づくCommandがデータデストの場合
            # そのデータデストの入力Pointを取得する
            for point in flow_points:
                if point.dst_tubes.have_step(src_tube.step):
                    return point
            # データデストの入力Pointが取得できなかった場合はNoneを返す
            return None

        elif src_tube.step.is_flow:
            # 出力Pointに紐づくCommandがデータデスト以外のフローの場合
            # そのフローの出力ポートに紐づくフロー出力Pointを取得する
            sub_flow_cmd = src_tube.step.command
            for flow_port in sub_flow_cmd.o_ports:
                if flow_port == src_tube.port:
                    # フロー出力Point
                    dst_point_of_sub_flow_cmd = flow_port.point
                    break
            # フロー出力Pointが取得できなかった場合はNoneを返す
            if dst_point_of_sub_flow_cmd is None:
                return None
            # サブフロー内へデータデストを探しに行く
            return self._get_src_point_of_data_dst(sub_flow_cmd.points, dst_point_of_sub_flow_cmd)

        else:
            # 出力Pointに紐づくCommandがフローでない場合はNoneを返す
            return None
