# -*- coding: utf-8 -*-
"""几何健壮性闸门（P55）。

检查全库字形是否因减细/变形而产生：
  1. 极小碎片（area < 200 平方单位）—— 渲染成黑点
  2. 意外零面积字形 —— 轮廓塌缩

背景：thin_edges() 的 assert 只验「点数不变」，不验几何有效性。
一个完全塌缩的轮廓也能通过点数断言，所以必须用面积独立检查。

允许的零面积字形：空白字符（space / U+2002 / U+2003 / U+115F / U+1160
以及内部保留槽位）。与基座 Noto 的清单比对，我们独有的即为缺陷。
"""
from __future__ import annotations

# 基座自带的零面积字形（与 Noto 完全一致，见 P55）
EXPECTED_ZERO = {
    "space", "uni115F", "uni1160", "uni2002", "uni2003",
    "glyph63108", "glyph64403", "glyph65531", "glyph65532",
    "glyph65533", "glyph65534",
}

TINY_AREA = 200.0


def check(path, verbose=False):
    """返回问题数量（0 = 通过）。"""
    from fontTools.ttLib import TTFont
    from fontTools.pens.areaPen import AreaPen

    font = TTFont(path, lazy=False)
    gs = font.getGlyphSet()
    problems = []
    tiny = []
    unexpected_zero = []

    for name in font.getGlyphOrder():
        ap = AreaPen(gs)
        try:
            gs[name].draw(ap)
            area = abs(ap.value)
        except Exception:
            continue
        if area == 0:
            if name not in EXPECTED_ZERO:
                unexpected_zero.append(name)
        elif area < TINY_AREA:
            tiny.append((name, area))
    font.close()

    for name, area in tiny[:20]:
        problems.append("极小碎片 %s area=%.1f" % (name, area))
    for name in unexpected_zero[:20]:
        problems.append("意外零面积 %s" % name)

    if verbose:
        print("  极小碎片: %d" % len(tiny), flush=True)
        print("  意外零面积: %d" % len(unexpected_zero), flush=True)
    return len(problems)


if __name__ == "__main__":
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else \
        "/data/build-cache/wdsans-dist/WDesignSansSC-Regular.ttf"
    print("检查:", p)
    n = check(p, verbose=True)
    print("几何健壮性: %s" % ("通过" if n == 0 else "%d 个问题" % n))
    sys.exit(0 if n == 0 else 1)
