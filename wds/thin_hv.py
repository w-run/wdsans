# -*- coding: utf-8 -*-
"""P97: 修正比例减细——保留横竖比（OPPO 1.074）。

## 问题（实测）

上一版 thin_edges_proportional 得到：
  我们: 横72.0 竖72.0 竖/横 1.000
  OPPO: 横68.0 竖73.0 竖/横 1.074

横竖比被抹平成 1.000，丢掉了光学补偿（竖略粗于横，视觉才等重）。

## 根因

原实现用「轮廓厚度 t = 2A/P」统一决定内缩量 d，
而 h_v_ratio 只是把 d_v 乘个系数——但 d 本身已经把横竖混在一起，
乘完再被「矢量和/交点」的法向合成均化，效果消失。

## 修法

按**边方向**分别给减量，且减量以「该方向笔画的典型厚度」归一：
  - 横边（法向竖直）：d_h = t * (1-ratio) / 2 * k_h
  - 竖边（法向水平）：d_v = t * (1-ratio) / 2 * k_v
其中 k_h/k_v 由目标横竖比反解，保证减细后 v/h 达到目标。

更稳的做法：直接用「目标厚度」而不是「比例系数」——
因为 Noto 的横竖厚度已接近（0.982），要变成 1.074 只需竖少减一点。
"""
from __future__ import annotations
import math

from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def contour_thickness(seg):
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


def _offset_miter_dir(seg, d_h, d_v, sign):
    """每条边按自身法向平移，角点取相邻偏移线交点。

    d_h 用于法向偏竖直的边（水平边 / 横画上下缘），
    d_v 用于法向偏水平的边（竖直边 / 竖画左右缘）。
    """
    n = len(seg)
    if n < 3:
        return seg

    def offset_line(i, j):
        x1, y1 = seg[i]
        x2, y2 = seg[j]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-9:
            return None
        nx, ny = -dy / L, dx / L
        d = d_h if abs(ny) >= abs(nx) else d_v
        return ((x1 + nx * d * sign, y1 + ny * d * sign), (dx, dy))

    lines = [offset_line(k, (k + 1) % n) for k in range(n)]

    def inter(l1, l2):
        if l1 is None or l2 is None:
            return None
        (p1, d1), (p2, d2) = l1, l2
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            return None
        t = ((p2[0]-p1[0])*d2[1] - (p2[1]-p1[1])*d2[0]) / den
        return (p1[0] + d1[0]*t, p1[1] + d1[1]*t)

    out = []
    maxmove = 3.0 * max(d_h, d_v)
    for k in range(n):
        prev = (k - 1) % n
        pt = inter(lines[prev], lines[k])
        if pt is None:
            l = lines[k] or lines[prev]
            if l is None:
                out.append(seg[k]); continue
            (px, py), (dx, dy) = l
            L2 = math.hypot(dx, dy)
            nx, ny = -dy/L2, dx/L2
            d = d_h if abs(ny) >= abs(nx) else d_v
            out.append((seg[k][0] + nx*d*sign, seg[k][1] + ny*d*sign))
            continue
        if math.hypot(pt[0]-seg[k][0], pt[1]-seg[k][1]) > maxmove:
            out.append(((seg[k][0]+pt[0])/2, (seg[k][1]+pt[1])/2))
        else:
            out.append(pt)
    return out


def _area(seg):
    n = len(seg)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = seg[i]
        x2, y2 = seg[(i+1) % n]
        a += x1*y2 - x2*y1
    return a / 2.0


def split_contours(g):
    coords = list(g.coordinates)
    segs = []
    start = 0
    for end in g.endPtsOfContours:
        segs.append(coords[start:end+1])
        start = end + 1
    return segs


def thin_proportional_hv(font, target_ratio=0.875, hv_boost=1.09,
                         min_thick=6.0, verbose=False):
    """比例减细，且保留/增强横竖比。

    target_ratio: 目标面积比
    hv_boost:     竖边减量相对横边的「放大」系数（>1 表示竖减得多 → 竖变细）。
                  Noto 竖/横=0.982，OPPO=1.074。要让竖相对横更粗，
                  应让竖边减得**更少**，故 hv_boost < 1。
    """
    glyf = font["glyf"]
    done = skipped = 0
    tb = ta = 0.0

    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            skipped += 1
            continue
        segs = split_contours(g)
        nb = sum(len(s) for s in segs)
        out = []
        for seg in segs:
            if len(seg) < 3:
                out.extend(seg); continue
            a0 = abs(_area(seg))
            if a0 <= 0:
                out.extend(seg); continue
            t = contour_thickness(seg)
            if t < min_thick:
                out.extend(seg); tb += a0; ta += a0; continue
            d = t * (1.0 - target_ratio) / 2.0
            # 竖边减得更少 → 竖相对变粗 → 竖/横 增大
            d_h = d
            d_v = d * hv_boost
            best = None
            for sign in (1.0, -1.0):
                s2 = _offset_miter_dir(seg, d_h, d_v, sign)
                a2 = abs(_area(s2))
                if best is None or a2 < best[0]:
                    best = (a2, s2)
            if best[0] < a0:
                out.extend(best[1]); tb += a0; ta += best[0]
            else:
                out.extend(seg); tb += a0; ta += a0
        assert len(out) == nb, name
        gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in out])
        gc.toInt()
        g.coordinates = gc
        for a in ("xMin","yMin","xMax","yMax"):
            if hasattr(g, a):
                delattr(g, a)
        done += 1

    if verbose and tb > 0:
        print("  实测面积比: %.4f (目标 %.4f)" % (ta/tb, target_ratio))
    return done, skipped