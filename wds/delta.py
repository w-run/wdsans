"""增量形变引擎 —— 本项目的心脏。

原理：
  基座 VF 里，每个字形的点 = Base(默认实例) + delta × f(wght)
  gvar 存的就是这份 delta（每字形 1 个 tuple，peak 0→1，即默认→900）。

做法：
  只改 delta 向量，不改 Base、不改点数、不改顺序。
  → 拓扑天然守恒，VF 天然成立，曲线天然不会退化。

已验证（spike）：
  identity 改写 delta → @400/@900 轮廓 maxdiff = 0，拓扑 100% 一致。
"""
from __future__ import annotations
from fontTools.ttLib import TTFont

from .base import glyph_point_counts
from .contours import read_points, flatten

PHANTOM = 4  # TrueType 每字形末尾有 4 个 phantom 点（左右 origin + 上下 advance）


class DeltaView:
    """对某个字形的 gvar delta 做读写。"""

    __slots__ = ("font", "name", "n_points", "tuple_index")

    def __init__(self, font: TTFont, name: str, tuple_index: int = 0):
        self.font = font
        self.name = name
        self.tuple_index = tuple_index
        counts = glyph_point_counts(font)
        n = counts[name]
        if n < 0:
            raise NotImplementedError(f"{name}: 复合字形需先展开")
        self.n_points = n

    @property
    def _tv(self):
        return self.font["gvar"].variations[self.name][self.tuple_index]

    def get(self):
        """返回真实点（不含 phantom）的 delta 列表 [(dx,dy), ...]。"""
        coords = self._tv.coordinates
        if len(coords) != self.n_points + PHANTOM:
            raise ValueError(
                f"{self.name}: gvar 坐标数 {len(coords)} != 点数 {self.n_points}+{PHANTOM}"
            )
        return [tuple(c) for c in coords[: self.n_points]]

    def set(self, deltas):
        if len(deltas) != self.n_points:
            raise ValueError(f"{self.name}: delta 数 {len(deltas)} != 点数 {self.n_points}")
        tv = self._tv
        coords = list(tv.coordinates)
        phantom = coords[self.n_points:]
        tv.coordinates = [tuple(d) for d in deltas] + phantom


def assert_same_shape(a, b, where=""):
    """断言两份轮廓点数/顺序/on-off 完全一致。任何算子后都必须过这一关。"""
    if len(a) != len(b):
        raise AssertionError(f"{where}: 轮廓数不同 {len(a)} != {len(b)}")
    for ci, (ca, cb) in enumerate(zip(a, b)):
        if len(ca) != len(cb):
            raise AssertionError(f"{where}: 轮廓 {ci} 点数不同 {len(ca)} != {len(cb)}")
        for pi, (pa, pb) in enumerate(zip(ca, cb)):
            if pa.on != pb.on:
                raise AssertionError(f"{where}: 轮廓 {ci} 点 {pi} on/off 类型变了")


def apply_to_glyph(font: TTFont, name: str, fn):
    """对单个字形的 delta 应用 fn(deltas) -> deltas'。

    fn 收到的坐标是**真实点空间**的位移量；返回同长度列表。
    内部自动做点数断言。
    """
    dv = DeltaView(font, name)
    before = dv.get()
    after = list(fn(list(before)))
    if len(after) != len(before):
        raise AssertionError(f"{name}: 算子改变了 delta 长度 {len(before)} -> {len(after)}")
    dv.set(after)
    return before, after


def transform_all(font: TTFont, fn, only=None):
    """对全字体（或指定字形集）的 delta 应用 fn。"""
    gvar = font["gvar"]
    names = [n for n in gvar.variations if (only is None or n in only)]
    done, skipped = 0, 0
    counts = glyph_point_counts(font)
    for name in names:
        if counts.get(name, -1) < 0:
            skipped += 1
            continue
        tvs = gvar.variations[name]
        if not tvs:
            skipped += 1
            continue
        try:
            apply_to_glyph(font, name, fn)
            done += 1
        except (ValueError, NotImplementedError):
            skipped += 1
    return done, skipped
