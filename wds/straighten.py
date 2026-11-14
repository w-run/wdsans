# -*- coding: utf-8 -*-
"""P99: 侧边拉直——去除 Noto 笔画侧边的装饰性弧线。

## 问题（实测）

曲率 = 侧边 RMS 偏离直线 / 笔画宽度（中位数）：
  Noto 0.1493 | OPPO 0.0785 | HOS 0.0746

Noto 的笔画侧边是弧线（装饰），OPPO/HOS 基本是直线。
无衬线字体不该有这些装饰。

## 方法（只移动节点，不增删）

1. PCA 求主轴 axis / 副轴 perp
2. 每点得 s（沿轴）、u（垂直轴）
3. 在中段区域（排除端部）把点按 s 分箱，取每箱 u 最大/最小得两侧边缘
4. 两侧边缘分别做最小二乘直线拟合 u = a*s + b
5. 把上侧点的 u 投影到上拟合线，下侧同理（只改 u，不改 s）
6. 端部区域用权重渐变过渡，避免断裂
"""
from __future__ import annotations
import math

import numpy as np
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def _contours(g):
    coords = list(g.coordinates)
    segs = []; st = 0
    for e in g.endPtsOfContours:
        segs.append(coords[st:e+1]); st = e+1
    return segs


def _area(seg):
    n = len(seg)
    if n < 3: return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = seg[i]; x2, y2 = seg[(i+1) % n]
        a += x1*y2 - x2*y1
    return abs(a) / 2.0




def _seg_cross(p1, p2, p3, p4):
    def d(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    d1 = d(p3, p4, p1); d2 = d(p3, p4, p2)
    d3 = d(p1, p2, p3); d4 = d(p1, p2, p4)
    return ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0))


def count_self_intersections(seg):
    n = len(seg)
    c = 0
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _seg_cross(seg[i], seg[(i+1) % n], seg[j], seg[(j+1) % n]):
                c += 1
    return c


def validate(before, after, max_area_pct=8.0):
    a0 = _area(before); a1 = _area(after)
    if a0 > 0:
        pct = abs(a1 - a0) / a0 * 100.0
        if pct > max_area_pct:
            return False, chr(97)+chr(114)+chr(101)+chr(97)
    i0 = count_self_intersections(before)
    i1 = count_self_intersections(after)
    if i1 > i0:
        return False, chr(115)+chr(105)
    return True, chr(111)+chr(107)


def straighten(seg, term_frac=0.15, min_len_ratio=1.5, nb=8,
               strength=1.0, max_shift_ratio=0.45):
    """把带状轮廓两侧的弧线拉直。返回 (新点列, 是否改动)。"""
    n = len(seg)
    if n < 6:
        return seg, False
    P = np.array([(float(p[0]), float(p[1])) for p in seg])
    c = P.mean(axis=0); Q = P - c
    cov = np.cov(Q.T)
    if cov.shape != (2, 2):
        return seg, False
    w, v = np.linalg.eigh(cov)
    axis = v[:, int(np.argmax(w))]
    perp = np.array([-axis[1], axis[0]])
    s = Q @ axis
    u = Q @ perp
    L = float(s.max() - s.min())
    W = float(u.max() - u.min())
    if L < 1e-6 or W < 8:
        return seg, False
    if L / W < min_len_ratio:
        return seg, False

    # 分箱求两侧边缘点
    edges = np.linspace(s.min(), s.max(), nb + 1)
    up_s, up_u, lo_s, lo_u = [], [], [], []
    for i in range(nb):
        m = (s >= edges[i]) & (s < edges[i+1]) if i < nb-1 else (s >= edges[i])
        if m.sum() < 2:
            continue
        ss = s[m]; uu = u[m]
        up_s.append(float(ss[np.argmax(uu)])); up_u.append(float(uu.max()))
        lo_s.append(float(ss[np.argmin(uu)])); lo_u.append(float(uu.min()))
    if len(up_s) < 3 or len(lo_s) < 3:
        return seg, False

    def fit(S, U):
        S = np.array(S); U = np.array(U)
        A = np.vstack([S, np.ones(len(S))]).T
        coef, *_ = np.linalg.lstsq(A, U, rcond=None)
        return coef

    cu = fit(up_s, up_u)
    cl = fit(lo_s, lo_u)
    pred_u = cu[0]*s + cu[1]
    pred_l = cl[0]*s + cl[1]
    gap = pred_u - pred_l
    if np.any(gap < 1.0):
        return seg, False

    # 判断每点属于上侧还是下侧（相对中线）
    mid = (pred_u + pred_l) / 2.0
    is_up = u >= mid
    target = np.where(is_up, pred_u, pred_l)

    # 端部渐变权重
    pos = (s - s.min()) / (s.max() - s.min())
    wt = np.ones(n)
    lo_m = pos < term_frac
    hi_m = pos > 1.0 - term_frac
    wt[lo_m] = pos[lo_m] / term_frac if term_frac > 0 else 1.0
    wt[hi_m] = (1.0 - pos[hi_m]) / term_frac if term_frac > 0 else 1.0
    wt = np.clip(wt, 0.0, 1.0) * strength

    # 安全阀：只有本来就接近直线的侧边才拉直。
    # 弧形的弯笔（如弯曲的长撇）PCA 主轴与真实走向不一致，
    # 强行拉直反而会扭曲它（实测轮廓#2 曲率 0.216 -> 0.253）。
    from .curv_metric import edge_curvature
    cb = edge_curvature([(float(p[0]), float(p[1])) for p in seg])
    if cb is None or cb > 0.18:
        return seg, False
    delta = (target - u) * wt
    # 限制位移幅度，避免剧烈变形
    lim = max_shift_ratio * W
    delta = np.clip(delta, -lim, lim)
    if np.max(np.abs(delta)) < 0.5:
        return seg, False

    new_u = u + delta
    Pn = c + np.outer(s, axis) + np.outer(new_u, perp)
    return [(float(x), float(y)) for x, y in Pn], True


def apply(font, min_area=800, verbose=False, **kw):
    glyf = font["glyf"]
    tot = done = 0
    rejected = []
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        segs = _contours(g)
        nb = sum(len(s) for s in segs)
        out = []
        for seg in segs:
            if _area(seg) < min_area:
                out.extend(seg); continue
            ns, ch = straighten(seg, **kw)
            if ch:
                ok, why = validate(seg, ns)
                if not ok:
                    ns = seg; ch = False
                    rejected.append((name, why))
            if ch: done += 1
            out.extend(ns)
        tot += 1
        assert len(out) == nb, name
        gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in out])
        gc.toInt()
        g.coordinates = gc
        for a in ("xMin", "yMin", "xMax", "yMax"):
            if hasattr(g, a):
                delattr(g, a)
    if verbose:
        print("  glyphs %d, straightened %d, rejected %d" % (tot, done, len(rejected)))
    return tot, done