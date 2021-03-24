from .tube import Tubes

class Point:
    """
    データノードのインスタンスを表現するクラス
    """
    def __init__(self, point_id, src_tube, datum, dst_tube, is_in=False, is_out=False, cache=False):
        if point_id is None:
            raise Exception('point_idにNoneは指定できません')

        self.id = point_id
        self.label = ''

        # 親フローに繋がるPoint、かつコマンドの出力Pointの場合、src_tubesは2つのTubeを持つ
        self.src_tubes = Tubes(src_tube)
        self.datum = datum
        self.dst_tubes = Tubes(dst_tube)

        # フローの入力ポートか
        self.is_in = is_in
        # フローの出力ポートか
        self.is_out = is_out
        
        self.cache = cache

    def __repr__(self):
        dom_o = ''
        for tube in self.src_tubes:
            if tube.port is not None:
                if tube.step is None:
                    dom_o += f'(None.{tube.port.label})'
                else:
                    dom_o += f'({tube.step}.{tube.port.label})'
            else:
                dom_o += f'({tube.step}.None)'

        cod_i = ''
        for tube in self.dst_tubes:
            if tube.port is not None:
                if tube.step is None:
                    cod_i += f'(None.{tube.port.label})'
                else:
                    cod_i += f'({tube.step}.{tube.port.label})'
            else:
                cod_i += f'({tube.step}.None)'

        if self.datum is None:
            return f'{self.id}<{dom_o} -> {cod_i}>'
        else:
            return f'{self.id}<{dom_o} -({self.datum})-> {cod_i}>'

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    def __hash__(self):
        # # PointをDictのキーとして扱う場合同じインスタンスで同じとみなす
        # return id(self)
        return hash(self.id)

    @property
    def is_for_input(self):
        """
        親フローに繋がるPointで、かつDatumが格納されていなければTrueを返す
        """
        return self.src_tubes.find_flow_tube() is not None and self.datum is None

    @property
    def is_store(self):
        from kskp.store import Store
        return self.datum is not None and isinstance(self.datum, Store)

    # @property
    # def src_port(self):
    #     return self.src_tubes[0].port

    # @property
    # def src_runnable(self):
    #     """
    #     入力元Tubeのうち1番目のRunnableオブジェクト
    #     """
    #     return self.src_tubes[0].step

    @property
    def is_last(self):
        """
        フローの終端のものかどうか（サブ、rootどちらでも良い）
        targetのrunnableにNoneがある場合は終端となっている
        """
        return any(dst_tube.step is None for dst_tube in self.dst_tubes)

    @property
    def is_root_last(self):
        """
        rootのフローの終端かどうか
        """
        return self.dst_tubes.is_null

    # @property
    # def is_root_first(self):
    #     """
    #     rootのフローの始端かどうか
    #     """
    #     return self.src_runnable is None and self.src_port is None

    @property
    def is_cache(self):
        """
        キャッシュを生成するかどうか
        """
        return self.cache

    # def add_src_tube(self, tube):
    #     """
    #     指定したTubeでsrc_tubesを更新する
    #     複数のsrc_tubeをもつPointはないので、上書きだけ（appendする必要がない）
    #     """
    #     if self.src_tubes is None or len(self.src_tubes)==0 or self.src_tubes[0].is_null:
    #         self.src_tubes = Tubes(tube)
    #     else:
    #         self.src_tubes.add(tube)

    # def add_dst_tube(self, tube):
    #     """
    #     指定したTubeでdst_tubesを更新する
    #     既にdst_tubesに有効なTubeがあった場合は追加、
    #     そうではなかったら上書きする

    #     初期値が[Tube(None, None)]のため、appendするとTube(None, None)が残る
    #     なので、上書きしている
    #     """
    #     # if self.is_root_last:
    #     #     self.dst_tubes = Tubes(tube)
    #     # else:
    #     #     self.dst_tubes.add(tube)

    #     if self.dst_tubes is None or len(self.dst_tubes)==0 or self.dst_tubes[0].is_null:
    #         self.dst_tubes = Tubes(tube)
    #     else:
    #         self.dst_tubes.add(tube)