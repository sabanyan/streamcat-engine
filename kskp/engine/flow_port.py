from kskp.core import Port
from .point import Point

class FlowPort(Port):
    """
    フローのPort
    - フローのPortとPointは一対一で対応する
    """
    def __init__(self, label, port_type, point:Point):
        super().__init__(label, port_type)

        # Portに対応するフロー内のPoint
        self.point = point
