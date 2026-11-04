"""增量形变引擎 —— 本项目的心脏。

原理：
  基座 VF 里，每个字形的点 = Base(默认实例) + delta * f(wght)
  gvar 存的就是这份 delta（每字形 1 个 tuple，peak 0->1）。

做法：只改 delta 向量，不改 Base、不改点数、不改顺序。
  -> 拓扑天然守恒，VF 天然成立，曲线天然不会退化。

注意：gvar 的 delta 必须是**整数**（TrueType 规范），算子输出一律四舍五入。
"""
from __future__ import annotations

from fontTools.ttLib import TTFont

PHANTOM = 4


def build_point_table(font: TTFont) -> dict:
    """一次性建好 {glyph: 真实点数}。复合字形记 -1。"""
    glyf = font["glyf"]
    out = {}
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0:
            out[name] = 0
        elif g.numberOfContours > 0:
            out[name] = len(g.coordinates)
        else:
            out[name] = -1
    return out


def _to_int_delta(d):
    """gvar delta 必须是整数。四舍五入并保持 tuple 结构。"""
    return (int(round(d[0])), int(round(d[1])))


def transform_all(font: TTFont, fn, only=None, point_table=None):
    """对全字体 delta 应用 fn(deltas) -> deltas'。输出强制取整。"""
    gvar = font["gvar"]
    tbl = point_table or build_point_table(font)
    done = skipped = 0
    variations = gvar.variations
    for name in list(variations.keys()):
        if only is not None and name not in only:
            continue
        n = tbl.get(name, -1)
        if n <= 0 or not variations[name]:
            skipped += 1
            continue
        tv = variations[name][0]
        c = tv.coordinates
        if len(c) != n + PHANTOM:
            skipped += 1
            continue
        new = list(fn(list(c[:n])))
        assert len(new) == n, f"{name} delta 长度变了"
        tv.coordinates = [_to_int_delta(d) for d in new] + list(c[n:])
        done += 1
    return done, skipped
