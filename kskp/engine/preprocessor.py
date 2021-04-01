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
        def __init__(self, flow_datum, activity_uuid):
            self.flow_datum = flow_datum
            self.flow_uuid = flow_datum.uuid
            self.flow_label = flow_datum.label

            # 処理のAcitivityのUUID
            self.activity_uuid = activity_uuid

            # 処理の開始時刻を取得する
            from datetime import datetime, timezone
            self.start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

            # ポート名の接尾語(ポート名が被らないようにするため)
            self.port_suffix_num = 0

    def __init__(self, flow_datum, datum_factory=None):
        from .appenders import (
            FolderDataDestAppender,
            CacheDataDestAppender,
            VisDataDestAppender,
            ActivityDataDestAppender,
            RunsCommandAppender
        )

        # Appenders
        self._runs_command_appender = RunsCommandAppender()
        self._activity_data_dest_appender = ActivityDataDestAppender(flow_datum.uuid)

        # Context
        self._context = Preprocessor.Context(flow_datum, self._activity_data_dest_appender.activity_uuid)
        
        # Appenders
        self._folder_data_dest_appender = FolderDataDestAppender(flow_datum, datum_factory, self._context.start_time)
        self._cache_data_dest_appender = CacheDataDestAppender(flow_datum, datum_factory, self._context.start_time)
        self._vis_data_dest_appender = VisDataDestAppender()

    def execute(self, flow_command:FlowCommand, vis_args):
        from kskp.depo.std.commands import SCommand
        from kskp.depo.std.commands.scmd.script import SaverCommand

        flow = flow_command

        # 
        # Rootフローの出力Pointから辿れないコマンドは実行されない
        # その為、SaverCommandはその副作用(出力処理)を実行する為に、そのコマンドの出力Pointをフローの出力Pointに設定する
        # TODO: SaverCommand以外に副作用を持つコマンドも同じ設定をする必要があるだろう
        # 

        # SaverCommandの出力PointをRootフローに中継する
        for point in flow.points:
            # 既にフロー出力Pointの場合は中継しない
            if flow.is_o_port(point):
                continue

            # コマンドの出力Pointでない場合も中継しない
            src_tube = point.src_tubes.find_command_tube()
            if src_tube is None:
                continue

            # SaverCommandとそのサブクラスのコマンドは、その出力ポイントをフローの出力Pointに設定する
            if isinstance(src_tube.step.runnable, SaverCommand):
                o_port = FlowPort(point.id, 'mcmd', point)
                flow.open_o_port(o_port)
                # 中継済みのポートとして記録する
                flow.relayed_o_ports.add(o_port)

        # 中継ポートを中継する
        for step in flow.substeps:
            # コマンドにはポートを動的に追加できないため、
            # コマンドがデータデストの場合は、そのコマンドは実行できない
            if not step.is_flow:
                continue

            # フローが中継ポートを持っている場合
            for port in step.runnable.relayed_o_ports:
                # 中継する
                new_port = self._relay_o_port(flow, step, port)
                # 中継済みのポートとして記録する
                flow.relayed_o_ports.add(new_port)


        # コマンド共通引数を設定する
        for step in flow.substeps:
            if step.is_flow:
                continue
            if isinstance(step.runnable, SCommand):
                # SCommand共通引数を作成する
                args = {'flow'         : self._context.flow_datum,
                        'flow_uuid'    : self._context.flow_uuid,
                        'flow_label'   : self._context.flow_label,
                        'result_folder': self._context.flow_datum.find_parent(),
                        'start_time'   : self._context.start_time,
                        'activity_uuid': self._context.activity_uuid}
                # 引数の設定が重複した場合は、コマンドの個別引数の方を優先する
                args.update(step.args)
                step.args = args


        # サブフローの場合、フロー出力PointへのSaverコマンド等の付加をしない
        # また、キャッシュの出力処理もしない
        if not flow.is_main:
            return flow

        # 
        # flowがもつPointを、実行に必要なものだけを絞り込んで取得している。
        # 
        # self.vis_idsには
        # メインフローの場合 ： /vizsするdatumのid群
        # サブフローの場合　 ： 親の実行に必要なlastのid群
        # が入っている。（はず）
        vis_ids = vis_args.keys()
        is_vis = len(vis_ids) > 0
        # /vizsしない場合はメインフローのlastのid群を使って絞り込みを行う。
        last_ids = self._pick_out_points(flow, flow.outs, flow.points, vis_ids)
        # 実行するのに必要なpointを取得する
        flow.points = self._pick_necessary_points(flow, last_ids, is_vis)


        # lasts出力処理（メインフローの場合のみ）
        if is_vis:
            for original_out_point in [flow.points[pid] for pid in vis_ids]:
                # Visualizerコマンドのための前処理コマンドを付加する
                out_point = self._vis_data_dest_appender.do_append(flow, original_out_point, vis_args)
                # Runsコマンドを付加する
                out_point = self._runs_command_appender.do_append(flow, out_point)
                # Visualizeコマンドを付加する
                out_point = self._vis_data_dest_appender.do_append_after_runs(flow, out_point, original_out_point, vis_args)
                # Activity Stepを付加する
                out_point = self._activity_data_dest_appender.do_append(flow, out_point, original_out_point)
                # 出力Point設定を元のPointからActivity_pointに変更する
                flow.close_o_port_by_point(original_out_point)
                out_point and flow.open_o_port(FlowPort(out_point.id, 'frame', out_point))
        else:

            for original_out_point in [p.point for p in flow.o_ports]:
                # original_out_pointが、中継したフロー出力Pointの場合はTrue
                src_tube = original_out_point.src_tubes.find_command_tube()
                in_port_label_exists = src_tube is not None and src_tube.port is not None
                out_point_is_relayed = in_port_label_exists and src_tube.port in flow.relayed_o_ports
                if out_point_is_relayed:
                    # フローの出力Pointが、中継したフロー出力Pointでもある場合、
                    # 既にSaverコマンドが繋がっているので、そのPointにSaverコマンドを付加しない
                    out_point = original_out_point
                else:
                    # Saverコマンドを付加する
                    out_point = self._folder_data_dest_appender.do_append(flow, original_out_point)
                # Runsコマンドを付加する
                out_point = self._runs_command_appender.do_append(flow, out_point)
                # Activity Stepを付加する
                out_point = self._activity_data_dest_appender.do_append(flow, out_point, original_out_point)
                # 出力Point設定を元のPointからActivity_pointに変更する
                flow.close_o_port_by_point(original_out_point)
                out_point and flow.open_o_port(FlowPort(out_point.id, 'frame', out_point))

        # キャッシュ作成処理
        # サブフロー内ではキャッシュは作成しない
        # is_outかつis_cacheなPointにも対応できるよう
        # データデストを付加した後にキャッシュデータデストを付加すること
        for cache_point in [p for p in flow.points if p.makeCache]:
            # Cache Stepを付加する
            out_point = self._cache_data_dest_appender.do_append(flow, cache_point)
            # Runsコマンドを付加する
            out_point = self._runs_command_appender.do_append(flow, out_point)
            # Activity Stepを付加する
            out_point = self._activity_data_dest_appender.do_append(flow, out_point, cache_point)
            # Activity_pointを出力Pointに設定する
            out_point and flow.open_o_port(FlowPort(out_point.id, 'frame', out_point))


        return flow

    def _relay_o_port(self, flow, step, port):
        """
        フローの出力ポートを親フローに中継する
        """
        from kskp.core import Datum, Port
        from .point import Point
        from .tube import Tube

        # サブフローから中継された出力Portに紐づくPointを新規作成する
        src_tube = Tube(Port(port.label, 'mcmd'), step)
        new_out_point = Point(f'{step.id}_{port.label}', src_tube)
        flow.points.add(new_out_point)

        # 親フロー内で出力Portのlabelが重複する場合は、末尾に数字を付加する
        port_label = port.label
        while flow.has_o_port(port_label):
            port_label = Datum._increment_file_name(port_label)

        # サブフローの出力を親フローに繋げる
        o_port = FlowPort(port_label, 'mcmd', new_out_point)
        flow.open_o_port(o_port)

        # 作成した親フローの出力Portを返す
        return o_port

    def _pick_out_points(self, flow, outs, points, vis_ids):
        # /vizsなど、lastsが指定されている場合
        if len(vis_ids) > 0:
            return vis_ids 

        # データデストの場合はoutsはないのでlastsを返す
        if flow.is_datadst:
            return flow.lasts

        # 出力のないサブフローの入力ポイントを集める
        # (入力ポイントを出力のないサブフローに渡すため)
        ret = self._pick_points_of_no_output_subflow(points)
        # outsを集める
        ret.extend(outs.keys())
        return ret

    def _pick_points_of_no_output_subflow(self, points):
        """
        入力のみのRunnableの手前のpointをすべて取得する
        """
        ret = []
        for point in points:
            for dst_tube in point.dst_tubes:
                if dst_tube.is_null:
                    continue
                if dst_tube.step is not None and len(dst_tube.step.runnable.o_ports) == 0: 
                    ret.append(point.id)
        return ret

    def _pick_necessary_points(self, flow:FlowCommand, last_ids, is_vis):
        """
        実行するのに必要なpointを取得する
        """
        from .point import Points
        
        necessary_points = set()

        for id in last_ids:
            lasts_point = flow.points[id]
            # if len(flow.o_ports) == 0:
            if flow.is_main and is_vis:
                # 今は/vizs対象のdatumで終わるように、/vizs対象pointのdst_tubesをTube(None,None)にしている。（正しいんかな？）
                # lasts_point.dst_tubes = None
                # lasts_point.is_out = True
                if not flow.is_o_port(lasts_point):
                    flow.open_o_port(FlowPort(id, 'frame', lasts_point))

            # lasts_pointの上に繋がっているpointsを取得する
            necessary_points.update(self._search_necessary_point(flow, lasts_point))
            necessary_points.add(lasts_point)

        return Points(necessary_points)

    def _search_necessary_point(self, flow:FlowCommand, current_point):
        """
        /vizsするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、src_tubes.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のsrc_tubes.runnableをdst_tubes.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        necessary_points = set()
        # current_pointの上につながっているPointを探す
        for point in flow.points:
            for p_dst_tube in point.dst_tubes:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）

                # if p_dst_tube.step is current_point.src_runnable:
                #     necessary_points.add(point)
                #     if not (point.datum is not None or point.is_first):
                #         necessary_points.extend(self._search_necessary_point(points, point))

                if current_point.src_tubes.have_step(p_dst_tube.step):
                    necessary_points.add(point)
                    # pointの出力Tubeが無い、またはサブフローとして実行される場合は、入力Pointの場合、is_first=True
                    is_first = point.dst_tubes.is_null or (not flow.is_main and flow.is_i_port(point))
                    if point.datum is None and not is_first:
                        necessary_points.update(self._search_necessary_point(flow, point))

        return necessary_points

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
