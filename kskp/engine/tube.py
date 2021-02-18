class Tube:
    """
    portとrunnableの入れ物
    """
    def __init__(self, port, runnable):
        self.port = port
        self.runnable = runnable

    def __repr__(self):
        return f'({self.port.label}, {str(self.runnable)})'

    @property
    def is_None(self):
        return self.port is None and self.runnable is None
