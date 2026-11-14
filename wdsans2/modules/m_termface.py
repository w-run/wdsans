#!/usr/bin/env python3
"""m_termface - 笔端面改直线

判据: 段长 0.8~1.5*SW 且 弯曲偏离比值 dev/L < 0.10
修复: C -> L (端面由微弧变平切)
已验证: 永(改3跳1) 建(改3跳2) 人 大 八 川 入 又
"""
import numpy as np

NAME = 'termface'
DESC = '笔端面改直线'
LO = 0.8
HI = 1.5
MAXR = 0.10


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def find(C, sw):
    res = []
    for ci, c in enumerate(C):
        segs = c['segs']
        pts = [np.array(c['start'], float)] + [endp(s) for s in segs]
        for k, s in enumerate(segs):
            if s[0] != 'C':
                continue
            p0 = pts[k]
            p1 = pts[k + 1]
            L = float(np.linalg.norm(p1 - p0))
            if not (LO * sw < L < HI * sw):
                continue
            c1 = np.array(s[1], float)
            c2 = np.array(s[2], float)
            dev = float(np.linalg.norm((c1 + c2) / 2 - (p0 + p1) / 2))
            if dev / L < MAXR:
                res.append((ci, k))
    return res


def apply(C, hits):
    NEW = [{'start': tuple(c['start']), 'segs': [list(s) for s in c['segs']]} for c in C]
    for ci, k in hits:
        if ci >= len(NEW):
            continue
        segs = NEW[ci]['segs']
        if k >= len(segs):
            continue
        s = segs[k]
        if s[0] != 'C':
            continue
        segs[k] = ['L', s[3]]
    return NEW
