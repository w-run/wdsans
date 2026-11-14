#!/usr/bin/env python3
"""m_yanrad - 廴旁顶端尖角消除（全自动识别，无硬编码坐标）

实测归纳（建/延/健/庭/廷/挺 六个字结构完全一致）:

廴旁顶端小块 = 9 段轮廓 CLCLLLCCL
  seg0 C   (a1) -> a2    左下斜段
  seg1 L   a2   -> a3    1单位假台阶
  seg2 C   a3   -> a4    主斜边（向上）
  seg3 L   a4   -> a5    ↑ 尖角上斜（缺陷）
  seg4 L   a5   -> a6    ↓ 尖角下斜（缺陷）
  seg5 L   a6   -> a7    短竖
  seg6 C   a7   -> a8    回程
  seg7 C   a8   -> a9    左中转折
  seg8 L   a9   -> a10   左下端面

修复（用户确认，以 建 为基准）:
  a4 -> (bar.xR, bar.yBot)   横线右下端点
  a5 -> (bar.xR, bar.yTop)   横线右上端点
  a6 -> 沿 a5->a6 方向内收，恢复斜边原宽
  a7 -> 沿 a6->a7 方向内收，同步
"""
import numpy as np

NAME = 'yanrad'
DESC = '廴旁顶端尖角消除'

SIG = 'CLCLLLCCL'      # 廴旁顶端小块的段签名
UPM = 1000.0
H_MIN = 0.30           # 最小高度（em）
GAP_LO = -0.60         # 横线右端可在 a4 左侧最多 0.6SW（建: -23单位 = -0.30SW）
GAP_HI = 1.20          # 上限

# 内收比例：a6/a7 沿原方向缩短，保持斜边宽度
SHRINK = 0.80


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def bbox(c):
    P = np.vstack([[np.array(c['start'], float)] + [endp(s) for s in c['segs']]])
    return (float(P[:, 0].min()), float(P[:, 0].max()),
            float(P[:, 1].min()), float(P[:, 1].max()))


def find(C, sw):
    """返回 [(ci, bi, bx1, byTop, byBot)]"""
    # 横线候选
    bars = []
    for i, c in enumerate(C):
        if not all(s[0] == 'L' for s in c['segs']):
            continue
        if len(c['segs']) != 3:
            continue
        x0, x1, y0, y1 = bbox(c)
        if (x1 - x0) >= 1.0 * sw and (y1 - y0) <= 2.5 * sw:
            bars.append((i, x1, y1, y0))
    if not bars:
        return []

    res = []
    for ci, c in enumerate(C):
        sig = ''.join(s[0] for s in c['segs'])
        if sig != SIG:
            continue
        x0, x1, y0, y1 = bbox(c)
        if (y1 - y0) < H_MIN * UPM:
            continue
        # a4 = seg2 终点（主斜边顶）
        a4 = endp(c['segs'][2])
        # 找横线：右端在 a4 右侧 GAP 范围内，且 y 区间覆盖 a4
        cand = [(bi, bx1, byT, byB) for bi, bx1, byT, byB in bars
                if GAP_LO * sw <= bx1 - a4[0] <= GAP_HI * sw
                and byB <= a4[1] <= byT + 0.05 * sw]
        if not cand:
            continue
        bi, bx1, byT, byB = min(cand, key=lambda t: abs(t[1] - a4[0]))
        res.append((ci, bi, float(bx1), float(byT), float(byB)))
    return res


def apply(C, hits):
    NEW = [{'start': tuple(c['start']),
            'segs': [list(s) for s in c['segs']]} for c in C]
    for ci, bi, bx1, byT, byB in hits:
        c = NEW[ci]
        segs = c['segs']
        # a4=seg2终点, a5=seg3终点, a6=seg4终点, a7=seg5终点
        s2, s3, s4, s5 = segs[2], segs[3], segs[4], segs[5]
        a5o = np.array(endp(s3), float)     # 原尖角顶点
        a6o = np.array(endp(s4), float)
        a7o = np.array(endp(s5), float)
        v56 = a6o - a5o
        v67 = a7o - a6o
        # 1) a4 -> 横线右下端点
        segs[2] = ['C', s2[1], s2[2], (bx1, byB)]
        # 2) a5 -> 横线右上端点（形成 s3 垂直新边）
        segs[3] = ['L', (bx1, byT)]
        # 3) a7 由 seg2 法向偏移决定：保持与 seg6 的原始法向笔宽
        a3o = np.array(endp(segs[1]), float)   # seg1 终点 = a3
        a4o = np.array(endp(s2), float)         # 原 a4
        v2o = a4o - a3o
        L2o = float(np.linalg.norm(v2o))
        if L2o < 1e-6:
            continue
        n2o = np.array([-v2o[1], v2o[0]]) / L2o   # 原 seg2 法向
        # 原始法向笔宽 = a7 到 seg2 直线 a3->a4 的法向距离
        w0 = abs(float(np.dot(a7o - a3o, n2o)))
        # 新 seg2 法向
        a4n = np.array((bx1, byB), float)
        v2n = a4n - a3o
        L2n = float(np.linalg.norm(v2n))
        n2n = np.array([-v2n[1], v2n[0]]) / L2n
        if float(np.dot(n2o, n2n)) < 0:
            n2n = -n2n
        a7n = a4n + n2n * w0
        segs[5] = ['L', tuple(a7n)]
        # 4) a6 = a7 沿原 a6->a7 反向，保持 seg5 原长与方向
        a6n = a7n - v67
        segs[4] = ['L', tuple(a6n)]
    return NEW
