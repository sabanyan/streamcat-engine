from typing import Iterator
from .tube import Tubes

class Point:
    """
    データノードのインスタンスを表現するクラス
    """
    def __init__(self, point_id, src_tube=None, datum=None, dst_tube=None, is_in=False, is_out=False, cache=False):
        if point_id is None:
            raise Exception('point_idにNoneは指定できません')

        self.id = point_id
        self.label = ''

        # 親フローに繋がるPoint、かつコマンドの出力Pointの場合、src_tubesは2つのTubeを持つ
        if src_tube is None:
            self.src_tubes = Tubes()
        else:
            self.src_tubes = Tubes(src_tube)
        self.datum = datum
        if dst_tube is None:
            self.dst_tubes = Tubes()
        else:
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
    def is_store(self):
        from kskp.store import Store
        return self.datum is not None and isinstance(self.datum, Store)

    @property
    def is_cache(self):
        """
        キャッシュを生成するかどうか
        """
        return self.cache

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


class Points:

    def __init__(self, points:set=set()):
        # pointsはset型なのでPointの重複は無い
        self._points = list(points)

    def add(self, point:Point):
        """
        Pointを追加する
        """
        if point in self._points:
            raise Exception(f'同じid({point.id})のPointが既に存在します')
        self._points.append(point)

    def update(self, points):
        """
        Pointを全て追加する
        重複する場合は引数で追加したPointで上書きする
        """
        for point in points:
            if point in self._points:
                i = self._points.index(point)
                self._points[i] = point
            else:
                self._points.append(point)

    def get(self, point_id:str) -> Point:
        for point in self._points:
            if point.id == point_id:
                return point
        return None

    def __repr__(self):
        return self._points.__repr__()

    def __iter__(self) -> Iterator[Point]:
        yield from self._points

    def __contains__(self, point:Point):
        return point in self._points

    def __getitem__(self, point_id:str):
        point = self.get(point_id)
        if point is None:
            raise Exception(f'PointsにPoint({point.id})は存在しません')
        else:
            return point
        
    def __len__(self):
        return len(self._points)