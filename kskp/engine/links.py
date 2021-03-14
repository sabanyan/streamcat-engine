from kskp.core import Port
from kskp.depo.std.commands import CommandLink
from .point import Point
from .step import Step
from .tube import Tube

class FolderDataSourcePrepender():
    def __init__(self, datum_factory):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self._datum_factory = datum_factory

    def do_prepend(self, flow, point, frame_uuid):
        frame = self._datum_factory.find_by_uuid(frame_uuid)
        folder_store = frame.find_parent()
        self._put_loader(frame_uuid, point, flow, folder_store)

    def _put_loader(self, frame_uuid, target_point, flow, store):
        """
        target_point(uuidが既にあるdatumのpoint)の前に
        LoaderStepとStorePointをくっつける
        Loaderは指定したstoreからデータを取ってくる
        """
        loader_step = self._make_loader_step(frame_uuid)
        point_id = target_point.id + '_loader_point'
        store_point = Point(point_id, [Tube(None, None)], store, [Tube(Port('folder', 'store'), loader_step)])
        target_point.src_tubes = [Tube(Port('o', 'frame'), loader_step)]
        flow.points.append(store_point)
        flow.substeps.append(loader_step)

    def _make_loader_step(self, node_uuid):
        """
        指定したuuidのデータを取ってくるLoaderStepを作成する
        """
        return Step('loader', CommandLink('loader').resolve(), {'uuid':node_uuid})

class FolderDataDestAppender():
    def __init__(self, flow_datum, datum_factory):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self.flow_datum = flow_datum
        self._datum_factory = datum_factory

    def do_append(self, flow, point, start_time):
        # フローの実行位置に実行結果フォルダ(フローの名前)が生成される
        folder_store = self.flow_datum.find_parent()
        saver = CommandLink('saver').resolve()
        # saver_step, saver_point, saver_point2 = self._put_saver(point, flow, folder_store, saver, start_time)
        saver_step, saver_point = self._put_saver(point, flow, folder_store, saver, start_time)
        # # ↓のappend()は↑の_put_saver()の中に記述したいが、そのようにするとtest_mainがパスしなくなる(T_T ??
        # flow.points.append(saver_point2)
        # return saver_point, saver_point2
        return saver_point

    def _put_saver(self, point, flow, store, saver, start_time):
        """
        指定したpointを保存する。保存先はstoreオブジェクトが指定する場所に。
        lastsなら最後に設置し、そうでないなら間に挟むように設置する
        """
        # 出力コマンドとそれが出すpointを追加

        # saverのargs設定
        # FlowUuidLinkならキャッシュ生成後にjsonを書き換える必要があるのでその情報を渡す。
        if self.flow_datum.uuid is None:
            args = {}
        else:
            args = {'flow_uuid':self.flow_datum.uuid, 'flow':self.flow_datum, 'result_folder':store, 'datum_id':point.id}
        # saverが作るframe及びcacheのlabelはここで設定できる
        args['flow_label'] = flow.label if flow.label is not None else ''
        # args['point_label'] = point.label if point.label is not None else point.id
        args['point'] = point
        args['start_time'] = start_time

        saver_step = self._make_step(args, saver)
        # store_point = Point(point.id + '_store_point', [Tube(None, None)], store, [Tube(Port('folder', 'store'), saver_step)])
        saver_point = Point(point.id + '_saver', [Tube(Port('o', 'mcmd'), saver_step)], None, [Tube(None, None)])
        # saver_point2 = Point(str(uuid.uuid4()), [Tube(Port('u', 'uuid'), saver_step)], None, [Tube(None, None)])

        self.switch_target(point, saver_step, saver_point)

        flow.substeps.append(saver_step)
        flow.points.append(saver_point)

        # return saver_step, saver_point, saver_point2
        return saver_step, saver_point

    def _make_step(self, args, cmd):
        """
        saverコマンドのstepを作成する
        """
        return Step(str(type(cmd)), cmd, args)

    # TODO: 解りづらい関数化
    # engineのリファクタリングで見直し予定
    def switch_target(self, point, saver_step, saver_point):
        if point.is_last:
            # lastsの場合は、pointをruns_stepに繋げるだけ
            point.dst_tubes = [Tube(Port('i', 'frame'), saver_step)]
        else:
            # lastsでない場合は、pointをと次のstepとruns_stepに繋げる(二股になる)
            point.dst_tubes.append(Tube(Port('i', 'frame'), saver_step))

class CacheDataDestAppender(FolderDataDestAppender):

    def do_append(self, flow, point, start_time):
        folder_store = self._datum_factory.load_cache_folder()
        saver = CommandLink('cachesaver').resolve()
        saver_step, saver_point = self._put_saver(point, flow, folder_store, saver, start_time)

        # flow.points.append(saver_point2)
        return saver_point

    def switch_target(self, point, saver_step, saver_point):
        if point.is_last:
            # lastsの場合は、pointをruns_stepに繋げるだけ
            point.dst_tubes = [Tube(Port('i', 'frame'), saver_step)]
        else:
            # lastsでない場合は、pointをと次のstepとruns_stepに繋げる(二股になる)
            tmp_tubes = point.dst_tubes
            point.dst_tubes = [Tube(Port('i', 'frame'), saver_step)]
            saver_point.dst_tubes = tmp_tubes
            
class VisDataDestAppender():
    def __init__(self, flow_uuid, vis_args={}):
        self.vis_args = vis_args

    def do_append(self, flow, point):
        """
        RowRangeコマンドを付加する
        ToListコマンドを付加する
        """
        if 'args' not in self.vis_args[point.id]:
            raise Exception(f'JSON属性({point.id})の下にargs属性を指定してください')

        # UTF-8への変換コマンドを作成する
        # (S_JISをwritelistコマンドに入力するとDockerが終了するので)
        convtoutf8 = CommandLink('convtoutf8').resolve()
        convtoutf8_step = self._make_step({'target_encoding':'utf-8','target_newline':'\n'}, convtoutf8)

        # RowRange Stepへの引数を作成する
        rowrange_args = self.vis_args[point.id]['args']
        # RowRange Stepを作成する
        rowrange_cmd = CommandLink('rowrange').resolve()
        rowrange_step = self._make_step(rowrange_args, rowrange_cmd)

        # MchkCsv Stepを作成する
        mchkcsv_cmd = CommandLink('mchkcsv').resolve()
        mchkcsv_step = self._make_step({}, mchkcsv_cmd)

        # ToList Stepを作成する 
        tolist_cmd = CommandLink('to_list').resolve()
        tolist_step = self._make_step({}, tolist_cmd)

        # ConvToUtf8 Stepを繋げる
        point_id = point.id + '_convtoutf8'
        convtoutf8_point = Point(point_id, [Tube(Port('o', 'frame'), convtoutf8_step)], None, [Tube(Port('i', 'frame'), rowrange_step)])
        # RowRange Stepを繋げる
        point_id = point.id + '_rowrange'
        rowrange_point = Point(point_id, [Tube(Port('o', 'frame'), rowrange_step)], None, [Tube(Port('i', 'frame'), mchkcsv_step)])
        # MchkCsv Stepを繋げる
        point_id = point.id + '_mchkcsv'
        mchkcsv_point = Point(point_id, [Tube(Port('o', 'frame'), mchkcsv_step)], None, [Tube(Port('i', 'frame'), tolist_step)])
        # ToListコマンドを繋げる
        point_id = point.id + '_tolist'
        tolist_point = Point(point_id, [Tube(Port('o', 'frame'), tolist_step)], None, [Tube(None, None)])

        self.switch_target(point, convtoutf8_step)

        flow.substeps.append(convtoutf8_step)
        flow.substeps.append(rowrange_step)
        flow.substeps.append(mchkcsv_step)
        flow.substeps.append(tolist_step)
        flow.points.append(convtoutf8_point)
        flow.points.append(rowrange_point)
        flow.points.append(mchkcsv_point)
        flow.points.append(tolist_point)

        return tolist_point

    def switch_target(self, point, step):
        if point.is_last:
            # lastsの場合は、pointをruns_stepに繋げるだけ
            point.dst_tubes = [Tube(Port('i', 'frame'), step)]
        else:
            # lastsでない場合は、pointをと次のstepとruns_stepに繋げる(二股になる)
            point.dst_tubes.append(Tube(Port('i', 'frame'), step))

    def do_append_after_runs(self, flow, point, original_out_point):
        visualizer_step, visualizer_point = self._put_visualizer(flow, point, original_out_point)
        return visualizer_point

    def _put_visualizer(self, flow, point, original_out_point):
        """
        Visualizerコマンドを付加する
        """
        if 'args' not in self.vis_args[original_out_point.id]:
            raise Exception(f'JSON属性({point.id})の下にargs属性を指定してください.')

        visualizer_args = self.vis_args[original_out_point.id]['args']
        if 'visualizer' not in visualizer_args:
            raise Exception('visualizer属性を指定してください')
        visualizer_cmd_name = visualizer_args['visualizer']
        visualizer_cmd = CommandLink(visualizer_cmd_name).resolve()
        visualizer_step = self._make_step(visualizer_args, visualizer_cmd)
        visualizer_point = Point(point.id + '_v', [Tube(Port('o', 'datum'), visualizer_step)], None, [Tube(None, None)])

        # VisPointにVisualizerフローを繋げる
        # point.id = str(uuid.uuid4())
        point.dst_tubes = [Tube(Port('i', 'frame'), visualizer_step)]

        flow.substeps.append(visualizer_step)
        flow.points.append(visualizer_point)

        return visualizer_step, visualizer_point

    def _make_step(self, args, cmd):
        """
        visualizerコマンドのstepを作成する
        """
        return Step(str(type(cmd)), cmd, args)

class ActivityDataDestAppender():
    def __init__(self, flow_uuid):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self.flow_uuid = flow_uuid

        # Activityコマンドを取得する
        activity_cmd = CommandLink('activity').resolve()
        # Activity Datumを作成する
        from kskp.store import Activity
        activity = Activity(None, None, 'activity', flow_uuid)
        # Activity Stepへの引数を作成する
        activity_args = {'activity': activity, 'points':{}}
        # Activity Stepを作成する
        self.activity_step = Step('activity', activity_cmd, activity_args, ex_acceptable=True)
        self.activity_uuid = activity.uuid
        # ポート名は0番から順に採番する
        self.next_port_no = 0
        # Flow.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = set()

    def do_append(self, flow, point, original_out_point):
        # Activity Stepのargsにpointを追加する
        port_label = str(self.next_port_no)
        self.activity_step.args['points'][port_label] = original_out_point

        # PointにActivity Stepを繋げる
        point.dst_tubes = [Tube(Port(port_label, 'datum'), self.activity_step)]

        # Activity_pointを作成し、これにActivity Stepを繋げる
        point_id = point.id + '_activity_' + port_label
        activity_point = Point(point_id,
                               [Tube(Port('o', 'activity'), self.activity_step)],
                               None,
                               [Tube(None, None)])

        # Stepのportsに追加する
        self.activity_step.i_ports.append(Port(port_label, 'datum'))

        if flow.uuid not in self._already_step_added:
            flow.substeps.append(self.activity_step)
            flow.points.append(activity_point)
            self._already_step_added.add(flow.uuid)

        self.next_port_no += 1

        return activity_point

class RunsCommandAppender():
    def __init__(self):
        # Runsコマンドを取得する
        runs_cmd = CommandLink('runs').resolve()
        # Runsステップを作成する
        # (CommandExceptionが入力された場合の処理をRunsCommand内で行うためex_acceptable=Trueとする)
        self.runs_step = Step('runs', runs_cmd, {}, ex_acceptable=True)
        # ポート名は0番から順に採番する
        self.next_port_no = 0
        # Flow.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = False

    def do_append(self, flow, point):
        # RunsCommandに繋げるPointを作成する
        port_label = str(self.next_port_no)
        point_id = point.id + '_runs'
        runs_point = Point(point_id, [Tube(Port(port_label, 'datum?'), self.runs_step)], None, [Tube(None, None)])

        # Stepのportsに追加する
        self.runs_step.i_ports.append(Port(port_label, 'mcmd'))
        self.runs_step.o_ports.append(Port(port_label, 'datum?'))

        # ここでRunsCommandを繋げる
        point.dst_tubes = [Tube(Port(port_label, 'mcmd'), self.runs_step)]

        if not self._already_step_added:
            flow.substeps.append(self.runs_step)
            self._already_step_added = True
        flow.points.append(runs_point)

        self.next_port_no += 1

        return runs_point


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
