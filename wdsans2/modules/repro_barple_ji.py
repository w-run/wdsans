#!/usr/bin/env python3
# repro_barple_ji - replay m_barple on T6 及 to confirm it moves c3
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
SW = 77.0


def right_contours(C):
    out = []
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
        if P[:,0].max() > 500:
            out.append((i, len(c["segs"]), round(P[:,0].min()), round(P[:,0].max())))
    return out


f = TTFont(T6, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("及")]].draw(rp); f.close()
C0 = contours_from_pen(rp.value)
print("T6 before barple:", right_contours(C0))

ops = m_barple.find(C0, SW)
print("barple ops:", ops)
if ops:
    C1 = m_barple.apply(C0, ops)
    print("after barple:      ", right_contours(C1))