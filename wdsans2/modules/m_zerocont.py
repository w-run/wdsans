#!/usr/bin/env python3
"""m_zerocont - 删除零面积退化轮廓

判据:
  轮廓面积 < 50 em² (基本为 0)
  典型形态: A->B->B->A 往返直线, 或用 3 段共线 L 围成

为什么安全:
  零面积轮廓不产生任何视觉内容, 只浪费数据。
  删除后渲染结果不变。

实测: 全库 20992 CJK 中 45 处, 全部是段数=3 的共线三角形。
"""
import numpy as np

NAME = 'zerocont'
DESC = '删除零面积退化轮廓'

AREA_MAX = 50.0     # em², 小于此为退化
FLATTEN = 30        # 曲线展平步数


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def flat(c, steps=FLATTEN):
    pts = [np.array(c['start'], float)]
    for s in c['segs']:
        if s[0] == 'L':
            pts.append(np.array(s[1], float))
        elif s[0] == 'C':
            p0 = pts[-1]
            c1 = np.array(s[1], float); c2 = np.array(s[2], float); e = np.array(s[3], float)
            for i in range(1, steps + 1):
                t = i / steps; mt = 1 - t
                pts.append(mt**3*p0 + 3*mt*mt*t*c1 + 3*mt*t*t*c2 + t**3*e)
        elif s[0] == 'Q':
            p0 = pts[-1]
            c1 = np.array(s[1], float); e = np.array(s[2], float)
            for i in range(1, steps + 1):
                t = i / steps; mt = 1 - t
                pts.append(mt*mt*p0 + 2*mt*t*c1 + t*t*e)
    return np.array(pts)


def shoelace(P):
    n = len(P)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += P[i][0] * P[j][1] - P[j][0] * P[i][1]
    return abs(s) / 2.0


def find(C, sw):
    """返回要删除的轮廓索引列表 [ci, ...]"""
    res = []
    for ci, c in enumerate(C):
        if len(C) <= 1:
            break      # 只删不能删到只剩 0 个轮廓
        P = flat(c)
        if len(P) < 3:
            res.append(ci)
            continue
        if shoelace(P) < AREA_MAX:
            res.append(ci)
    # 保证至少留一个轮廓
    if len(res) >= len(C):
        res = res[:len(C) - 1]
    return res


def apply(C, hits):
    if not hits:
        return C
    keep = [c for ci, c in enumerate(C) if ci not in set(hits)]
    return [{'start': tuple(c['start']),
             'segs': [list(s) for s in c['segs']]} for c in keep]
