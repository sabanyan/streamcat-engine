from .point import Points, Point
from .flow_port import FlowPort
from .tube import Tube

def union(sets:list[set]):
    """
    ユーティリティ関数
    与えられた集合のiterableから、全体の和を作る
    """
    r = set()
    for s in sets:
        r |= s
    return r

class Upstreamer:
    """
    フロー構造を逆に辿る
    """
    def __init__(self, points:Points) -> None:
        self._points = points

    def _search_up_all_invokable_steps(self, o_ports:set[FlowPort]):
        """
        指定されたo_portsからフロー構造を逆に辿って、実行準備が整ったstepを見つけ出す
        """
        # まず、グラフ構造を解析する必要がある

        # 最初に「最後の矢印」を集める
        # 「最後」とはis_out=TrueのPointのことである
        # last_steps = set()
        # for p in self.o_ports:
        #     if p.point.datum is None:
        #         for src_tube in p.point.src_tubes:
        #             last_steps.add(src_tube.step)
        last_tubes = {src_tube for p in o_ports if not self._is_start_point(p.point) for src_tube in p.point.src_tubes}

        # それぞれについて、実行を開始するstepを探しに、巻き戻ってグラフ構造を辿る
        start_steps = union(self._search_up_invokable_steps(last_tube) for last_tube in last_tubes)

        return start_steps

    def _search_up_invokable_steps(self, last_tube:Tube):
        """
        指定された最後のTubeからフロー構造を逆に辿って、実行準備が整ったstepを見つけ出す
        """
        step = last_tube.step

        prev_points = self._get_prev_points(last_tube)

        # # Stepの入力にフローの出力Pointが含まれていたら、そこで試合終了ですよ
        # if not self.is_main and any(p.point in prev_points for p in self.o_ports):
        #     return set()

        # 全ての入力値が埋まっていれば、実行可能とみなして走査終了
        if all([self._is_start_point(p) for p in prev_points]):
            return {step}

        # 埋まっていないpointがあれば、それを逆に辿る
        return union(self._search_up_invokable_steps(last_tube=src_tube)
                     for p in prev_points if not self._is_start_point(p) for src_tube in p.src_tubes if src_tube.step is not None)

    def _get_prev_points(self, last_tube:Tube):
        """
        コマンドからの出力Tubeから入力Pointを取得する
        """
        step = last_tube.step
        return {p for p in self._points if p.dst_tubes.have_step(step)}

    def _is_start_point(self, p:Point):
        return p.datum is not None
