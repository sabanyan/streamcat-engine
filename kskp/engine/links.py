from kskp.core import Port
from .point import Point
from .tube import Tube
from .appenders import (
    FolderDataDestAppender,
    CacheDataDestAppender,
    VisDataDestAppender,
    ActivityDataDestAppender,
    RunsCommandAppender
)

class FlowJsonLink:
    """
    フローへのリンク
    """

    class FlowLinkContext():
        """
        FlowJsonLinkを再帰的に下降して呼び出すときに参照する共通の格納場所
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

            # {flow : [port_label]}
            self.relay_ports = {}

            # ポート名の接尾語(ポート名が被らないようにするため)
            self.port_suffix_num = 0

    def __init__(self, flow_datum, factory=None, vis_args={}, context=None, is_root=True):
        # フローJSONの書式の検証をする
        flow_datum.flow_data.valid_flow_json_or_raise()

        # self.factory = factory
        from kskp.store.factory import DatumFactory
        self.datum_factory = DatumFactory(flow_datum._session)

        self.label = flow_datum.label
        self.flow_data = flow_datum.flow_data
        self.is_root = is_root
        self.vis_ids = vis_args.keys()

        if is_root:
            self.runs_command_appender = RunsCommandAppender()
            self.activity_data_dest_appender = ActivityDataDestAppender(flow_datum.uuid)

        if context is None:
            self.context = FlowJsonLink.FlowLinkContext(flow_datum, self.activity_data_dest_appender.activity_uuid)
        else:
            self.context = context

        self.folder_data_dest_appender = FolderDataDestAppender(flow_datum, self.datum_factory, self.context.start_time)
        self.vis_data_dest_appender = VisDataDestAppender(flow_datum.uuid, vis_args)
        self.cache_data_dest_appender = CacheDataDestAppender(flow_datum, self.datum_factory, self.context.start_time)
            
    def resolve(self):
        # Flowを生成する
        from kskp.depo.std.commands.scmd.script import SaverCommand
        from .flow import Flow
        flow = Flow(self.flow_data, self.is_root, self.context, self.datum_factory)

        self.context.relay_ports[flow] = []

        # SaverCommandの出力PointをRootフローに中継する
        # TODO : ここの処理、再設計の必要あり！！
        for p in flow.points:

            # Rootフローの出力Pointから辿れないコマンドは実行されない
            # その為、SaverCommandはその副作用(出力処理)を実行する為に、そのコマンドの出力Pointをフローの出力Pointに設定する
            # TODO: SaverCommand以外に副作用を持つコマンドも同じ設定をする必要があるだろう
            if not p.is_out:
                src_tube = p.src_tubes.find_command_tube()
                if src_tube is not None:
                    step = src_tube.step
                    # SaverCommandとそのサブクラスのコマンドは、その出力ポイントをフローの出力Pointに設定する
                    if isinstance(step.runnable, SaverCommand):
                        o_port = Port(p.id, 'mcmd')
                        flow.open_o_port(o_port, p)
                        # 
                        self.context.relay_ports[flow].append(o_port.label)

            for dst_tube in p.dst_tubes:
                step = dst_tube.step
                if step is None:
                    continue

                # コマンドにはポートを動的に追加できないため、コマンドがデータデストの場合は、そのコマンドは実行できない
                if not step.is_flow:
                    continue

                # # フローがデータデストでない場合は、ポート中継の処理対象ではない？
                # if not step.is_datadst:
                #     continue

                # フローが'o','u'の出力ポートを持っている場合
                for port_label in self.context.relay_ports[step.runnable]:
                    # oポートの中継
                    self._relay_o_port(flow, step, port_label)
                    # 
                    self.context.relay_ports[flow].append(port_label)


        # 
        # flowがもつPointを、実行に必要なものだけを絞り込んで取得している。
        # 
        # self.vis_idsには
        # メインフローの場合 ： /vizsするdatumのid群
        # サブフローの場合　 ： 親の実行に必要なlastのid群
        # が入っている。（はず）
        # /vizsしない場合はメインフローのlastのid群を使って絞り込みを行う。
        last_ids = self._pick_out_points(flow, flow.outs, flow.points)

        # 実行するのに必要なpointを取得する
        is_vis = len(self.vis_ids) > 0
        flow.points = self._pick_necessary_points(flow, last_ids, is_vis)

        if flow.is_root:
            # lasts出力処理（メインフローの場合のみ）
            if is_vis:
                for original_out_point in [flow.points[pid] for pid in self.vis_ids]:
                    # Visualizerコマンドのための前処理コマンドを付加する
                    out_point = self.vis_data_dest_appender.do_append(flow, original_out_point)
                    # Runsコマンドを付加する
                    out_point = self.runs_command_appender.do_append(flow, out_point)
                    # Visualizeコマンドを付加する
                    out_point = self.vis_data_dest_appender.do_append_after_runs(flow, out_point, original_out_point)
                    # Activity Stepを付加する
                    out_point = self.activity_data_dest_appender.do_append(flow, out_point, original_out_point)
                    # 出力Point設定を元のPointからActivity_pointに変更する
                    original_out_point.is_out = False
                    out_point.is_out = True
            else:

                for original_out_point in [p for p in flow.points if p.is_out]:
                    src_tube = original_out_point.src_tubes.find_command_tube()
                    if src_tube is not None and src_tube.step.is_datadst:
                        # フローの出力Pointが、データデストの出力Pointでもある場合、そのPointにSaverコマンドを付加しない
                        out_point = original_out_point
                    else:
                        # Saverコマンドを付加する
                        out_point = self.folder_data_dest_appender.do_append(flow, original_out_point)
                    # Runsコマンドを付加する
                    out_point = self.runs_command_appender.do_append(flow, out_point)
                    # Activity Stepを付加する
                    out_point = self.activity_data_dest_appender.do_append(flow, out_point, original_out_point)
                    # 出力Point設定を元のPointからActivity_pointに変更する
                    original_out_point.is_out = False
                    out_point.is_out = True


            # キャッシュ作成処理
            # サブフロー内ではキャッシュは作成しない
            # is_outかつis_cacheなPointにも対応できるよう
            # データデストを付加した後にキャッシュデータデストを付加すること
            for cache_point in [p for p in flow.points if p.is_cache]:
                # Cache Stepを付加する
                out_point = self.cache_data_dest_appender.do_append(flow, cache_point)
                # Runsコマンドを付加する
                out_point = self.runs_command_appender.do_append(flow, out_point)
                # Activity Stepを付加する
                out_point = self.activity_data_dest_appender.do_append(flow, out_point, cache_point)
                # Activity_pointを出力Pointに設定する
                out_point.is_out = True

        return flow

    def _relay_o_port(self, flow, step, port_label):
        """
        フローの出力ポートを親フローに中継する
        """
        # 出力ポートの中継
        src_tube = Tube(Port(port_label, 'mcmd'), step)

        # NOTE: 同じフロー内であれば、port_labelは重複しないだろう
        new_out_point = Point(f'{step.id}_{port_label}', src_tube, is_out=True)
        flow.points.add(new_out_point)

        if flow.is_root:
            # 親フローでは、Runsコマンドの出力がその親フローの出力ポイントに設定され、これがフロー探索の開始ポイントになる
            # そのため、ここでデータデストの出力を、出力ポイントに設定する必要はない
            pass
        else:
            # データデストの出力を親フローに繋げる
            o_port = Port(port_label, 'mcmd')
            flow.open_o_port(o_port, new_out_point)


    def _pick_out_points(self, flow, outs, points):
        # /vizsなど、lastsが指定されている場合
        if len(self.vis_ids) > 0:
            return self.vis_ids 

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

    def _pick_necessary_points(self, flow, last_ids, is_vis):
        """
        実行するのに必要なpointを取得する
        """
        from .point import Points
        
        necessary_points = set()

        for id in last_ids:
            lasts_point = flow.points[id]
            # if len(flow.o_ports) == 0:
            if flow.is_root and is_vis:
                # 今は/vizs対象のdatumで終わるように、/vizs対象pointのdst_tubesをTube(None,None)にしている。（正しいんかな？）
                # lasts_point.dst_tubes = None
                lasts_point.is_out = True

            # lasts_pointの上に繋がっているpointsを取得する
            necessary_points.update(self._search_necessary_point(flow.points, lasts_point))
            necessary_points.add(lasts_point)

        return Points(necessary_points)

    def _search_necessary_point(self, points, current_point):
        """
        /vizsするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、src_tubes.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のsrc_tubes.runnableをdst_tubes.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        necessary_points = set()
        # current_pointの上につながっているPointを探す
        for point in points:
            for p_dst_tube in point.dst_tubes:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）

                # if p_dst_tube.step is current_point.src_runnable:
                #     necessary_points.add(point)
                #     if not (point.datum is not None or point.is_first):
                #         necessary_points.extend(self._search_necessary_point(points, point))

                if current_point.src_tubes.have_step(p_dst_tube.step):
                    necessary_points.add(point)
                    # pointの出力Tubeが無い、またはサブフローとして実行される場合は、入力Pointの場合、is_first=True
                    is_first = point.dst_tubes.is_null or (not self.is_root and point.is_in)
                    if point.datum is None and not is_first:
                        necessary_points.update(self._search_necessary_point(points, point))

        return necessary_points
