#!/usr/bin/env python3
# dbg_ratio - why does every contour hit the ratio test?
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


def poly(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def area(P):
    x = P[:,0]; y = P[:,1]
    return 0.5*abs(float(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))))


f = TTFont('/workspace/wdsans2/build/masters_R30/master-Regular-400.otf', lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
for ch in "丁口日一十":
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C = contours_from_pen(rp.value)
    print("【%s】%d contours" % (ch, len(C)))
    for ci, c in enumerate(C):
        st = np.array(c["start"], float); e = endp(c["segs"][-1])
        gap = float(np.hypot(*(e-st)))
        A = area(poly(c))
        r = A/max(gap,1e-6)
        hit = "HIT" if (0.8 < gap < 12 and r > 1000) else "skip"
        print("   c%d segs=%d gap=%.1f area=%.0f ratio=%.0f  %s" % (ci, len(c["segs"]), gap, A, r, hit))
f.close()