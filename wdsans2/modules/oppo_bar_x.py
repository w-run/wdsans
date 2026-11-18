#!/usr/bin/env python3
# oppo_bar_x - OPPO 横笔右端 x 归一化 (x / glyph_width)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def bar_right(path, ch, qt=False):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None, None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    if qt:
        # OPPO: 二次曲线, 直接收集所有点
        xs = []; ys = []
        for op, args in rp.value:
            if op in ("moveTo","lineTo"):
                xs.append(args[0][0]); ys.append(args[0][1])
            elif op == "qCurveTo":
                for p in args:
                    if p: xs.append(p[0]); ys.append(p[1])
        if not xs: return None, None
        return max(xs), max(xs)-min(xs)
    C = contours_from_pen(rp.value)
    allx = []; ally = []
    for c in C:
        pts = [np.array(c["start"], float)]
        for s in c["segs"]:
            if s[0] == "QM":
                for q in s[1]: pts.append(np.array(q, float))
            elif s[0] == "C":
                pts.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
            elif s[0] == "Q":
                pts.extend([np.array(s[1],float), np.array(s[2],float)])
            else:
                pts.append(np.array(s[1], float))
        P = np.array(pts)
        allx.extend(P[:,0]); ally.extend(P[:,1])
    return max(allx), max(allx)-min(allx)

print("char  OPPO_x/ratio      R31_x/ratio       diff")
for ch in "多及力刀乃予了":
    ox, ow = bar_right("/workspace/wdsans/ref/ops/ops-400.ttf", ch, qt=True)
    rx, rw = bar_right("/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", ch)
    if not ox or not rx: continue
    orat = ox/ow; rrat = rx/rw
    print("%-4s %-12s %-12s %+.1f%%" % (ch,
        "%.0f/%.3f" % (ox, orat), "%.0f/%.3f" % (rx, rrat), (rrat-orat)*100))