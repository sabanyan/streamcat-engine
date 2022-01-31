from typing import Iterator
from kskp.core import Port
from .step import Step

class Tube:
    """
    PortとStepの入れ物
    """
    def __init__(self, port:Port, step:Step):
        self.port = port
        self.step = step

    def __repr__(self):
        if self.is_null:
            return f'(None.None)'
        else:
            return f'({self.step}.{self.port.label})'

    def __eq__(self, other):
        return self.port == other.port and self.step == other.step

    def __ne__(self, other):
        return self.port != other.port or self.step != other.step

    def __lt__(self, other):
        return self.port < other.port

    def __gt__(self, other):
        return self.port > other.port

    @property
    def is_null(self):
        return self.port is None and self.step is None

    @property
    def is_command_tube(self):
        """
        コマンドに繋がるTubeの場合はTrueを返す
        """
        return self.port is not None and self.step is not None

    @property
    def is_flow_tube(self):
        """
        親フローに繋がるTubeの場合はTrueを返す
        """
        return self.port is not None and self.step is None


class Tubes:
    """
    Tubeのリスト
    """
    def __init__(self, *tubes) -> None:
        if len(tubes)==0:
            self._tubes = []
        else:
            self._tubes = list(tubes)

    def add(self, tube):
        """
        Tubeを追加する
        """
        self._tubes.append(tube)

    def remove(self, tube):
        """
        Tubeを削除する
        """
        for t in self._tubes:
            if t.port == tube.port and t.step == tube.step:
                self._tubes.remove(tube)
                return
        return

    @property
    def is_null(self):
        return len(self._tubes) == 0 or all(tube.is_null for tube in self._tubes)

    def find_command_tube(self) -> Tube:
        """
        コマンドに繋がるTubeを返す
        """
        for tube in self._tubes:
            # Pointの入力Tubeの場合、1つのPointに、コマンドに繋がるTubeが複数存在することはないだろう
            if tube.is_command_tube:
                return tube
        return None 

    def find_flow_tube(self) -> Tube:
        """
        親フローに繋がるTubeを返す
        """
        for tube in self._tubes:
            if tube.is_flow_tube:
                # 1つのPointに、フローに繋がるTubeが複数存在することはない
                return tube
        # フローに繋がるTubeが無ければNoneを返す
        return None

    def select_flow_tube(self):
        """
        親フローに繋がるTubeを返す、無ければ他のTubeを返す
        """
        return self.find_flow_tube() or self._tubes[0]

    def filter_by_step(self, step):
        """
        Stepに紐づくTubesを返す
        """
        rets = Tubes()
        rets._tubes = [tube for tube in self._tubes if tube.step==step]
        return rets

    def sort(self):
        """
        Portのlabelでソートする
        """
        return sorted(self._tubes)

    def have_step(self, step):
        return len(self.filter_by_step(step)) > 0

    def __repr__(self):
        return self._tubes.__repr__()

    def __iter__(self) -> Iterator[Tube]:
        yield from self._tubes

    def __getitem__(self, index) -> Tube:
        return self._tubes[index]

    def __len__(self):
        return len(self._tubes)