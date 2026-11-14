#!/usr/bin/env python3
"""m_barple - 横线+撇/捺 根部悬空修复 (E3 定稿, ratio=0)

判据:
  bar : 3段纯L, 宽>=1.5*SW, 高<=2.5*SW
  body: >=4段, 末段回折(dist(E1,start) < dist(E2,start)), 落点 E2 = 倒数第2段终点
        dx = E2.x - bar.right in [0.02SW, 1.00SW]
        bar.bottom < E2.y < bar.top
        body 与 bar x重叠 >= 0.8SW
  交叉处 y=bar.bottom 求 body 左右交点 xL,xR, 要求 xR-bar.right >= 0.02SW

修复:
  1. bar 右端 -> xR
  2. body 倒数第2段终点 -> (xR, bar.bottom)
  3. 删除回折段
"""
import numpy as np

NAME = 'barple'
DESC = '横线+撇/捺根部悬空'
RATIO = 0.0


def endp(s):
    return np.array(s[-1], float)


def bbox(c):
    P = np.vstack([[c['start']] + [endp(s) for s in c['segs']]])
    return float(P[:, 0].min()), float(P[:, 0].max()), float(P[:, 1].min()), float(P[:, 1].max())


def poly(c, steps=300):
    pts = [np.array(c['start'], float)]
    for s in c['segs']:
        if s[0] == 'L':
            pts.append(np.array(s[1], float))
        elif s[0] == 'C':
            p0 = pts[-1]
            c1 = np.array(s[1], float)
            c2 = np.array(s[2], float)
            p3 = np.array(s[3], float)
            for i in range(1, steps + 1):
                t = i / steps
                mt = 1 - t
                pts.append(mt**3 * p0 + 3 * mt * mt * t * c1 + 3 * mt * t * t * c2 + t**3 * p3)
    return np.array(pts)


def xcross(P, y):
    xs = []
    for i in range(len(P) - 1):
        a = P[i]
        b = P[i + 1]
        if (a[1] - y) * (b[1] - y) <= 0 and abs(b[1] - a[1]) > 1e-12:
            t = (y - a[1]) / (b[1] - a[1])
            xs.append(a[0] + t * (b[0] - a[0]))
    return sorted(xs)


def find(C, sw):
    res = []
    bars = [i for i, c in enumerate(C)
            if all(s[0] == 'L' for s in c['segs']) and len(c['segs']) == 3
            and bbox(c)[1] - bbox(c)[0] >= 1.5 * sw
            and bbox(c)[3] - bbox(c)[2] <= 2.5 * sw]
    for bi in bars:
        bx0, bx1, by0, by1 = bbox(C[bi])
        for ci, c in enumerate(C):
            if ci == bi:
                continue
            segs = c['segs']
            n = len(segs)
            if n < 4:
                continue
            st = np.array(c['start'], float)
            E1 = endp(segs[-1])
            E2 = endp(segs[-2])
            if np.linalg.norm(E1 - st) >= np.linalg.norm(E2 - st):
                continue
            cx0, cx1, cy0, cy1 = bbox(c)
            if min(cx1, bx1) - max(cx0, bx0) < 0.8 * sw:
                continue
            dx = E2[0] - bx1
            if not (0.02 * sw <= dx <= 1.0 * sw):
                continue
            if not (by0 < E2[1] < by1):
                continue
            xs = xcross(poly(c, 200), by0)
            if len(xs) < 2:
                continue
            xL, xR = xs[-2], xs[-1]
            if xR - bx1 < 0.02 * sw:
                continue
            res.append((bi, ci, n - 2, xL, xR, by0))
    return res


def apply(C, hits):
    NEW = [{'start': tuple(c['start']), 'segs': [list(s) for s in c['segs']]} for c in C]
    for bi, ci, ei, xL, xR, by0 in hits:
        bar = NEW[bi]
        body = NEW[ci]
        bar['start'] = (xR, bar['start'][1])
        s2 = bar['segs'][2]
        bar['segs'][2] = ['L', (xR, s2[-1][1])]
        if ei >= len(body['segs']):
            continue
        s = body['segs'][ei]
        body['segs'][ei] = ['C', s[1], s[2], (xR, by0)] if s[0] == 'C' else ['L', (xR, by0)]
        del body['segs'][ei + 1:]
    return NEW
