from collections import Iterator
from .tube import Tube, Tubes

class Point:
    """
    データノードのインスタンスを表現するクラス
    """
    def __init__(self, id:str, src_tube:Tube=None, datum=None, dst_tube:Tube=None, makeCache:bool=False):
        if id is None:
            raise Exception('point_idにNoneは指定できません')

        self.id = id
        # ラベルが指定されない場合はidと同じ値を設定する
        self.label = id

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

        # 入力ポートと出力ポートの型が不一致ならば例外を送出する
        self._validate_port_type(src_tube)
        
        self.makeCache = makeCache

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
        return other is not None and self.id == other.id

    def __ne__(self, other):
        return other is None or self.id != other.id

    def __hash__(self):
        # # PointをDictのキーとして扱う場合同じインスタンスで同じとみなす
        # return id(self)
        return hash(self.id)

    @property
    def is_store(self):
        from streamcat.store import Store
        return self.datum is not None and isinstance(self.datum, Store)

    @property
    def is_cache(self):
        """
        キャッシュを生成するかどうか
        """
        return self.makeCache

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

    def add_src_tube(self, src_tube:Tube):
        """
        入力ポートを追加する
        """
        # 入力ポートと出力ポートの型が不一致ならば例外を送出する
        self._validate_port_type(src_tube)
        # 入力ポートを追加する
        self.src_tubes.add(src_tube)

    def add_dst_tube(self, dst_tube:Tube):
        """
        出力ポートを追加する
        """
        # 入力ポートと出力ポートの型が不一致ならば例外を送出する
        self._validate_port_type(dst_tube)
        # 出力ポートを追加する
        self.dst_tubes.add(dst_tube)

    def _validate_port_type(self, tube:Tube):
        """
        引数で指定したPortが入出力Portの型に一致していることを確認する
        """
        def are_equal_type(tube1:Tube, tube2:Tube):
            # Portの型を比較する
            return tube1.port.types in tube2.port.types

        def raise_type_error(self_tube:Tube, other_tube:Tube):
            port_types = self_tube.port.types
            cmd_label = self_tube.step.command.label
            step_id = self_tube.step.id
            other_port_types = other_tube.port.types
            other_cmd_label = other_tube.step.command.label
            other_step_id = other_tube.step.id
            raise Exception(
                f'{cmd_label}({step_id})と{other_cmd_label}({other_step_id})の間でPortの型が一致しません' + \
                f'({port_types}!={other_port_types})')

        # 指定したPortがNoneの場合は確認しない
        if tube is None:
            return
        # 入力Portと一致することを確認する
        if not self.src_tubes.is_null and not are_equal_type(tube, self.src_tubes[0]):
            raise_type_error(tube, self.src_tubes[0])
        # 出力Portと一致することを確認する
        elif not self.dst_tubes.is_null and not are_equal_type(tube, self.dst_tubes[0]):
            raise_type_error(tube, self.dst_tubes[0])

class Points:

    def __init__(self, points:set=set()):
        # pointsはset型なのでPointの重複は無い
        # NOTE: setよりlistの方がイテレーション速度が若干早いらしいのでlistを用いる
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
            raise Exception(f'PointsにPoint({point_id})は存在しません')
        else:
            return point
        
    def __len__(self):
        return len(self._points)