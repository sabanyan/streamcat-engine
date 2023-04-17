
from .flow_command import FlowCommand
from .point import Points, Point
from .tube import Tube
from .flow_port import FlowPort
from .upstreamer import Upstreamer

class Pruner(Upstreamer):
    """
    フローを縦型探索して不要な接続を刈る
    """
    def __init__(self, points:Points, i_ports:list[FlowPort], is_main:bool) -> None:
        super().__init__(points)
        self._i_ports = i_ports
        self._is_main = is_main

    def search_up_i_ports(self, o_ports:set[FlowPort]):
        """
        指定するフロー出力Portからフロー構造を逆に辿って、実行可能Stepとフロー入力Portを返す
        """
        # 指定するフロー出力Portから実行可能Stepを取得する
        invokable_steps = self._search_up_all_invokable_steps(o_ports)

        # 指定するフロー出力Portに紐づく開始Pointを取得する
        in_points = {p.point for p in o_ports if self._is_start_point(p.point)}

        # 実行可能Stepの入力Pointを取得する
        in_points.update({p for s in invokable_steps for p in self._points if p.dst_tubes.have_step(s)})

        # 開始Pointに紐づくフローの入力Portを取得する
        filtered_i_ports = {i_port for in_point in in_points for i_port in self._i_ports if i_port.point == in_point}

        # 実行可能Stepとフロー入力Portを返す
        return invokable_steps, filtered_i_ports

    def _get_prev_points(self, last_tube:Tube):
        
        step = last_tube.step
        o_port = last_tube.port

        # 該当stepの実行に必要なpointを取得する
        # prev_points = set()
        # for p in self.points:
        #     if p.dst_tubes.have_step(step):
        #         prev_points.add(p)

        if step.is_flow:
            # サブフローCommand
            subflow:FlowCommand = step.command

            # 指定するフロー出力PortをFlowPort型で取得する
            o_ports = {p for p in subflow.o_ports if p == o_port}

            # サブフローの出力Portからサブフローの開始Stepと入力Portを取得する
            subflow_pruner = Pruner(subflow.points, subflow.i_ports, subflow.is_main)
            start_steps, i_ports = subflow_pruner.search_up_i_ports(o_ports)

            # そのサブフローの入力Portに紐づく入力Pointを取得する
            prev_points = {p for i_port in i_ports for p in self._points if p.dst_tubes.have_tube(i_port, step)}

            # サブフローの実行に必要な出力PortだけをStepに設定する
            if 'o_ports' not in step.args:
                step.args['o_ports'] = set()
            step.args['o_ports'].update(o_ports)

            # サブフローの実行に必要な入力PointだけをStepに設定する
            if 'prev_points' not in step.args:
                step.args['prev_points'] = set()
            step.args['prev_points'].update(prev_points)

        else:
            prev_points = {p for p in self._points if p.dst_tubes.have_step(step)}

        return prev_points

    def _is_start_point(self, p:Point):
        """
        入力値が埋まっている、または、サブフローかつフロー入力Pointの場合はTrueを返す
        """
        return p.datum is not None or (not self._is_main and p in {i_port.point for i_port in self._i_ports})
