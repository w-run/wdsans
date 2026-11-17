#!/usr/bin/env python3
"""dbg_chu - 调试 出 的轮廓识别"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

f = TTFont('/workspace/wdsans2/build/masters_R27/master-Regular-400.otf')
gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("出")]].draw(rp); f.close()
C = contours_from_pen(rp.value)


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


print('轮廓数', len(C))
for i, c in enumerate(C):
    P = allpts(c)
    print("  c%d x[%4.0f,%4.0f] y[%4.0f,%4.0f] w=%3.0f h=%3.0f 段%d %s" % (
        i, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(),
        P[:,0].max()-P[:,0].min(), P[:,1].max()-P[:,1].min(),
        len(c["segs"]), "".join(s[0] for s in c["segs"])))
gx1 = max(allpts(c)[:,0].max() for c in C)
gy0 = min(allpts(c)[:,1].min() for c in C)
print("字形 gx1=%.0f gy0=%.0f" % (gx1, gy0))