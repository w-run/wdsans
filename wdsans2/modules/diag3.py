#!/usr/bin/env python3
"""diag3 - 诊断 到 / 出 / 永 三处缺陷"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def dump(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
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
        sig = []
        for op, args in sg:
            for p in args: pts.append(np.array(p, float))
            sig.append("C" if op=="curveTo" else "Q" if op=="qCurveTo" else "L")
        P = np.array(pts)
        print("    c%-2d %-10s %d段 x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (
            i, "".join(sig), len(sg), P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))


for ch in '到出永':
    print("=" * 56)
    print("【%s】" % ch)
    dump(VF, ch, "我们")
    dump(SHS, ch, "SHS ")
    print()