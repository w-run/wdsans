#!/usr/bin/env python3
"""ledge_probe2 - 分析未被 m_ledge 覆盖的顶部横笔形态"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
NFLAT = 12


def contour_info(c, rp_idx):
    """返回 (段型, 段数, xmin, xmax, ymin, ymax, 顶部墨宽)"""
    from canonpen3 import contours_from_pen
    return None


def analyze(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    # 按 moveTo 切分轮廓
    cs = []
    cur = None
    ops = None
    for op, args in rp.value:
        if op == "moveTo":
            if cur:
                cs.append((cur, ops))
            cur = [np.array(args[0], float)]
            ops = []
        elif op == "lineTo":
            cur.append(np.array(args[0], float)); ops.append("L")
        elif op == "curveTo":
            cur.extend([np.array(a, float) for a in args]); ops.append("C")
        elif op == "qCurveTo":
            cur.extend([np.array(a, float) for a in args]); ops.append("Q")
        elif op == "closePath":
            if cur:
                cs.append((cur, ops))
            cur = None; ops = None
    if cur:
        cs.append((cur, ops))

    print("  %s: %d 轮廓" % (lbl, len(cs)))
    # 找全局 ymax
    gmax = max(max(p[1] for p in c[0]) for c in cs)
    for i, (c, o) in enumerate(cs):
        P = np.array(c)
        y0, y1 = P[:, 1].min(), P[:, 1].max()
        x0, x1 = P[:, 0].min(), P[:, 0].max()
        if y1 < gmax - 150:
            continue
        # 顶部 5 单位墨宽
        topmask = P[:, 1] > y1 - 5
        topx = P[topmask][:, 0]
        tw = topx.max() - topx.min() if len(topx) > 1 else 0
        sig = "".join(o)
        print("    c%-2d %-12s %2d段 x[%4.0f,%4.0f] y[%4.0f,%4.0f] 顶宽%4.0f" %
              (i, sig, len(o), x0, x1, y0, y1, tw))


print('=== 夏 麦 玫 玖 的顶部轮廓 ===')
for ch in '夏麦玫玖':
    analyze(VF, ch, "我们 " + ch)
    analyze("/workspace/wdsans/ref/hos/hos-400.ttf", ch, "HOS  " + ch)
    analyze("/workspace/wdsans/ref/ops4/OPPOSans4.ttf", ch, "OPPO " + ch)
    print()