from .upstreamer import Upstreamer
from .. import FlowCommand
from ..elements import FlowElements, Step, Point, FlowPorts, Tube, Tubes

class Pruner(Upstreamer):
    """
    フローを縦型探索して不要な接続を刈る
    """
    def __init__(self, flow_elements:FlowElements, is_main:bool=False) -> None:
        super().__init__(flow_elements.points)
        self._i_ports = flow_elements.i_ports
        self._o_ports = flow_elements.o_ports
        self._is_main = is_main

        # 全てのサブフローStepに対して、その入力Portへ繋がり、実行時に使用されるTube
        self._using_flow_dst_tubes = Tubes()

        # 全てのサブフローStepに対して、その出力Portから繋がり、実行時に使用されるTube
        self._using_flow_src_tubes = Tubes()

        # 全てのサブフローStepに対して、一つのPrunerオブジェクトを用意する
        self._subflow_pruners:dict[Step, Pruner] = {}
        for s in flow_elements.steps:
            if s.is_flow:
                subflow_elements = FlowElements(s.command.steps, s.command.points, s.command.i_ports, s.command.o_ports)
                self._subflow_pruners[s] = Pruner(subflow_elements)

    def traverse(self):
        """
        不要な接続を刈る
        """
        # フローの出力Portから入力Portを取得する
        self._search_up_i_ports(self._o_ports)

        # 全てのサブフローの探索を終えた後に不要な接続を刈る
        if self._is_main:
            self._cut_unusing_tubes()

    def _search_up_i_ports(self, o_ports:FlowPorts):
        """
        指定するフロー出力Portからフロー構造を逆に辿って、実行可能Stepとフロー入力Portを返す
        """
        # 指定するフロー出力Portから実行可能Stepを取得する
        invokable_steps = self._search_up_all_invokable_steps(o_ports)

        # 指定するフロー出力Portに紐づく開始Pointを取得する
        in_points = {p.point for p in o_ports if self._is_start_point(p.point)}

        # 実行可能Stepの入力Pointを取得する
        in_points.update({p for s in invokable_steps for p in self._points if p.dst_tubes.have_step(s)})

        # 開始Pointに紐づくフローの入力Portを返す
        return {i_port for in_point in in_points for i_port in self._i_ports if i_port.point == in_point}

    def _cut_unusing_tubes(self):
        """
        実行時に使用されないTubeを切断する
        """
        # サブフローを再起的に探索して使用されないTubeを切断する
        for subflow_pruner in self._subflow_pruners.values():
            subflow_pruner._cut_unusing_tubes()

        # 全てのサブフローStepへの入出力Tubeを集める
        all_flow_dst_tubes = Tubes({t for p in self._points for t in p.dst_tubes.filter_with_subflow()})
        all_flow_src_tubes = Tubes({t for p in self._points for t in p.src_tubes.filter_with_subflow()})

        # 使用されないサブフローStepへの入出力Tubeを集める
        prune_flow_dst_tubes = all_flow_dst_tubes - self._using_flow_dst_tubes
        prune_flow_src_tubes = all_flow_src_tubes - self._using_flow_src_tubes

        for p in self._points:
            # 使用されないサブフローStepへの入力Tubeを切断する
            for prune_flow_dst_tube in prune_flow_dst_tubes:
                p.dst_tubes.remove(prune_flow_dst_tube)
                # Invoker._prepare_inputs()での例外送出を防ぐため使用されない入力Portも閉じる
                prune_flow_dst_tube.step.command.close_i_port(prune_flow_dst_tube.port.label)
            # 使用されないサブフローStepからの出力Tubeを切断する
            for prune_flow_src_tube in prune_flow_src_tubes:
                p.src_tubes.remove(prune_flow_src_tube)
                prune_flow_src_tube.step.command.close_o_port(prune_flow_src_tube.port.label)

    def _get_prev_points(self, last_tube:Tube):
        """
        コマンドからの出力Tubeから入力Pointを取得する
        """
        step = last_tube.step
        o_port = last_tube.port

        if step.is_flow:
            # サブフローCommand
            subflow:FlowCommand = step.command

            # 指定するフロー出力PortをFlowPort型で取得する
            o_ports = {p for p in subflow.o_ports if p == o_port}

            # サブフローの出力Portからサブフローの入力Portを取得する
            subflow_pruner = self._subflow_pruners[step]
            i_ports = subflow_pruner._search_up_i_ports(o_ports)

            # そのサブフローの入力Portに紐づく入力Pointを取得する
            prev_points = {p for i_port in i_ports for p in self._points if p.dst_tubes.have_tube(i_port, step)}

            # サブフローの実行に必要な入力Tubeを記録する
            using_flow_dst_tubes = Tubes({Tube(i_port, step) for i_port in i_ports})
            self._using_flow_dst_tubes.update(using_flow_dst_tubes)

            # サブフローの実行に必要な出力Tubeを記録する
            using_flow_src_tubes = Tubes({Tube(o_port, step) for o_port in o_ports})
            self._using_flow_src_tubes.update(using_flow_src_tubes)

        else:
            prev_points = {p for p in self._points if p.dst_tubes.have_step(step)}

        return prev_points

    def _is_start_point(self, p:Point):
        """
        入力値が埋まっている、または、サブフローかつフロー入力Pointの場合はTrueを返す
        """
        return p.datum is not None or (not self._is_main and p in {i_port.point for i_port in self._i_ports})
