#!/usr/bin/env python3
"""yan_c4 - 精确打印「眼」艮部撇轮廓 c4 的点"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

FONTS = [('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
         ('R15', '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'),
         ('R29', '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'),
         ('VF',  '/workspace/static/wdsans/WDesignSans-VF.otf')]


def endp(s):
    if s[0] == "QM": return np.array(s[1][-1], float)
    return np.array(s[-1], float)


for lbl, p in FONTS:
    f = TTFont(p, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = DecomposingRecordingPen(gs); gs[cm[ord("眼")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("【%s】" % lbl)
    for i, c in enumerate(C):
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
        # 只看底部右侧（艮的撇）
        if P[:,1].min() < 50 and P[:,0].min() > 380:
            print("  c%d %d段 x[%.0f,%.0f] y[%.0f,%.0f]" % (i, len(c["segs"]),
                P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
            print("     起点 (%.1f, %.1f)" % (c["start"][0], c["start"][1]))
            for k, s in enumerate(c["segs"]):
                if s[0] == "L":
                    print("       %d L -> (%.1f, %.1f)" % (k, s[1][0], s[1][1]))
                elif s[0] == "C":
                    print("       %d C c1(%.1f,%.1f) c2(%.1f,%.1f) -> (%.1f,%.1f)" % (
                        k, s[1][0],s[1][1], s[2][0],s[2][1], s[3][0],s[3][1]))
                elif s[0] == "Q":
                    print("       %d Q c(%.1f,%.1f) -> (%.1f,%.1f)" % (k, s[1][0],s[1][1], s[2][0],s[2][1]))
                elif s[0] == "QM":
                    print("       %d QM %s" % (k, [(round(q[0]),round(q[1])) for q in s[1]]))
    print()