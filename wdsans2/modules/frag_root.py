#!/usr/bin/env python3
"""frag_root - 查 嘴 底部碎块的几何根源，并逐阶段溯源"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen


def blk(path, ch, lbl, ymin=520, ymax=630):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    # 收集 y 区间内的轮廓
    cs = []
    cur = None
    for op, args in rp.value:
        if op == "moveTo":
            cur = [np.array(args[0], float)]
        elif op == "lineTo":
            cur.append(np.array(args[0], float))
        elif op == "curveTo":
            cur.extend([np.array(a, float) for a in args])
        elif op == "qCurveTo":
            cur.extend([np.array(a, float) for a in args])
        elif op == "closePath":
            if cur and len(cur) >= 3:
                cs.append(np.array(cur))
            cur = None
    if cur and len(cur) >= 3:
        cs.append(np.array(cur))
    print("  %s: %d 轮廓" % (lbl, len(cs)))
    for i, c in enumerate(cs):
        y0, y1 = c[:, 1].min(), c[:, 1].max()
        x0, x1 = c[:, 0].min(), c[:, 0].max()
        if y1 >= ymin and y0 <= ymax:
            print("    c%-2d x[%4.0f,%4.0f] y[%4.0f,%4.0f]  %d点" % (i, x0, x1, y0, y1, len(c)))


print("=== 嘴 底部区域 (y 520-630) ===")
STAGES = [('当前 VF', '/workspace/static/wdsans/WDesignSans-VF.otf'),
          ('SHS 原始', '/workspace/wdsans/ref/shs/shs-400.otf'),
          ('T6 基座', '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'),
          ('MOD', '/workspace/wdsans2/build/masters_MOD/master-Regular-400.otf'),
          ('R16', '/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'),
          ('R25', '/workspace/wdsans2/build/masters_R25/master-Regular-400.otf')]
for lbl, p in STAGES:
    if os.path.exists(p):
        blk(p, "嘴", lbl)
    else:
        print("  %s 不存在" % lbl)
    print()