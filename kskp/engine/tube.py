class Tube:
    """
    portとrunnableの入れ物
    """
    def __init__(self, port, runnable):
        self.port = port
        self.runnable = runnable

    def __repr__(self):
        if self.is_None:
            return f'(None, None)'
        else:
            return f'({self.port.label}, {str(self.runnable)})'

    @property
    def is_None(self):
        return self.port is None and self.runnable is None

    @property
    def is_flow_tube(self):
        """
        親フローに繋がるTubeの場合はTrueを返す
        """
        return self.port is not None and self.runnable is None

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
        self._tubes.append(tube)

    def get_flow_tube(self):
        """
        親フローに繋がるTubeがあれば返す
        """
        for tube in self._tubes:
            if tube.is_flow_tube:
                # 1つのPointoに、フローに繋がるTubeが複数存在することはない
                return tube
        return None

    def __iter__(self):
        yield from self._tubes

    def __getitem__(self, index) -> Tube:
        return self._tubes[index]

    def __len__(self):
        return len(self._tubes)