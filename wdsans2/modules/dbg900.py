#!/usr/bin/env python3
"""dbg900 - 查 出 在 900 档的结构"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

f = TTFont('/workspace/wdsans2/build/masters_R27/master-Heavy-900.otf')
gs = f.getGlyphSet(); cm = f.getBestCmap()


def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for p in s[1]: P.append(np.array(p, float))
        elif s[0] == "C":
            P.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


for ch in "出屈拙咄础茁黜":
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C = contours_from_pen(rp.value)
    gx1 = max(allpts(c)[:,0].max() for c in C)
    gy0 = min(allpts(c)[:,1].min() for c in C)
    print("【%s】gx1=%.0f gy0=%.0f  %d轮廓" % (ch, gx1, gy0, len(C)))
    for i, c in enumerate(C):
        P = allpts(c)
        x0,x1 = P[:,0].min(), P[:,0].max()
        y0,y1 = P[:,1].min(), P[:,1].max()
        print("    c%d x[%4.0f,%4.0f] y[%4.0f,%4.0f] w=%3.0f h=%3.0f" % (i,x0,x1,y0,y1,x1-x0,y1-y0))
f.close()