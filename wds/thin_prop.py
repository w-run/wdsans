# -*- coding: utf-8 -*-
"""P95: 按轮廓厚度比例减细（修正固定 upm 导致的不均匀）。

## 问题（实测）

固定偏移 d_h=6.0 / d_v=3.5（横减12、竖减7）对不同厚度的笔画打击不同：
  口   厚度 [75, 69]  → 减 12 是 16%
  餐   厚度 [37..59]  → 减 12 是 32%

实测墨量比（我们/Noto）随字数复杂度下降：
  轮廓 6-9   → 0.846
  轮廓 21-23 → 0.809
  与点数的相关系数 r = -0.589

这就是「同一字体笔画不均匀」的数学来源。

## 修法

按每条轮廓自身的平均厚度 t 决定内缩量：
    d = t * (1 - target_ratio) / 2
其中 t ≈ 2*面积/周长（等厚笔画的解析厚度）。

这样每条轮廓的面积都乘以 target_ratio，粗细比例得以保持。
"""
from __future__ import annotations
import math

from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def contour_thickness(seg):
    """平均笔画厚度 ≈ 2*面积/周长。"""
    n = len(seg)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = seg[i]
        x2, y2 = seg[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    a = abs(a) / 2.0
    p = 0.0
    for i in range(n):
        x1, y1 = seg[i]
        x2, y2 = seg[(i + 1) % n]
        p += math.hypot(x2 - x1, y2 - y1)
    if p < 1e-6:
        return 0.0
    return 2.0 * a / p


def thin_edges_proportional(font, target_ratio=0.875, h_v_ratio=0.946,
                            min_thick=6.0, verbose=False):
    """按轮廓厚度比例减细。

    target_ratio: 目标面积比（OPPO 相对 Noto = 0.8746）
    h_v_ratio:    横竖减薄比（保持 0.946 的光学补偿）
    min_thick:    厚度下限，避免极细笔画减成负数
    """
    from .thinning import _offset_miter, _area, split_contours

    glyf = font["glyf"]
    done = skipped = 0
    total_before = total_after = 0.0

    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            skipped += 1
            continue
        segs = split_contours(g)
        n_before = sum(len(s) for s in segs)
        out = []
        for seg in segs:
            if len(seg) < 3:
                out.extend(seg)
                continue
            a0 = abs(_area(seg))
            if a0 <= 0:
                out.extend(seg)
                continue
            t = contour_thickness(seg)
            if t < min_thick:
                out.extend(seg)
                continue
            # 每边内缩量：使面积乘以 target_ratio
            d = t * (1.0 - target_ratio) / 2.0
            d_h = d
            d_v = d * h_v_ratio
            best = None
            for sign in (1.0, -1.0):
                s2 = _offset_miter(seg, d_h, d_v, sign)
                a2 = abs(_area(s2))
                if best is None or a2 < best[0]:
                    best = (a2, s2)
            if best[0] < a0:
                out.extend(best[1])
                total_before += a0
                total_after += best[0]
            else:
                out.extend(seg)
                total_before += a0
                total_after += a0
        assert len(out) == n_before, f"{name}: 点数变了"
        gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in out])
        gc.toInt()
        g.coordinates = gc
        for a in ("xMin", "yMin", "xMax", "yMax"):
            if hasattr(g, a):
                delattr(g, a)
        done += 1

    if verbose and total_before > 0:
        print("  实测面积比: %.4f (目标 %.4f)" % (
            total_after / total_before, target_ratio))
    return done, skipped