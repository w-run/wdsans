#!/usr/bin/env python3
"""dao_probe - 查 到 顶部到底多出什么"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def dump(path, ch, lbl, ymin=650, ymax=850):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    parts = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None: parts.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None: parts.append((start, segs))
            start = None; segs = None
    if start is not None: parts.append((start, segs))
    print("  %s: %d 轮廓" % (lbl, len(parts)))
    for i, (st, sg) in enumerate(parts):
        pts = [np.array(st, float)]
        for op, args in sg:
            for p in args: pts.append(np.array(p, float))
        P = np.array(pts)
        if P[:,1].max() < ymin or P[:,1].min() > ymax:
            continue
        sig = "".join("C" if o=="curveTo" else "Q" if o=="qCurveTo" else "L" for o,_ in sg)
        print("    c%-2d %-9s %d段 x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (
            i, sig, len(sg), P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
        if len(P) <= 10:
            for k, q in enumerate(P):
                print("         p%d (%.1f, %.1f)" % (k, q[0], q[1]))


print('=== 到 顶部区域 y>=650 ===')
dump(VF, '到', '我们')
dump(SHS, '到', 'SHS')