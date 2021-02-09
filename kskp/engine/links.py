import uuid

from kskp.core import Port
from kskp.depo.std.commands import CommandLink, SCommand
from .core import Step, Point, Tube

class FolderDataSourcePrepender():
    def __init__(self, factory):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self._factory = factory

    def do_prepend(self, f, point, frame_uuid):
        frame = self._factory.data.find_by_uuid(frame_uuid)
        folder_store = frame.find_parent()
        self._put_loader(frame_uuid, point, f, folder_store)

    def _put_loader(self, frame_uuid, target_point, f, store):
        """
        target_point(uuidが既にあるdatumのpoint)の前に
        LoaderStepとStorePointをくっつける
        Loaderは指定したstoreからデータを取ってくる
        """
        loader_step = self._make_loader_step(frame_uuid)
        store_point = Point(frame_uuid + '_loader_point', [Tube(None, None)], store, [Tube(Port('folder', 'store'), loader_step)])
        target_point.origin = [Tube(Port('o', 'frame'), loader_step)]
        f.points.append(store_point)
        f.substeps.append(loader_step)

    def _make_loader_step(self, node_uuid):
        """
        指定したuuidのデータを取ってくるLoaderStepを作成する
        """
        return Step(str(uuid.uuid4()), CommandLink('loader').resolve(), {'uuid':node_uuid})

class FolderDataDestAppender():
    def __init__(self, flow, factory):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self.flow = flow
        self._factory = factory

    def do_append(self, f, point, start_time):
        # フローの実行位置に実行結果フォルダ(フローの名前)が生成される
        folder_store = self.flow.find_parent()
        saver = CommandLink('saver').resolve()
        # saver_step, saver_point, saver_point2 = self._put_saver(point, f, folder_store, saver, start_time)
        saver_step, saver_point = self._put_saver(point, f, folder_store, saver, start_time)
        # # ↓のappend()は↑の_put_saver()の中に記述したいが、そのようにするとtest_mainがパスしなくなる(T_T ??
        # f.points.append(saver_point2)
        # return saver_point, saver_point2
        return saver_point

    def _put_saver(self, point, f, store, saver, start_time):
        """
        指定したpointを保存する。保存先はstoreオブジェクトが指定する場所に。
        lastsなら最後に設置し、そうでないなら間に挟むように設置する
        """
        # 出力コマンドとそれが出すpointを追加

        # saverのargs設定
        # FlowUuidLinkならキャッシュ生成後にjsonを書き換える必要があるのでその情報を渡す。
        args = {'flow_uuid':self.flow.uuid, 'flow':self.flow, 'datum_id':point.id} if self.flow.uuid is not None else {}
        # saverが作るframe及びcacheのlabelはここで設定できる
        args['flow_label'] = f.label if f.label is not None else ''
        # args['point_label'] = point.label if point.label is not None else point.id
        args['point'] = point
        args['start_time'] = start_time

        saver_step = self._make_step(args, saver)
        store_point = Point(point.id + '_store_point', [Tube(None, None)], store, [Tube(Port('folder', 'store'), saver_step)])
        saver_point = Point(point.id + '_saver', [Tube(Port('o', 'mcmd'), saver_step)], None, [Tube(None, None)])
        # saver_point2 = Point(str(uuid.uuid4()), [Tube(Port('u', 'uuid'), saver_step)], None, [Tube(None, None)])

        self.switch_target(point, saver_step, saver_point)

        f.substeps.append(saver_step)
        f.points.extend([saver_point, store_point])

        # return saver_step, saver_point, saver_point2
        return saver_step, saver_point

    def _make_step(self, args, cmd):
        """
        saverコマンドのstepを作成する
        """
        return Step(str(uuid.uuid4()) + str(type(cmd)), cmd, args)

    # TODO: 解りづらい関数化
    # engineのリファクタリングで見直し予定
    def switch_target(self, point, saver_step, saver_point):
        if point.is_last:
            # lastsの場合は、pointをruns_stepに繋げるだけ
            point.target = [Tube(Port('i', 'frame'), saver_step)]
        else:
            # lastsでない場合は、pointをと次のstepとruns_stepに繋げる(二股になる)
            point.target.append(Tube(Port('i', 'frame'), saver_step))


class CacheDataDestAppender(FolderDataDestAppender):

    def do_append(self, f, point, start_time):
        folder_store = self._factory.data.load_cache_folder()
        saver = CommandLink('cachesaver').resolve()
        saver_step, saver_point = self._put_saver(point, f, folder_store, saver, start_time)

        # f.points.append(saver_point2)
        return saver_point

    def switch_target(self, point, saver_step, saver_point):
        if point.is_last:
            # lastsの場合は、pointをruns_stepに繋げるだけ
            point.target = [Tube(Port('i', 'frame'), saver_step)]
        else:
            # lastsでない場合は、pointをと次のstepとruns_stepに繋げる(二股になる)
            tmp_targets = point.target
            point.target = [Tube(Port('i', 'frame'), saver_step)]
            saver_point.target = tmp_targets
            

class VisDataDestAppender():
    def __init__(self, flow_uuid, vis_args={}):
        self.vis_args = vis_args

    def do_append(self, f, point):
        """
        RowRangeコマンドを付加する
        ToListコマンドを付加する
        """
        if 'args' not in self.vis_args[point.id]:
            raise Exception(f'JSON属性({point.id})の下にargs属性を指定してください')

        # UTF-8への変換コマンドを作成する
        # (S_JISをwritelistコマンドに入力するとDockerが終了するので)
        convtoutf8 = CommandLink('convtoutf8').resolve()
        convtoutf8_step = self._make_step({}, convtoutf8)

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

        f.substeps.append(convtoutf8_step)
        f.substeps.append(rowrange_step)
        f.substeps.append(mchkcsv_step)
        f.substeps.append(tolist_step)
        f.points.append(convtoutf8_point)
        f.points.append(rowrange_point)
        f.points.append(mchkcsv_point)
        f.points.append(tolist_point)

        return tolist_point

    def switch_target(self, point, step):
        if point.is_last:
            # lastsの場合は、pointをruns_stepに繋げるだけ
            point.target = [Tube(Port('i', 'frame'), step)]
        else:
            # lastsでない場合は、pointをと次のstepとruns_stepに繋げる(二股になる)
            point.target.append(Tube(Port('i', 'frame'), step))

    def do_append_after_runs(self, f, point, original_out_point):
        visualizer_step, visualizer_point = self._put_visualizer(f, point, original_out_point)
        return visualizer_point

    def _put_visualizer(self, f, point, original_out_point):
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
        point.target = [Tube(Port('i', 'frame'), visualizer_step)]

        f.substeps.append(visualizer_step)
        f.points.append(visualizer_point)

        return visualizer_step, visualizer_point

    def _make_step(self, args, cmd):
        """
        visualizerコマンドのstepを作成する
        """
        return Step(str(uuid.uuid4()), cmd, args)

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
        self.activity_step = Step(str(uuid.uuid4()) + '_activity', activity_cmd, activity_args, ex_acceptable=True)
        self.activity_uuid = activity.uuid
        # ポート名は0番から順に採番する
        self.next_port_no = 0
        # Flow.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = set()

    def do_append(self, f, point, original_out_point):
        # Activity Stepのargsにpointを追加する
        port_name = str(self.next_port_no)
        self.activity_step.args['points'][port_name] = original_out_point

        # PointにActivity Stepを繋げる
        point.target = [Tube(Port(port_name, 'datum'), self.activity_step)]

        # Activity_pointを作成し、これにActivity Stepを繋げる
        point_id = point.id + '_activity_' + port_name
        activity_point = Point(point_id,
                               [Tube(Port('o', 'activity'), self.activity_step)],
                               None,
                               [Tube(None, None)])

        # Stepのportsに追加する
        self.activity_step.i_ports.append(Port(port_name, 'datum'))

        if f.uuid not in self._already_step_added:
            f.substeps.append(self.activity_step)
            f.points.append(activity_point)
            self._already_step_added.add(f.uuid)

        self.next_port_no += 1

        return activity_point

class RunsCommandAppender():
    def __init__(self):
        # Runsコマンドを取得する
        runs_cmd = CommandLink('runs').resolve()
        # Runsステップを作成する
        # (CommandExceptionが入力された場合の処理をRunsCommand内で行うためex_acceptable=Trueとする)
        self.runs_step = Step(str(uuid.uuid4()) + '_runs', runs_cmd, {}, ex_acceptable=True)
        # ポート名は0番から順に採番する
        self.next_port_no = 0
        # Flow.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = False

    def do_append(self, f, point):
        # RunsCommandに繋げるPointを作成する
        port_name = str(self.next_port_no)
        point_id = point.id + '_runs'
        runs_point = Point(point_id, [Tube(Port(port_name, 'datum?'), self.runs_step)], None, [Tube(None, None)])

        # Stepのportsに追加する
        self.runs_step.i_ports.append(Port(port_name, 'mcmd'))
        self.runs_step.o_ports.append(Port(port_name, 'datum?'))

        # ここでRunsCommandを繋げる
        point.target = [Tube(Port(port_name, 'mcmd'), self.runs_step)]

        if not self._already_step_added:
            f.substeps.append(self.runs_step)
            self._already_step_added = True
        f.points.append(runs_point)

        self.next_port_no += 1

        return runs_point

class FlowLinkContext():
    """
    FlowJsonLinkを再帰的に下降して呼び出すときに参照する共通の格納場所
    """
    def __init__(self, flow):
        self.flow = flow
        self.flow_uuid = flow.uuid
        self.flow_label = flow.label

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        self.start_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.runs_command_appender = RunsCommandAppender()
        self.activity_data_dest_appender = ActivityDataDestAppender(flow.uuid)

        # {flow_uuid:, [(original_out_point:, points: ,port_name:)]}
        self.detadst_o_points = {}
        # データデストの'u'ポートは削除したので、以下の処理を削除する
        # self.detadst_u_points = {}
        # ポート名の接尾語(ポート名が被らないようにするため)
        self.port_suffix_num = 0

class FlowJsonLink:
    """
    フローへのリンク
    """
    def __init__(self, flow, factory, vis_args={}, context=None):
        self.factory = factory

        self.label = flow.label
        self.flow_data = flow.flow_data
        self.is_root = False
        self.vis_ids = vis_args.keys()

        self.folder_data_source_prepender = FolderDataSourcePrepender(factory)

        self.folder_data_dest_appender = FolderDataDestAppender(flow, factory)

        self.vis_data_dest_appender = VisDataDestAppender(flow.uuid, vis_args)

        self.cache_data_dest_appender = CacheDataDestAppender(flow, factory)

        if context is None:
            self.context = FlowLinkContext(flow)
        else:
            self.context = context
            
    def _node2link(self, node):
        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            # ret = FlowUuidLink(node['uuid'], {}, self.context)
            from kskp.store.auth import NotAuthorizedException
            try:
                flow = self.factory.data.find_by_uuid(node['uuid'])
                ret = FlowJsonLink(flow, self.factory, {}, self.context)
            except NotAuthorizedException:
                raise NotAuthorizedException(f'共有フロー({node.get("id")})の参照権限がありません')

            # # かなりの力技・・・。
            # # 実行を行う場合、サブフロー内で余分な処理が走らないように
            # # 親フローが子フロー（使用するサブフロー）に、このoutputが必要だということを教える。

            # # メインフローで/vizs時、どのdstsを通るかを求める
            # dst_ids = self._pick_necessary_dst_ids(self.flow_data, self.vis_ids)
            # # メインフローで使われるdstsの中に、対象のnode（サブフロー）が出力するものがあれば教えてあげる
            # if len(dst_ids) > 0:
            #     ret.last_ids = [port for port, datum_id in node['dsts'].items() for dst_id in dst_ids if datum_id == dst_id]

        return ret

    def resolve(self):
        f = self._make_flow(self.label, self.flow_data)

        self.context.detadst_o_points[f.uuid] = []
        # データデストの'u'ポートは削除したので、以下の処理を削除する
        # self.context.detadst_u_points[f.uuid] = []

        # Runs/Activity Commandへ渡すポートを中継する
        for p in f.points:
            for p_target in p.target:
                if p_target.runnable is None:
                    continue

                step = p_target.runnable
                # データデストの場合
                if step.is_datadst:
                    # oポートの中継
                    self._relay_o_port(f, step, p)
                    # データデストの'u'ポートは削除したので、以下の処理を削除する
                    # # uポートの中継
                    # self._relay_u_port(f, step, p)

                elif step.is_flow:
                    # データデスト以外のサブフローの場合
                    inner_flow = step.runnable
                    # フローが'o','u'の出力ポートを持っている場合
                    if inner_flow.uuid in self.context.detadst_o_points:
                        for i in range(len(self.context.detadst_o_points[inner_flow.uuid])):
                            original_out_point, out_point, port_name = self.context.detadst_o_points[inner_flow.uuid][i]
                            # oポートの中継
                            self._relay_o_port(f, step, original_out_point, port_name)
                        # データデストの'u'ポートは削除したので、以下の処理を削除する
                        # for i in range(len(self.context.detadst_u_points[inner_flow.uuid])):
                        #     original_out_point, out_point, port_name = self.context.detadst_u_points[inner_flow.uuid][i]
                        #     # uポートの中継
                        #     self._relay_u_port(f, step, original_out_point, port_name)

        # flowがもつPointを、実行に必要なものだけを絞り込んで取得している。

        # self.vis_idsには
        # メインフローの場合 ： /vizsするdatumのid群
        # サブフローの場合　 ： 親の実行に必要なlastのid群
        # が入っている。（はず）
        # /vizsしない場合はメインフローのlastのid群を使って絞り込みを行う。
        last_ids = self._pick_out_points(f, f.outs, f.points)

        # 実行するのに必要なpointを取得する
        is_vis = len(self.vis_ids) > 0
        f.points = self._pick_necessary_points(f, last_ids, is_vis)

        if self.is_root:
            # lasts出力処理（メインフローの場合のみ）
            if is_vis:
                for first_out_point in [f.select_point_by_id(pid) for pid in self.vis_ids]:
                    # Visualizerコマンドのための前処理コマンドを付加する
                    out_point = self.vis_data_dest_appender.do_append(f, first_out_point)
                    # Runsコマンドを付加する
                    out_point = self.context.runs_command_appender.do_append(f, out_point)
                    # Visualizeコマンドを付加する
                    visualizer_point = self.vis_data_dest_appender.do_append_after_runs(f, out_point, first_out_point)
                    # Activity Stepを付加する
                    self.context.activity_data_dest_appender.do_append(f, visualizer_point, first_out_point)

            else:

                for first_out_point in [point for point in f.points if point.is_out]:
                    point_is_input_datadest = False

                    if first_out_point.o_runnable is not None and first_out_point.o_runnable.is_flow:
                        # ↓どちらかのFor文しか通らない、いまいちなコード
                        for detadst_o_points in self.context.detadst_o_points[f.uuid]:
                            if detadst_o_points[1] == first_out_point:
                                # Runsコマンドを付加する
                                out_point = self.context.runs_command_appender.do_append(f, first_out_point)
                                # Activity Stepを付加する
                                self.context.activity_data_dest_appender.do_append(f, out_point, first_out_point)
                                point_is_input_datadest = True

                        # データデストの'u'ポートは削除したので、以下の処理を削除する
                        # for detadst_u_points in self.context.detadst_u_points[f.uuid]:
                        #     if detadst_u_points[1] == first_out_point:
                        #         # Activity Stepを付加する
                        #         original_out_point = detadst_u_points[0]
                        #         self.context.activity_data_dest_appender.do_append(f, first_out_point, original_out_point)
                        #         point_is_input_datadest = True

                    if not point_is_input_datadest:
                        # Saverコマンドを付加する
                        out_point = self.folder_data_dest_appender.do_append(f, first_out_point, self.context.start_time)
                        # Runsコマンドを付加する
                        out_point = self.context.runs_command_appender.do_append(f, out_point)
                        # Activity Stepを付加する
                        self.context.activity_data_dest_appender.do_append(f, out_point, first_out_point)

        elif f.is_datadst:
            # 1出力StepのCommandの出力Pointを取得する
            out_point = None
            # activity_point = None
            for p in f.points:
                if p.o_runnable is None or \
                   p.o_runnable.is_flow or \
                   len(p.o_runnable.runnable.o_ports) != 1:
                    continue
                if p.o_port.name == 'o':
                    out_point = p
                # elif p.o_port.name =='u':
                #     activity_point = p

            # if out_point is None or activity_point is None:
            if out_point is None:
                raise Exception('saver output [o] is required !')
            
            # データデストの出力を親フローに繋げる
            o_port = Port('o', 'mcmd')
            # u_port = Port('u', 'frame')
            self._open_flow_out_port(f, o_port, out_point)
            # self._open_flow_out_port(f, u_port, activity_point)


        # キャッシュ作成処理
        # is_outかつis_cacheなPointにも対応できるよう
        # データデストを付加した後にキャッシュデータデストを付加すること
        for cache_point in [point for point in f.points if point.is_cache]:
            # Cache Stepを付加する
            out_point = self.cache_data_dest_appender.do_append(f, cache_point, self.context.start_time)
            # Activity Stepを付加する
            # self.context.activity_data_dest_appender.do_append(f, activity_point, cache_point)

        return f

    def _relay_o_port(self, flow, step, out_point, port_name=None):
        """
        フローの'o'ポートを親フローに中継する
        """
        # oポートの中継
        if port_name is None:
            port_name = 'o_' + str(self.context.port_suffix_num)
            self.context.port_suffix_num += 1
            # データデストからの入力ポート名は'o'固定
            origin_tubes = [Tube(Port('o', 'frame'), step)]
        else:
            origin_tubes = [Tube(Port(port_name, 'mcmd'), step)]

        # NOTE: stepとnew_pointのidが重複するが、フローエディタにロードされない上、保存もされないので問題にはならないだろう
        new_point = self._insert_point(flow, step.id, origin=origin_tubes, target=[Tube(None, None)], is_in=False, is_out=True)
        self.context.detadst_o_points[flow.uuid].append((out_point, new_point, port_name))

        # データデストの出力を親フローに繋げる)
        if not self.is_root:
            port = Port(port_name, 'mcmd')
            self._open_flow_out_port(flow, port, new_point)

    def _relay_u_port(self, flow, step, out_point, port_name=None):
        """
        フローの'u'ポートを親フローに中継する
        """
        # uポートの中継
        if port_name is None:
            port_name = 'u_' + str(self.context.port_suffix_num)
            self.context.port_suffix_num += 1
            # データデスト空の入力ポート名は'u'固定
            origin_tubes = [Tube(Port('u', 'frame'), step)]
        else:
            origin_tubes = [Tube(Port(port_name, 'frame'), step)]
        new_point = self._insert_point(flow, step.id, origin=origin_tubes, target=[Tube(None, None)], is_in=False, is_out=True)
        self.context.detadst_u_points[flow.uuid].append((out_point, new_point, port_name))

        # データデストの出力を親フローに繋げる)
        if not self.is_root:
            port = Port(port_name, 'frame')
            self._open_flow_out_port(flow, port, new_point)

    def _open_flow_out_port(self, flow, out_point, out_port):
        """
        指定するPointを出力PointとするPortを、フローに設定する
        """
        flow.o_ports.append(out_point)
        self._update_point(point=out_port, target=Tube(out_point, None))

    def _pick_out_points(self, f, outs, points):
        # /vizsなど、lastsが指定されている場合
        if len(self.vis_ids) > 0:
            return self.vis_ids 

        # データデストの場合はoutsはないのでlastsを返す
        if f.is_datadst:
            return f.lasts

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
            for t_tube in point.target:
                if t_tube.is_None:
                    continue
                if t_tube.runnable is not None and len(t_tube.runnable.runnable.o_ports) == 0: 
                    ret.append(point.id)
        return ret

    def _make_flow(self, label, flow_data):
        from .core import Flow
        flow = Flow(label)

        # portを読む
        ports = flow_data.ports
        flow.i_ports = self._parse_ports(ports[0])
        flow.o_ports = self._parse_ports(ports[1])

        # flowを更新する
        if flow_data.has_nodes:
            # フローの参照権限がなくても実行権限があれば、フローJSONを参照する必要がある
            # そのため、use_exec_auth=Trueを指定する
            self._update_flow_by_runnable(flow, flow_data.get_nodes(use_exec_auth=True))
            self._update_flow_by_other_than_runnable(flow, flow_data.get_nodes(use_exec_auth=True))

        return flow

    def _parse_ports(self, port_dict_list):
        """ dictのリストからportインスタンスのリストを作る """
        return [Port(p['nodeId'], p['type']) for p in port_dict_list]

    def _update_flow_by_runnable(self, flow, nodes):
        """
        指定したnodesの中にある、runnableのnodeを使ってFlowオブジェクトの属性を更新する
        """
        # まず、runnableを集める
        for node in nodes:
            if not self._is_runnable_node(node):
                continue

            # CommandまたはFlowを取得する
            cmd_or_flow = self._node2link(node).resolve()
            
            if isinstance(cmd_or_flow, SCommand):
                # SCommand共通引数を作成する
                args = {'flow_uuid'    : self.context.flow_uuid,
                        'flow_label'   : self.context.flow_label,
                        'result_folder': self.context.flow.find_parent(),
                        'start_time'   : self.context.start_time,
                        'activity_uuid': self.context.activity_data_dest_appender.activity_uuid}
                # 引数の設定が重複した場合は、コマンドの個別引数の方を優先する
                args.update(node['args'])
            else:
                # MCommandに不要な引数を設定するとエラーになる
                args = node['args']

            srcs = node['srcs']
            dsts = node['dsts']

            i_ports = self._replace_multi_inputs(cmd_or_flow.i_ports, srcs)
            o_ports = self._replace_multi_inputs(cmd_or_flow.o_ports, dsts)

            # runnableのインスタンス化を行う
            step = Step(node['id'], cmd_or_flow, args, i_ports=i_ports, o_ports=o_ports)
            flow.substeps.append(step)

            # srcとdstからpointを作る
            for s_port_name, s_node_id in srcs.items():
                # 可変長引数で入力PointがNoneになる場合に備える
                if s_node_id is None:
                    raise Exception(f"コマンド({node['label']})の入力({s_port_name})が指定されていません")

                # 定義上に存在しないポート名がsrcsに存在していないかの確認
                src_port = self._get_port_by_name(i_ports, s_port_name)
                if src_port is None:
                    raise Exception(f"指定しているport名({s_port_name})がrunnable {node['id']}の定義しているポート群({i_ports})に存在しません")

                # out/inポートフラグの取得
                is_in = self._is_in_point(flow, s_node_id)
                is_out = self._is_out_point(flow, s_node_id)

                # pointを作成する（作成対象がすでにあれば更新する）
                src_point = self._upsert_point(flow=flow, point_id=s_node_id, is_in=is_in, is_out=is_out,
                                              origin=Tube(None, None), target=Tube(src_port, step))

                # 上記src_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにoriginを置き換える
                [self._update_point(point=src_point, origin=Tube(i_port, None))
                 for i_port in flow.i_ports if i_port.name == src_point.id]

            for d_port_name, d_node_id in dsts.items():
                if d_node_id is None:
                    raise Exception(f"コマンド({node['label']})の出力({d_port_name})が指定されていません")

                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self._get_port_by_name(step.runnable.o_ports, d_port_name)
                if dst_port is None:
                    raise Exception(f"指定しているport名({d_port_name})がrunnable {node['id']}の定義しているポート群({step.runnable.o_ports})に存在しません")

                # out/inポートフラグの取得
                is_in = self._is_in_point(flow, d_node_id) 
                is_out = self._is_out_point(flow, d_node_id)

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self._upsert_point(flow=flow, point_id=d_node_id, is_in=is_in, is_out=is_out,
                                              origin=Tube(dst_port, step), target=Tube(None, None))

                # 上記dst_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにtargetを置き換える
                # (メインフローの場合は繋げる必要がない、かつ次のStepへ繋げる為にtarget変数が必要なので、何もしない)
                if not self.is_root:
                    [self._update_point(point=dst_point, target=Tube(o_port, None))
                    for o_port in flow.o_ports if o_port.name == dst_point.id]


    def _update_flow_by_other_than_runnable(self, flow, nodes):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        # 実行に関係ないnodeのtype群
        except_type_list = ['note']

        for node in nodes:
            # pointにdatumを入れていく
            if self._is_runnable_node(node) or node['type'] in except_type_list:
                continue
                
            target_points = [point for point in flow.points if point.id == node['id']]
            if len(target_points) < 1:
                continue

            target_point = target_points[0]
            target_point.cache = node.get('makeCache')
            target_point.label = node.get('label')

            # Storeの場合、Storeオブジェクトをpointに格納する
            if self._is_store_node(node):
                store_uuid = node.get('uuid')
                store = self.factory.data.find_by_uuid(store_uuid)

                # StoreにDatabaseを設定する
                target_point.datum = store
                continue

            # データの取得先の設定
            # サブフローの先頭は外部からデータをもらうので、それ以外の場合に処理を行う
            if not (len(flow.i_ports) > 0 and target_point.is_first):
                if self._is_value_node(node):
                    # nodeのvalue属性はテストで用いるためだけに存在する
                    # テストコードからvalue属性を無くした後、この分岐は削除したい
                    if isinstance(node['value'], list):
                        from kskp.store import List
                        target_point.datum = List(node['value'])
                    else:
                        target_point.datum = node['value']
                elif node.get('uuid') is not None:
                    # uuidが既に振られている場合は、loaderから取ってくるようにする
                    # self._put_loader(node.get('uuid'), target_point, flow, Folder)
                    self.folder_data_source_prepender.do_prepend(flow, target_point, node.get('uuid'))
                    # キャッシュが既にあるpointをTrueにしてもしょうがないのでFalseにする
                    target_point.cache = False
        return flow

    def _is_out_point(self, flow, node_id):
        for port in flow.o_ports:
            if port.name == node_id:
                return True
        return False

    def _is_in_point(self, flow, node_id):
        for port in flow.i_ports:
            if port.name == node_id:
                return True
        return False

    def _get_port_by_name(self, runnable_ports, port_name):
        """
        指定したport_nameをもつportを取得する。
        runnableというクラスがあったらそこにあるべきなのだろうけど
        今はないし、作るの面倒なのでとりあえずここに。
        絶対必要になった時に作ろう。。。
        """
        for runnable_port in runnable_ports:
            if runnable_port.name == port_name:
                return runnable_port
        return None

    def _replace_multi_inputs(self, i_ports, srcs):
        """
        *のportをport群に変換する
        """
        ret = []
        for src_port in i_ports:
            if src_port.name == '*':
                ret.extend([Port(p, 'frame') for p in srcs.keys()])
            else:
                ret.append(src_port)
        return ret

    def _upsert_point(self, flow, point_id, is_in, is_out, target, origin):
        """
        指定したpoint_idのpointを作成する
        対象のpointがすでに存在していればそのpointを更新する
        """
        point_ids = [point.id for point in flow.points]
        if point_id in point_ids:
            point = self._update_point(point=flow.select_point_by_node_id(point_id), is_in=is_in, is_out=is_out, origin=origin, target=target)
        else:
            point = self._insert_point(flow=flow, point_id=point_id, is_in=is_in, is_out=is_out, origin=[origin], target=[target])
        return point

    def _insert_point(self, flow, point_id, is_in, is_out, origin, target):
        """
        pointを新規作成し、flowのpointsに追加する
        """
        point = Point(point_id, origin, None, target, is_in, is_out)
        flow.points.append(point)
        return point

    def _update_point(self, point, is_in=None, is_out=None, origin=Tube(None, None), target=Tube(None, None)):
        """
        既存のpointを更新する
        """
        if is_in is not None:
            point.is_in = is_in

        if is_out is not None:
            point.is_out = is_out

        if not origin.is_None:
            point.update_origin(origin)

        if not target.is_None:
            point.update_target(target)

        return point

    def _is_value_node(self, node):
        """
        valueをもつnodeかどうか
        uuidが入っていたらそっちを優先する
        """
        return node.get('value') is not None and node.get('uuid') is None

    def _is_store_node(self, node):
        """
        指定されたnodeがStoreの場合はTrueを返す
        """
        return node['type'] == 'store'

    def _is_runnable_node(self, node):
        """
        指定されたnodeがrunnableかどうかを判断する
        """
        return node['type'] == 'command' or node['type'] == 'flow'

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
                # 今は/vizs対象のdatumで終わるように、/vizs対象pointのtargetのtubeをNone,Noneにしている。（正しいんかな？）
                # lasts_point.target = [Tube(None, None)]
                lasts_point.is_out = True

            # lasts_pointの上に繋がっているpointsを取得する
            necessary_points.extend(self._search_necessary_point(flow.points, lasts_point))
            necessary_points.append(lasts_point)

        return list(set(necessary_points))

    def _search_necessary_point(self, points, current_point):
        """
        /vizsするdatumを作成するために必要なPointを絞り込む
        既にdatumを持つpointに当たるか、origin.runnableを持たないpointに当たるまで登る

        1. 指定されたstep_idをもつpointのidを始点にする（current_pointのこと）
        2. 始点のorigin.runnableをtarget.runnableにもつpointを保持する（上に上がっていく）
        3. 保持対象のpointのidを新たな始点として再帰的に再びsearch_necessary_pointに潜る
        """
        necessary_points = []
        # current_pointの上につながっているPointを探す
        for point in points:
            for p_target in point.target:
                # 同じステップかどうかの比較はオブジェクトidで比較している（同じ箇所には同じstepオブジェクトを使い回していたはずなので）
                if p_target.runnable is current_point.o_runnable:
                    necessary_points.append(point)
                    if not (point.datum is not None or point.is_first):
                        necessary_points.extend(self._search_necessary_point(points, point))

        return necessary_points

    def _put_store(self, store_uuid, store_point):
        from kskp.store import Store
        # ライブラリからDatabaseを取得する
        store = Store.find_by_uuid(store_uuid)
        # StoreにDatabaseを設定する
        store_point.datum = store
