#!/usr/bin/env python3
"""ledge_chk - 为什么 各 仍然偏短（m_ledge 声称已命中）"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen


def topbar(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    cs = []
    cur = None
    for op, args in rp.value:
        if op == "moveTo":
            if cur and len(cur) >= 3:
                cs.append(np.array(cur))
            cur = [np.array(args[0], float)]
        elif op == "lineTo":
            cur.append(np.array(args[0], float))
        elif op in ("curveTo", "qCurveTo"):
            cur.extend([np.array(a, float) for a in args])
        elif op == "closePath":
            if cur and len(cur) >= 3:
                cs.append(np.array(cur))
            cur = None
    if cur and len(cur) >= 3:
        cs.append(np.array(cur))
    gmax = max(c[:, 1].max() for c in cs)
    gx1 = np.vstack(cs)[:, 0].max()
    print("  %-10s %d轮廓 gmax=%.0f 右界=%.0f" % (lbl, len(cs), gmax, gx1))
    for i, c in enumerate(cs):
        x0, x1 = c[:, 0].min(), c[:, 0].max()
        y0, y1 = c[:, 1].min(), c[:, 1].max()
        if y1 < gmax - 180:
            continue
        pad = gx1 - x1
        print("    c%-2d x[%4.0f,%4.0f] y[%4.0f,%4.0f] 宽%4.0f 右余%4.0f" %
              (i, x0, x1, y0, y1, x1 - x0, pad))


print("=== 各 顶部横笔逐阶段 ===")
BASE = "/workspace/wdsans2/build/"
for lbl, p in [('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
               ('T6', BASE + 'masters_T6/master-Regular-400.otf'),
               ('MOD', BASE + 'masters_MOD/master-Regular-400.otf'),
               ('R6(ledge前)', BASE + 'masters_R6/master-Regular-400.otf'),
               ('R16(ledge后)', BASE + 'masters_R16/master-Regular-400.otf'),
               ('R25', BASE + 'masters_R25/master-Regular-400.otf'),
               ('VF', '/workspace/static/wdsans/WDesignSans-VF.otf')]:
    if os.path.exists(p):
        topbar(p, "各", lbl)
    else:
        print("  %s 不存在" % lbl)
print()
print("=== 食 顶部横笔 ===")
for lbl, p in [("SHS", "/workspace/wdsans/ref/shs/shs-400.otf"),
               ("R25", BASE + "masters_R25/master-Regular-400.otf"),
               ("VF", "/workspace/static/wdsans/WDesignSans-VF.otf")]:
    if os.path.exists(p):
        topbar(p, "食", lbl)