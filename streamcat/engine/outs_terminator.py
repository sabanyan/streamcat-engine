from .flow_command import FlowCommand
from .point import Point, Points
from .flow_port import FlowPort

class OutsTerminator:
    """
    コマンドやデータデストを付加する
    """
    def __init__(self, flow_cmd:FlowCommand, flow, datum_factory, lock_uuid) -> None:
        from .appenders import (
            CacheDataDestAppender,
            VisDataDestAppender,
            ActivityDataDestAppender,
            RunsCommandAppender
        )

        # Appenders
        self._runs_command_appender = RunsCommandAppender()
        self._activity_data_dest_appender = ActivityDataDestAppender(datum_factory, flow)

        # Appenders
        start_at = self._activity_data_dest_appender.activity._start_at
        self._cache_data_dest_appender = CacheDataDestAppender(flow, datum_factory, lock_uuid, start_at)
        self._vis_data_dest_appender = VisDataDestAppender()

        # FlowCommand
        self._flow_cmd = flow_cmd
        self._flow = flow
        self._datum_factory = datum_factory
        self._lock_uuid = lock_uuid

    def init(self, args:dict):
        """
        初期状態に戻す
        """
        from .appenders import ActivityDataDestAppender, CacheDataDestAppender
        self._activity_data_dest_appender = ActivityDataDestAppender(self._datum_factory,
                                                                     self._flow,
                                                                     args)

        start_at = self._activity_data_dest_appender.activity._start_at
        self._cache_data_dest_appender = CacheDataDestAppender(self._flow, self._datum_factory, self._lock_uuid, start_at)

    @property
    def activity(self):
        return self._activity_data_dest_appender.activity
    
    def terminate(self, vis_args:dict, use_cache:bool=False):
        # サブフローの場合、フロー出力PointへのSaverコマンド等の付加をしない
        # また、キャッシュの出力処理もしない
        if self._flow_cmd.is_main:
            # プレビューを取得するPoint
            vis_ids = vis_args.keys()
            is_vis = len(vis_ids) > 0

            # outs出力処理
            if is_vis:
                # Vis出力PointにVisコマンド、RunsコマンドとActivityコマンドを付加する
                self._terminate_for_vizs(self._flow_cmd, vis_args, vis_ids)
            else:
                # フロー出力PointにRunsコマンドとActivityコマンドを付加する
                self._terminate_for_exec(self._flow_cmd)

            # キャッシュを利用する指定がされていれば、キャッシュデータデストを付加する
            if use_cache:
                # キャッシュ出力=ONのPointにキャッシュデータデストを付加する
                # ・サブフロー内ではキャッシュは作成しない
                # ・is_outかつis_cacheなPointにも対応できるよう
                #   データデストを付加した後にキャッシュデータデストを付加すること
                self._append_cache_saver_cmds(self._flow_cmd)

    def _terminate_for_vizs(self, flow_cmd:FlowCommand, vis_args:dict, vis_ids:list[str]):
        """
        Vis出力PointにVisコマンド、RunsコマンドとActivityコマンドを付加する
        """
        # プレビューの結果を得るのに不要なコマンドをInvokerでrun()させない為
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
            out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'outs', out_point))

    def _terminate_for_exec(self, flow_cmd:FlowCommand):
        """
        フロー出力PointにRunsコマンドとActivityコマンドを付加する
        """
        # 実行結果情報をライブラリに保存する
        self._activity_data_dest_appender.save_activity()

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
            out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'outs', out_point))

        # SaverCommandとそのサブクラスのコマンドが存在しない場合でも、Activity Stepを付加する
        if len(flow_cmd.o_ports) == 0:
            out_point = self._activity_data_dest_appender.make_activity_point(flow_cmd, 'activity_0')
            flow_cmd.open_o_port(FlowPort(out_point.id, 'outs', out_point))

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
            # out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'outs', out_point))

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
