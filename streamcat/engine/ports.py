from collections import Iterator
from streamcat.core import Port

class Ports():
    """
    Portの集合
    TODO: 全てのCommandクラスでlistから置き換えるたいけど手間
    """

    def __init__(self, ports:set=set()):
        # portsはset型なのでPortの重複は無い
        # NOTE: setよりlistの方がイテレーション速度が若干早いらしいのでlistを用いる
        self._ports = list(ports)

    def add(self, port:Port):
        """
        Portを追加する
        """
        if port in self._ports:
            raise Exception(f'同じid({port.label})のPortが既に存在します')
        self._ports.append(port)

    def get(self, port_label:str) -> Port:
        for port in self._ports:
            if port.label == port_label:
                return port
        return None

    def __repr__(self):
        return self._ports.__repr__()

    def __iter__(self) -> Iterator[Port]:
        yield from self._ports

    def __contains__(self, port:Port):
        return port in self._ports

    def __getitem__(self, port_label:str):
        port = self.get(port_label)
        if port is None:
            raise Exception(f'PortsにPort({port.label})は存在しません')
        else:
            return port

    def __len__(self):
        return len(self._ports)

