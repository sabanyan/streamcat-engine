from typing import Iterator
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

class FlowPorts():
    """
    FlowPortの集合
    """
    def __init__(self, ports:set[FlowPort]=set()):
        # portsはset型なのでPortの重複は無い
        # NOTE: setよりlistの方がイテレーション速度が若干早いらしいのでlistを用いる
        self._ports = list(ports)

    def __repr__(self):
        return self._ports.__repr__()

    def __iter__(self) -> Iterator[FlowPort]:
        yield from self._ports

    def __contains__(self, port:FlowPort):
        return port in self._ports

    def __getitem__(self, port_label:str):
        port = self.get(port_label)
        if port is None:
            raise Exception(f'PortsにPort({port.label})は存在しません')
        else:
            return port

    def __len__(self):
        return len(self._ports)

    def add(self, port:FlowPort):
        """
        Portを追加する
        """
        if port in self._ports:
            raise Exception(f'同じid({port.label})のPortが既に存在します')
        self._ports.append(port)

    def get(self, port_label:str):
        for port in self._ports:
            if port.label == port_label:
                return port
        return None

    def remove(self, port_label:str):
        """
        Portを削除する
        """
        for port in self._ports:
            if port.label == port_label:
                self._ports.remove(port)
                return
        return Exception(f'指定されたPort({port_label})は存在しませんでした')

    def remove_by_point(self, point:Point):
        """
        Portを削除する
        """
        for port in self._ports:
            if port.point == point:
                self._ports.remove(port)
                return
        return Exception(f'指定されたPoint({port})に紐づくPortは存在しませんでした')

    def clear(self):
        """
        全てのPortを削除する
        """
        self._ports.clear()

    def exists(self, port_label:str):
        return any(p.label==port_label for p in self._ports)

    def exists_by_point(self, point:Point):
        return any(p.point==point for p in self._ports)
