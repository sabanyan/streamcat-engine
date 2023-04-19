from collections import Iterator
from streamcat.core import Port
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

    def __hash__(self):
        return hash(self.port.label + self.step.id)

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


class Tubes:

    def __init__(self, tubes:set[Tube]=set()):
        # tubesはset型なのでTubeの重複は無い
        # NOTE: setよりlistの方がイテレーション速度が若干早いらしいのでlistを用いる
        self._tubes = list(tubes)

    def __repr__(self):
        return self._tubes.__repr__()

    def __iter__(self) -> Iterator[Tube]:
        yield from self._tubes

    def __contains__(self, tube:Tube):
        return tube in self._tubes

    def __getitem__(self, index) -> Tube:
        return self._tubes[index]

    def __len__(self):
        return len(self._tubes)
    
    def __sub__(self, other):
        return Tubes(set(self._tubes) - set(other._tubes))

    def add(self, tube:Tube):
        """
        Tubeを追加する
        """
        if tube in self._tubes:
            raise Exception(f'同じTube({tube})が既に存在します')
        self._tubes.append(tube)

    def update(self, tubes):
        """
        Tubeを全て追加する
        重複する場合は引数で追加したTubeで上書きする
        """
        for tube in tubes:
            if tube in self._tubes:
                i = self._tubes.index(tube)
                self._tubes[i] = tube
            else:
                self._tubes.append(tube)

    def remove(self, tube:Tube):
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

    def filter_by_step(self, step:Step):
        """
        Stepに紐づくTubesを返す
        """
        rets = Tubes()
        rets._tubes = [tube for tube in self._tubes if tube.step==step]
        return rets

    def filter_with_subflow(self):
        """
        Flow Stepに紐づくTubesを返す
        """
        rets = Tubes()
        rets._tubes = [tube for tube in self._tubes if tube.step.is_flow]
        return rets

    def sort(self):
        """
        Portのlabelでソートする
        """
        return sorted(self._tubes)

    def have_step(self, step:Step):
        return len(self.filter_by_step(step)) > 0

    def have_tube(self, port:Port, step:Step):
        rets = Tubes()
        rets = self.filter_by_step(step)
        return len([t for t in rets if t.port == port]) > 0
