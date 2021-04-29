from .flow_command import FlowCommand
from .flow_port import FlowPort

class Preprocessor:
    """
    実行可能フローの前処理
    """

    class Context():
        """
        Preprocessorを再帰的に下降して呼び出すときに参照する共通の格納場所
        """
        def __init__(self, flow, activity_uuid):
            self.flow = flow
            self.flow_uuid = flow.uuid
            self.flow_label = flow.label

            # 処理のAcitivityのUUID
            self.activity_uuid = activity_uuid

            # 処理の開始時刻を取得する
            from datetime import datetime, timezone
            self.start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

            # ポート名の接尾語(ポート名が被らないようにするため)
            self.port_suffix_num = 0

    def __init__(self, flow, datum_factory=None, lock_uuid=None):
        from .appenders import (
            FolderDataDestAppender,
            CacheDataDestAppender,
            VisDataDestAppender,
            ActivityDataDestAppender,
            RunsCommandAppender
        )

        # Appenders
        self._runs_command_appender = RunsCommandAppender()
        self._activity_data_dest_appender = ActivityDataDestAppender(flow.uuid)

        # Context
        self._context = Preprocessor.Context(flow, self._activity_data_dest_appender.activity_uuid)
        
        # Appenders
        self._folder_data_dest_appender = FolderDataDestAppender(flow, datum_factory, lock_uuid, self._context.start_time)
        self._cache_data_dest_appender = CacheDataDestAppender(flow, datum_factory, lock_uuid, self._context.start_time)
        self._vis_data_dest_appender = VisDataDestAppender()

        # flow_datumのLockのUUID
        self._lock_uuid = lock_uuid

    def execute(self, flow_cmd:FlowCommand, vis_args:dict, use_cache:bool=False):
        from kskp.depo.std.commands import SCommand
        from kskp.depo.std.commands.scmd.script import SaverCommand

        # 
        # Rootフローの出力Pointから辿れないコマンドは実行されない
        # その為、SaverCommandはその副作用(出力処理)を実行する為に、そのコマンドの出力Pointをフローの出力Pointに設定する
        # TODO: SaverCommand以外に副作用を持つコマンドも同じ設定をする必要があるだろう
        # 

        # SaverCommandの出力PointをRootフローに中継する
        for point in flow_cmd.points:
            # 既にフロー出力Pointの場合は中継しない
            if flow_cmd.is_o_port(point):
                continue

            # コマンドの出力Pointでない場合も中継しない
            src_tube = point.src_tubes.find_command_tube()
            if src_tube is None:
                continue

            # SaverCommandとそのサブクラスのコマンドは、その出力ポイントをフローの出力Pointに設定する
            if isinstance(src_tube.step.runnable, SaverCommand):
                o_port = FlowPort(point.id, 'mcmd', point)
                flow_cmd.open_o_port(o_port)
                # 中継済みのポートとして記録する
                flow_cmd.relayed_o_ports.add(o_port)

        # 中継ポートを中継する
        for step in flow_cmd.substeps:
            # コマンドにはポートを動的に追加できないため、
            # コマンドがデータデストの場合は、そのコマンドは実行できない
            if not step.is_flow:
                continue

            # フローが中継ポートを持っている場合
            for port in step.runnable.relayed_o_ports:
                # 中継する
                new_port = self._relay_o_port(flow_cmd, step, port)
                # 中継済みのポートとして記録する
                flow_cmd.relayed_o_ports.add(new_port)


        # コマンド共通引数を設定する
        for step in flow_cmd.substeps:
            if step.is_flow:
                continue
            if isinstance(step.runnable, SCommand):
                # SCommand共通引数を作成する
                args = {'flow'         : self._context.flow,
                        'flow_uuid'    : self._context.flow_uuid,
                        'flow_label'   : self._context.flow_label,
                        'result_folder': self._context.flow.find_parent(),
                        'start_time'   : self._context.start_time,
                        'activity_uuid': self._context.activity_uuid}
                # 引数の設定が重複した場合は、コマンドの個別引数の方を優先する
                args.update(step.args)
                step.args = args


        # サブフローの場合、フロー出力PointへのSaverコマンド等の付加をしない
        # また、キャッシュの出力処理もしない
        if not flow_cmd.is_main:
            return flow_cmd


        # プレビューを取得するPoint
        vis_ids = vis_args.keys()
        is_vis = len(vis_ids) > 0


        # lasts出力処理（メインフローの場合のみ）
        if is_vis:
            # プレビューの結果を得るのに不要なコマンドをStepointsでrun()させない為
            # メインフローの全ての出力Portを閉じる
            # (_search_invokable_steps()では出力Portを起点に実行すべきコマンドを探す)
            flow_cmd.close_all_o_ports()

            for original_out_point in [flow_cmd.points[pid] for pid in vis_ids]:
                # Visualizerコマンドのための前処理コマンドを付加する
                out_point = self._vis_data_dest_appender.do_append(flow_cmd, original_out_point, vis_args)
                # Runsコマンドを付加する
                out_point = self._runs_command_appender.do_append(flow_cmd, out_point)
                # Visualizeコマンドを付加する
                out_point = self._vis_data_dest_appender.do_append_after_runs(flow_cmd, out_point, original_out_point, vis_args)
                # Activity Stepを付加する
                out_point = self._activity_data_dest_appender.do_append(flow_cmd, out_point, original_out_point)
                # Activity_pointを出力Pointに設定する
                out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'frame', out_point))
        else:

            for original_out_point in [p.point for p in flow_cmd.o_ports]:
                # original_out_pointが、中継したフロー出力Pointの場合はTrue
                src_tube = original_out_point.src_tubes.find_command_tube()
                in_port_label_exists = src_tube is not None and src_tube.port is not None
                out_point_is_relayed = in_port_label_exists and src_tube.port in flow_cmd.relayed_o_ports
                if out_point_is_relayed:
                    # フローの出力Pointが、中継したフロー出力Pointでもある場合、
                    # 既にSaverコマンドが繋がっているので、そのPointにSaverコマンドを付加しない
                    out_point = original_out_point
                else:
                    # Saverコマンドを付加する
                    out_point = self._folder_data_dest_appender.do_append(flow_cmd, original_out_point)
                # Runsコマンドを付加する
                out_point = self._runs_command_appender.do_append(flow_cmd, out_point)
                # Activity Stepを付加する
                out_point = self._activity_data_dest_appender.do_append(flow_cmd, out_point, original_out_point)
                # 出力Point設定を元のPointからActivity_pointに変更する
                flow_cmd.close_o_port_by_point(original_out_point)
                out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'frame', out_point))


        # キャッシュを利用しない指定がされていれば、キャッシュデータデストを付加しない
        if not use_cache:
            return flow_cmd


        # キャッシュ作成処理
        # サブフロー内ではキャッシュは作成しない
        # is_outかつis_cacheなPointにも対応できるよう
        # データデストを付加した後にキャッシュデータデストを付加すること
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
            # out_point and flow_cmd.open_o_port(FlowPort(out_point.id, 'frame', out_point))


        return flow_cmd

    def _relay_o_port(self, flow_cmd, step, port):
        """
        フローの出力ポートを親フローに中継する
        """
        from kskp.core import Datum, Port
        from .point import Point
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
        o_port = FlowPort(port_label, 'mcmd', new_out_point)
        flow_cmd.open_o_port(o_port)

        # 作成した親フローの出力Portを返す
        return o_port

    # def _pick_necessary_dst_ids(self, nodes, datum_ids):
    #     """
    #     指定したnodesの中で、指定したdatum_id群を取得するのに必要なdstsのid群を取得する
    #     """
    #     ids = []
    #     for datum_id in datum_ids:
    #         for node in nodes['nodes']:
    #             if self._is_outputting_datum_node(node, datum_id):
    #                 # 対象のnode
    #                 ids.extend(self._pick_necessary_dst_ids(nodes, list(node['srcs'].values())))
    #         ids.append(datum_id)
    #     return list(set(ids))

    # def _is_outputting_datum_node(self, node, datum_id):
    #     """
    #     指定したdatumを出力するnodeかを調べる
    #     """
    #     return self._is_runnable_node(node) and datum_id in list(node['dsts'].values())
