# -*- coding: utf-8 -*-
"""P98: 端部宽度归一化——消除喇叭口与笔末凹进。

## 目标（用户指出）

Noto/SHS 特有缺陷，OPPO/HOS 没有：
  1. 喇叭口：笔画从起始端逐渐变粗（撇/捺/点最常见）
  2. 笔末凹进：笔画末端端面向内凹进，且端面倾角过大

## 锚点级证据（永字）

Noto: 7 轮廓 78 点，笔画轮廓有多余 off 点做外鼓
OPPO: 3 轮廓 64 点，笔画是细长四边形，端面平行短边

## 方法（只移动节点，不增删）

对每个「细长带状」轮廓：
  1. PCA 求主轴 axis 与副轴 perp
  2. 每点投影得 s（沿轴）与 u（垂直轴）
  3. 按 s 分箱，箱宽度 w(bin) = max(u) - min(u)
  4. 取中段箱的中位数为 target_w
  5. 端部区域（首尾各 term_frac）把 u 按 target_w/w 缩放 → 宽度被拉平
  6. 同时把端面 u 极值对齐，消除斜切
"""
from __future__ import annotations
import math

import numpy as np
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def _contours(g):
    coords = list(g.coordinates)
    segs = []
    st = 0
    for e in g.endPtsOfContours:
        segs.append(coords[st:e+1])
        st = e + 1
    return segs


def _area(seg):
    n = len(seg)
    if n < 3: return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = seg[i]; x2, y2 = seg[(i+1) % n]
        a += x1*y2 - x2*y1
    return abs(a)/2.0


def normalize_stroke(seg, term_frac=0.22, max_ratio=1.35, min_bins=5):
    """把一条带状轮廓的端部宽度拉平。返回 (新点列, 是否改动)。"""
    n = len(seg)
    if n < 6:
        return seg, False
    P = np.array([(p[0], p[1]) for p in seg], dtype=float)
    c = P.mean(axis=0)
    Q = P - c
    cov = np.cov(Q.T)
    w, v = np.linalg.eigh(cov)
    axis = v[:, int(np.argmax(w))]
    perp = np.array([-axis[1], axis[0]])
    s = Q @ axis
    u = Q @ perp
    L = s.max() - s.min()
    if L < 1e-6:
        return seg, False
    # 分箱测宽
    nb = max(min_bins, min(20, n // 2))
    edges = np.linspace(s.min(), s.max(), nb + 1)
    widths = np.zeros(nb)
    idxs = []
    for i in range(nb):
        m = (s >= edges[i]) & (s < edges[i+1]) if i < nb-1 else (s >= edges[i])
        idxs.append(np.nonzero(m)[0])
        if m.sum() >= 2:
            widths[i] = u[m].max() - u[m].min()
    valid = widths > 1.0
    if valid.sum() < 3:
        return seg, False
    # 中段中位宽（排除端部）
    k0 = int(nb * term_frac); k1 = nb - k0
    mid = widths[k0:k1][valid[k0:k1]] if k1 > k0 else widths[valid]
    if len(mid) == 0:
        return seg, False
    target_w = float(np.median(mid))
    if target_w < 3.0:
        return seg, False
    # 端部区域：把宽度向 target 收敛
    changed = False
    new_u = u.copy()
    for i in range(nb):
        if not valid[i] or widths[i] < 1.0:
            continue
        # 端部权重：靠两端为 1，中段为 0
        pos = (i + 0.5) / nb
        if pos < term_frac:
            wt = 1.0 - pos / term_frac
        elif pos > 1.0 - term_frac:
            wt = 1.0 - (1.0 - pos) / term_frac
        else:
            continue
        # 只压「端部比中段粗」的隆起（喇叭口），
        # 绝不动正常的撇捺收锋（端部比中段细是应有的锥度）。
        if widths[i] <= target_w * 1.02:
            continue
        ratio = target_w / widths[i]
        # 限幅，避免剧烈变形
        ratio = max(1.0/max_ratio, min(max_ratio, ratio))
        if abs(ratio - 1.0) < 0.02:
            continue
        idx = idxs[i]
        if len(idx) < 2:
            continue
        uu = u[idx]
        um = uu.mean()
        f = 1.0 + (ratio - 1.0) * wt
        new_u[idx] = um + (uu - um) * f
        changed = True
    if not changed:
        return seg, False
    Pn = c + np.outer(s, axis) + np.outer(new_u, perp)
    return [(float(x), float(y)) for x, y in Pn], True


def apply(font, term_frac=0.22, max_ratio=1.35, min_area=800, verbose=False):
    glyf = font["glyf"]
    done = 0; tot = 0
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
            ns, ch = normalize_stroke(seg, term_frac, max_ratio)
            if ch: done += 1
            out.extend(ns)
        tot += 1
        assert len(out) == nb, name
        gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in out])
        gc.toInt()
        g.coordinates = gc
        for a in ("xMin","yMin","xMax","yMax"):
            if hasattr(g, a):
                delattr(g, a)
    if verbose:
        print("  处理 %d 字形，%d 条轮廓被归一化" % (tot, done))
    return tot, done