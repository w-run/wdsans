#!/usr/bin/env python3
"""digit_final - 用几何量测真实笔画厚度（不受曲线细分影响）"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'


def flatten(path, ch, inst=None, N=24):
    f = TTFont(path, lazy=True)
    if inst and "fvar" in f:
        from fontTools.varLib.instancer import instantiateVariableFont
        f = instantiateVariableFont(f, {"wght": inst}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    adv = f["hmtx"][cm[ord(ch)]][0]
    f.close()
    contours = []; cur = None; prev = None
    for op, args in rp.value:
        if op == "moveTo":
            if cur: contours.append(np.array(cur))
            cur = [np.array(args[0], float)]; prev = cur[0]
        elif op == "lineTo":
            p = np.array(args[0], float); cur.append(p); prev = p
        elif op == "curveTo":
            P = [prev] + [np.array(a, float) for a in args]
            for k in range(1, N+1):
                cur.append(bezierTools.splitCubicAtT(*P, k/N)[0][-1])
            prev = P[-1]
        elif op == "qCurveTo":
            P = [prev] + [np.array(a, float) for a in args]
            for k in range(1, N+1):
                cur.append(bezierTools.splitQuadraticAtT(*P, k/N)[0][-1])
            prev = P[-1]
        elif op == "closePath":
            if cur: contours.append(np.array(cur))
            cur = None
    if cur: contours.append(np.array(cur))
    return contours, adv


def row_width(P, y, tol=1.5):
    """给定展平点集，返回 y 处墨段总宽（交点法）"""
    xs = []
    n = len(P)
    for i in range(n):
        p0, p1 = P[i], P[(i+1) % n]
        if abs(p0[1]-p1[1]) < 1e-9:
            continue
        if min(p0[1],p1[1]) <= y <= max(p0[1],p1[1]):
            t = (y-p0[1])/(p1[1]-p0[1])
            xs.append(p0[0] + t*(p1[0]-p0[0]))
    if len(xs) < 2:
        return 0
    xs.sort()
    return sum(xs[i+1]-xs[i] for i in range(0, len(xs)-1, 2))


print('=== 数字笔画：y 处墨宽（几何量测）===')
print('%-3s %-8s %-8s %-8s %s' % ('字','我们','SHS','Mona','判定'))
for ch in "0123456789":
    v = flatten(VF, ch); s = flatten(SHS, ch); m = flatten(MONA, ch, 400)
    if not v: continue
    # 中部 50% 高度
    ys = np.vstack(v[0])[:,1]
    ymid = (ys.min() + ys.max()) / 2
    wv = sum(row_width(P, ymid) for P in v[0])
    ws = sum(row_width(P, ymid) for P in s[0]) if s else 0
    wm = sum(row_width(P, ymid) for P in m[0]) if m else 0
    dev = (wv-ws)/ws*100 if ws else 0
    print('%-3s %-8.0f %-8.0f %-8.0f %+.0f%%' % (ch, wv, ws, wm, dev))