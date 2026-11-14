#!/usr/bin/env python3
"""m_bardiag - 横线右端未达斜边外缘 (台阶)

结构: 3段纯L横线(bar) + 同字内的斜边轮廓(diag)
缺陷: bar 右端 x < diag 在该 y 处的外缘 x, 差 0.05~0.6 SW -> 台阶
修复: bar 两个右端点 -> diag 外缘 x (各自 y 处)

已验证: 建 左上横折 (bar右292 -> 315, 消 23 单位台阶)
"""
import numpy as np

NAME = 'bardiag'
DESC = '横线右端延伸到斜边外缘'
SW400 = 77.0
DX_LO, DX_HI = 0.05, 0.60   # 以 SW 为单位
FW_MIN = 1.0                # bar 宽 >= 1.0 SW
FH_MAX = 2.5                # bar 高 <= 2.5 SW


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def flat(c, steps=80):
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
        elif s[0] == 'QM':
            q = s[1]
            p0 = pts[-1]
            for i in range(len(q) - 1):
                c1 = np.array(q[i], float); e = np.array(q[i + 1], float)
                for k in range(1, 21):
                    t = k / 20; mt = 1 - t
                    pts.append(mt*mt*p0 + 2*mt*t*c1 + t*t*e)
                p0 = e
    return np.array(pts)


def xcross(P, y):
    xs = []
    for i in range(len(P) - 1):
        a = P[i]; b = P[i + 1]
        if (a[1] - y) * (b[1] - y) <= 0 and abs(b[1] - a[1]) > 1e-12:
            t = (y - a[1]) / (b[1] - a[1])
            xs.append(a[0] + t * (b[0] - a[0]))
    return sorted(xs)


def find(C, sw):
    """返回 [(bi, di, y0, y1, xr0, xr1)]"""
    res = []
    bars = []
    for i, c in enumerate(C):
        if not all(s[0] == 'L' for s in c['segs']):
            continue
        if len(c['segs']) != 3:
            continue
        P = np.vstack([[np.array(c['start'], float)] + [endp(s) for s in c['segs']]])
        w = P[:, 0].max() - P[:, 0].min()
        h = P[:, 1].max() - P[:, 1].min()
        if w >= FW_MIN * sw and h <= FH_MAX * sw:
            bars.append((i, P))
    if not bars:
        return res
    flats = [flat(c) for c in C]
    for bi, BP in bars:
        bx1 = BP[:, 0].max()
        by0 = BP[:, 1].min()
        by1 = BP[:, 1].max()
        for di in range(len(C)):
            if di == bi:
                continue
            DP = flats[di]
            if DP[:, 1].max() < by0 or DP[:, 1].min() > by1:
                continue
            # 外缘: 在 by0 与 by1 处的最大 x
            xs0 = xcross(DP, by0)
            xs1 = xcross(DP, by1)
            if not xs0 or not xs1:
                continue
            xo0, xo1 = xs0[-1], xs1[-1]
            xi0 = xs0[0] if len(xs0) >= 2 else xs0[-1]
            # bar 右端必须落在斜边内 (x 在 inner 与 outer 之间)
            if not (xi0 - 0.1 * sw <= bx1 <= xo0):
                continue
            d0 = xo0 - bx1
            d1 = xo1 - bx1
            if not (DX_LO * sw <= d0 <= DX_HI * sw):
                continue
            if not (DX_LO * sw <= d1 <= DX_HI * sw):
                continue
            res.append((bi, di, float(by0), float(by1), float(xo0), float(xo1)))
    return res


def apply(C, hits):
    NEW = [{'start': tuple(c['start']), 'segs': [list(s) for s in c['segs']]} for c in C]
    for bi, di, by0, by1, xo0, xo1 in hits:
        c = NEW[bi]
        # 收集 bar 的点: ('start',None,p) 或 ('seg',k,p)
        entries = [('start', None, np.array(c['start'], float))]
        for k, s in enumerate(c['segs']):
            entries.append(('seg', k, endp(s)))
        # 只改最右端的点! 按 x 最大者选 (每层 y 各一个)
        for ytarget, xnew in ((by0, xo0), (by1, xo1)):
            cands = [(kind, k, p) for kind, k, p in entries if abs(p[1] - ytarget) < 0.5]
            if not cands:
                continue
            kind, k, p = max(cands, key=lambda t: t[2][0])
            # 安全阀: 新 x 必须严格大于旧 x (只向右延伸, 不反向)
            if xnew <= p[0] + 0.5:
                continue
            newp = (float(xnew), float(p[1]))
            if kind == 'start':
                c['start'] = newp
            else:
                sg = c['segs'][k]
                if sg[0] == 'L':
                    c['segs'][k] = ['L', newp]
                elif sg[0] == 'C':
                    c['segs'][k] = ['C', sg[1], sg[2], newp]
    return NEW
