#!/usr/bin/env python3
"""two_detail - 精确打印 出 和 永 的问题点坐标"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'


def dump(path, ch, lbl):
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
    print("  ---- %s (%d 轮廓) ----" % (lbl, len(C)))
    for i, (st, sg) in enumerate(C):
        pts = [np.array(st, float)]
        for op, args in sg:
            for q in args: pts.append(np.array(q, float))
        P = np.array(pts)
        print("    c%d  x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (i, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
        if P[:,1].min() < 100:
            print("        起点 (%.1f,%.1f)" % (st[0], st[1]))
            for k, (op, args) in enumerate(sg):
                e = np.array(args[-1], float)
                print("          %d %-8s -> (%.1f,%.1f)" % (k, op, e[0], e[1]))


print('='*60)
print('【出】底部轮廓')
print('='*60)
dump(VF, '出', '我们')
dump('/workspace/wdsans/ref/shs/shs-400.otf', '出', 'SHS')

print()
print('='*60)
print('【永】竖弯钩轮廓 c4')
print('='*60)
f = TTFont(VF, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
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
st, sg = C[4]
print("  起点 (%.1f, %.1f)" % (st[0], st[1]))
for k, (op, args) in enumerate(sg):
    e = np.array(args[-1], float)
    print("    %d %-8s -> (%.1f, %.1f)" % (k, op, e[0], e[1]))