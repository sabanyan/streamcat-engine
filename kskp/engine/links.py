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
        def __init__(self, flow_datum):
            self.flow_datum = flow_datum
            self.flow_uuid = flow_datum.uuid
            self.flow_label = flow_datum.label

            # 処理の開始時刻を取得する
            from datetime import datetime, timezone
            self.start_time = datetime.utcnow().replace(tzinfo=timezone.utc)
            self.runs_command_appender = RunsCommandAppender()
            self.activity_data_dest_appender = ActivityDataDestAppender(flow_datum.uuid)

            # {flow_uuid:, [(original_out_point:, points: ,port_label:)]}
            self.detadst_o_points = {}
            # データデストの'u'ポートは削除したので、以下の処理を削除する
            # self.detadst_u_points = {}
            # ポート名の接尾語(ポート名が被らないようにするため)
            self.port_suffix_num = 0

    def __init__(self, flow_datum, factory=None, vis_args={}, context=None):

        # フローJSONの書式の検証をする
        flow_datum.flow_data.valid_flow_json_or_raise()

        # self.factory = factory
        from kskp.store.factory import DatumFactory
        self.datum_factory = DatumFactory(flow_datum._session)

        self.label = flow_datum.label
        self.flow_data = flow_datum.flow_data
        self.is_root = False
        self.vis_ids = vis_args.keys()

        self.folder_data_dest_appender = FolderDataDestAppender(flow_datum, self.datum_factory)

        self.vis_data_dest_appender = VisDataDestAppender(flow_datum.uuid, vis_args)

        self.cache_data_dest_appender = CacheDataDestAppender(flow_datum, self.datum_factory)

        if context is None:
            self.context = FlowJsonLink.FlowLinkContext(flow_datum)
        else:
            self.context = context
            
    def resolve(self):
        # Flowを生成する
        from .flow import Flow
        flow = Flow(self.flow_data, self.is_root, self.context, self.datum_factory)

        self.context.detadst_o_points[flow.uuid] = []
        # データデストの'u'ポートは削除したので、以下の処理を削除する
        # self.context.detadst_u_points[flow.uuid] = []

        # Runs/Activity Commandへ渡すポートを中継する
        for p in flow.points:
            for p_dst_tube in p.dst_tubes:
                if p_dst_tube.runnable is None:
                    continue

                step = p_dst_tube.runnable
                # データデストの場合
                if step.is_datadst:
                    # oポートの中継
                    self._relay_o_port(flow, step, p)
                    # データデストの'u'ポートは削除したので、以下の処理を削除する
                    # # uポートの中継
                    # self._relay_u_port(flow, step, p)

                elif step.is_flow:
                    # データデスト以外のサブフローの場合
                    inner_flow = step.runnable
                    # フローが'o','u'の出力ポートを持っている場合
                    if inner_flow.uuid in self.context.detadst_o_points:
                        for i in range(len(self.context.detadst_o_points[inner_flow.uuid])):
                            original_out_point, out_point, port_label = self.context.detadst_o_points[inner_flow.uuid][i]
                            # oポートの中継
                            self._relay_o_port(flow, step, original_out_point, port_label)
                        # データデストの'u'ポートは削除したので、以下の処理を削除する
                        # for i in range(len(self.context.detadst_u_points[inner_flow.uuid])):
                        #     original_out_point, out_point, port_label = self.context.detadst_u_points[inner_flow.uuid][i]
                        #     # uポートの中継
                        #     self._relay_u_port(flow, step, original_out_point, port_label)

        # flowがもつPointを、実行に必要なものだけを絞り込んで取得している。

        # self.vis_idsには
        # メインフローの場合 ： /vizsするdatumのid群
        # サブフローの場合　 ： 親の実行に必要なlastのid群
        # が入っている。（はず）
        # /vizsしない場合はメインフローのlastのid群を使って絞り込みを行う。
        last_ids = self._pick_out_points(flow, flow.outs, flow.points)

        # 実行するのに必要なpointを取得する
        is_vis = len(self.vis_ids) > 0
        flow.points = self._pick_necessary_points(flow, last_ids, is_vis)

        if self.is_root:
            # lasts出力処理（メインフローの場合のみ）
            if is_vis:
                for first_out_point in [flow.select_point_by_id(pid) for pid in self.vis_ids]:
                    # Visualizerコマンドのための前処理コマンドを付加する
                    out_point = self.vis_data_dest_appender.do_append(flow, first_out_point)
                    # Runsコマンドを付加する
                    out_point = self.context.runs_command_appender.do_append(flow, out_point)
                    # Visualizeコマンドを付加する
                    visualizer_point = self.vis_data_dest_appender.do_append_after_runs(flow, out_point, first_out_point)
                    # Activity Stepを付加する
                    self.context.activity_data_dest_appender.do_append(flow, visualizer_point, first_out_point)

            else:

                for first_out_point in [point for point in flow.points if point.is_out]:
                    point_is_input_datadest = False

                    if first_out_point.src_runnable is not None and first_out_point.src_runnable.is_flow:
                        # ↓どちらかのFor文しか通らない、いまいちなコード
                        for detadst_o_points in self.context.detadst_o_points[flow.uuid]:
                            if detadst_o_points[1] == first_out_point:
                                # Runsコマンドを付加する
                                out_point = self.context.runs_command_appender.do_append(flow, first_out_point)
                                # Activity Stepを付加する
                                self.context.activity_data_dest_appender.do_append(flow, out_point, first_out_point)
                                point_is_input_datadest = True

                        # データデストの'u'ポートは削除したので、以下の処理を削除する
                        # for detadst_u_points in self.context.detadst_u_points[flow.uuid]:
                        #     if detadst_u_points[1] == first_out_point:
                        #         # Activity Stepを付加する
                        #         original_out_point = detadst_u_points[0]
                        #         self.context.activity_data_dest_appender.do_append(flow, first_out_point, original_out_point)
                        #         point_is_input_datadest = True

                    if not point_is_input_datadest:
                        # Saverコマンドを付加する
                        out_point = self.folder_data_dest_appender.do_append(flow, first_out_point, self.context.start_time)
                        # Runsコマンドを付加する
                        out_point = self.context.runs_command_appender.do_append(flow, out_point)
                        # Activity Stepを付加する
                        self.context.activity_data_dest_appender.do_append(flow, out_point, first_out_point)

        elif flow.is_datadst:
            # 1出力StepのCommandの出力Pointを取得する
            out_point = None
            # activity_point = None
            for p in flow.points:
                if p.src_runnable is None or \
                   p.src_runnable.is_flow or \
                   len(p.src_runnable.runnable.o_ports) != 1:
                    continue
                if p.src_port.label == 'o':
                    out_point = p
                # elif p.src_port.label =='u':
                #     activity_point = p

            # if out_point is None or activity_point is None:
            if out_point is None:
                raise Exception('saver output [o] is required !')
            
            # データデストの出力を親フローに繋げる
            o_port = Port('o', 'mcmd')
            # u_port = Port('u', 'frame')
            self._open_flow_out_port(flow, o_port, out_point)
            # self._open_flow_out_port(flow, u_port, activity_point)


        # キャッシュ作成処理
        # is_outかつis_cacheなPointにも対応できるよう
        # データデストを付加した後にキャッシュデータデストを付加すること
        for cache_point in [point for point in flow.points if point.is_cache]:
            # Cache Stepを付加する
            out_point = self.cache_data_dest_appender.do_append(flow, cache_point, self.context.start_time)
            # Activity Stepを付加する
            # self.context.activity_data_dest_appender.do_append(flow, activity_point, cache_point)

        return flow

    def _relay_o_port(self, flow, step, out_point, port_label=None):
        """
        フローの'o'ポートを親フローに中継する
        """
        # oポートの中継
        if port_label is None:
            port_label = 'o_' + str(self.context.port_suffix_num)
            self.context.port_suffix_num += 1
            # データデストからの入力ポート名は'o'固定
            src_tubes = [Tube(Port('o', 'frame'), step)]
        else:
            src_tubes = [Tube(Port(port_label, 'mcmd'), step)]

        # NOTE: stepとnew_pointのidが重複するが、フローエディタにロードされない上、保存もされないので問題にはならないだろう
        new_point = Point(step.id, src_tubes, None, [Tube(None, None)], is_in=False, is_out=True)
        flow.points.append(new_point)
        self.context.detadst_o_points[flow.uuid].append((out_point, new_point, port_label))

        # データデストの出力を親フローに繋げる)
        if not self.is_root:
            port = Port(port_label, 'mcmd')
            self._open_flow_out_port(flow, port, new_point)

    def _relay_u_port(self, flow, step, out_point, port_label=None):
        """
        フローの'u'ポートを親フローに中継する
        """
        # uポートの中継
        if port_label is None:
            port_label = 'u_' + str(self.context.port_suffix_num)
            self.context.port_suffix_num += 1
            # データデスト空の入力ポート名は'u'固定
            src_tubes = [Tube(Port('u', 'frame'), step)]
        else:
            src_tubes = [Tube(Port(port_label, 'frame'), step)]
        new_point = Point(step.id, src_tubes, None, [Tube(None, None)], is_in=False, is_out=True)
        flow.points.append(new_point)
        self.context.detadst_u_points[flow.uuid].append((out_point, new_point, port_label))

        # データデストの出力を親フローに繋げる)
        if not self.is_root:
            port = Port(port_label, 'frame')
            self._open_flow_out_port(flow, port, new_point)

    def _open_flow_out_port(self, flow, out_port, out_point):
        """
        指定するPointを出力PointとするPortを、フローに設定する
        """
        flow.o_ports.append(out_port)
        out_point.add_dst_tube(Tube(out_port, None))

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
                if dst_tube.is_None:
                    continue
                if dst_tube.runnable is not None and len(dst_tube.runnable.runnable.o_ports) == 0: 
                    ret.append(point.id)
        return ret

    def _pick_necessary_dst_ids(self, nodes, datum_ids):
        """
        指定したnodesの中で、指定したdatum_id群を取得するのに必要なdstsのid群を取得する
        """
        ids = []
        for datum_id in datum_ids:
            for node in nodes['nodes']:
                if self._is_outputting_datum_node(node, datum_id):
                    # 対象のnode
                    ids.extend(self._pick_necessary_dst_ids(nodes, list(node['srcs'].values())))
            ids.append(datum_id)
        return list(set(ids))

    def _is_outputting_datum_node(self, node, datum_id):
        """
        指定したdatumを出力するnodeかを調べる
        """
        return self._is_runnable_node(node) and datum_id in list(node['dsts'].values())

    def _pick_necessary_points(self, flow, last_ids, is_vis):
        """
        実行するのに必要なpointを取得する
        """
        necessary_points = []

        for id in last_ids:
            lasts_point = flow.select_point_by_id(id)
            # if len(flow.o_ports) == 0:
            if self.is_root and is_vis:
                # 今は/vizs対象のdatumで終わるように、/vizs対象pointのdst_tubesをTube(None,None)にしている。（正しいんかな？）
                # lasts_point.dst_tubes = [Tube(None, None)]
                lasts_point.is_out = True

            # lasts_pointの上に繋がっているpointsを取得する
            necessary_points.extend(self._search_necessary_point(flow.points, lasts_point))
            necessary_points.append(lasts_point)

        return list(set(necessary_points))

    def _search_necessary_point(self, points, current_point):
        """
        /vizsするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、src_tubes.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のsrc_tubes.runnableをdst_tubes.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        necessary_points = []
        # current_pointの上につながっているPointを探す
        for point in points:
            for p_dst_tube in point.dst_tubes:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）
                if p_dst_tube.runnable is current_point.src_runnable:
                    necessary_points.append(point)
                    if not (point.datum is not None or point.is_first):
                        necessary_points.extend(self._search_necessary_point(points, point))

        return necessary_points
