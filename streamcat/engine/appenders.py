from streamcat.core import Port
from streamcat.store import Flow
from streamcat.depo.std.commands import CommandLink
from .flow_command import FlowCommand
from .point import Point
from .step import Step
from .tube import Tubes, Tube

class BeamToNysolInserter():

    def __init__(self):
        beamrun_cmd = CommandLink('beam_run').resolve()
        outtonysol_cmd = CommandLink('outtonysol').resolve()
        self._tolist_cmd = CommandLink('beam_tolist').resolve()

        self._beamrun_step = Step('beamrun', beamrun_cmd)
        self._outtonysol_step = Step('outtonysol', outtonysol_cmd)

        self._first = True

        # ポート名は0番から順に採番する
        self._next_port_no = 0

    def add_dst_tube(self, point:Point, dst_tube:Tube):

        port_label = str(self._next_port_no)
        self._next_port_no += 1

        # pointをBeamToListコマンドに繋げる
        tolist_step = Step('beam_tolist', self._tolist_cmd)
        point.add_dst_tube(Tube(Port(dst_tube.port.label, 'beam'), tolist_step))

        # BeamToListコマンドの出力Pointを作成する
        beamtolist_id = f'{point.id}_{port_label}_beamtolist'
        beamtolist_point = Point(beamtolist_id,
                            src_tube=Tube(Port('o', 'beam'), tolist_step),
                            dst_tube=Tube(Port(port_label, 'beam'), self._beamrun_step))

        # BeamRunコマンドの出力Pointを作成する
        beamrun_point_id = f'{point.id}_{port_label}_beamrun'
        beamrun_point = Point(beamrun_point_id,
                            src_tube=Tube(Port(port_label, 'out'), self._beamrun_step),
                            dst_tube=Tube(Port(port_label, 'out'), self._outtonysol_step))
        # OutToNysolコマンドの出力Pointを作成する
        outtonysol_point_id = f'{point.id}_{port_label}_outtonysol'
        outtonysol_point = Point(outtonysol_point_id,
                            src_tube=Tube(Port(port_label, 'mcmd'), self._outtonysol_step),
                            dst_tube=Tube(Port(dst_tube.port.label, 'mcmd'), dst_tube.step))

        if self._first:
            self._first = False
            return ([tolist_step,self._beamrun_step,self._outtonysol_step], [beamtolist_point,beamrun_point,outtonysol_point])
        else:
            return ([tolist_step], [beamtolist_point,beamrun_point,outtonysol_point])

 

class FolderDataSourcePrepender():
    def __init__(self, datum_factory):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self._datum_factory = datum_factory

    def do_prepend(self, flow_cmd:FlowCommand, point:Point, frame_uuid):
        frame = self._datum_factory.find_by_uuid(frame_uuid)
        folder_store = frame.find_parent()
        self._put_loader(flow_cmd, point, folder_store, frame_uuid)

    def _put_loader(self, flow_cmd:FlowCommand, target_point:Point, store, frame_uuid):
        """
        target_point(uuidが既にあるdatumのpoint)の前に
        LoaderStepとStorePointをくっつける
        Loaderは指定したstoreからデータを取ってくる
        """
        loader_cmd = CommandLink('loader').resolve()
        loader_step = Step('loader', loader_cmd, {'uuid':frame_uuid})
        point_id = target_point.id + '_loader'
        store_point = Point(point_id, None, store, Tube(Port('folder', 'store'), loader_step))
        target_point.src_tubes = Tubes()
        target_point.add_src_tube(Tube(Port('o', 'mcmd'), loader_step))
        flow_cmd.points.add(store_point)
        flow_cmd.substeps.append(loader_step)


class FolderDataDestAppender():
    def __init__(self, flow:Flow, datum_factory, lock_uuid, start_at):
        # core.pyで定義されているFlowはf
        # flow.pyで定義されているFlowはflowと表記する
        self.flow = flow
        self._datum_factory = datum_factory
        # フローのlock_uuid
        self._lock_uuid = lock_uuid
        self._start_at = start_at

    def do_append(self, flow_cmd:FlowCommand, point:Point):
        # フローの実行位置に実行結果フォルダ(フローの名前)が生成される
        folder_store = self.flow.find_parent()
        saver = CommandLink('saver').resolve()
        # saver_step, saver_point, saver_point2 = self._put_saver(point, flow, folder_store, saver, start_at)
        saver_point = self._put_saver(flow_cmd, point, folder_store, saver, 'saver')
        # # ↓のappend()は↑の_put_saver()の中に記述したいが、そのようにするとtest_mainがパスしなくなる(T_T ??
        # flow.points.add(saver_point2)
        # return saver_point, saver_point2
        return saver_point

    def _put_saver(self, flow_cmd:FlowCommand, point:Point, store, saver, command_id):
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
        args['start_at'] = self._start_at

        # saverコマンドのstepを作成する
        saver_step = Step(saver.label, saver, args)
        saver_point = Point(f'{point.id}_{command_id}', Tube(Port('o', 'mcmd'), saver_step))

        # pointにsaverコマンドを付加する
        # (pointが終端でない場合は、二股の出力Portになる)
        point.add_dst_tube(Tube(Port('i', 'mcmd'), saver_step))

        flow_cmd.substeps.append(saver_step)
        flow_cmd.points.add(saver_point)

        return saver_point


class CacheDataDestAppender(FolderDataDestAppender):
    def do_append(self, flow_cmd:FlowCommand, point:Point):
        # TODO: 適当なコードだがまた後で修正することになるからとりあえずこれで

        folder_store = self._datum_factory.load_cache_folder()
        saver = CommandLink('cachesaver').resolve()

        # pointの次に繋がっていたstepは、saver_pointの後に繋げる
        tmp_tubes = point.dst_tubes
        point.dst_tubes = Tubes()

        # saver_pointを作成し、pointの後に繋げる
        saver_point = self._put_saver(flow_cmd, point, folder_store, saver, 'cachesaver')

        # saver_pointの後に繋げる
        for tmp_tube in tmp_tubes:
            saver_point.add_dst_tube(tmp_tube)

        # saver_pointからsaver stepを取り出して
        saver_step = saver_point.src_tubes[0].step
        # saver stepの"u"Portからframe_pointを繋げる
        frame_point = Point(f'{point.id}_cacheframe', Tube(Port('u', 'mcmd'), saver_step))
        flow_cmd.points.add(frame_point)

        return saver_point, frame_point


class VisDataDestAppender():
    def __init__(self):
        pass

    def do_append(self, flow_cmd:FlowCommand, point:Point, vis_args:dict):
        """
        テーブル又はグラフ表示のための前処理を繋げる
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

        if 'beam' in point.src_tubes[0].port.types:
            # 接続先Pointの入力Portの型が'beam'の場合は、Beam用の前処理Stepを繋げる
            return self._append_beams(flow_cmd, point, vcmd_args, vcmd_is_table)
        else:
            # 'mcmd'の場合は、nysol_python用の前処理Stepを繋げる
            return self._append_mcmds(flow_cmd, point, vcmd_args, vcmd_is_table)

    def _append_beams(self, flow_cmd:FlowCommand, point:Point, vcmd_args:dict, vcmd_is_table:bool):

        # RowRange Stepを作成する
        rowrange_cmd = CommandLink('beam_rowrange').resolve()
        rowrange_step = Step(rowrange_cmd.label, rowrange_cmd, vcmd_args)

        # ToList Stepを作成する 
        tolist_cmd = CommandLink('beam_tolist').resolve()
        tolist_step = Step(tolist_cmd.label, tolist_cmd, vcmd_args)

        # RowRangeの出力Pointを作成する
        point_id = point.id + '_rowrange'
        rowrange_point = Point(point_id, Tube(Port('o', 'beam'), rowrange_step), None, Tube(Port('i', 'beam'), tolist_step))
        # ToListの出力Pointを作成する
        point_id = point.id + '_tolist_o'
        tolist_point_o = Point(point_id, Tube(Port('o', 'beam'), tolist_step))

        # pointにRowRangeを繋げる
        point.add_dst_tube(Tube(Port('i', 'beam'), rowrange_step))

        # 作成したPointとStepをフローコマンドに登録する
        flow_cmd.substeps.append(rowrange_step)
        flow_cmd.substeps.append(tolist_step)
        flow_cmd.points.add(rowrange_point)
        flow_cmd.points.add(tolist_point_o)

        return tolist_point_o, None

    def _append_mcmds(self, flow_cmd:FlowCommand, point:Point, vcmd_args:dict, vcmd_is_table:bool):

        # UTF-8への変換コマンドを作成する
        # (S_JISをwritelistコマンドに入力するとDockerが終了するので)
        convtoutf8 = CommandLink('convtoutf8').resolve()
        convtoutf8_step = Step(convtoutf8.label, convtoutf8, {'target_encoding':'utf-8','target_newline':'\n'})

        # RowRange Stepを作成する
        rowrange_cmd = CommandLink('rowrange').resolve()
        rowrange_step = Step(rowrange_cmd.label, rowrange_cmd, vcmd_args)

        # Align Stepを作成する
        align_cmd = CommandLink('align').resolve()
        align_step = Step(align_cmd.label, align_cmd)

        # ToList Stepを作成する 
        # tolist_cmd = CommandLink('to_pipe').resolve()
        if vcmd_is_table:
            tolist_cmd = CommandLink('to_list').resolve()
        else:
            tolist_cmd = CommandLink('to_tlist').resolve()
        tolist_step = Step(tolist_cmd.label, tolist_cmd, vcmd_args)

        # ConvToUtf8の出力Pointを作成する
        point_id = point.id + '_convtoutf8'
        convtoutf8_point = Point(point_id, Tube(Port('o', 'mcmd'), convtoutf8_step), None, Tube(Port('i', 'mcmd'), rowrange_step))
        # RowRangeの出力Pointを作成する
        point_id = point.id + '_rowrange'
        rowrange_point = Point(point_id, Tube(Port('o', 'mcmd'), rowrange_step), None, Tube(Port('i', 'mcmd'), align_step))
        # Alignの出力Pointを作成する
        point_id = point.id + '_align'
        align_point = Point(point_id, Tube(Port('o', 'mcmd'), align_step), None, Tube(Port('i', 'mcmd'), tolist_step))
        # ToListの出力Pointを作成する
        point_id = point.id + '_tolist_o'
        tolist_point_o = Point(point_id, Tube(Port('o', 'mcmd'), tolist_step))
        if not vcmd_is_table:
            point_id = point.id + '_tolist_u'
            tolist_point_u = Point(point_id, Tube(Port('u', 'mcmd'), tolist_step))
        else:
            tolist_point_u = None

        # pointにConvToUtf8 Stepを繋げる
        point.add_dst_tube(Tube(Port('i', ['mcmd','matrix']), convtoutf8_step))

        flow_cmd.substeps.append(convtoutf8_step)
        flow_cmd.substeps.append(rowrange_step)
        flow_cmd.substeps.append(align_step)
        flow_cmd.substeps.append(tolist_step)
        flow_cmd.points.add(convtoutf8_point)
        flow_cmd.points.add(rowrange_point)
        flow_cmd.points.add(align_point)
        flow_cmd.points.add(tolist_point_o)
        if tolist_point_u is not None:
            flow_cmd.points.add(tolist_point_u)

        return tolist_point_o, tolist_point_u

    def do_append_after_runs(self, flow_cmd:FlowCommand, o_point:Point, u_point:Point, vis_arg:dict):
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
        vcmd_point = Point(o_point.id + '_v', Tube(Port('o', 'out'), vcmd_step))

        # VCommandにRunsCommandの出力Pointを繋げる
        o_point.add_dst_tube(Tube(Port('i', 'out'), vcmd_step))
        # グラフ表示の場合はVCommandにヘッダ出力(u)も繋げる
        if u_point is not None:
            u_point.add_dst_tube(Tube(Port('m', 'out'), vcmd_step))

        flow_cmd.substeps.append(vcmd_step)
        flow_cmd.points.add(vcmd_point)

        return vcmd_point


class RunsCommandAppender():
    class Appender():
        def __init__(self, runs_command_id:str, in_port_type:str):
            # Runsコマンドへの入力Portの型
            self._in_port_type = in_port_type
            # Runsコマンドを取得する
            runs_cmd = CommandLink(runs_command_id).resolve()
            # Runsステップのo_portsへはdo_append()を呼び出す度に出力Portを1つ追加する
            self.runs_o_ports = []
            # Runsステップを作成する
            # (CommandExceptionが入力された場合の処理をRunsCommand内で行うためex_acceptable=Trueとする)
            self.runs_step = Step('runs', runs_cmd, o_ports=self.runs_o_ports, ex_acceptable=True)
            # ポート名は0番から順に採番する
            self._next_port_no = 0
            # FlowCommand.substepsにruns_stepをすでに追加した場合はTrue
            self._already_step_added = False

        def do_append(self, flow_cmd:FlowCommand, point1:Point, point2:Point=None):
            if point2 is None:
                return self._do_append_one(flow_cmd, point1), None
            else:
                return self._do_append_one(flow_cmd, point1), self._do_append_one(flow_cmd, point2)

        def _do_append_one(self, flow_cmd:FlowCommand, point:Point):
            # RunsCommandに繋げるPointを作成する
            port_label = str(self._next_port_no)
            self._next_port_no += 1

            point_id = point.id + '_runs'
            runs_point = Point(point_id, Tube(Port(port_label, 'out'), self.runs_step))

            # Stepのportsに追加する
            self.runs_o_ports.append(Port(port_label, 'out'))

            # ここでRunsCommandを繋げる
            point.add_dst_tube(Tube(Port(port_label, self._in_port_type), self.runs_step))

            if not self._already_step_added:
                flow_cmd.substeps.append(self.runs_step)
                self._already_step_added = True

            flow_cmd.points.add(runs_point)
            return runs_point

    def __init__(self):
        # Apache Beam
        self._beam_runs_cmd_appender = RunsCommandAppender.Appender('beam_run', 'beam')
        # nysol_python
        self._mcmd_runs_cmd_appender = RunsCommandAppender.Appender('runs', 'mcmd')

    def do_append(self, flow_cmd:FlowCommand, point1:Point, point2:Point=None):
        if 'beam' in point1.src_tubes[0].port.types:
            # 接続先Pointの入力Portの型が'beam'の場合は、BeamのRunStepを繋げる
            return self._beam_runs_cmd_appender.do_append(flow_cmd, point1, point2)
        else:
            # 'mcmd'の場合は、nysol_pythonのRunsStepを繋げる
            return self._mcmd_runs_cmd_appender.do_append(flow_cmd, point1, point2)


class ActivityDataDestAppender():
    def __init__(self, datum_factory, flow:Flow, args:dict={}):
        self.flow_uuid = flow.uuid
        # アクティビティフォルダを取得する
        folder_store = datum_factory.load_activity_folder()
        # Activityコマンドを取得する
        activity_cmd = CommandLink('activity').resolve()
        # Activity Datumを作成する
        activity = folder_store.create_activity(flow.label, flow, args)
        # Activity Stepへの引数を作成する
        activity_args = {'activity': activity, 'is_vis':False, 'points':{}}
        # Activity Stepを作成する
        self.activity_step = Step('activity', activity_cmd, activity_args, ex_acceptable=True)
        self.activity_uuid = activity.uuid
        # ポート名は0番から順に採番する
        self._next_port_no = 0
        # FlowCommand.substepsにruns_stepをすでに追加した場合はTrue
        self._already_step_added = False

    def set_is_vis(self):
        self.activity_step.args['is_vis'] = True

    def do_append(self, flow_cmd:FlowCommand, point:Point, src_point_of_data_dst):
        # Activity Stepのargsにpointを追加する
        port_label = str(self._next_port_no)
        self.activity_step.args['points'][port_label] = src_point_of_data_dst

        # PointにActivity Stepを繋げる
        point.add_dst_tube(Tube(Port(port_label, 'out'), self.activity_step))

        self._next_port_no += 1

        if self._already_step_added:
            # Pointを新規追加しない場合はNoneを返す
            return None

        # Activity_pointを作成し、これにActivity Stepを繋げる
        point_id = point.id + '_activity_' + port_label
        return self.make_activity_point(flow_cmd, point_id)

    def make_activity_point(self, flow_cmd:FlowCommand, point_id:str):
        """
        Activity Pointを作成する
        """
        activity_point = Point(point_id, Tube(Port('o', 'activity'), self.activity_step))
        flow_cmd.substeps.append(self.activity_step)
        flow_cmd.points.add(activity_point)
        self._already_step_added = True
        return activity_point
