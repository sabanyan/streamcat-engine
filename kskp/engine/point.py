class Point:
    """
    o->iの順番なので注意
    """

    def __init__(self, point_id, origin_tubes, datum, target_tubes, is_in=False, is_out=False, cache=False):
        if point_id is None:
            raise Exception('point_idにNoneは指定できません')

        self.id = point_id
        self.label = ''

        self.origin = origin_tubes
        self.datum = datum
        self.target = target_tubes

        # フローの入力ポートか
        self.is_in = is_in
        # フローの出力ポートか
        self.is_out = is_out
        
        self.cache = cache

    def __repr__(self):

        if self.o_port is not None:
            if self.o_runnable is None:
                dom_o = f'self.{self.o_port.label}'
            else:
                dom_o = f'{self.o_runnable}.{self.o_port.label}'
        else:
            dom_o = f'{self.o_runnable}.None'

        cod_i = ''
        for tube in self.target:
            if tube.port is not None:
                if tube.runnable is None:
                    cod_i += f'(self.{tube.port.label})'
                else:
                    cod_i += f'({tube.runnable}.{tube.port.label})'
            else:
                cod_i += f'({tube.runnable}.None)'

        if self.datum is None:
            return f'{self.id}<{dom_o} -> {cod_i}>'
        else:
            return f'{self.id}<{dom_o} -({self.datum})-> {cod_i}>'

    def __hash__(self):
        # PointをDictのキーとして扱う場合同じインスタンスで同じとみなす
        return id(self)

    @property
    def is_for_input(self):
        return self.o_runnable is None and self.o_port is not None and self.datum is None

    @property
    def is_store(self):
        from kskp.store import Store
        return self.datum is not None and isinstance(self.datum, Store)

    @property
    def o_port(self):
        return self.origin[0].port

    @property
    def o_runnable(self):
        """
        out_runableの略称ではないことに注意!
        """
        return self.origin[0].runnable

    @property
    def is_last(self):
        """
        フローの終端のものかどうか（サブ、rootどちらでも良い）
        targetのrunnableにNoneがある場合は終端となっている
        """
        return any(t_tube.runnable is None for t_tube in self.target)

    @property
    def is_root_last(self):
        """
        rootのフローの終端かどうか
        """
        return any(t_tube.runnable is None and t_tube.port is None for t_tube in self.target)

    @property
    def is_first(self):
        """
        フローの始端のものかどうか（サブ、rootどちらでも良い）
        """
        return self.o_runnable is None

    @property
    def is_root_first(self):
        """
        rootのフローの始端かどうか
        """
        return self.o_runnable is None and self.o_port is None

    @property
    def is_cache(self):
        """
        キャッシュを生成するかどうか
        """
        return self.cache

    def update_origin(self, tube):
        """
        指定したTubeでoriginを更新する
        複数のoriginをもつPointはないので、上書きだけ（appendする必要がない）
        """
        self.origin = [tube]

    def update_target(self, tube):
        """
        指定したTubeでtargetを更新する
        既にtargetに有効なTubeがあった場合は追加、
        そうではなかったら上書きする

        初期値が[Tube(None, None)]のため、appendするとTube(None, None)が残る
        なので、上書きしている
        """
        if self.is_root_last:
            self.target = [tube]
        else:
            self.target.append(tube)
