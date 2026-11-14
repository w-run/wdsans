# -*- coding: utf-8 -*-
"""曲率度量：侧边 RMS 偏离直线 / 笔画宽度。"""
from __future__ import annotations
import numpy as np


def edge_curvature(seg, nb=8):
    n = len(seg)
    if n < 6:
        return None
    P = np.array(seg, dtype=float)
    if P.shape[0] < 4:
        return None
    c = P.mean(axis=0); Q = P - c
    cov = np.cov(Q.T)
    if cov.shape != (2, 2):
        return None
    w, v = np.linalg.eigh(cov)
    axis = v[:, int(np.argmax(w))]
    perp = np.array([-axis[1], axis[0]])
    s = Q @ axis; u = Q @ perp
    L = float(s.max() - s.min()); W = float(u.max() - u.min())
    if L < 1e-6 or W < 8 or L / W < 1.5:
        return None
    edges = np.linspace(s.min(), s.max(), nb + 1)
    up = [[], []]; lo = [[], []]
    for i in range(nb):
        m = (s >= edges[i]) & (s < edges[i+1]) if i < nb-1 else (s >= edges[i])
        if m.sum() < 2:
            continue
        ss = s[m]; uu = u[m]
        up[0].append(float(ss[np.argmax(uu)])); up[1].append(float(uu.max()))
        lo[0].append(float(ss[np.argmin(uu)])); lo[1].append(float(uu.min()))
    devs = []
    for S, U in (up, lo):
        if len(S) < 3:
            continue
        S = np.array(S); U = np.array(U)
        A = np.vstack([S, np.ones(len(S))]).T
        coef, *_ = np.linalg.lstsq(A, U, rcond=None)
        devs.append(float(np.sqrt(np.mean((U - (A @ coef))**2))))
    if not devs:
        return None
    return float(np.mean(devs)) / W