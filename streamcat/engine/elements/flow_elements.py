from .step import Steps
from .point import Points
from .flow_port import FlowPorts

class FlowElements():
    """
    フローが含むStep、Point、フロー入出力Portを保持する
    """
    def __init__(self, steps:Steps=Steps(),
                 points:Points=Points(),
                 i_ports:FlowPorts=FlowPorts(),
                 o_ports:FlowPorts=FlowPorts()):
        self.steps = steps
        self.points = points
        self.i_ports = i_ports
        self.o_ports = o_ports
