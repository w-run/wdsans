#!/usr/bin/env python3
"""m_stepalign - 相邻轮廓台阶对齐

检测: body 首两段为 L 小台阶 (各 4~0.32*SW, 近似水平/垂直)
      另一轮廓存在同向长 L 段, 与其 y 差 0.4~4.0
修复: 台阶起点 y 对齐到该长段 y, 删除第二小段
"""
import numpy as np

NAME = 'stepalign'
DESC = '相邻轮廓台阶对齐'
STEP_MIN = 4.0
STEP_MAX = 0.32
ALIGN_LO = 0.4
ALIGN_HI = 4.0
TOL = 2.0


def endp(s):
    return np.array(s[-1], float)


def find(C, sw):
    res = []
    for ci, c in enumerate(C):
        segs = c['segs']
        if len(segs) < 3:
            continue
        if segs[0][0] != 'L' or segs[1][0] != 'L':
            continue
        st = np.array(c['start'], float)
        p1 = endp(segs[0])
        p2 = endp(segs[1])
        L1 = float(np.linalg.norm(p1 - st))
        L2 = float(np.linalg.norm(p2 - p1))
        if not (STEP_MIN <= L1 <= STEP_MAX * sw):
            continue
        if not (STEP_MIN <= L2 <= STEP_MAX * sw):
            continue
        if abs(p1[1] - st[1]) > TOL:
            continue
        if abs(p2[0] - p1[0]) > TOL:
            continue
        yA = st[1]
        best = None
        for cj, o in enumerate(C):
            if cj == ci:
                continue
            Po = [np.array(o['start'], float)] + [endp(s) for s in o['segs']]
            for k, s in enumerate(o['segs']):
                if s[0] != 'L':
                    continue
                a = Po[k]
                b = Po[k + 1] if k + 1 < len(Po) else Po[0]
                if abs(a[1] - b[1]) > TOL:
                    continue
                if float(np.linalg.norm(b - a)) < 1.5 * sw:
                    continue
                dy = abs(a[1] - yA)
                if ALIGN_LO <= dy <= ALIGN_HI:
                    if best is None or dy < best[1]:
                        best = (cj, float(a[1]), dy)
        if best is not None:
            res.append((ci, float(best[1]) - yA))
    return res


def apply(C, ops):
    NEW = [{'start': tuple(c['start']), 'segs': [list(s) for s in c['segs']]} for c in C]
    for ci, dy in sorted(ops, key=lambda x: -x[0]):
        if ci >= len(NEW):
            continue
        segs = NEW[ci]['segs']
        if len(segs) < 3:
            continue
        st = np.array(NEW[ci]['start'], float)
        yt = st[1] + dy
        NEW[ci]['start'] = (st[0], yt)
        p1 = np.array(segs[0][-1], float)
        segs[0] = ['L', (p1[0], yt)]
        del segs[1]
    return NEW
