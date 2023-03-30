from streamcat.core import Port
from .point import Point

class FlowPort(Port):
    """
    フローのPort
    - フローのPortとPointは一対一で対応する
    """
    def __init__(self, label, port_types, point:Point, relayed=False):
        super().__init__(label, port_types)

        # Portに対応するフロー内のPoint
        self.point = point

        # SaverActivatorの中継Portとして開いた場合はTrue
        self.relayed = relayed

    def __repr__(self):
        return f'<Port({self.label}: {self.point.label})>'
