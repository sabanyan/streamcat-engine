from kskp.core import Port

class Tube:
    """
    portとstepの入れ物
    """
    def __init__(self, port:Port, step):
        self.port = port
        self.step = step

    def __repr__(self):
        if self.is_null:
            return f'(None.None)'
        else:
            return f'({self.step}.{self.port.label})'

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
        if self.is_null:
            # 初期値が[Tube(None, None)]のため、appendするとTube(None, None)が残る、なので上書きしている
            self._tubes = [tube]
        else:
            self._tubes.append(tube)

    @property
    def is_null(self):
        # return len([tube for tube in self._tubes if not tube.is_null]) == 0
        return len(self._tubes) == 0 or all(tube.is_null for tube in self._tubes)

    @property
    def is_in(self):
        """
        フローの開始Pointの場合にTrueを返す
        """
        return any(tube.is_flow_tube for tube in self._tubes)

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
        ret = Tubes()
        ret._tubes = [tube for tube in self._tubes if tube.step==step]
        return ret

    def have_step(self, step):
        return len(self.filter_by_step(step)) > 0

    def __iter__(self):
        yield from self._tubes

    def __getitem__(self, index) -> Tube:
        return self._tubes[index]

    def __len__(self):
        return len(self._tubes)