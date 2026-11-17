#!/usr/bin/env python3
"""verify_3w - 验证 出/永 缺陷在三档是否一致"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

BASE = '/workspace/wdsans2/build/masters_R27/'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}


def conts(path, ch):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    f.close()
    C = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None: C.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None: C.append((start, segs))
            start = None; segs = None
    if start is not None: C.append((start, segs))
    return C


print('=== 出：底横笔右端 vs 右竖左缘 ===')
for tag in ['250','400','900']:
    C = conts(BASE + FN[tag], "出")
    # 找右下竖（y 最低、x>700）
    vert = None; bar = None
    for st, sg in C:
        pts = [np.array(st, float)]
        for op, args in sg:
            for q in args: pts.append(np.array(q, float))
        P = np.array(pts)
        if P[:,1].min() < -30 and P[:,0].min() > 700:
            vert = P
        if P[:,1].min() < 0 and P[:,0].max() > 700 and P[:,0].max() < 900 and len(sg) >= 4:
            bar = P
    if vert is None or bar is None:
        print("  %s: 未识别 vert=%s bar=%s" % (tag, vert is not None, bar is not None)); continue
    print("  %s: 右竖 x[%.0f,%.0f] y[%.0f,%.0f]   底横 x[%.0f,%.0f] y[%.0f,%.0f]  伸入 %.0f" % (
        tag, vert[:,0].min(), vert[:,0].max(), vert[:,1].min(), vert[:,1].max(),
        bar[:,0].min(), bar[:,0].max(), bar[:,1].min(), bar[:,1].max(),
        bar[:,0].max() - vert[:,0].min()))

print()
print('=== 永：竖弯钩首尾缺口 ===')
for tag in ['250','400','900']:
    C = conts(BASE + FN[tag], "永")
    best = None
    for i, (st, sg) in enumerate(C):
        if len(sg) < 5:
            continue
        ex = None
        for op, args in sg:
            if op in ("lineTo","curveTo","qCurveTo"):
                ex = np.array(args[-1], float)
        if ex is None:
            continue
        s = np.array(st, float)
        d = float(np.hypot(*(s - ex)))
        ymin = min([s[1]] + [np.array(a[-1],float)[1] for o,a in sg])
        if ymin < 50 and (best is None or d > best[0]):
            best = (d, i, s, ex)
    if best:
        print("  %s: 轮廓%d 缺口%.1f  起(%.1f,%.1f) 终(%.1f,%.1f)" % (
            tag, best[1], best[0], best[2][0], best[2][1], best[3][0], best[3][1]))