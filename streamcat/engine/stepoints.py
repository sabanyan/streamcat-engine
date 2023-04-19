from .flow_port import FlowPort
from .step import Steps
from .point import Points

class Stepoints():
    """
    フローが含むStep、Point、フロー入出力Portを保持する
    """
    def __init__(self, steps:Steps, points:Points, i_ports:list[FlowPort], o_ports:list[FlowPort]):
        self.substeps = steps
        self.points = points
        self.i_ports = i_ports
        self.o_ports = o_ports
