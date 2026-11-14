#!/usr/bin/env python3
"""m_taper - 撇/提/捺 末端收窄

NARROW=0.95 由回归拟合得出 (MAE 4.29 最低)
检测: 长度 0.55~1.45*SW 的 L 段, 前段为 C 且夹角 75~115deg, 非轴对齐
修复: 该 L 段两端向中点收 NARROW, 前段 C 的第二控制点向中点拉 C2PULL
"""
import numpy as np

NAME = 'taper'
DESC = '撇提捺末端收窄'
NARROW = 0.95
C2PULL = 0.24
FACE_MIN = 0.85
AXIS_TOL = 8.0
SEG_LO = 0.55
SEG_HI = 1.45
ANG_LO = 75.0
ANG_HI = 115.0


def endp(s):
    return np.array(s[-1], float)


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else None


def find(C, sw):
    ops = []
    for ci, c in enumerate(C):
        segs = [list(s) for s in c['segs']]
        P = [np.array(c['start'], float)] + [endp(s) for s in segs]
        m = len(segs)
        for k in range(m):
            sk = segs[k]
            if sk[0] != 'L':
                continue
            a = P[k]
            b = P[k + 1] if k + 1 <= m else P[0]
            Lk = float(np.linalg.norm(b - a))
            if not (SEG_LO * sw < Lk < SEG_HI * sw):
                continue
            j = (k - 1) % m
            sj = segs[j]
            if sj[0] != 'C':
                continue
            aj = P[j]
            bj = P[j + 1] if j + 1 <= m else P[0]
            if float(np.linalg.norm(bj - aj)) < 2.0 * sw:
                continue
            d_m = norm(bj - aj)
            d_f = norm(b - a)
            if d_m is None or d_f is None:
                continue
            ang = float(np.degrees(np.arccos(np.clip(np.dot(d_m, d_f), -1, 1))))
            if not (ANG_LO <= ang <= ANG_HI):
                continue
            angm = abs(float(np.degrees(np.arctan2(d_m[1], d_m[0])))) % 180
            if angm > 90:
                angm = 180 - angm
            if min(angm, 90 - angm) < AXIS_TOL:
                continue
            if Lk < FACE_MIN * sw:
                continue
            ops.append((ci, k, j))
    return ops


def apply(C, ops):
    NEW = [{'start': tuple(c['start']), 'segs': [list(s) for s in c['segs']]} for c in C]
    for ci, k, j in ops:
        c = C[ci]
        segs = [list(s) for s in c['segs']]
        P = [np.array(c['start'], float)] + [endp(s) for s in segs]
        m = len(segs)
        if k >= m or j >= m:
            continue
        a = P[k]
        b = P[k + 1] if k + 1 <= m else P[0]
        mid = (a + b) / 2.0
        an = mid + (a - mid) * NARROW
        bn = mid + (b - mid) * NARROW
        sj = segs[j]
        c1 = np.array(sj[1], float)
        c2 = np.array(sj[2], float)
        c2n = c2 + (mid - c2) * C2PULL
        NEW[ci]['segs'][j] = ['C', tuple(c1), tuple(c2n), tuple(an)]
        sk = NEW[ci]['segs'][k]
        NEW[ci]['segs'][k] = ['L', tuple(bn)] if sk[0] == 'L' else list(sk)
    return NEW
