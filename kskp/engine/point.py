class Point:
    """
    データノードのインスタンスを表現するクラス
    """
    def __init__(self, point_id, src_tubes, datum, dst_tubes, is_in=False, is_out=False, cache=False):
        if point_id is None:
            raise Exception('point_idにNoneは指定できません')

        self.id = point_id
        self.label = ''

        self.src_tubes = src_tubes
        self.datum = datum
        self.dst_tubes = dst_tubes

        # フローの入力ポートか
        self.is_in = is_in
        # フローの出力ポートか
        self.is_out = is_out
        
        self.cache = cache

    def __repr__(self):

        if self.src_port is not None:
            if self.src_runnable is None:
                dom_o = f'self.{self.src_port.label}'
            else:
                dom_o = f'{self.src_runnable}.{self.src_port.label}'
        else:
            dom_o = f'{self.src_runnable}.None'

        cod_i = ''
        for tube in self.dst_tubes:
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
        return self.src_runnable is None and self.src_port is not None and self.datum is None

    @property
    def is_store(self):
        from kskp.store import Store
        return self.datum is not None and isinstance(self.datum, Store)

    @property
    def src_port(self):
        return self.src_tubes[0].port

    @property
    def src_runnable(self):
        """
        入力元Tubeのうち1番目のRunnableオブジェクト
        """
        return self.src_tubes[0].runnable

    @property
    def is_last(self):
        """
        フローの終端のものかどうか（サブ、rootどちらでも良い）
        targetのrunnableにNoneがある場合は終端となっている
        """
        return any(t_tube.runnable is None for t_tube in self.dst_tubes)

    @property
    def is_root_last(self):
        """
        rootのフローの終端かどうか
        """
        return any(t_tube.runnable is None and t_tube.port is None for t_tube in self.dst_tubes)

    @property
    def is_first(self):
        """
        フローの始端のものかどうか（サブ、rootどちらでも良い）
        """
        return self.src_runnable is None

    @property
    def is_root_first(self):
        """
        rootのフローの始端かどうか
        """
        return self.src_runnable is None and self.src_port is None

    @property
    def is_cache(self):
        """
        キャッシュを生成するかどうか
        """
        return self.cache

    def add_src_tube(self, tube):
        """
        指定したTubeでsrc_tubesを更新する
        複数のsrc_tubeをもつPointはないので、上書きだけ（appendする必要がない）
        """
        self.src_tubes = [tube]

    def add_dst_tube(self, tube):
        """
        指定したTubeでdst_tubesを更新する
        既にdst_tubesに有効なTubeがあった場合は追加、
        そうではなかったら上書きする

        初期値が[Tube(None, None)]のため、appendするとTube(None, None)が残る
        なので、上書きしている
        """
        if self.is_root_last:
            self.dst_tubes = [tube]
        else:
            self.dst_tubes.append(tube)
