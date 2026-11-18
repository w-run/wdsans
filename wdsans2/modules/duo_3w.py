#!/usr/bin/env python3
# duo_3w - compare 多 contour structure at 250/400/900 + SHS counterparts
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R31/'
SETS = [('R31-250','master-ExtraLight-250.otf'), ('R31-400','master-Regular-400.otf'), ('R31-900','master-Heavy-900.otf')]
SH = [('SHS-250','/workspace/wdsans/ref/shs/shs-250.otf'), ('SHS-300','/workspace/wdsans/ref/shs/shs-300.otf'), ('SHS-400','/workspace/wdsans/ref/shs/shs-400.otf')]


def info(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s: %d contours ===" % (lbl, len(C)))
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
        print("   c%d %-16s x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (
            ci, sig[:16], P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    print()


for lbl, fn in SETS:
    info(B + fn, lbl)
for lbl, p in SH:
    info(p, lbl)