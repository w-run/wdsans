# -*- coding: utf-8 -*-
"""P100: 端部隆起局部压缩（只压 bulge，不动整体边线）。

## 与前几版的区别

straighten.py: 拟整条边为直线 -> 影响面太大，16/22 被校验门拒绝，剩下位移≈0
本模块: 只在端部 18% 长度内，把「比中段宽」的点压回中段宽度

## 判据（实测支撑）

曲率中位: Noto 0.1493 / OPPO 0.0785 / HOS 0.0746
用户目视指出：起笔处外鼓（喇叭口）、端面内凹翘边

## 方法

1. PCA 求轴 axis/perp，得 s(沿轴) u(垂直轴)
2. 中段(30%-70%)分箱取宽度，中位数为 target_w
3. 端部(首尾各18%)逐点：若局部截面宽 > target_w*1.08，把该点 u 往中线收
4. 只收不放，且限幅，保证不产生新形态
"""
from __future__ import annotations
import math

import numpy as np
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def _contours(g):
    coords = list(g.coordinates)
    segs = []; st = 0
    for e in g.endPtsOfContours:
        segs.append(coords[st:e+1]); st = e + 1
    return segs


def _area(seg):
    n = len(seg)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = seg[i]; x2, y2 = seg[(i+1) % n]
        a += x1*y2 - x2*y1
    return abs(a) / 2.0


def clamp_bulge(seg, term_frac=0.18, bulge_tol=1.08, max_pull=0.30):
    """端部隆起压缩。返回 (新点列, 是否改动)。"""
    n = len(seg)
    if n < 8:
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
    if L / W < 1.5:
        return seg, False

    # 中段宽度
    s0, s1 = s.min(), s.max()
    m_lo = s0 + 0.30 * L
    m_hi = s0 + 0.70 * L
    mid = (s >= m_lo) & (s <= m_hi)
    if mid.sum() < 4:
        return seg, False
    target_w = float(u[mid].max() - u[mid].min())
    if target_w < 4.0:
        return seg, False

    # 端部区域权重
    pos = (s - s0) / L
    wt = np.zeros(n)
    low = pos < term_frac
    high = pos > 1.0 - term_frac
    wt[low] = 1.0 - pos[low] / term_frac
    wt[high] = 1.0 - (1.0 - pos[high]) / term_frac
    # 两端各自算局部宽度
    new_u = u.copy()
    changed = False
    for mask, side in ((low, "lo"), (high, "hi")):
        if mask.sum() < 3:
            continue
        uu = u[mask]
        local_w = float(uu.max() - uu.min())
        if local_w <= target_w * bulge_tol:
            continue
        # 按比例收缩到 target_w
        ratio = target_w / local_w
        ratio = max(1.0 - max_pull, min(1.0, ratio))
        um = float(uu.mean())
        idx = np.nonzero(mask)[0]
        new_u[idx] = um + (u[idx] - um) * ratio
        changed = True
    if not changed:
        return seg, False

    Pn = c + np.outer(s, axis) + np.outer(new_u, perp)
    return [(float(x), float(y)) for x, y in Pn], True


def apply(font, min_area=600, verbose=False, **kw):
    glyf = font["glyf"]
    tot = done = 0
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
            ns, ch = clamp_bulge(seg, **kw)
            if ch:
                from .straighten import validate
                ok, _why = validate(seg, ns, max_area_pct=6.0)
                if not ok:
                    ns = seg
                    ch = False
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
        print("  glyphs %d, bulge-clamped %d" % (tot, done))
    return tot, done