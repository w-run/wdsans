#!/usr/bin/env python3
"""dbg_san - 分析 散/形/几 的轮廓结构，找判据失效原因"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'


def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for p in s[1]: P.append(np.array(p, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


f = TTFont(R15, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
for ch in "散形几条极小":
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C = contours_from_pen(rp.value)
    gx1 = max(allpts(c)[:,0].max() for c in C)
    gy1 = max(allpts(c)[:,1].max() for c in C)
    print("【%s】gx1=%.0f gy1=%.0f  %d轮廓" % (ch, gx1, gy1, len(C)))
    for i, c in enumerate(C):
        P = allpts(c)
        sig = "".join(s[0] for s in c["segs"])
        print("    c%d x[%4.0f,%4.0f] y[%4.0f,%4.0f] 余%3.0f w=%3.0f h=%3.0f  %d%s" % (
            i, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(),
            gx1 - P[:,0].max(), P[:,0].max()-P[:,0].min(), P[:,1].max()-P[:,1].min(), len(c["segs"]), sig))
f.close()