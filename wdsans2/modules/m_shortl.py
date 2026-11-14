#!/usr/bin/env python3
"""m_shortl - 删除曲线间的冗余短直线段

判据:
  1. L 段，长度 0.3 ~ 15 单位（< 0.2 SW）
  2. 前后段都是 C（曲线）→ 纯冗余，删掉后曲线直接衔接
  3. 删除后前后曲线端点一致（不产生缺口）

为什么安全:
  短直线段夹在两条曲线之间，是台阶对齐的残留物。
  删掉后两条曲线的端点重合，几何形状不变。

已被 m_stepalign 覆盖部分场景，但残留 3523 处未处理。
"""
import numpy as np

NAME = 'shortl'
DESC = '删除曲线间冗余短直线段'

LEN_LO = 0.3      # 最小长度（排除真正的零长度）
LEN_HI = 15.0     # 最大长度（超此不算冗余）


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def find(C, sw):
    """返回 [(ci, [k, ...])]  每轮廓要删的段索引"""
    res = []
    hi = min(LEN_HI, 0.20 * sw)
    for ci, c in enumerate(C):
        segs = c['segs']
        n = len(segs)
        if n < 4:
            continue
        pts = [np.array(c['start'], float)] + [endp(s) for s in segs]
        dels = []
        for k, s in enumerate(segs):
            if s[0] != 'L':
                continue
            L = float(np.linalg.norm(pts[k + 1] - pts[k]))
            if not (LEN_LO < L < hi):
                continue
            prev = segs[k - 1][0] if k > 0 else segs[-1][0]
            nxt = segs[k + 1][0] if k + 1 < n else segs[0][0]
            if prev == 'C' and nxt == 'C':
                dels.append(k)
        # 相邻段不连删（避免连续删导致结构崩坏）
        if dels:
            keep = []
            last = -99
            for k in dels:
                if k - last > 1:
                    keep.append(k)
                    last = k
            if keep:
                res.append((ci, keep))
    return res


def apply(C, hits):
    NEW = [{'start': tuple(c['start']),
            'segs': [list(s) for s in c['segs']]} for c in C]
    for ci, ks in hits:
        if ci >= len(NEW):
            continue
        segs = NEW[ci]['segs']
        # 倒序删除，索引不失效
        for k in sorted(ks, reverse=True):
            if 0 <= k < len(segs):
                del segs[k]
    return NEW
