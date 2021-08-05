from kskp.core import Port
from kskp.depo.std.commands import CommandLink
from .point import Point
from .step import Step
from .tube import Tubes, Tube

class FolderDataSourcePrepender():
    def __init__(self, datum_factory):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self._datum_factory = datum_factory

    def do_prepend(self, flow, point, frame_uuid):
        frame = self._datum_factory.find_by_uuid(frame_uuid)
        folder_store = frame.find_parent()
        self._put_loader(flow, point, folder_store, frame_uuid)

    def _put_loader(self, flow, target_point, store, frame_uuid):
        """
        target_point(uuidが既にあるdatumのpoint)の前に
        LoaderStepとStorePointをくっつける
        Loaderは指定したstoreからデータを取ってくる
        """
        loader_cmd = CommandLink('loader').resolve()
        loader_step = Step('loader', loader_cmd, {'uuid':frame_uuid})
        point_id = target_point.id + '_loader'
        store_point = Point(point_id, None, store, Tube(Port('folder', 'store'), loader_step))
        target_point.src_tubes = Tubes(Tube(Port('o', 'frame'), loader_step))
        flow.points.add(store_point)
        flow.substeps.append(loader_step)


class FolderDataDestAppender():
    def __init__(self, flow, datum_factory, lock_uuid, start_time):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self.flow = flow
        self._datum_factory = datum_factory
        # フローのlock_uuid
        self._lock_uuid = lock_uuid
        self._start_time = start_time

    def do_append(self, flow, point):
        # フローの実行位置に実行結果フォルダ(フローの名前)が生成される
        folder_store = self.flow.find_parent()
        saver = CommandLink('saver').resolve()
        # saver_step, saver_point, saver_point2 = self._put_saver(point, flow, folder_store, saver, start_time)
        saver_point = self._put_saver(flow, point, folder_store, saver, 'saver')
        # # ↓のappend()は↑の_put_saver()の中に記述したいが、そのようにするとtest_mainがパスしなくなる(T_T ??
        # flow.points.add(saver_point2)
        # return saver_point, saver_point2
        return saver_point

    def _put_saver(self, flow, point, store, saver, command_id):
        """
        指定したpointを保存する。保存先はstoreオブジェクトが指定する場所に。
        lastsなら最後に設置し、そうでないなら間に挟むように設置する
        """
        # 出力コマンドとそれが出すpointを追加

        # saverのargs設定
        # FlowUuidLinkならキャッシュ生成後にjsonを書き換える必要があるのでその情報を渡す。
        if self.flow.uuid is None:
            args = {}
        else:
            args = {'flow_uuid':self.flow.uuid,
                    'flow':self.flow,
                    'result_folder':store,
                    'point_id':point.id,
                    'lock_uuid':self._lock_uuid}
        # saverが作るframe及びcacheのlabelはここで設定できる
        args['flow_label'] = self.flow.label if self.flow.label is not None else ''
        # args['point_label'] = point.label if point.label is not None else point.id
        args['point'] = point
        args['start_time'] = self._start_time

        # saverコマンドのstepを作成する
        saver_step = Step(saver.label, saver, args)
        saver_point = Point(f'{point.id}_{command_id}', Tube(Port('o', 'mcmd'), saver_step))

        # pointにsaverコマンドを付加する
        # (pointが終端でない場合は、二股の出力Portになる)
        point.dst_tubes.add(Tube(Port('i', 'frame'), saver_step))

        flow.substeps.append(saver_step)
        flow.points.add(saver_point)

        return saver_point


class CacheDataDestAppender(FolderDataDestAppender):
    def do_append(self, flow, point):
        # TODO: 適当なコードだがまた後で修正することになるからとりあえずこれで

        folder_store = self._datum_factory.load_cache_folder()
        saver = CommandLink('cachesaver').resolve()

        # pointの次に繋がっていたstepは、saver_pointの後に繋げる
        tmp_tubes = point.dst_tubes
        point.dst_tubes = Tubes()

        # saver_pointを作成し、pointの後に繋げる
        saver_point = self._put_saver(flow, point, folder_store, saver, 'cachesaver')

        # saver_pointの後に繋げる
        saver_point.dst_tubes = tmp_tubes

        # saver_pointからsaver stepを取り出して
        saver_step = saver_point.src_tubes[0].step
        # saver stepの"u"Portからframe_pointを繋げる
        frame_point = Point(f'{point.id}_cacheframe', Tube(Port('u', 'frame'), saver_step))
        flow.points.add(frame_point)

        return saver_point, frame_point


class VisDataDestAppender():
    def __init__(self):
        pass

    def do_append(self, flow, point, vis_args):
        """
        テーブル又はグラフ表示のための前処理を付加する
        """
        if 'args' not in vis_args[point.id]:
            raise Exception(f'JSON属性({point.id})の下にargs属性を指定してください')

        # グラフ種別を取得する
        vcmd_args = vis_args[point.id]['args']
        vcmd_id = vis_args[point.id].get('command_id') or vcmd_args.get('visualizer')
        if vcmd_id is None:
            raise Exception('command_id属性でvcmdのidを指定してください')

        # テーブル表示の場合はTrue
        vcmd_is_table = vcmd_id == 'csvtohtmltable'

        # UTF-8への変換コマンドを作成する
        # (S_JISをwritelistコマンドに入力するとDockerが終了するので)
        convtoutf8 = CommandLink('convtoutf8').resolve()
        convtoutf8_step = Step(convtoutf8.label, convtoutf8, {'target_encoding':'utf-8','target_newline':'\n'})

        # RowRange Stepへの引数を作成する
        rowrange_args = vis_args[point.id]['args']
        # RowRange Stepを作成する
        if vcmd_is_table:
            rowrange_cmd = CommandLink('rowrange').resolve()
        else:
            rowrange_cmd = CommandLink('rowrandom').resolve()
        rowrange_step = Step(rowrange_cmd.label, rowrange_cmd, rowrange_args)

        # MchkCsv Stepを作成する
        mchkcsv_cmd = CommandLink('mchkcsv').resolve()
        mchkcsv_step = Step(mchkcsv_cmd.label, mchkcsv_cmd)

        # ToList Stepを作成する 
        # tolist_cmd = CommandLink('to_pipe').resolve()
        if vcmd_is_table:
            tolist_cmd = CommandLink('to_list').resolve()
        else:
            tolist_cmd = CommandLink('to_tlist').resolve()
        tolist_step = Step(tolist_cmd.label, tolist_cmd, vcmd_args)

        # ConvToUtf8 Stepを繋げる
        point_id = point.id + '_convtoutf8'
        convtoutf8_point = Point(point_id, Tube(Port('o', 'frame'), convtoutf8_step), None, Tube(Port('i', 'frame'), rowrange_step))
        # RowRange Stepを繋げる
        point_id = point.id + '_rowrange'
        rowrange_point = Point(point_id, Tube(Port('o', 'frame'), rowrange_step), None, Tube(Port('i', 'frame'), mchkcsv_step))
        # MchkCsv Stepを繋げる
        point_id = point.id + '_mchkcsv'
        mchkcsv_point = Point(point_id, Tube(Port('o', 'frame'), mchkcsv_step), None, Tube(Port('i', 'frame'), tolist_step))
        # ToListコマンドを繋げる
        point_id = point.id + '_tolist_o'
        tolist_point_o = Point(point_id, Tube(Port('o', 'frame'), tolist_step))
        if not vcmd_is_table:
            point_id = point.id + '_tolist_u'
            tolist_point_u = Point(point_id, Tube(Port('u', 'frame'), tolist_step))
        else:
            tolist_point_u = None

        # pointにsaverコマンドを付加する
        # (pointが終端でない場合は、二股の出力Portになる)
        point.dst_tubes.add(Tube(Port('i', 'frame'), convtoutf8_step))

        flow.substeps.append(convtoutf8_step)
        flow.substeps.append(rowrange_step)
        flow.substeps.append(mchkcsv_step)
        flow.substeps.append(tolist_step)
        flow.points.add(convtoutf8_point)
        flow.points.add(rowrange_point)
        flow.points.add(mchkcsv_point)
        flow.points.add(tolist_point_o)
        if tolist_point_u is not None:
            flow.points.add(tolist_point_u)

        return tolist_point_o, tolist_point_u

    def do_append_after_runs(self, flow, o_point:Point, u_point:Point, vis_arg:dict):
        """
        VCommandを付加する
        """
        if vis_arg is None:
            raise Exception(f'APIのJSON引数にPoint idを指定してください')

        if 'args' not in vis_arg:
            raise Exception(f'APIのJSON引数({o_point.id})の下にargs属性を指定してください.')

        vcmd_args = vis_arg['args']
        vcmd_id = vis_arg.get('command_id') or vcmd_args.get('visualizer')
        
        if vcmd_id is None:
            raise Exception('command_id属性でvcmdのidを指定してください')

        # VCommandを作成する
        vcmd = CommandLink(vcmd_id).resolve()
        vcmd_step = Step(vcmd.label, vcmd, vcmd_args)
        # VCommandの出力Pointを作成する
        vcmd_point = Point(o_point.id + '_v', Tube(Port('o', 'datum'), vcmd_step))

        # VCommandにRunsCommandの出力Pointを繋げる
        o_point.dst_tubes = Tubes(Tube(Port('i', 'frame'), vcmd_step))
        # グラフ表示の場合はVCommandにヘッダ出力(u)も繋げる
        if u_point is not None:
            u_point.dst_tubes = Tubes(Tube(Port('m', 'frame'), vcmd_step))

        flow.substeps.append(vcmd_step)
        flow.points.add(vcmd_point)

        return vcmd_point


class RunsCommandAppender():
    def __init__(self):
        # Runsコマンドを取得する
        runs_cmd = CommandLink('runs').resolve()
        # Runsステップのo_portsへはdo_append()を呼び出す度に出力Portを1つ追加する
        self.runs_o_ports = []
        # Runsステップを作成する
        # (CommandExceptionが入力された場合の処理をRunsCommand内で行うためex_acceptable=Trueとする)
        self.runs_step = Step('runs', runs_cmd, o_ports=self.runs_o_ports, ex_acceptable=True)
        # ポート名は0番から順に採番する
        self._next_port_no = 0
        # FlowCommand.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = False

    def do_append(self, flow, point1:Point, point2:Point=None):
        if point2 is None:
            return self._do_append_one(flow, point1), None
        else:
            return self._do_append_one(flow, point1), self._do_append_one(flow, point2)

    def _do_append_one(self, flow, point):
        # RunsCommandに繋げるPointを作成する
        port_label = str(self._next_port_no)
        self._next_port_no += 1

        point_id = point.id + '_runs'
        runs_point = Point(point_id, Tube(Port(port_label, 'datum?'), self.runs_step))

        # Stepのportsに追加する
        self.runs_o_ports.append(Port(port_label, 'datum?'))

        # ここでRunsCommandを繋げる
        point.dst_tubes = Tubes(Tube(Port(port_label, 'mcmd'), self.runs_step))

        if not self._already_step_added:
            flow.substeps.append(self.runs_step)
            self._already_step_added = True

        flow.points.add(runs_point)
        return runs_point


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
        self._next_port_no = 0
        # FlowCommand.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = False

    def do_append(self, flow, point, src_point_of_data_dst):
        # Activity Stepのargsにpointを追加する
        port_label = str(self._next_port_no)
        self.activity_step.args['points'][port_label] = src_point_of_data_dst

        # PointにActivity Stepを繋げる
        point.dst_tubes = Tubes(Tube(Port(port_label, 'datum'), self.activity_step))

        # Activity_pointを作成し、これにActivity Stepを繋げる
        point_id = point.id + '_activity_' + port_label
        activity_point = Point(point_id, Tube(Port('o', 'activity'), self.activity_step))

        self._next_port_no += 1

        if self._already_step_added:
            # Pointを新規追加しない場合はNoneを返す
            return None

        flow.substeps.append(self.activity_step)
        flow.points.add(activity_point)
        self._already_step_added = True
        return activity_point
