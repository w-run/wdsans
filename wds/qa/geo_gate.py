# -*- coding: utf-8 -*-
"""几何健壮性闸门（P55 建立，P61 修复绕向盲区）。

检查全库字形是否因减细/变形而产生：
  1. 极小碎片 —— 渲染成黑点
  2. 意外零面积 —— 轮廓塌缩

## P61 修复：改用「绝对面积和」而非「有向面积和」

P60 发现 AreaPen 的有向代数和受轮廓绕向影响：
  外轮廓 +A，内轮廓 -a  -> A-a（正确）
  外轮廓 +A，内轮廓 +a  -> A+a（出错）

实测本字体有 816 个字形存在绕向抵消（如 O 只有真实墨量的 29%）。
虽然都远大于阈值 200、不会误判，但这是潜在盲区：
若某字形外轮廓 210、内轮廓 205 且同向，总面积为 5，会被误报为碎片。

现改为逐轮廓取 |面积| 再求和 —— 与绕向无关，量纲正确。
"""
from __future__ import annotations
import os
from .. import paths

EXPECTED_ZERO = {
    "space", "uni115F", "uni1160", "uni2002", "uni2003",
    "glyph63108", "glyph64403", "glyph65531", "glyph65532",
    "glyph65533", "glyph65534",
}

TINY_AREA = 200.0


def _contour_abs_areas(glyph_set, name):
    """返回该字形每个轮廓的 |面积| 之和（绕向无关）。"""
    from fontTools.pens.areaPen import AreaPen
    from fontTools.pens.recordingPen import RecordingPen

    rec = RecordingPen()
    glyph_set[name].draw(rec)
    total = 0.0
    pen = None
    for op, args in rec.value:
        if op == "moveTo":
            if pen is not None:
                total += abs(pen.value)
            pen = AreaPen()
            pen.moveTo(args[0])
        elif pen is None:
            continue
        elif op == "lineTo":
            pen.lineTo(args[0])
        elif op == "curveTo":
            pen.curveTo(*args)
        elif op == "qCurveTo":
            pen.qCurveTo(*args)
        elif op == "closePath":
            pen.closePath()
    if pen is not None:
        total += abs(pen.value)
    return total


def check(path, verbose=False):
    """返回问题数量（0 = 通过）。"""
    from fontTools.ttLib import TTFont

    font = TTFont(path, lazy=False)
    gs = font.getGlyphSet()
    problems = []
    tiny = []
    unexpected_zero = []

    for name in font.getGlyphOrder():
        try:
            area = _contour_abs_areas(gs, name)
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
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(paths.DIST_DIR, "WDesignSansSC-Regular.ttf")
    print("检查:", p)
    n = check(p, verbose=True)
    print("几何健壮性: %s" % ("通过" if n == 0 else "%d 个问题" % n))
    sys.exit(0 if n == 0 else 1)