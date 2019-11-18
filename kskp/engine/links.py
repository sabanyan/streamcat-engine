import functools
import json
import uuid

from pathlib import Path

from kskp.engine import Flow, Step, Point, Tube
from kskp.store import Port, FlowLink, Library, Folder
from kskp.store.commands import CommandLink

root = Library.load_root()
result_folder = Library.load_result_folder()
cache_folder = Library.load_cache_folder()

class FolderDataSourcePrepender():
    def __init__(self):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        pass

    def do_prepend(self, f, point, frame_uuid):
        from kskp.store import Folder

        folder_store = Folder.convert_to_folder(result_folder)
        self._put_loader(frame_uuid, point, f, folder_store)

    def _put_loader(self, frame_uuid, target_point, f, store):
        """
        target_point(uuidが既にあるdatumのpoint)の前に
        LoaderStepとStorePointをくっつける
        Loaderは指定したstoreからデータを取ってくる
        """
        loader_step = self._make_loader_step(frame_uuid)
        store_point = Point(frame_uuid + '_loader_point', [Tube(None, None)], store, [Tube(Port('store', 'store'), loader_step)])
        target_point.origin = [Tube(Port('o', 'frame'), loader_step)]
        f.points.append(store_point)
        f.substeps.append(loader_step)

    def _make_loader_step(self, node_uuid):
        """
        指定したuuidのデータを取ってくるLoaderStepを作成する
        """
        return Step(str(uuid.uuid4()), CommandLink("loader").resolve(), {'uuid':node_uuid})

class FolderDataDestAppender():
    def __init__(self, flow_uuid):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self.flow_uuid = flow_uuid

    def do_append(self, f, point, start_time):
        from kskp.store import Folder

        # folder_store = Library.load_result_folder()
        folder_store = Folder.convert_to_folder(result_folder)
        saver = CommandLink("saver").resolve()
        saver_step, saver_point, saver_point2 = self._put_saver(point, f, folder_store, saver, start_time)
        # ↓のappend()は↑の_put_saver()の中に記述したいが、そのようにするとtest_mainがパスしなくなる(T_T ??
        f.points.append(saver_point2)
        return saver_point, saver_point2

    def _put_saver(self, point, f, store, saver, start_time):
        """
        指定したpointを保存する。保存先はstoreオブジェクトが指定する場所に。
        lastsなら最後に設置し、そうでないなら間に挟むように設置する
        """
        # 出力コマンドとそれが出すpointを追加

        # saverのargs設定
        # FlowUuidLinkならキャッシュ生成後にjsonを書き換える必要があるのでその情報を渡す。
        args = {'flow_uuid': self.flow_uuid, 'datum_id':point.id} if self.flow_uuid is not None else {}
        # saverが作るframe及びcacheのlabelはここで設定できる
        from datetime import datetime, timezone
        args['flow_label'] = f.label if f.label is not None else ''
        # args['point_label'] = point.label if point.label is not None else point.id
        args['point'] = point
        args['start_time'] = start_time

        saver_step = self._make_step(args, saver)
        store_point = Point(point.id + '_store_point', [Tube(None, None)], store, [Tube(Port('store', 'store'), saver_step)])
        saver_point = Point(point.id, [Tube(Port('o', 'mcmd'), saver_step)], None, [Tube(None, None)])
        saver_point2 = Point(str(uuid.uuid4()), [Tube(Port('u', 'uuid'), saver_step)], None, [Tube(None, None)])

        # lastsじゃない場合は追加したpointを次のstepに繋げる
        if not point.is_last:
            saver_point.target = point.target
        # pointの向き先を変更する
        point.target = [Tube(Port('i', 'frame'), saver_step)]

        f.substeps.append(saver_step)
        f.points.extend([saver_point, store_point])

        return saver_step, saver_point, saver_point2

    def _make_step(self, args, cmd):
        """
        saverコマンドのstepを作成する
        """
        return Step(str(uuid.uuid4()), cmd, args)

class CacheDataDestAppender(FolderDataDestAppender):
    def do_append(self, f, point, start_time):
        from kskp.store import Folder

        # folder_store = Library.load_result_folder()
        folder_store = Folder.convert_to_folder(cache_folder)
        saver = CommandLink("cachesaver").resolve()
        self._put_saver(point, f, folder_store, saver, start_time)

class PreviewDataDestAppender():
    def __init__(self, flow_uuid, preview_args={}):
        self.preview_args = preview_args

    def do_append(self, f, point, start_time):
        """
        RowRangeコマンドを付加する
        ToListコマンドを付加する
        """
        if 'args' not in self.preview_args[point.id]:
            raise Exception(f'JSON属性({point.id})の下にargs属性を指定してください')

        # RowRange Stepへの引数を作成する
        rowrange_args = self.preview_args[point.id]['args']

        # RowRange Stepを作成する
        rowrange_cmd = CommandLink('rowrange').resolve()
        rowrange_step = self._make_step(rowrange_args, rowrange_cmd)

        # ToList Stepを作成する 
        tolist_cmd = CommandLink('to_list').resolve()
        tolist_step = self._make_step({}, tolist_cmd)

        # RowRange Stepを繋げる
        point_id = point.id + '_rowrange'
        rowrange_point = Point(point_id, [Tube(Port('o', 'frame'), rowrange_step)], None, [Tube(Port('i', 'frame'), tolist_step)])
        # ToListコマンドを繋げる
        point_id = point.id + '_tolist'
        tolist_point = Point(point_id, [Tube(Port('o', 'frame'), tolist_step)], None, [Tube(None, None)])

        # point.id = str(uuid.uuid4())
        point.target = [Tube(Port('i', 'frame'), rowrange_step)]

        f.substeps.append(rowrange_step)
        f.substeps.append(tolist_step)
        f.points.append(rowrange_point)
        f.points.append(tolist_point)

        return tolist_point

    def do_append_after_runs(self, f, point, start_time, original_last_point):
        visualizer_step, visualizer_point = self._put_visualizer(f, point, original_last_point, start_time)
        return visualizer_point

    def _put_visualizer(self, f, point, original_last_point, start_time):
        """
        Visualizerコマンドを付加する
        """
        if 'args' not in self.preview_args[original_last_point.id]:
            raise Exception(f'JSON属性({point.id})の下にargs属性を指定してください.')

        visualizer_args = self.preview_args[original_last_point.id]['args']
        if 'visualizer' not in visualizer_args:
            raise Exception('visualizer属性を指定してください')
        visualizer_cmd_name = visualizer_args['visualizer']
        visualizer_cmd = CommandLink(visualizer_cmd_name).resolve()
        visualizer_step = self._make_step(visualizer_args, visualizer_cmd)
        visualizer_point = Point(point.id + '_v', [Tube(Port('o', 'datum'), visualizer_step)], None, [Tube(None, None)])

        # プレビューPointにVisualizerフローを繋げる
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
        activity_cmd = CommandLink("activity").resolve()
        # Activity Datumを作成する
        from kskp.store import Activity
        activity = Activity(None, 'activity', flow_uuid)
        # Activity Stepへの引数を作成する
        activity_args = {'activity': activity, 'points':{}}
        # Activity Stepを作成する
        self.activity_step = Step(str(uuid.uuid4()), activity_cmd, activity_args)
        # ポート名は0番から順に採番する
        self.next_port_no = 0
        # Flow.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = set()

    def do_append(self, f, point, original_last_point, start_time):
        # Activity Stepのargsにpointを追加する
        port_name = str(self.next_port_no)
        self.activity_step.args['points'][port_name] = original_last_point

        # PointにActivity Stepを繋げる
        point.target = [Tube(Port(port_name, 'datum'), self.activity_step)]

        # Activity_pointを作成し、これにActivity Stepを繋げる
        point_id = point.id + '_activity_' + port_name
        activity_point = Point(point_id,
                               [Tube(Port('o', 'activity'), self.activity_step)],
                               None,
                               [Tube(None, None)])

        if f.uuid not in self._already_step_added:
            f.substeps.append(self.activity_step)
            f.points.append(activity_point)
            self._already_step_added.add(f.uuid)

        self.next_port_no += 1

        return activity_point

class RunsCommandAppender():
    def __init__(self):
        # Runsコマンドを取得する
        runs_cmd = CommandLink("runs").resolve()
        # Runsステップを作成する
        self.runs_step = Step(str(uuid.uuid4()), runs_cmd, {})
        # ポート名は0番から順に採番する
        self.next_port_no = 0
        # Flow.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = False

    def do_append(self, f, point, start_time):
        # RunsCommandに繋げるPointを作成する
        port_name = str(self.next_port_no)
        point_id = point.id + '_runs'
        runs_point = Point(point_id, [Tube(Port(port_name, 'datum?'), self.runs_step)], None, [Tube(None, None)])

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
    def __init__(self, flow_uuid=None):
        self.runs_command_appender = RunsCommandAppender()
        self.activity_data_dest_appender = ActivityDataDestAppender(flow_uuid)

        # {flow_uuid:, [(original_last_point:, points: )]}
        self.detadst_o_ports = {}
        self.detadst_u_ports = {}

class FlowJsonLink:
    """
    フローへのリンク
    """
    def __init__(self, label, json_str, context, last_ids=[], preview_args={}):
        self.label = label
        self.json_str = json_str
        self.is_root = False
        # self.last_ids = last_ids
        self.last_ids = preview_args.keys()

        self.folder_data_source_prepender = FolderDataSourcePrepender()

        self.folder_data_dest_appender = FolderDataDestAppender(None)

        self.preview_data_dest_appender = PreviewDataDestAppender(None, preview_args)

        self.cache_data_dest_appender = CacheDataDestAppender(None)

        self.context = context
            
    def _node2link(self, node):
        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(node['uuid'], self.context)

            # かなりの力技・・・。
            # 実行を行う場合、サブフロー内で余分な処理が走らないように
            # 親フローが子フロー（使用するサブフロー）に、このoutputが必要だということを教える。

            # メインフローでプレビュー時、どのdstsを通るかを求める
            dst_ids = self._pick_necessary_dst_ids(json.loads(self.json_str), self.last_ids)
            # メインフローで使われるdstsの中に、対象のnode（サブフロー）が出力するものがあれば教えてあげる
            if len(dst_ids) > 0:
                ret.last_ids = [port for port, datum_id in node['dsts'].items() for dst_id in dst_ids if datum_id == dst_id]

        return ret

    def resolve(self):
        f = self._make_flow(self.label, self.json_str)

        self.context.detadst_o_ports[f.uuid] = []
        self.context.detadst_u_ports[f.uuid] = []

        for p in f.points:
            for p_target in p.target:
                if p_target.runnable is None:
                    continue

                # import pprint
                # pprint.pprint(p_target)

                step = p_target.runnable
                # データデストの場合
                if step.is_datadst:
                    
                    print('>> step.is_datadst')     

                    # oポートの中継
                    origin_tubes = [Tube(Port('o', 'mcmd'), step)]
                    new_point = self._insert_point(f, str(uuid.uuid4()), origin=origin_tubes, target=[Tube(None, None)])
                    self.context.detadst_o_ports[f.uuid].append((p, new_point))
                    # データデストの出力を親フローに繋げる)
                    if not self.is_root:
                        port = Port(new_point.id, 'mcmd')
                        f.o_ports.append(port)
                        self._update_point(point=new_point, target=Tube(port, None))

                    # uポートの中継
                    origin_tubes = [Tube(Port('u', 'frame'), step)]
                    new_point = self._insert_point(f, str(uuid.uuid4()), origin=origin_tubes, target=[Tube(None, None)])
                    self.context.detadst_u_ports[f.uuid].append((p, new_point))
                    # データデストの出力を親フローに繋げる)
                    if not self.is_root:
                        port = Port(new_point.id, 'frame')
                        f.o_ports.append(port)
                        self._update_point(point=new_point, target=Tube(port, None))
            
                elif step.is_flow:
                    # 中継リレーですね
                    inner_flow = step.runnable

                    # フローが'o','u'の出力ポートを持っている場合
                    if inner_flow.uuid in self.context.detadst_o_ports:

                        for i in range(len(self.context.detadst_o_ports[inner_flow.uuid])):
                            original_last_point, last_point = self.context.detadst_o_ports[inner_flow.uuid][i]

                            # oポートの中継
                            origin_tubes = [Tube(Port('o', 'mcmd'), step)]
                            new_point = self._insert_point(f, str(uuid.uuid4()), origin=origin_tubes, target=[Tube(None, None)])
                            self.context.detadst_o_ports[f.uuid].append((original_last_point, new_point))

                            # データデストの出力を親フローに繋げる)
                            if not self.is_root:
                                port = Port(new_point.id, 'mcmd')
                                f.o_ports.append(port)
                                self._update_point(point=new_point, target=Tube(port, None))

                        for i in range(len(self.context.detadst_u_ports[inner_flow.uuid])):
                            original_last_point, last_point = self.context.detadst_u_ports[inner_flow.uuid][i]

                            # uポートの中継
                            origin_tubes = [Tube(Port('u', 'frame'), step)]
                            new_point = self._insert_point(f, str(uuid.uuid4()), origin=origin_tubes, target=[Tube(None, None)])
                            self.context.detadst_u_ports[f.uuid].append((original_last_point, new_point))

                            # データデストの出力を親フローに繋げる)
                            if not self.is_root:
                                port = Port(new_point.id, 'frame')
                                f.o_ports.append(port)
                                self._update_point(point=new_point, target=Tube(port, None))



        # flowがもつPointを、実行に必要なものだけを絞り込んで取得している。

        # self.last_idsには
        # メインフローの場合 ： プレビューするdatumのid群
        # サブフローの場合　 ： 親の実行に必要なlastのid群
        # が入っている。（はず）
        # プレビューしない場合はメインフローのlastのid群を使って絞り込みを行う。
        last_ids = self._pick_last_points(f.lasts, f.points)

        # 実行するのに必要なpointを取得する
        is_preview = len(self.last_ids) > 0
        f.points = self._pick_necessary_points(f, last_ids, is_preview)

        # 処理の開始時刻を取得する
        from datetime import datetime, timezone
        start_time = datetime.utcnow().replace(tzinfo=timezone.utc)

        # キャッシュ作成処理
        cache_points = [point for point in f.points if point.is_cache]
        for point in cache_points:
            self.cache_data_dest_appender.do_append(f, point, start_time)

        if self.is_root:
            # lasts出力処理（メインフローの場合のみ）
            for first_last_point in [point for point in f.points if point.is_last]:
                if is_preview:
                    # Visualizerコマンドのための前処理コマンドを付加する
                    last_point = self.preview_data_dest_appender.do_append(f, first_last_point, start_time)
                    # Runsコマンドを付加する
                    last_point = self.context.runs_command_appender.do_append(f, last_point, start_time)
                    # Visualizeコマンドを付加する
                    visualizer_point = self.preview_data_dest_appender.do_append_after_runs(f, last_point, start_time, first_last_point)
                    # Activity Stepを付加する
                    self.context.activity_data_dest_appender.do_append(f, visualizer_point, first_last_point, start_time)

                else:

                    point_is_input_datadest = False

                    if first_last_point.o_runnable.is_flow:
                        # ↓どちらかのFor文しか通らない、いまいちなコード
                        for detadst_o_points in self.context.detadst_o_ports[f.uuid]:
                            if detadst_o_points[1] == first_last_point:
                                # Runsコマンドを付加する
                                last_point = self.context.runs_command_appender.do_append(f, first_last_point, start_time)
                                point_is_input_datadest = True

                        for detadst_u_points in self.context.detadst_u_ports[f.uuid]:
                            if detadst_u_points[1] == first_last_point:
                                # Activity Stepを付加する
                                original_last_point = detadst_u_points[0]
                                self.context.activity_data_dest_appender.do_append(f, first_last_point, original_last_point, start_time)
                                point_is_input_datadest = True

                    if not point_is_input_datadest:
                        # Saverコマンドを付加する
                        last_point, activity_point = self.folder_data_dest_appender.do_append(f, first_last_point, start_time)
                        # Activity Stepを付加する
                        self.context.activity_data_dest_appender.do_append(f, activity_point, first_last_point, start_time)
                        # Runsコマンドを付加する
                        last_point = self.context.runs_command_appender.do_append(f, last_point, start_time)


        elif f.is_datadst:
            # データデストの場合はその中のLastsにRunsコマンドを付加する

            # 2出力StepのCommandの出力Pointを取得する
            last_point = None
            activity_point = None
            for p in f.points:
                if p.o_runnable is None:
                    continue
                if p.o_runnable.is_flow:
                    continue
                if len(p.o_runnable.runnable.o_ports) != 2:
                    continue
                if p.o_port.name == 'o':
                    last_point = p
                elif p.o_port.name =='u':
                    activity_point = p

            if last_point is None or activity_point is None:
                raise Exception('No out point of saver found !!')
            
            # # Activity Stepを付加する
            # self.context.activity_data_dest_appender.do_append(f, activity_point, last_point, start_time)
            # # Runsコマンドを付加する
            # self.context.runs_command_appender.do_append(f, last_point, start_time)

            # データデストの出力を親フローに繋げる
            o_port = Port('o', 'mcmd')
            u_port = Port('u', 'frame')

            f.o_ports.append(o_port)
            f.o_ports.append(u_port)
            
            self._update_point(point=last_point, target=Tube(o_port, None))
            self._update_point(point=activity_point, target=Tube(u_port, None))

            print('>> f.is_datadst')    

        return f

    # def _find_step_by_o_port(self, steps, port):
    #     for step in steps:
    #         if not step.is_flow:
    #             continue
    #         for o_port in step.runnable.o_ports:
    #             if o_port.name == port.name:
    #                 return step
    #     raise Exception('No step found in flow!')

    def _pick_last_points(self, lasts, points):
        # プレビューなど、lastsが指定されている場合
        if len(self.last_ids) > 0:
            return self.last_ids 

        # 出力のないサブフローの入力ポイントを集める
        # (入力ポイントを出力のないサブフローに渡すため)
        ret = self._pick_points_of_no_output_subflow(points)
        # lastsを集める
        ret.extend(lasts.keys())
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

    def _make_flow(self, label, json_str):

        # JSONを読み込む
        json_obj = json.loads(json_str)

        flow = Flow(label)

        # portを読む
        ports = json_obj['ports']
        flow.i_ports = self._parse_ports(ports[0])
        flow.o_ports = self._parse_ports(ports[1])

        # flowを更新する
        if 'nodes' in json_obj:
            self._update_flow_by_runnable(flow, json_obj['nodes'])
            self._update_flow_by_other_than_runnable(flow, json_obj['nodes'])

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

            # runnableのインスタンス化を行う
            step = Step(node['id'], self._node2link(node).resolve(), node['args'])
            flow.substeps.append(step)

            srcs = node['srcs']
            dsts = node['dsts']

            self._replace_multi_inputs(step, srcs)

            # srcとdstからpointを作る
            for s_port_name, s_node_id in srcs.items():
                # 定義上に存在しないポート名がsrcsに存在していないかの確認
                src_port = self._get_port_by_name(step.runnable.i_ports, s_port_name)
                if src_port is None:
                    raise Exception(f"指定しているport名({s_port_name})がrunnable {node['id']}の定義しているポート群({step.runnable.i_ports})に存在しません")

                # pointを作成する（作成対象がすでにあれば更新する）
                src_point = self._upsert_point(flow=flow, point_id=s_node_id,
                                              origin=Tube(None, None), target=Tube(src_port, step))

                # 上記src_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにoriginを置き換える
                [self._update_point(point=src_point, origin=Tube(i_port, None))
                 for i_port in flow.i_ports if i_port.name == src_point.id]

            for d_port_name, d_node_id in dsts.items():
                # 定義上に存在しないポート名がdstsに存在していないかの確認
                dst_port = self._get_port_by_name(step.runnable.o_ports, d_port_name)
                if dst_port is None:
                    raise Exception(f"指定しているport名({d_port_name})がrunnable {node['id']}の定義しているポート群({step.runnable.o_ports})に存在しません")

                # pointを作成する（作成対象がすでにあれば更新する）
                dst_point = self._upsert_point(flow=flow, point_id=d_node_id,
                                              origin=Tube(dst_port, step), target=Tube(None, None))

                # 上記dst_pointがサブフローのもので、かつ親フローと繋がっているpointならば
                # 繋げるためにtargetを置き換える
                [self._update_point(point=dst_point, target=Tube(o_port, None))
                 for o_port in flow.o_ports if o_port.name == dst_point.id]

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

    def _replace_multi_inputs(self, step, srcs):
        """
        *のportをport群に変換する
        """
        for src_port in step.runnable.i_ports:
            if src_port.name == '*':
                step.runnable.i_ports = [Port(p, 'frame') for p in srcs.keys()]

    def _upsert_point(self, flow, point_id, target, origin):
        """
        指定したpoint_idのpointを作成する
        対象のpointがすでに存在していればそのpointを更新する
        """
        point_ids = [point.id for point in flow.points]
        if point_id in point_ids:
            point = self._update_point(point=flow.select_point_by_node_id(point_id), origin=origin, target=target)
        else:
            point = self._insert_point(flow=flow, point_id=point_id, origin=[origin], target=[target])
        return point

    def _insert_point(self, flow, point_id, origin, target):
        """
        pointを新規作成し、flowのpointsに追加する
        """
        point = Point(point_id, origin, None, target)
        flow.points.append(point)
        return point

    def _update_point(self, point, origin=Tube(None, None), target=Tube(None, None)):
        """
        既存のpointを更新する
        """
        if not origin.is_None:
            point.update_origin(origin)

        if not target.is_None:
            point.update_target(target)

        return point

    def _update_flow_by_other_than_runnable(self, flow, nodes):
        """
        指定したnodesの中にある、runnable以外のnodeを使ってFlowオブジェクトの属性を更新する
        """
        # 実行に関係ないnodeのtype群
        except_type_list = ['note']

        for node in nodes:
            # pointにdatumを入れていく
            if not self._is_runnable_node(node) and not node['type'] in except_type_list:
                
                target_points = [point for point in flow.points if point.id == node['id']]
                if len(target_points) < 1:
                    continue

                target_point = target_points[0]
                target_point.cache = node.get('makeCache')
                target_point.label = node.get('label')

                # Storeの場合、Storeオブジェクトをpointに格納する
                if self._is_store_node(node):
                    self._put_store(node.get('uuid'), target_point)

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
        """ 指定されたnodeがrunnableかどうかを判断する """
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

    def _pick_necessary_points(self, flow, last_ids, is_preview):
        """
        実行するのに必要なpointを取得する
        """
        necessary_points = []

        for id in last_ids:
            lasts_point = flow.select_point_by_id(id)
            # if len(flow.o_ports) == 0:
            if self.is_root and is_preview:
                # 今はプレビュー対象のdatumで終わるように、プレビュー対象pointのtargetのtubeをNone,Noneにしている。（正しいんかな？）
                lasts_point.target = [Tube(None, None)]

            # lasts_pointの上に繋がっているpointsを取得する
            necessary_points.extend(self._search_necessary_point(flow.points, lasts_point))
            necessary_points.append(lasts_point)

        return list(set(necessary_points))

    def _search_necessary_point(self, points, current_point):
        """
        プレビューするdatumを作成するために必要なPointを絞り込む
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


class FlowUuidLink(FlowJsonLink):
    """
    UUIDを元にFlowを返却するリンク
    """

    def __init__(self, flow_uuid, context, last_ids=[], preview_args={}):
        self.flow_uuid = flow_uuid
        flow_link = FlowLink(flow_uuid)
        flow_data = flow_link.resolve()
        flow_label = flow_link.resolve_label()

        super().__init__(flow_label, json.dumps(flow_data), context, last_ids, preview_args)

        # super().__init__より下に記述すること
        is_preview =  len(self.last_ids) > 0
        if is_preview:
            self.preview_data_dest_appender = PreviewDataDestAppender(flow_uuid, preview_args)
        else:
            self.folder_data_dest_appender = FolderDataDestAppender(flow_uuid)
        self.cache_data_dest_appender = CacheDataDestAppender(flow_uuid)
        # self.activity_data_dest_appender = ActivityDataDestAppender(flow_uuid)

    def node2link(self, node):
        if node['type'] == 'command':
            ret = CommandLink(node['commandId'])
        elif node['type'] == 'flow':
            ret = FlowUuidLink(node['uuid'], self.context)

        return ret
