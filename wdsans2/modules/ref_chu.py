#!/usr/bin/env python3
"""ref_chu - 四家 出字 完整轮廓对比"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen

FONTS = [('我们', '/workspace/static/wdsans/WDesignSans-VF.otf'),
         ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
         ('OPPO', '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
         ('HOS', '/workspace/wdsans/ref/hos/hos-400.ttf')]


def dump(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
    gn = cm[ord(ch)]
    rp = DecomposingRecordingPen(gs); gs[gn].draw(rp)
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

    # 找所有「底部」边的 y 值分布
    ys = []
    for st, sg in C:
        for op, args in sg:
            for q in args:
                if hasattr(q, "__len__") and len(q)==2:
                    ys.append(q[1])
    ymin = min(ys) if ys else 0
    # 统计 y < ymin+10 的 x 范围（真正的最低边）
    lox = []
    for st, sg in C:
        for op, args in sg:
            for q in args:
                if hasattr(q, "__len__") and len(q)==2 and q[1] < ymin + 10:
                    lox.append(q[0])
    print('  %-5s %d轮廓  ymin=%.0f  最低边 x[%.0f,%.0f] 宽%.0f' % (
        lbl, len(C), ymin, min(lox), max(lox), max(lox)-min(lox)))
    # 打印每个轮廓的底部 y
    for i, (st, sg) in enumerate(C):
        py = [st[1]]
        px = [st[0]]
        for op, args in sg:
            for q in args:
                if hasattr(q, "__len__") and len(q)==2:
                    py.append(q[1]); px.append(q[0])
        print("       c%d  x[%4.0f,%4.0f] y[%4.0f,%4.0f]  %d段" % (
            i, min(px), max(px), min(py), max(py), len(sg)))


print('='*70)
print('【出】四家对比')
print('='*70)
for lbl, p in FONTS:
    dump(p, '出', lbl)