# -*- coding: utf-8 -*-
"""P101: 曲线段拉直 —— 把「近似直线却被画成曲线」的段改成真直线。

## 原理

TrueType 每个曲线 span = 两个 on 点之间夹着若干 off 点。
若 off 点偏离 on-on 弦线的程度很小（相对弦长），说明这段「本该是直线」，
只是用了曲线控制点 —— 这就是装饰性曲线。

做法：把这些 off 点垂直投影到 on-on 弦上 => 曲线段退化为直线段。
只移动节点，不增删，拓扑不变。

## 判据

dev   = max(off 点到弦的垂直距离)
ratio = dev / chord_length

若 ratio < tol 且 chord_length > min_len，则拉直。
真正的弯笔（撇、捺）dev 很大，ratio 远超阈值，会被保留。
"""

from __future__ import annotations
import math


def _perp_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return math.hypot(px - ax, py - ay)
    return abs((px - ax) * dy - (py - ay) * dx) / L


def _project(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < 1e-9:
        return (px, py)
    t = ((px - ax) * dx + (py - ay) * dy) / L2
    return (ax + t * dx, ay + t * dy)


def flatten_span_in_contour(coords, flags, idxs, tol, min_len, max_dev_abs):
    """对单个轮廓 id 列表处理，返回 (flat, total)。coords 会被原地修改。"""
    n = len(idxs)
    if n < 4:
        return 0, 0

    # 局部序号 -> 全局序号
    g = idxs
    on_local = [i for i in range(n) if flags[g[i]]]
    if len(on_local) < 2:
        return 0, 0

    flat = total = 0
    m = len(on_local)
    for k in range(m):
        li0 = on_local[k]
        li1 = on_local[(k + 1) % m]
        # 收集 li0 与 li1 之间的 off 点（沿局部环）
        offs = []
        j = (li0 + 1) % n
        guard = 0
        while j != li1 and guard < n:
            offs.append(g[j])
            j = (j + 1) % n
            guard += 1
        if not offs:
            continue
        total += 1

        gi0 = g[li0]
        gi1 = g[li1]
        a = (coords[gi0][0], coords[gi0][1])
        b = (coords[gi1][0], coords[gi1][1])
        chord = math.hypot(b[0] - a[0], b[1] - a[1])
        if chord < min_len:
            continue

        dev = 0.0
        for oi in offs:
            p = (coords[oi][0], coords[oi][1])
            d = _perp_dist(p, a, b)
            if d > dev:
                dev = d
        if dev > max_dev_abs:
            continue
        if dev / chord > tol:
            continue

        for oi in offs:
            p = (coords[oi][0], coords[oi][1])
            q = _project(p, a, b)
            coords[oi] = [q[0], q[1]]
        flat += 1

    return flat, total


def flatten_glyph(glyph, tol=0.055, min_len=30.0, max_dev_abs=60.0):
    """处理整个字形。返回 (flat, total)。"""
    if glyph.numberOfContours <= 0:
        return 0, 0
    coords = [[float(p[0]), float(p[1])] for p in glyph.coordinates]
    flags = [int(f) & 1 for f in glyph.flags]

    st = 0
    flats = totals = 0
    for e in list(glyph.endPtsOfContours):
        idxs = list(range(st, e + 1))
        st = e + 1
        f, t = flatten_span_in_contour(coords, flags, idxs, tol, min_len, max_dev_abs)
        flats += f
        totals += t

    if flats:
        from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
        gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in coords])
        gc.toInt()
        glyph.coordinates = gc
        for at in ("xMin", "yMin", "xMax", "yMax"):
            if hasattr(glyph, at):
                delattr(glyph, at)
    return flats, totals


def apply(font, verbose=False, **kw):
    glyf = font["glyf"]
    tot = changed = 0
    fs = ts = 0
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        f, t = flatten_glyph(g, **kw)
        fs += f
        ts += t
        if f:
            changed += 1
        tot += 1
    if verbose:
        print("  glyphs %d, changed %d, spans flattened %d/%d" % (tot, changed, fs, ts))
    return tot, changed, fs, ts
