#!/usr/bin/env python3
# vf_seam2 - check VF seams without full instantiation (use default master)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'


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


f = TTFont(VF, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
print("VF default instance (wght=400) seam scan:")
for ch in "永丁口日一十及":
    if ord(ch) not in cm:
        continue
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C = contours_from_pen(rp.value)
    seams = []
    for ci, c in enumerate(C):
        if len(c["segs"]) < 3:
            continue
        st = np.array(c["start"], float)
        gap = float(np.hypot(*(endp(c["segs"][-1]) - st)))
        if 0.8 < gap < 12 and area(poly(c))/max(gap,1e-6) > 1000:
            seams.append((ci, round(gap,1)))
    print("  %s: %d contours, seams=%s" % (ch, len(C), seams if seams else "NONE"))
f.close()