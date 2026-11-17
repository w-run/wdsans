#!/usr/bin/env python3
"""two_more - 精查 出 右下脚 与 永 竖弯钩闭合台阶"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'

FONTS = [('我们', VF), ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
         ('OPPO', '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
         ('HOS', '/workspace/wdsans/ref/hos/hos-400.ttf')]


def contours(path, ch):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    f.close()
    out = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None: out.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None: out.append((start, segs))
            start = None; segs = None
    if start is not None: out.append((start, segs))
    return out


print("="*66)
print("【出】右下脚：各字体底部左侧/右侧竖笔下探深度")
print("="*66)
for lbl, p in FONTS:
    C = contours(p, "出")
    if not C:
        print("  %-5s 无此字" % lbl); continue
    # 找所有轮廓的最低点
    low = []
    for st, sg in C:
        pts = [np.array(st, float)]
        for op, args in sg:
            for q in args: pts.append(np.array(q, float))
        P = np.array(pts)
        low.append((P[:,1].min(), P[:,0].min(), P[:,0].max()))
    low.sort()
    ybot = low[0][0]
    print('  %-5s 轮廓%d  最低点 y=%.0f' % (lbl, len(C), ybot))
    for y, x0, x1 in low[:4]:
        print('        y=%4.0f  x[%4.0f,%4.0f]' % (y, x0, x1))

print()
print("="*66)
print("【永】竖弯钩轮廓：起点与终点是否闭合")
print("="*66)
for lbl, p in FONTS:
    C = contours(p, "永")
    if not C:
        print("  %-5s 无此字" % lbl); continue
    worst = None
    for i, (st, sg) in enumerate(C):
        ex = None
        for op, args in sg:
            if op in ("lineTo","curveTo","qCurveTo"):
                ex = np.array(args[-1], float)
        if ex is None:
            continue
        s = np.array(st, float)
        d = float(np.hypot(*(s - ex)))
        if worst is None or d > worst[0]:
            worst = (d, i, s, ex)
    print("  %-5s 最大闭合缺口 %.1f  轮廓%d  起(%.1f,%.1f) 终(%.1f,%.1f)" % (
        lbl, worst[0], worst[1], worst[2][0], worst[2][1], worst[3][0], worst[3][1]))