#!/usr/bin/env python3
# repro_barple_duo - confirm barple ops on T6 多
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
SW = 77.0

f = TTFont(T6, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
C0 = contours_from_pen(rp.value)

def show(C, lbl):
    print(lbl)
    for ci, c in enumerate(C):
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
        sig = "".join(s[0] for s in c["segs"])
        if P[:,1].max() > 600 and P[:,0].max() > 700:
            print("   c%d %-18s x[%.0f,%.0f] y[%.0f,%.0f]" % (
                ci, sig[:18], P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    print()

show(C0, "T6 before:")
ops = m_barple.find(C0, SW)
print("barple ops:", len(ops))
for o in ops:
    print("   ", o)
if ops:
    C1 = m_barple.apply(C0, ops)
    show(C1, "after barple:")